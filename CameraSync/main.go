package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	lipgloss "charm.land/lipgloss/v2"
)

type compressionConfig struct {
	PromptAfterSync    bool    `json:"prompt_after_sync"`
	MinSizeMB          int     `json:"min_size_mb"`
	SegmentThresholdMB int     `json:"segment_threshold_mb"`
	SegmentDurationSec int     `json:"segment_duration_sec"`
	BitrateReduction   float64 `json:"bitrate_reduction"`
	AudioBitrateKbps   int     `json:"audio_bitrate_kbps"`
	SegmentWorkers     int     `json:"segment_workers"`
}

type config struct {
	Source      string            `json:"source"`
	Destination string            `json:"destination"`
	Workers     int               `json:"workers"`
	VideoExts   []string          `json:"video_extensions,omitempty"`
	PhotoExts   []string          `json:"photo_extensions,omitempty"`
	Compression compressionConfig `json:"compression"`
}

func defaultConfig() config {
	return config{
		Source:      "/Volumes/MicroSD/DCIM",
		Destination: "/Volumes/External",
		Workers:     8,
		Compression: compressionConfig{
			PromptAfterSync:    true,
			MinSizeMB:          100,
			SegmentThresholdMB: 1024,
			SegmentDurationSec: 30,
			BitrateReduction:   0.3,
			AudioBitrateKbps:   128,
			SegmentWorkers:     4,
		},
	}
}

func loadConfig(path string) (config, error) {
	cfg := defaultConfig()

	candidates := []string{path}
	if path == "" {
		candidates = []string{"config.json"}
		if home, err := os.UserHomeDir(); err == nil {
			candidates = append(candidates, filepath.Join(home, ".config", "camera-sync", "config.json"))
		}
	}

	for _, p := range candidates {
		if p == "" {
			continue
		}
		data, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		if err := json.Unmarshal(data, &cfg); err != nil {
			return cfg, fmt.Errorf("invalid config %s: %w", p, err)
		}
		lipgloss.Println(timestamp() + " " + dimStyle.Render("Loaded config:") + " " + valueStyle.Render(p))

		if len(cfg.VideoExts) > 0 {
			videoExts = make(map[string]bool)
			for _, ext := range cfg.VideoExts {
				videoExts[ext] = true
			}
		}
		if len(cfg.PhotoExts) > 0 {
			photoExts = make(map[string]bool)
			for _, ext := range cfg.PhotoExts {
				photoExts[ext] = true
			}
		}

		return cfg, nil
	}

	return cfg, nil
}

// prompt asks yes/no on stdin. Returns false if stdin is not a terminal.
func promptYesNo(question string, defaultYes bool) bool {
	// If stdin is not a terminal, don't block.
	fi, err := os.Stdin.Stat()
	if err != nil || (fi.Mode()&os.ModeCharDevice) == 0 {
		return defaultYes
	}

	suffix := " [y/N]: "
	if defaultYes {
		suffix = " [Y/n]: "
	}
	fmt.Print(question + suffix)
	reader := bufio.NewReader(os.Stdin)
	line, err := reader.ReadString('\n')
	if err != nil {
		return defaultYes
	}
	line = strings.ToLower(strings.TrimSpace(line))
	if line == "" {
		return defaultYes
	}
	return line == "y" || line == "yes"
}

func main() {
	// Subcommand: camera-sync install --source
	if len(os.Args) >= 2 && os.Args[1] == "install" {
		runInstall(os.Args[2:])
		return
	}

	configPath := flag.String("config", "", "path to config.json")
	srcFlag := flag.String("src", "", "source DCIM path (overrides config)")
	dstFlag := flag.String("dst", "", "destination base path (overrides config)")
	workersFlag := flag.Int("workers", 0, "number of concurrent copy workers (overrides config)")
	compressFlag := flag.Bool("compress", false, "compress after sync without prompting")
	noCompressFlag := flag.Bool("no-compress", false, "skip compression entirely")
	compressAllFlag := flag.Bool("compress-all", false, "skip sync; compress all videos on destination")
	compressFileFlag := flag.String("compress-file", "", "skip sync; compress a single file and exit")
	flag.Parse()

	cfg, err := loadConfig(*configPath)
	if err != nil {
		lipgloss.Fprintln(os.Stderr, errorStyle.Render("Error: "+err.Error()))
		os.Exit(1)
	}

	if *srcFlag != "" {
		cfg.Source = *srcFlag
	}
	if *dstFlag != "" {
		cfg.Destination = *dstFlag
	}
	if *workersFlag > 0 {
		cfg.Workers = *workersFlag
	}

	// Install Ctrl+C handler that cancels the shared context used by
	// long-running ffmpeg subprocesses in compress.go.
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Println()
		lipgloss.Println(warnStyle.Render("Interrupt received, cleaning up..."))
		cancel()
	}()

	lipgloss.Println(titleStyle.Render("Camera Sync"))

	// Mode: --compress-file <path>
	if *compressFileFlag != "" {
		lipgloss.Println(
			labelStyle.Render("  Mode:        ") + valueStyle.Render("compress-file"))
		lipgloss.Println(
			labelStyle.Render("  Target:      ") + valueStyle.Render(*compressFileFlag))
		fmt.Println()
		if err := runCompressFile(ctx, cfg, *compressFileFlag); err != nil {
			lipgloss.Fprintln(os.Stderr, errorStyle.Render("Error: "+err.Error()))
			os.Exit(1)
		}
		return
	}

	// Mode: --compress-all
	if *compressAllFlag {
		lipgloss.Println(
			labelStyle.Render("  Mode:        ") + valueStyle.Render("compress-all (backprop)"))
		lipgloss.Println(
			labelStyle.Render("  Destination: ") + valueStyle.Render(cfg.Destination))
		fmt.Println()
		if err := runCompressAll(ctx, cfg); err != nil {
			lipgloss.Fprintln(os.Stderr, errorStyle.Render("Error: "+err.Error()))
			os.Exit(1)
		}
		return
	}

	// Normal mode: sync, then optionally compress.
	lipgloss.Println(
		labelStyle.Render("  Source:      ") + valueStyle.Render(cfg.Source))
	lipgloss.Println(
		labelStyle.Render("  Destination: ") + valueStyle.Render(cfg.Destination))
	lipgloss.Println(
		labelStyle.Render("  Workers:     ") + valueStyle.Render(fmt.Sprintf("%d", cfg.Workers)))
	fmt.Println()

	sr, err := runSync(cfg)
	if err != nil {
		lipgloss.Fprintln(os.Stderr, errorStyle.Render("Error: "+err.Error()))
		os.Exit(1)
	}

	// Sync summary.
	divider := dividerStyle.Render(strings.Repeat("━", 50))
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Sync complete") + " " +
		dimStyle.Render(fmt.Sprintf("in %s", sr.elapsed)))
	fmt.Println()
	lipgloss.Println(labelStyle.Render("  Copied:  ") + copiedStyle.Render(fmt.Sprintf("%d", sr.copied)))
	lipgloss.Println(labelStyle.Render("  Skipped: ") + skippedStyle.Render(fmt.Sprintf("%d", sr.skipped)))
	lipgloss.Println(labelStyle.Render("  Failed:  ") + errorStyle.Render(fmt.Sprintf("%d", sr.failed)))
	lipgloss.Println(labelStyle.Render("  Total:   ") + valueStyle.Render(fmt.Sprintf("%d", sr.total)))
	fmt.Println()

	// Decide whether to run compression.
	if *noCompressFlag {
		if sr.failed > 0 {
			os.Exit(1)
		}
		return
	}

	if len(sr.copiedVideos) == 0 {
		if sr.failed > 0 {
			os.Exit(1)
		}
		return
	}

	eligible := filterBySize(sr.copiedVideos, int64(cfg.Compression.MinSizeMB)*1024*1024)
	if len(eligible) == 0 {
		lipgloss.Println(dimStyle.Render(fmt.Sprintf(
			"No videos above %d MB threshold — skipping compression.", cfg.Compression.MinSizeMB)))
		if sr.failed > 0 {
			os.Exit(1)
		}
		return
	}

	totalSize := totalBytes(eligible)
	lipgloss.Println(infoStyle.Render(fmt.Sprintf(
		"%d video(s) eligible for compression (%s total).",
		len(eligible), formatBytes(totalSize))))

	shouldCompress := *compressFlag
	if !shouldCompress {
		if cfg.Compression.PromptAfterSync {
			shouldCompress = promptYesNo("Compress now?", false)
		}
	}

	if !shouldCompress {
		lipgloss.Println(dimStyle.Render("Skipping compression."))
		if sr.failed > 0 {
			os.Exit(1)
		}
		return
	}

	fmt.Println()
	if err := runCompression(ctx, cfg, eligible); err != nil {
		lipgloss.Fprintln(os.Stderr, errorStyle.Render("Compression error: "+err.Error()))
		os.Exit(1)
	}

	if sr.failed > 0 {
		os.Exit(1)
	}
}

func filterBySize(paths []string, minBytes int64) []string {
	var out []string
	for _, p := range paths {
		info, err := os.Stat(p)
		if err != nil {
			continue
		}
		if info.Size() >= minBytes {
			out = append(out, p)
		}
	}
	return out
}

func totalBytes(paths []string) int64 {
	var total int64
	for _, p := range paths {
		if info, err := os.Stat(p); err == nil {
			total += info.Size()
		}
	}
	return total
}

// runInstall rebuilds the camera-sync binary from source and installs it
// to wherever the current binary lives on PATH.
//
// Usage: camera-sync install --source
//
// BOOTSTRAP: If the binary is broken and can't run this command, rebuild
// directly with the Go toolchain:
//
//	go build -o camera-sync .
//	sudo go build -o /usr/local/bin/camera-sync .
func runInstall(args []string) {
	fs := flag.NewFlagSet("install", flag.ExitOnError)
	source := fs.Bool("source", false, "rebuild from source (required)")
	fs.Parse(args)

	if !*source {
		fmt.Println("Usage: camera-sync install --source")
		fmt.Println("  Rebuilds and installs camera-sync from source.")
		return
	}

	wd, err := os.Getwd()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	if _, err := os.Stat(filepath.Join(wd, "go.mod")); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: not in the camera-sync source directory (no go.mod found in %s)\n", wd)
		os.Exit(1)
	}

	binName := "camera-sync"

	// Build to project directory.
	binPath := filepath.Join(wd, binName)
	fmt.Printf("Building %s from source...\n", binName)
	start := time.Now()

	buildCmd := exec.Command("go", "build", "-o", binPath, ".")
	buildCmd.Dir = wd
	buildCmd.Stdout = os.Stdout
	buildCmd.Stderr = os.Stderr
	if err := buildCmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Build failed: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Built %s in %s\n", binPath, time.Since(start).Round(time.Millisecond))

	// Find where the running binary lives on PATH and install there.
	// This handles /usr/local/bin, $GOPATH/bin, or wherever it was
	// originally installed. We build a second time instead of copying
	// because macOS quarantines copied binaries (com.apple.provenance
	// xattr), causing SIGKILL.
	installPath, err := exec.LookPath(binName)
	if err != nil {
		// Not on PATH yet — fall back to /usr/local/bin.
		installPath = filepath.Join("/usr/local/bin", binName)
	}
	// Resolve symlinks to get the real path.
	if resolved, err := filepath.EvalSymlinks(installPath); err == nil {
		installPath = resolved
	}

	fmt.Printf("Installing to %s...\n", installPath)
	pathCmd := exec.Command("go", "build", "-o", installPath, ".")
	pathCmd.Dir = wd
	pathCmd.Stdout = os.Stdout
	pathCmd.Stderr = os.Stderr
	if err := pathCmd.Run(); err != nil {
		// Permission denied — retry with sudo.
		fmt.Println("Permission denied, retrying with sudo...")
		sudoCmd := exec.Command("sudo", "go", "build", "-o", installPath, ".")
		sudoCmd.Dir = wd
		sudoCmd.Stdout = os.Stdout
		sudoCmd.Stderr = os.Stderr
		sudoCmd.Stdin = os.Stdin // allow password prompt
		if err := sudoCmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Install failed: %v\n", err)
			fmt.Fprintf(os.Stderr, "Manual fallback: sudo go build -o %s .\n", installPath)
			os.Exit(1)
		}
	}
	fmt.Printf("Installed to %s\n", installPath)
	fmt.Println("Done. Run 'camera-sync' to start.")
}
