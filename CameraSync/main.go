package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	lipgloss "charm.land/lipgloss/v2"
)

var (
	videoExts = map[string]bool{
		".mp4": true, ".mov": true, ".avi": true,
		".mkv": true, ".m4v": true, ".3gp": true,
	}
	photoExts = map[string]bool{
		".jpg": true, ".jpeg": true, ".png": true,
		".tiff": true, ".tif": true, ".heic": true, ".heif": true,
	}
)

// -- Styles --

var (
	hasDark = lipgloss.HasDarkBackground(os.Stdin, os.Stdout)
	ld      = lipgloss.LightDark(hasDark)

	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FF79C6")).
			PaddingBottom(1)

	labelStyle = lipgloss.NewStyle().
			Foreground(ld(lipgloss.Color("#555555"), lipgloss.Color("#888888")))

	valueStyle = lipgloss.NewStyle().
			Foreground(ld(lipgloss.Color("#333333"), lipgloss.Color("#FFFFFF")))

	successStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#50FA7B"))

	errorStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF5555")).
			Bold(true)

	warnStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFB86C"))

	dimStyle = lipgloss.NewStyle().
			Foreground(ld(lipgloss.Color("#999999"), lipgloss.Color("#666666")))

	infoStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#8BE9FD"))

	barFillStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#50FA7B"))

	barEmptyStyle = lipgloss.NewStyle().
			Foreground(ld(lipgloss.Color("#CCCCCC"), lipgloss.Color("#444444")))

	dividerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#BD93F9"))

	copiedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#50FA7B")).
			Bold(true)

	skippedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFB86C"))

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#BD93F9"))
)

type config struct {
	Source      string   `json:"source"`
	Destination string   `json:"destination"`
	Workers     int      `json:"workers"`
	VideoExts   []string `json:"video_extensions,omitempty"`
	PhotoExts   []string `json:"photo_extensions,omitempty"`
}

type mediaFile struct {
	path     string
	date     time.Time
	fileType string // "video" or "photo"
}

type copyResult struct {
	src     string
	dst     string
	copied  bool
	skipped bool
	err     error
}

type job struct {
	file  mediaFile
	index int
}

func timestamp() string {
	return dimStyle.Render(time.Now().Format("2006-01-02 15:04:05"))
}

func loadConfig(path string) (config, error) {
	cfg := config{
		Source:      "/Volumes/MicroSD/DCIM",
		Destination: "/Volumes/External",
		Workers:     8,
	}

	candidates := []string{path}
	if path == "" {
		candidates = []string{
			"config.json",
		}
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

func getFileDate(path string) (time.Time, error) {
	info, err := os.Stat(path)
	if err != nil {
		return time.Time{}, err
	}
	return info.ModTime(), nil
}

func daySuffix(day int) string {
	if day >= 10 && day <= 20 {
		return fmt.Sprintf("%dth", day)
	}
	switch day % 10 {
	case 1:
		return fmt.Sprintf("%dst", day)
	case 2:
		return fmt.Sprintf("%dnd", day)
	case 3:
		return fmt.Sprintf("%drd", day)
	default:
		return fmt.Sprintf("%dth", day)
	}
}

func buildDestPath(outputBase string, date time.Time, fileType string) string {
	year := fmt.Sprintf("%d", date.Year())
	month := date.Format("January")
	day := daySuffix(date.Day())

	if fileType == "photo" {
		return filepath.Join(outputBase, year, month, day, "photos")
	}
	return filepath.Join(outputBase, year, month, day)
}

func generateFilename(index int, date time.Time, fileType, ext string) string {
	return fmt.Sprintf("%s-%03d-%s%s", fileType, index, date.Format("2006-01-02"), ext)
}

func discoverMedia(dcimPath string) ([]mediaFile, error) {
	var files []mediaFile

	err := filepath.WalkDir(dcimPath, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			return nil
		}

		ext := strings.ToLower(filepath.Ext(path))
		var fileType string
		if videoExts[ext] {
			fileType = "video"
		} else if photoExts[ext] {
			fileType = "photo"
		} else {
			return nil
		}

		date, err := getFileDate(path)
		if err != nil {
			return nil
		}

		files = append(files, mediaFile{path: path, date: date, fileType: fileType})
		return nil
	})
	if err != nil {
		return nil, err
	}

	sort.Slice(files, func(i, j int) bool {
		return files[i].date.Before(files[j].date)
	})

	return files, nil
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return err
	}

	info, err := os.Stat(src)
	if err == nil {
		os.Chtimes(dst, info.ModTime(), info.ModTime())
	}

	return out.Close()
}

func processFile(outputBase string, mf mediaFile, index int) copyResult {
	destDir := buildDestPath(outputBase, mf.date, mf.fileType)
	ext := strings.ToLower(filepath.Ext(mf.path))
	filename := generateFilename(index, mf.date, mf.fileType, ext)
	destPath := filepath.Join(destDir, filename)

	if _, err := os.Stat(destPath); err == nil {
		return copyResult{src: mf.path, dst: destPath, skipped: true}
	}

	if err := os.MkdirAll(destDir, 0755); err != nil {
		return copyResult{src: mf.path, err: err}
	}

	if err := copyFile(mf.path, destPath); err != nil {
		return copyResult{src: mf.path, err: err}
	}

	return copyResult{src: mf.path, dst: destPath, copied: true}
}

func renderProgressBar(current, total int, width int, elapsed time.Duration) string {
	pct := float64(current) / float64(total)
	filled := int(pct * float64(width))
	if filled > width {
		filled = width
	}

	bar := barFillStyle.Render(strings.Repeat("█", filled)) +
		barEmptyStyle.Render(strings.Repeat("░", width-filled))

	pctStr := fmt.Sprintf("%3.0f%%", pct*100)

	// Calculate speed and ETA
	var speedStr, etaStr string
	if elapsed > 0 && current > 0 {
		speed := float64(current) / elapsed.Seconds()
		speedStr = fmt.Sprintf("%.1f file/s", speed)
		remaining := float64(total-current) / speed
		if remaining > 0 {
			etaStr = time.Duration(remaining * float64(time.Second)).Round(time.Second).String()
		} else {
			etaStr = "0s"
		}
	} else {
		speedStr = "-- file/s"
		etaStr = "--"
	}

	return fmt.Sprintf("Syncing: %s %s %s/%s [%s, %s]",
		headerStyle.Render(pctStr),
		bar,
		dimStyle.Render(fmt.Sprintf("%d", current)),
		dimStyle.Render(fmt.Sprintf("%d", total)),
		dimStyle.Render(etaStr),
		dimStyle.Render(speedStr),
	)
}

func main() {
	configPath := flag.String("config", "", "path to config.json")
	srcFlag := flag.String("src", "", "source DCIM path (overrides config)")
	dstFlag := flag.String("dst", "", "destination base path (overrides config)")
	workersFlag := flag.Int("workers", 0, "number of concurrent copy workers (overrides config)")
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

	// Header
	lipgloss.Println(titleStyle.Render("Camera Sync"))
	lipgloss.Println(
		labelStyle.Render("  Source:      ") + valueStyle.Render(cfg.Source))
	lipgloss.Println(
		labelStyle.Render("  Destination: ") + valueStyle.Render(cfg.Destination))
	lipgloss.Println(
		labelStyle.Render("  Workers:     ") + valueStyle.Render(fmt.Sprintf("%d", cfg.Workers)))
	fmt.Println()

	if _, err := os.Stat(cfg.Source); os.IsNotExist(err) {
		lipgloss.Fprintln(os.Stderr,
			errorStyle.Render("Error: source path does not exist: "+cfg.Source))
		os.Exit(1)
	}

	// Discovery
	lipgloss.Print(timestamp() + " " + infoStyle.Render("Discovering media files..."))
	discoverStart := time.Now()
	files, err := discoverMedia(cfg.Source)
	if err != nil {
		lipgloss.Fprintln(os.Stderr, "\n"+errorStyle.Render("Error scanning: "+err.Error()))
		os.Exit(1)
	}
	discoverElapsed := time.Since(discoverStart).Round(time.Millisecond)
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d files", len(files))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", discoverElapsed)))
	fmt.Println()

	if len(files) == 0 {
		lipgloss.Println(warnStyle.Render("No media files found."))
		return
	}

	// Group by date+type for per-day indexing
	type dayKey struct {
		date     string
		fileType string
	}
	groups := make(map[dayKey][]mediaFile)
	for _, f := range files {
		k := dayKey{date: f.date.Format("2006-01-02"), fileType: f.fileType}
		groups[k] = append(groups[k], f)
	}

	var jobs []job
	for _, group := range groups {
		for i, f := range group {
			jobs = append(jobs, job{file: f, index: i + 1})
		}
	}

	// Worker pool
	jobCh := make(chan job, len(jobs))
	resultCh := make(chan copyResult, len(jobs))
	var wg sync.WaitGroup

	for i := 0; i < cfg.Workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobCh {
				resultCh <- processFile(cfg.Destination, j.file, j.index)
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

	// Process results with per-file logging and progress bar
	var copied, skipped, failed atomic.Int32
	total := len(jobs)
	processed := 0
	syncStart := time.Now()
	var printMu sync.Mutex

	for r := range resultCh {
		processed++
		printMu.Lock()

		switch {
		case r.err != nil:
			failed.Add(1)
			// Clear progress bar line, print error, then re-render progress
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + errorStyle.Render("FAIL") + " " +
				dimStyle.Render(filepath.Base(r.src)) + " " + errorStyle.Render(r.err.Error()))
		case r.copied:
			copied.Add(1)
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + copiedStyle.Render("COPY") + " " +
				dimStyle.Render(r.src) + " " + dimStyle.Render("->") + " " + valueStyle.Render(r.dst))
		case r.skipped:
			skipped.Add(1)
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + skippedStyle.Render("SKIP") + " " +
				dimStyle.Render("File already exists:") + " " + valueStyle.Render(r.dst))
		}

		// Render progress bar
		elapsed := time.Since(syncStart)
		bar := renderProgressBar(processed, total, 30, elapsed)
		fmt.Print("\r" + bar)

		printMu.Unlock()
	}

	// Final progress bar at 100%
	elapsed := time.Since(syncStart)
	bar := renderProgressBar(total, total, 30, elapsed)
	fmt.Print("\r\033[K" + bar)
	fmt.Println()
	fmt.Println()

	// Summary
	totalElapsed := time.Since(discoverStart).Round(time.Millisecond)
	divider := dividerStyle.Render(strings.Repeat("━", 50))
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Sync complete") + " " +
		dimStyle.Render(fmt.Sprintf("in %s", totalElapsed)))
	fmt.Println()
	lipgloss.Println(labelStyle.Render("  Copied:  ") + copiedStyle.Render(fmt.Sprintf("%d", copied.Load())))
	lipgloss.Println(labelStyle.Render("  Skipped: ") + skippedStyle.Render(fmt.Sprintf("%d", skipped.Load())))
	lipgloss.Println(labelStyle.Render("  Failed:  ") + errorStyle.Render(fmt.Sprintf("%d", failed.Load())))
	lipgloss.Println(labelStyle.Render("  Total:   ") + valueStyle.Render(fmt.Sprintf("%d", total)))
	fmt.Println()

	if failed.Load() > 0 {
		os.Exit(1)
	}
}
