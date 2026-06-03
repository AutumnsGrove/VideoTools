package main

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"os"

	lipgloss "charm.land/lipgloss/v2"
)

// verifyStatus describes the state of a single source → destination mapping.
type verifyStatus int

const (
	verifyPass       verifyStatus = iota // destination matches source (identical size)
	verifyCompressed                     // destination is a valid compressed version
	verifyPlayable                       // video is playable (has duration) but unrecognized state
	verifyMissing                        // destination does not exist
	verifyEmpty                          // destination is 0 bytes (interrupted copy)
	verifyCorrupt                        // destination exists but is broken (size mismatch + not compressed + not playable)
	verifyTruncated                      // destination exists, wrong size, no compressed tag, but IS playable (partial?)
)

func (v verifyStatus) String() string {
	switch v {
	case verifyPass:
		return "PASS"
	case verifyCompressed:
		return "PASS"
	case verifyPlayable:
		return "PASS"
	case verifyMissing:
		return "MISSING"
	case verifyEmpty:
		return "EMPTY"
	case verifyCorrupt:
		return "CORRUPT"
	case verifyTruncated:
		return "TRUNCATED"
	default:
		return "UNKNOWN"
	}
}

// verifyResult holds the audit result for one source file.
type verifyResult struct {
	src       string
	dst       string
	srcSize   int64
	dstSize   int64
	status    verifyStatus
	detail    string // human-readable detail
	fileType  string // "video" or "photo"
}

// probeDuration runs a lightweight ffprobe to get the duration of a video file.
// Returns 0 if the file can't be probed or has no duration.
func probeDuration(path string) float64 {
	cmd := exec.Command("ffprobe",
		"-v", "quiet",
		"-print_format", "json",
		"-show_entries", "format=duration",
		path,
	)
	out, err := cmd.Output()
	if err != nil {
		return 0
	}
	var data struct {
		Format struct {
			Duration string `json:"duration"`
		} `json:"format"`
	}
	if err := json.Unmarshal(out, &data); err != nil {
		return 0
	}
	dur, _ := strconv.ParseFloat(data.Format.Duration, 64)
	return dur
}

// verifyFile checks whether a source file has a valid destination on the
// external drive. It never modifies anything.
func verifyFile(outputBase string, mf mediaFile, index int) verifyResult {
	destDir := buildDestPath(outputBase, mf.date, mf.fileType)
	ext := strings.ToLower(mf.path[strings.LastIndex(mf.path, "."):])
	filename := generateFilename(index, mf.date, mf.fileType, ext)
	destPath := destDir + "/" + filename

	srcInfo, err := os.Stat(mf.path)
	if err != nil {
		return verifyResult{src: mf.path, dst: destPath, status: verifyCorrupt,
			detail: "cannot stat source", fileType: mf.fileType}
	}

	res := verifyResult{
		src:      mf.path,
		dst:      destPath,
		srcSize:  srcInfo.Size(),
		fileType: mf.fileType,
	}

	dstInfo, err := os.Stat(destPath)
	if err != nil {
		res.status = verifyMissing
		res.detail = "not on external drive"
		return res
	}
	res.dstSize = dstInfo.Size()

	// 0-byte file — interrupted copy.
	if dstInfo.Size() == 0 {
		res.status = verifyEmpty
		res.detail = "0 bytes (interrupted copy)"
		return res
	}

	// Exact size match — perfect copy.
	if dstInfo.Size() == srcInfo.Size() {
		res.status = verifyPass
		res.detail = fmt.Sprintf("identical (%s)", formatBytes(srcInfo.Size()))
		return res
	}

	// Size mismatch — check if it's a valid compressed version.
	if isVideoPath(destPath) && checkCompressedTag(destPath) {
		ratio := float64(dstInfo.Size()) / float64(srcInfo.Size()) * 100
		res.status = verifyCompressed
		res.detail = fmt.Sprintf("compressed (%.0f%%, %s → %s)",
			ratio, formatBytes(srcInfo.Size()), formatBytes(dstInfo.Size()))
		return res
	}

	// Size mismatch, no compressed tag — probe to see if it's at least playable.
	if isVideoPath(destPath) {
		dur := probeDuration(destPath)
		if dur > 0 {
			res.status = verifyTruncated
			res.detail = fmt.Sprintf("playable but wrong size (src %s, dst %s, %.1fs)",
				formatBytes(srcInfo.Size()), formatBytes(dstInfo.Size()), dur)
			return res
		}
	}

	// For photos, size mismatch without further checks means corrupt.
	res.status = verifyCorrupt
	res.detail = fmt.Sprintf("size mismatch (src %s, dst %s)",
		formatBytes(srcInfo.Size()), formatBytes(dstInfo.Size()))
	return res
}

// verifyAudit holds the aggregated results of a full verification pass.
type verifyAudit struct {
	results  []verifyResult
	pass     int32
	fail     int32
	total    int
	elapsed  time.Duration
}

// runVerify performs a full aftercare audit: discovers all files on the source,
// maps each to its expected destination, and verifies integrity. Returns a
// non-nil error only for fatal issues (source missing, etc).
func runVerify(cfg config, workers int) (verifyAudit, error) {
	audit := verifyAudit{}
	start := time.Now()

	fmt.Println()
	lipgloss.Println(dividerStyle.Render(strings.Repeat("━", 50)))
	lipgloss.Println(headerStyle.Render("Aftercare Verification"))
	fmt.Println()

	if _, err := os.Stat(cfg.Source); os.IsNotExist(err) {
		lipgloss.Println(warnStyle.Render("Source not mounted — skipping verification."))
		return audit, nil
	}

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Discovering source files..."))
	files, err := discoverMedia(cfg.Source)
	if err != nil {
		return audit, fmt.Errorf("scanning source: %w", err)
	}
	discoverDur := time.Since(start).Round(time.Millisecond)
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d files", len(files))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", discoverDur)))
	fmt.Println()

	if len(files) == 0 {
		return audit, nil
	}

	// Group by date+type for per-day indexing (same logic as sync).
	type dayKey struct {
		date     string
		fileType string
	}
	groups := make(map[dayKey][]mediaFile)
	for _, f := range files {
		k := dayKey{date: f.date.Format("2006-01-02"), fileType: f.fileType}
		groups[k] = append(groups[k], f)
	}

	type verifyJob struct {
		file  mediaFile
		index int
	}

	var jobs []verifyJob
	for _, group := range groups {
		for i, f := range group {
			jobs = append(jobs, verifyJob{file: f, index: i + 1})
		}
	}

	jobCh := make(chan verifyJob, len(jobs))
	resultCh := make(chan verifyResult, len(jobs))
	var wg sync.WaitGroup

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobCh {
				resultCh <- verifyFile(cfg.Destination, j.file, j.index)
			}
		}()
	}

	for _, j := range jobs {
		jobCh <- j
	}
	close(jobCh)

	go func() {
		wg.Wait()
		close(resultCh)
	}()

	var pass, fail atomic.Int32
	total := len(jobs)
	processed := 0
	verifyStart := time.Now()
	var printMu sync.Mutex
	var allResults []verifyResult
	var failures []verifyResult

	for r := range resultCh {
		processed++
		printMu.Lock()

		allResults = append(allResults, r)

		switch r.status {
		case verifyPass, verifyCompressed, verifyPlayable:
			pass.Add(1)
			fmt.Print("\r\033[K")
			label := successStyle.Render("PASS")
			detail := dimStyle.Render(r.detail)
			lipgloss.Println(timestamp() + " " + label + " " + detail +
				" " + valueStyle.Render(r.dst))
		default:
			fail.Add(1)
			failures = append(failures, r)
			fmt.Print("\r\033[K")
			label := errorStyle.Render(r.status.String())
			detail := dimStyle.Render(r.detail)
			lipgloss.Println(timestamp() + " " + label + " " + detail +
				" " + valueStyle.Render(r.dst))
		}

		elapsed := time.Since(verifyStart)
		bar := renderSyncProgressBar(processed, total, 30, elapsed)
		bar = strings.Replace(bar, "Syncing:", "Auditing:", 1)
		fmt.Print("\r" + bar)

		printMu.Unlock()
	}

	elapsed := time.Since(verifyStart)
	bar := renderSyncProgressBar(total, total, 30, elapsed)
	bar = strings.Replace(bar, "Syncing:", "Auditing:", 1)
	fmt.Print("\r\033[K" + bar)
	fmt.Println()
	fmt.Println()

	// Summary.
	passCount := pass.Load()
	failCount := fail.Load()

	lipgloss.Println(labelStyle.Render("  Passed: ") + successStyle.Render(fmt.Sprintf("%d", passCount)))
	lipgloss.Println(labelStyle.Render("  Failed: ") + errorStyle.Render(fmt.Sprintf("%d", failCount)))
	lipgloss.Println(labelStyle.Render("  Total:  ") + valueStyle.Render(fmt.Sprintf("%d", total)))
	fmt.Println()

	if failCount > 0 {
		lipgloss.Println(errorStyle.Render("Files needing attention:"))
		fmt.Println()
		for _, f := range failures {
			lipgloss.Println("  " + errorStyle.Render(f.status.String()) + " " +
				dimStyle.Render(f.detail))
			lipgloss.Println("    " + dimStyle.Render("src: ") + valueStyle.Render(f.src))
			lipgloss.Println("    " + dimStyle.Render("dst: ") + valueStyle.Render(f.dst))
			fmt.Println()
		}
		lipgloss.Println(warnStyle.Render(fmt.Sprintf(
			"Run 'camera-sync' to re-sync the %d failed file(s).", failCount)))
	} else {
		lipgloss.Println(successStyle.Render("All files verified. Every source file is accounted for on the external drive."))
	}
	fmt.Println()

	audit.results = allResults
	audit.pass = passCount
	audit.fail = failCount
	audit.total = total
	audit.elapsed = time.Since(start).Round(time.Millisecond)
	return audit, nil
}
