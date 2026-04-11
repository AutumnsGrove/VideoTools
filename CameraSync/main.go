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

// loadConfig searches for config.json in order:
// 1. Path passed via -config flag
// 2. ./config.json (current directory)
// 3. ~/.config/camera-sync/config.json
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
		fmt.Printf("Loaded config: %s\n", p)

		// Apply custom extensions if provided
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

func main() {
	configPath := flag.String("config", "", "path to config.json")
	srcFlag := flag.String("src", "", "source DCIM path (overrides config)")
	dstFlag := flag.String("dst", "", "destination base path (overrides config)")
	workersFlag := flag.Int("workers", 0, "number of concurrent copy workers (overrides config)")
	flag.Parse()

	cfg, err := loadConfig(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		os.Exit(1)
	}

	// CLI flags override config values
	if *srcFlag != "" {
		cfg.Source = *srcFlag
	}
	if *dstFlag != "" {
		cfg.Destination = *dstFlag
	}
	if *workersFlag > 0 {
		cfg.Workers = *workersFlag
	}

	fmt.Printf("Camera Sync\n")
	fmt.Printf("  Source:      %s\n", cfg.Source)
	fmt.Printf("  Destination: %s\n", cfg.Destination)
	fmt.Printf("  Workers:     %d\n\n", cfg.Workers)

	if _, err := os.Stat(cfg.Source); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: source path does not exist: %s\n", cfg.Source)
		os.Exit(1)
	}

	fmt.Print("Discovering media files...")
	start := time.Now()
	files, err := discoverMedia(cfg.Source)
	if err != nil {
		fmt.Fprintf(os.Stderr, "\nError scanning: %s\n", err)
		os.Exit(1)
	}
	fmt.Printf(" found %d files (%s)\n\n", len(files), time.Since(start).Round(time.Millisecond))

	if len(files) == 0 {
		fmt.Println("No media files found.")
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

	var copied, skipped, failed atomic.Int32
	total := len(jobs)
	processed := 0

	for r := range resultCh {
		processed++
		switch {
		case r.err != nil:
			failed.Add(1)
			fmt.Fprintf(os.Stderr, "  \033[31m✗\033[0m %s: %s\n", filepath.Base(r.src), r.err)
		case r.copied:
			copied.Add(1)
		case r.skipped:
			skipped.Add(1)
		}
		fmt.Printf("\r  [%d/%d] copied: %d  skipped: %d  failed: %d",
			processed, total, copied.Load(), skipped.Load(), failed.Load())
	}

	elapsed := time.Since(start)
	fmt.Printf("\n\n%s\n", strings.Repeat("=", 50))
	fmt.Printf("Sync complete in %s\n", elapsed.Round(time.Millisecond))
	fmt.Printf("  Copied:  %d\n", copied.Load())
	fmt.Printf("  Skipped: %d\n", skipped.Load())
	fmt.Printf("  Failed:  %d\n", failed.Load())
	fmt.Printf("  Total:   %d\n", total)

	if failed.Load() > 0 {
		os.Exit(1)
	}
}
