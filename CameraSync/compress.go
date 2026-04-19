package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	lipgloss "charm.land/lipgloss/v2"
)

// probeInfo holds what we need about an input file.
type probeInfo struct {
	durationSec          float64
	bitrateBps           int64
	sizeBytes            int64
	videoCodec           string  // codec name of the main video stream (e.g. "h264", "hevc")
	frameRate            float64 // frames per second for the main video stream
	totalFrames          int64   // estimated total frames (from duration * frameRate)
	hasAttachedPic       bool
	attachedPicStreamIdx int
}

type compressionError struct {
	path  string
	stage string
	err   error
}

// -------- ffmpeg / ffprobe primitives --------

// detectEncoder chooses the best available H.265 encoder. Prefers hardware
// (VideoToolbox on Apple Silicon), falls back to libx265.
func detectEncoder() string {
	cmd := exec.Command("ffmpeg", "-hide_banner", "-encoders")
	out, err := cmd.CombinedOutput()
	if err == nil && strings.Contains(string(out), "hevc_videotoolbox") {
		return "hevc_videotoolbox"
	}
	return "libx265"
}

// probe reads format + stream metadata for a media file.
func probe(path string) (probeInfo, error) {
	cmd := exec.Command("ffprobe",
		"-v", "quiet",
		"-print_format", "json",
		"-show_format",
		"-show_streams",
		path,
	)
	out, err := cmd.Output()
	if err != nil {
		return probeInfo{}, fmt.Errorf("ffprobe failed: %w", err)
	}
	var data struct {
		Format struct {
			Duration string `json:"duration"`
			BitRate  string `json:"bit_rate"`
			Size     string `json:"size"`
		} `json:"format"`
		Streams []struct {
			Index        int            `json:"index"`
			CodecType    string         `json:"codec_type"`
			CodecName    string         `json:"codec_name"`
			Disposition  map[string]int `json:"disposition"`
			BitRate      string         `json:"bit_rate"`
			RFrameRate   string         `json:"r_frame_rate"`
			AvgFrameRate string         `json:"avg_frame_rate"`
			NbFrames     string         `json:"nb_frames"`
		} `json:"streams"`
	}
	if err := json.Unmarshal(out, &data); err != nil {
		return probeInfo{}, fmt.Errorf("ffprobe parse: %w", err)
	}

	info := probeInfo{attachedPicStreamIdx: -1}
	if data.Format.Duration != "" {
		info.durationSec, _ = strconv.ParseFloat(data.Format.Duration, 64)
	}
	if data.Format.BitRate != "" {
		info.bitrateBps, _ = strconv.ParseInt(data.Format.BitRate, 10, 64)
	}
	if data.Format.Size != "" {
		info.sizeBytes, _ = strconv.ParseInt(data.Format.Size, 10, 64)
	}

	// Fallback: sum video-stream bitrates (skipping attached_pic) if format bitrate absent.
	if info.bitrateBps == 0 {
		for _, s := range data.Streams {
			if s.CodecType != "video" {
				continue
			}
			if s.Disposition != nil && s.Disposition["attached_pic"] == 1 {
				continue
			}
			if s.BitRate != "" {
				br, _ := strconv.ParseInt(s.BitRate, 10, 64)
				info.bitrateBps += br
			}
		}
	}

	// Locate the main video stream (not attached_pic) to get frame rate / count,
	// and flag any attached_pic stream (DJI cover image) for later preservation.
	for _, s := range data.Streams {
		if s.CodecType != "video" {
			continue
		}
		isAttached := s.Disposition != nil && s.Disposition["attached_pic"] == 1
		if isAttached {
			info.hasAttachedPic = true
			info.attachedPicStreamIdx = s.Index
			continue
		}
		if info.videoCodec == "" {
			info.videoCodec = s.CodecName
		}
		if info.frameRate == 0 {
			info.frameRate = parseFraction(s.RFrameRate)
			if info.frameRate == 0 {
				info.frameRate = parseFraction(s.AvgFrameRate)
			}
			if s.NbFrames != "" {
				info.totalFrames, _ = strconv.ParseInt(s.NbFrames, 10, 64)
			}
		}
	}

	// Fall back to duration × fps if nb_frames wasn't reported.
	if info.totalFrames == 0 && info.frameRate > 0 && info.durationSec > 0 {
		info.totalFrames = int64(info.durationSec * info.frameRate)
	}

	return info, nil
}

// parseFraction parses "num/den" (e.g. "60000/1001") into a float.
func parseFraction(s string) float64 {
	if s == "" {
		return 0
	}
	parts := strings.SplitN(s, "/", 2)
	if len(parts) != 2 {
		v, _ := strconv.ParseFloat(s, 64)
		return v
	}
	num, err1 := strconv.ParseFloat(parts[0], 64)
	den, err2 := strconv.ParseFloat(parts[1], 64)
	if err1 != nil || err2 != nil || den == 0 {
		return 0
	}
	return num / den
}

// parseOutTime parses ffmpeg "HH:MM:SS.ffffff" to microseconds.
func parseOutTime(s string) int64 {
	parts := strings.Split(s, ":")
	if len(parts) != 3 {
		return 0
	}
	h, _ := strconv.Atoi(parts[0])
	m, _ := strconv.Atoi(parts[1])
	sParts := strings.Split(parts[2], ".")
	sec, _ := strconv.Atoi(sParts[0])
	var us int64
	if len(sParts) == 2 {
		frac := sParts[1]
		if len(frac) < 6 {
			frac = frac + strings.Repeat("0", 6-len(frac))
		} else if len(frac) > 6 {
			frac = frac[:6]
		}
		us, _ = strconv.ParseInt(frac, 10, 64)
	}
	return int64(h)*3600_000_000 + int64(m)*60_000_000 + int64(sec)*1_000_000 + us
}

// runFFmpegSilent runs ffmpeg with no progress output. Captures stderr tail on failure.
func runFFmpegSilent(ctx context.Context, args []string) error {
	cmd := exec.CommandContext(ctx, "ffmpeg", args...)
	var stderr bytes.Buffer
	cmd.Stdout = io.Discard
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		tail := strings.TrimSpace(stderr.String())
		lines := strings.Split(tail, "\n")
		if len(lines) > 3 {
			lines = lines[len(lines)-3:]
		}
		return fmt.Errorf("%w: %s", err, strings.Join(lines, " | "))
	}
	return nil
}

// runFFmpegWithProgress runs ffmpeg streaming -progress output to stdout and
// calling onProgress with (pct, mbps) as numbers update.
//
// Progress % is computed from whichever signal ffmpeg emits reliably: out_time
// when available (libx265), frame count when out_time is "N/A" (VideoToolbox).
func runFFmpegWithProgress(ctx context.Context, args []string, durationSec float64, totalFrames int64, onProgress func(pct, mbps float64)) error {
	cmd := exec.CommandContext(ctx, "ffmpeg", args...)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return err
	}
	var stderr bytes.Buffer
	cmd.Stderr = &stderr

	if err := cmd.Start(); err != nil {
		return err
	}

	done := make(chan struct{})
	go func() {
		defer close(done)
		scanner := bufio.NewScanner(stdout)
		scanner.Buffer(make([]byte, 64*1024), 1024*1024)
		var outTimeUs, totalSize, frameNum int64
		start := time.Now()
		for scanner.Scan() {
			line := scanner.Text()
			eq := strings.IndexByte(line, '=')
			if eq < 0 {
				continue
			}
			key, val := line[:eq], line[eq+1:]
			switch key {
			case "frame":
				if v, err := strconv.ParseInt(strings.TrimSpace(val), 10, 64); err == nil {
					frameNum = v
				}
			case "out_time_us":
				if val != "N/A" {
					if v, err := strconv.ParseInt(val, 10, 64); err == nil {
						outTimeUs = v
					}
				}
			case "out_time_ms":
				// ffmpeg emits microseconds here despite the name.
				if val != "N/A" && outTimeUs == 0 {
					if v, err := strconv.ParseInt(val, 10, 64); err == nil {
						outTimeUs = v
					}
				}
			case "out_time":
				if val != "N/A" && outTimeUs == 0 {
					outTimeUs = parseOutTime(val)
				}
			case "total_size":
				if v, err := strconv.ParseInt(val, 10, 64); err == nil {
					totalSize = v
				}
			case "progress":
				elapsed := time.Since(start).Seconds()
				pct := 0.0
				// Prefer time-based progress when available, else fall back to frames.
				if outTimeUs > 0 && durationSec > 0 {
					pct = float64(outTimeUs) / 1e6 / durationSec
				} else if totalFrames > 0 && frameNum > 0 {
					pct = float64(frameNum) / float64(totalFrames)
				}
				if pct > 1 {
					pct = 1
				}
				mbps := 0.0
				if elapsed > 0 {
					mbps = float64(totalSize) / elapsed
				}
				onProgress(pct, mbps)
				if val == "end" {
					return
				}
			}
		}
	}()

	waitErr := cmd.Wait()
	<-done
	if waitErr != nil {
		tail := strings.TrimSpace(stderr.String())
		lines := strings.Split(tail, "\n")
		if len(lines) > 3 {
			lines = lines[len(lines)-3:]
		}
		return fmt.Errorf("%w: %s", waitErr, strings.Join(lines, " | "))
	}
	return nil
}

// -------- Top-level compression runners --------

// runCompression compresses a list of file paths in place.
func runCompression(ctx context.Context, cfg config, paths []string) error {
	encoder := detectEncoder()

	lipgloss.Println(labelStyle.Render("  Encoder:     ") + valueStyle.Render(encoder) + " " +
		dimStyle.Render(ternaryStr(encoder == "libx265", "(software)", "(VideoToolbox hardware)")))
	lipgloss.Println(labelStyle.Render("  Bitrate:     ") + valueStyle.Render(
		fmt.Sprintf("%.0f%% of original", cfg.Compression.BitrateReduction*100)))
	lipgloss.Println(labelStyle.Render("  Segment ≥:   ") + valueStyle.Render(
		fmt.Sprintf("%d MB (%ds chunks × %d parallel)",
			cfg.Compression.SegmentThresholdMB,
			cfg.Compression.SegmentDurationSec,
			cfg.Compression.SegmentWorkers)))
	fmt.Println()

	start := time.Now()
	var errors []compressionError
	var totalOrig, totalAfter int64

	for i, p := range paths {
		select {
		case <-ctx.Done():
			lipgloss.Println(warnStyle.Render("Compression cancelled."))
			return nil
		default:
		}

		origInfo, err := os.Stat(p)
		if err != nil {
			errors = append(errors, compressionError{path: p, stage: "stat", err: err})
			continue
		}
		totalOrig += origInfo.Size()

		newSize, stage, err := compressOne(ctx, cfg, p, encoder, i+1, len(paths))
		if err != nil {
			errors = append(errors, compressionError{path: p, stage: stage, err: err})
			totalAfter += origInfo.Size() // original kept, so after = before
			continue
		}
		totalAfter += newSize
	}

	// Summary
	fmt.Println()
	divider := dividerStyle.Render(strings.Repeat("━", 50))
	lipgloss.Println(divider)
	elapsed := time.Since(start).Round(time.Second)
	lipgloss.Println(headerStyle.Render("Compression complete") + " " +
		dimStyle.Render(fmt.Sprintf("in %s", elapsed)))
	fmt.Println()
	done := len(paths) - len(errors)
	lipgloss.Println(labelStyle.Render("  Compressed: ") + copiedStyle.Render(
		fmt.Sprintf("%d/%d", done, len(paths))))
	lipgloss.Println(labelStyle.Render("  Before:     ") + valueStyle.Render(formatBytes(totalOrig)))
	lipgloss.Println(labelStyle.Render("  After:      ") + valueStyle.Render(formatBytes(totalAfter)))
	saved := totalOrig - totalAfter
	if saved > 0 && totalOrig > 0 {
		pct := float64(saved) / float64(totalOrig) * 100
		lipgloss.Println(labelStyle.Render("  Saved:      ") + copiedStyle.Render(
			fmt.Sprintf("%s (%.1f%%)", formatBytes(saved), pct)))
	}
	fmt.Println()

	if len(errors) > 0 {
		lipgloss.Println(errorStyle.Render(fmt.Sprintf("Failed: %d file(s)", len(errors))))
		for _, e := range errors {
			lipgloss.Println("  " + errorStyle.Render("✗") + " " +
				valueStyle.Render(filepath.Base(e.path)) + " " +
				dimStyle.Render(fmt.Sprintf("[%s]", e.stage)) + " " +
				dimStyle.Render(e.err.Error()))
		}
		fmt.Println()
		lipgloss.Println(dimStyle.Render("  Retry one file: ") + valueStyle.Render("camera-sync --compress-file <path>"))
	}

	return nil
}

// runCompressFile compresses a single file path (for retry after errors).
func runCompressFile(ctx context.Context, cfg config, path string) error {
	if _, err := os.Stat(path); err != nil {
		return fmt.Errorf("file not found: %w", err)
	}
	return runCompression(ctx, cfg, []string{path})
}

// runCompressAll walks the given root tree and compresses all videos >= min size,
// skipping files that are already HEVC-encoded or have low enough bitrate.
func runCompressAll(ctx context.Context, cfg config, root string) error {
	var allVideos []string
	minBytes := int64(cfg.Compression.MinSizeMB) * 1024 * 1024

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Scanning destination for video files..."))
	scanStart := time.Now()
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			// Skip hidden dirs (our .compress-* work dirs).
			if d.Name() != filepath.Base(root) && strings.HasPrefix(d.Name(), ".") {
				return filepath.SkipDir
			}
			return nil
		}
		if !isVideoPath(path) {
			return nil
		}
		info, err := os.Stat(path)
		if err != nil {
			return nil
		}
		if info.Size() >= minBytes {
			allVideos = append(allVideos, path)
		}
		return nil
	})
	if err != nil {
		return err
	}
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d candidates", len(allVideos))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", time.Since(scanStart).Round(time.Millisecond))))

	if len(allVideos) == 0 {
		lipgloss.Println(dimStyle.Render(fmt.Sprintf("No videos ≥ %d MB found.", cfg.Compression.MinSizeMB)))
		return nil
	}

	// Probe each file to check if already compressed.
	lipgloss.Print(timestamp() + " " + infoStyle.Render("Probing codecs..."))
	var eligible []string
	var skippedCount int
	for _, path := range allVideos {
		compressed, _, _, err := isAlreadyCompressed(path, cfg)
		if err != nil {
			skippedCount++
			continue
		}
		if compressed {
			skippedCount++
			continue
		}
		eligible = append(eligible, path)
	}
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("%d to compress", len(eligible))) +
		dimStyle.Render(fmt.Sprintf(", %d already compressed", skippedCount)))
	fmt.Println()

	if len(eligible) == 0 {
		lipgloss.Println(dimStyle.Render("All videos are already compressed."))
		return nil
	}

	// Sort by size descending so big wins come first (user visibility).
	sort.Slice(eligible, func(i, j int) bool {
		si, _ := os.Stat(eligible[i])
		sj, _ := os.Stat(eligible[j])
		return si.Size() > sj.Size()
	})

	totalSize := totalBytes(eligible)
	lipgloss.Println(infoStyle.Render(fmt.Sprintf(
		"%d video(s) to compress (%s total).", len(eligible), formatBytes(totalSize))))

	if !promptYesNo("Proceed?", false) {
		lipgloss.Println(dimStyle.Render("Cancelled."))
		return nil
	}
	fmt.Println()

	return runCompression(ctx, cfg, eligible)
}

// isAlreadyCompressed probes a video and returns true if it's already HEVC
// (our compression target codec) or if its bitrate is already at/below the
// target we'd set. Returns (compressed, codec, bitrateBps, error).
func isAlreadyCompressed(path string, cfg config) (bool, string, int64, error) {
	info, err := probe(path)
	if err != nil {
		return false, "", 0, err
	}
	codec := info.videoCodec
	// Already HEVC — we compressed this.
	if codec == "hevc" || codec == "h265" {
		return true, codec, info.bitrateBps, nil
	}
	// Bitrate already at or below what we'd target — no meaningful gain.
	targetBps := int64(float64(info.bitrateBps) * cfg.Compression.BitrateReduction)
	if targetBps < 500_000 {
		return true, codec, info.bitrateBps, nil
	}
	return false, codec, info.bitrateBps, nil
}

// runCompressDir walks a directory and compresses all uncompressed videos in it.
func runCompressDir(ctx context.Context, cfg config, dir string) error {
	minBytes := int64(cfg.Compression.MinSizeMB) * 1024 * 1024

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Scanning directory for video files..."))
	scanStart := time.Now()

	var allVideos []string
	err := filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			// Skip hidden dirs (our .compress-* work dirs).
			if d.Name() != filepath.Base(dir) && strings.HasPrefix(d.Name(), ".") {
				return filepath.SkipDir
			}
			return nil
		}
		if !isVideoPath(path) {
			return nil
		}
		info, err := os.Stat(path)
		if err != nil {
			return nil
		}
		if info.Size() >= minBytes {
			allVideos = append(allVideos, path)
		}
		return nil
	})
	if err != nil {
		return err
	}
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d video(s)", len(allVideos))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", time.Since(scanStart).Round(time.Millisecond))))

	if len(allVideos) == 0 {
		lipgloss.Println(dimStyle.Render(fmt.Sprintf("No videos ≥ %d MB found in %s.", cfg.Compression.MinSizeMB, dir)))
		return nil
	}

	// Probe each file to check if already compressed.
	lipgloss.Print(timestamp() + " " + infoStyle.Render("Probing codecs..."))
	var eligible []string
	var skippedCount int
	for _, path := range allVideos {
		compressed, _, _, err := isAlreadyCompressed(path, cfg)
		if err != nil {
			// Can't probe — skip it.
			skippedCount++
			continue
		}
		if compressed {
			skippedCount++
			continue
		}
		eligible = append(eligible, path)
	}
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("%d to compress", len(eligible))) +
		dimStyle.Render(fmt.Sprintf(", %d already compressed", skippedCount)))
	fmt.Println()

	if len(eligible) == 0 {
		lipgloss.Println(dimStyle.Render("All videos in this directory are already compressed."))
		return nil
	}

	// Sort by size descending.
	sort.Slice(eligible, func(i, j int) bool {
		si, _ := os.Stat(eligible[i])
		sj, _ := os.Stat(eligible[j])
		return si.Size() > sj.Size()
	})

	totalSize := totalBytes(eligible)
	lipgloss.Println(infoStyle.Render(fmt.Sprintf(
		"%d video(s) eligible for compression (%s total).", len(eligible), formatBytes(totalSize))))

	if !promptYesNo("Compress now?", false) {
		lipgloss.Println(dimStyle.Render("Cancelled."))
		return nil
	}
	fmt.Println()

	return runCompression(ctx, cfg, eligible)
}

// -------- Per-file compression --------

// compressOne compresses one file in place. Returns (final_size_after, stage_on_err, err).
// If the compressed output would not save space, the original is preserved and an
// error with stage="verify" is returned.
func compressOne(ctx context.Context, cfg config, srcPath, encoder string, idx, total int) (int64, string, error) {
	info, err := probe(srcPath)
	if err != nil {
		return 0, "probe", err
	}
	if info.durationSec <= 0 {
		return 0, "probe", fmt.Errorf("invalid duration")
	}

	origStat, err := os.Stat(srcPath)
	if err != nil {
		return 0, "stat", err
	}
	origSize := origStat.Size()

	// Target bitrate: reduction fraction of original (total bitrate).
	targetKbps := int(float64(info.bitrateBps) / 1000.0 * cfg.Compression.BitrateReduction)
	if targetKbps < 500 {
		targetKbps = 500
	}
	audioKbps := cfg.Compression.AudioBitrateKbps
	if audioKbps <= 0 {
		audioKbps = 128
	}

	// Workspace alongside the source file (same filesystem → atomic rename).
	workDir, err := os.MkdirTemp(filepath.Dir(srcPath), ".compress-")
	if err != nil {
		return 0, "setup", err
	}
	defer os.RemoveAll(workDir)

	outTemp := filepath.Join(workDir, "output.mp4")
	filename := filepath.Base(srcPath)

	// Print header for this file.
	compressMu.Lock()
	fmt.Print("\r\033[K")
	lipgloss.Println(timestamp() + " " + compressStyle.Render("COMPRESS") + " " +
		valueStyle.Render(filename) + " " +
		dimStyle.Render(fmt.Sprintf("(%s · %.0f kbps → %d kbps, audio %d kbps)",
			formatBytes(origSize), float64(info.bitrateBps)/1000, targetKbps, audioKbps)))
	compressMu.Unlock()

	segmentThresholdBytes := int64(cfg.Compression.SegmentThresholdMB) * 1024 * 1024

	onProgress := func(stage string, pct, mbps float64) {
		compressMu.Lock()
		defer compressMu.Unlock()
		fmt.Print("\r\033[K" + renderCompressLine(idx, total, filename, origSize, stage, pct, mbps, 20))
	}

	if origSize < segmentThresholdBytes {
		onProgress("compressing", 0, 0)
		err := compressDirect(ctx, srcPath, outTemp, encoder, targetKbps, audioKbps, info, func(pct, mbps float64) {
			onProgress("compressing", pct, mbps)
		})
		if err != nil {
			fmt.Print("\r\033[K")
			return 0, "compress", err
		}
	} else {
		if err := compressSegmented(ctx, cfg, srcPath, outTemp, encoder, targetKbps, audioKbps, info, func(stage string, pct, mbps float64) {
			onProgress(stage, pct, mbps)
		}); err != nil {
			fmt.Print("\r\033[K")
			return 0, "compress", err
		}
	}

	// Verify output
	onProgress("verifying", 1, 0)
	newInfo, err := probe(outTemp)
	if err != nil {
		fmt.Print("\r\033[K")
		return 0, "verify", fmt.Errorf("probe output: %w", err)
	}
	if diff := newInfo.durationSec - info.durationSec; diff > 1.0 || diff < -1.0 {
		fmt.Print("\r\033[K")
		return 0, "verify", fmt.Errorf("duration mismatch: %.2fs → %.2fs", info.durationSec, newInfo.durationSec)
	}
	newStat, err := os.Stat(outTemp)
	if err != nil {
		fmt.Print("\r\033[K")
		return 0, "verify", err
	}
	if newStat.Size() >= int64(float64(origSize)*0.95) {
		fmt.Print("\r\033[K")
		return 0, "verify", fmt.Errorf("no meaningful gain (%s → %s); keeping original",
			formatBytes(origSize), formatBytes(newStat.Size()))
	}

	// Preserve original mtime on the replacement.
	_ = os.Chtimes(outTemp, origStat.ModTime(), origStat.ModTime())

	// Atomic replace.
	if err := os.Rename(outTemp, srcPath); err != nil {
		fmt.Print("\r\033[K")
		return 0, "replace", err
	}

	// Clear progress line and print final summary for this file.
	compressMu.Lock()
	fmt.Print("\r\033[K")
	saved := origSize - newStat.Size()
	pct := float64(saved) / float64(origSize) * 100
	lipgloss.Println(timestamp() + " " + copiedStyle.Render("DONE    ") + " " +
		valueStyle.Render(filename) + " " +
		dimStyle.Render(fmt.Sprintf("%s → %s", formatBytes(origSize), formatBytes(newStat.Size()))) + " " +
		successStyle.Render(fmt.Sprintf("(-%.1f%%)", pct)))
	compressMu.Unlock()

	return newStat.Size(), "", nil
}

// compressDirect re-encodes the whole file in a single ffmpeg call.
// Preserves the MJPEG cover-image stream (attached_pic) via `-map 0:v` while
// excluding DJI's proprietary `djmd`/`dbgi` data streams that the MP4 muxer
// cannot write (their codec is reported as "none"). Audio is re-encoded to
// AAC at audioKbps; the attached_pic stream is stream-copied untouched.
func compressDirect(ctx context.Context, src, dst, encoder string, videoKbps, audioKbps int, info probeInfo, onProgress func(pct, mbps float64)) error {
	args := []string{
		"-hide_banner", "-nostats",
		"-i", src,
		"-map", "0:v",
		"-map", "0:a?",
		"-c", "copy",
		"-c:v:0", encoder,
		"-tag:v:0", "hvc1",
		"-b:v:0", fmt.Sprintf("%dk", videoKbps),
		"-c:a", "aac",
		"-b:a", fmt.Sprintf("%dk", audioKbps),
		"-movflags", "+faststart",
		"-progress", "pipe:1",
		"-y",
		dst,
	}
	return runFFmpegWithProgress(ctx, args, info.durationSec, info.totalFrames, onProgress)
}

// compressSegmented handles files above the segment threshold.
//
// Strategy:
//  1. Split main video + audio into N-second segments (stream copy, no re-encode).
//  2. Compress each segment in parallel (just video+audio).
//  3. Concat compressed segments (stream copy).
//  4. Re-mux with the original's extra streams (attached_pic cover image, data
//     streams, timecode, format metadata) so macOS Finder still shows the cover
//     and DJI metadata survives.
func compressSegmented(ctx context.Context, cfg config, src, dst, encoder string, videoKbps, audioKbps int, info probeInfo, onProgress func(stage string, pct, mbps float64)) error {
	workDir := filepath.Dir(dst)

	// Step 1 — split.
	onProgress("segmenting", 0, 0)
	rawPattern := filepath.Join(workDir, "raw_%04d.mp4")
	splitArgs := []string{
		"-hide_banner", "-nostats",
		"-i", src,
		"-map", "0:v:0",
		"-map", "0:a?",
		"-c", "copy",
		"-f", "segment",
		"-segment_time", fmt.Sprintf("%d", cfg.Compression.SegmentDurationSec),
		"-reset_timestamps", "1",
		"-y",
		rawPattern,
	}
	if err := runFFmpegSilent(ctx, splitArgs); err != nil {
		return fmt.Errorf("split: %w", err)
	}
	rawSegments, err := filepath.Glob(filepath.Join(workDir, "raw_*.mp4"))
	if err != nil {
		return fmt.Errorf("glob raw segments: %w", err)
	}
	sort.Strings(rawSegments)
	if len(rawSegments) == 0 {
		return fmt.Errorf("no segments produced")
	}

	// Step 2 — compress segments in parallel.
	compressed := make([]string, len(rawSegments))
	var completed atomic.Int32
	var bytesWritten atomic.Int64
	compressStart := time.Now()
	totalSegs := int32(len(rawSegments))

	workers := cfg.Compression.SegmentWorkers
	if workers < 1 {
		workers = 2
	}
	if workers > len(rawSegments) {
		workers = len(rawSegments)
	}

	type segJob struct {
		idx  int
		path string
	}
	jobs := make(chan segJob)
	errCh := make(chan error, len(rawSegments))
	var wg sync.WaitGroup

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				outPath := filepath.Join(workDir, fmt.Sprintf("comp_%04d.mp4", j.idx))
				args := []string{
					"-hide_banner", "-nostats",
					"-i", j.path,
					"-map", "0:v:0",
					"-map", "0:a?",
					"-c:v:0", encoder,
					"-tag:v:0", "hvc1",
					"-b:v:0", fmt.Sprintf("%dk", videoKbps),
					"-c:a", "aac",
					"-b:a", fmt.Sprintf("%dk", audioKbps),
					"-y",
					outPath,
				}
				if err := runFFmpegSilent(ctx, args); err != nil {
					errCh <- fmt.Errorf("segment %d: %w", j.idx, err)
					return
				}
				if st, e := os.Stat(outPath); e == nil {
					bytesWritten.Add(st.Size())
				}
				compressed[j.idx] = outPath
				done := completed.Add(1)
				elapsed := time.Since(compressStart).Seconds()
				var mbps float64
				if elapsed > 0 {
					mbps = float64(bytesWritten.Load()) / elapsed
				}
				onProgress("compressing", float64(done)/float64(totalSegs), mbps)
			}
		}()
	}

	for i, p := range rawSegments {
		select {
		case <-ctx.Done():
			close(jobs)
			wg.Wait()
			return ctx.Err()
		case jobs <- segJob{idx: i, path: p}:
		}
	}
	close(jobs)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		if err != nil {
			return err
		}
	}

	// Step 3 — concat.
	onProgress("concatenating", 1, 0)
	concatPath := filepath.Join(workDir, "concat.mp4")
	listPath := filepath.Join(workDir, "concat_list.txt")
	lf, err := os.Create(listPath)
	if err != nil {
		return fmt.Errorf("concat list: %w", err)
	}
	for _, s := range compressed {
		escaped := strings.ReplaceAll(s, "'", "'\\''")
		fmt.Fprintf(lf, "file '%s'\n", escaped)
	}
	lf.Close()

	concatArgs := []string{
		"-hide_banner", "-nostats",
		"-f", "concat",
		"-safe", "0",
		"-i", listPath,
		"-map", "0:v",
		"-map", "0:a?",
		"-c", "copy",
		"-y",
		concatPath,
	}
	if err := runFFmpegSilent(ctx, concatArgs); err != nil {
		return fmt.Errorf("concat: %w", err)
	}

	// Step 4 — re-mux with original's cover-image stream + format metadata.
	// DJI djmd/dbgi data streams are dropped — MP4 muxer can't write them.
	onProgress("muxing", 1, 0)
	muxArgs := []string{
		"-hide_banner", "-nostats",
		"-i", concatPath,
		"-i", src,
		"-map", "0:v:0",
		"-map", "0:a?",
	}
	if info.hasAttachedPic {
		muxArgs = append(muxArgs, "-map", fmt.Sprintf("1:%d", info.attachedPicStreamIdx))
	}
	muxArgs = append(muxArgs,
		"-map_metadata", "1",
		"-c", "copy",
		"-tag:v:0", "hvc1",
		"-movflags", "+faststart",
	)
	if info.hasAttachedPic {
		// Output video stream index 1 is the attached_pic.
		muxArgs = append(muxArgs, "-disposition:v:1", "attached_pic")
	}
	muxArgs = append(muxArgs, "-y", dst)

	if err := runFFmpegSilent(ctx, muxArgs); err != nil {
		return fmt.Errorf("final mux: %w", err)
	}
	return nil
}

// -------- Helpers --------

var compressMu sync.Mutex // serialize terminal writes during compression

func ternaryStr(cond bool, a, b string) string {
	if cond {
		return a
	}
	return b
}
