package main

import (
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

// syncResult summarizes a sync run and returns the paths of the video files that
// were copied (not skipped), for downstream compression.
type syncResult struct {
	copied         int32
	skipped        int32
	failed         int32
	total          int
	elapsed        time.Duration
	copiedVideos   []string // destination paths of video files that were actually copied this run
	discoverStart  time.Time
	totalDiscover  time.Duration
}

// runSync performs discovery and the copy phase. It returns the paths of video
// files that were newly copied this session.
func runSync(cfg config) (syncResult, error) {
	res := syncResult{discoverStart: time.Now()}

	if _, err := os.Stat(cfg.Source); os.IsNotExist(err) {
		return res, fmt.Errorf("source path does not exist: %s", cfg.Source)
	}

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Discovering media files..."))
	files, err := discoverMedia(cfg.Source)
	if err != nil {
		return res, fmt.Errorf("scanning: %w", err)
	}
	res.totalDiscover = time.Since(res.discoverStart).Round(time.Millisecond)
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d files", len(files))) +
		" " + dimStyle.Render(fmt.Sprintf("(%s)", res.totalDiscover)))
	fmt.Println()

	if len(files) == 0 {
		lipgloss.Println(warnStyle.Render("No media files found."))
		return res, nil
	}

	// Group by date+type for per-day indexing.
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
	syncStart := time.Now()
	var printMu sync.Mutex
	var copiedVideos []string

	for r := range resultCh {
		processed++
		printMu.Lock()

		switch {
		case r.err != nil:
			failed.Add(1)
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + errorStyle.Render("FAIL") + " " +
				dimStyle.Render(filepath.Base(r.src)) + " " + errorStyle.Render(r.err.Error()))
		case r.copied:
			copied.Add(1)
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + copiedStyle.Render("COPY") + " " +
				dimStyle.Render(r.src) + " " + dimStyle.Render("->") + " " + valueStyle.Render(r.dst))
			if isVideoPath(r.dst) {
				copiedVideos = append(copiedVideos, r.dst)
			}
		case r.skipped:
			skipped.Add(1)
			fmt.Print("\r\033[K")
			lipgloss.Println(timestamp() + " " + skippedStyle.Render("SKIP") + " " +
				dimStyle.Render("File already exists:") + " " + valueStyle.Render(r.dst))
		}

		elapsed := time.Since(syncStart)
		bar := renderSyncProgressBar(processed, total, 30, elapsed)
		fmt.Print("\r" + bar)

		printMu.Unlock()
	}

	elapsed := time.Since(syncStart)
	bar := renderSyncProgressBar(total, total, 30, elapsed)
	fmt.Print("\r\033[K" + bar)
	fmt.Println()
	fmt.Println()

	res.copied = copied.Load()
	res.skipped = skipped.Load()
	res.failed = failed.Load()
	res.total = total
	res.elapsed = time.Since(res.discoverStart).Round(time.Millisecond)
	res.copiedVideos = copiedVideos
	return res, nil
}

func isVideoPath(path string) bool {
	return videoExts[strings.ToLower(filepath.Ext(path))]
}
