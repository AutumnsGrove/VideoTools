package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"syscall"

	lipgloss "charm.land/lipgloss/v2"
)

// assignStems computes the destination filename stem (no extension) that each
// source file would receive if synced, using the same day+type grouping and
// chronological 1-based indexing as runSync's job-building step. Keep this in
// sync with that logic — it must reproduce the same names or the audit will
// misreport files as not-yet-backed-up.
func assignStems(files []mediaFile) map[string]string {
	type dayKey struct {
		date     string
		fileType string
	}
	groups := make(map[dayKey][]mediaFile)
	for _, f := range files {
		k := dayKey{date: f.date.Format("2006-01-02"), fileType: f.fileType}
		groups[k] = append(groups[k], f)
	}

	stems := make(map[string]string, len(files))
	for _, group := range groups {
		for i, f := range group {
			ext := strings.ToLower(filepath.Ext(f.path))
			filename := generateFilename(i+1, f.date, f.fileType, ext)
			stems[f.path] = strings.TrimSuffix(filename, filepath.Ext(filename))
		}
	}
	return stems
}

// sdVideo is one video found on the source card, annotated with whether its
// computed stem already has a transcript in the journal.
type sdVideo struct {
	path string
	size int64
	stem string
	safe bool
}

// freeSpace returns free bytes on the filesystem containing path.
func freeSpace(path string) (int64, error) {
	var stat syscall.Statfs_t
	if err := syscall.Statfs(path, &stat); err != nil {
		return 0, err
	}
	return int64(stat.Bsize) * int64(stat.Bfree), nil
}

// runAuditJournal cross-references videos on the source (microSD) card against
// the Obsidian auto-journal to find which ones already have a transcript —
// meaning they're safely backed up as text and are candidates for deletion to
// free card space. It never deletes or modifies anything; it only reports.
func runAuditJournal(cfg config, source, journalDir string) error {
	if _, err := os.Stat(source); os.IsNotExist(err) {
		return fmt.Errorf("source path does not exist: %s", source)
	}
	if _, err := os.Stat(journalDir); os.IsNotExist(err) {
		return fmt.Errorf("journal directory does not exist: %s", journalDir)
	}

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Scanning source card..."))
	files, err := discoverMedia(source)
	if err != nil {
		return fmt.Errorf("scanning source: %w", err)
	}
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d file(s)", len(files))))

	lipgloss.Print(timestamp() + " " + infoStyle.Render("Scanning journal for transcribed videos..."))
	transcribed := getTranscribedVideoNames(journalDir)
	lipgloss.Println(" " + successStyle.Render(fmt.Sprintf("found %d transcript(s)", len(transcribed))))
	fmt.Println()

	stems := assignStems(files)

	var videos []sdVideo
	var photoCount int
	var photoBytes int64
	for _, f := range files {
		if f.fileType == "photo" {
			if info, err := os.Stat(f.path); err == nil {
				photoCount++
				photoBytes += info.Size()
			}
			continue
		}
		info, err := os.Stat(f.path)
		if err != nil {
			continue
		}
		stem := stems[f.path]
		videos = append(videos, sdVideo{
			path: f.path,
			size: info.Size(),
			stem: stem,
			safe: transcribed[stem],
		})
	}

	// Safe-to-delete first, largest first (frees the most space fastest).
	// Not-yet-backed-up after, also largest first for visibility.
	sort.SliceStable(videos, func(i, j int) bool {
		if videos[i].safe != videos[j].safe {
			return videos[i].safe // safe ones first
		}
		return videos[i].size > videos[j].size
	})

	var safeCount, unsafeCount int
	var safeBytes, unsafeBytes int64

	divider := dividerStyle.Render(strings.Repeat("━", 70))
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Safe to delete") + " " + dimStyle.Render("(transcript already saved to journal)"))
	lipgloss.Println(divider)
	for _, v := range videos {
		if !v.safe {
			continue
		}
		safeCount++
		safeBytes += v.size
		lipgloss.Println("  " + successStyle.Render("✓") + " " +
			valueStyle.Render(fmt.Sprintf("%-10s", formatBytes(v.size))) + " " +
			dimStyle.Render(filepath.Base(v.path)) + " " +
			dimStyle.Render("→") + " " + dimStyle.Render(v.stem))
	}
	if safeCount == 0 {
		lipgloss.Println("  " + dimStyle.Render("(none)"))
	}
	fmt.Println()

	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Keep — not yet transcribed") + " " + dimStyle.Render("(no journal entry found)"))
	lipgloss.Println(divider)
	for _, v := range videos {
		if v.safe {
			continue
		}
		unsafeCount++
		unsafeBytes += v.size
		lipgloss.Println("  " + errorStyle.Render("✗") + " " +
			valueStyle.Render(fmt.Sprintf("%-10s", formatBytes(v.size))) + " " +
			dimStyle.Render(filepath.Base(v.path)) + " " +
			dimStyle.Render("(would be: "+v.stem+")"))
	}
	if unsafeCount == 0 {
		lipgloss.Println("  " + dimStyle.Render("(none)"))
	}
	fmt.Println()

	// Summary.
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Summary"))
	lipgloss.Println(divider)
	lipgloss.Println(labelStyle.Render("  Total videos:      ") + valueStyle.Render(fmt.Sprintf("%d", len(videos))))
	lipgloss.Println(labelStyle.Render("  Safe to delete:    ") + successStyle.Render(fmt.Sprintf("%d videos, %s", safeCount, formatBytes(safeBytes))))
	lipgloss.Println(labelStyle.Render("  Keep (untranscribed):") + errorStyle.Render(fmt.Sprintf(" %d videos, %s", unsafeCount, formatBytes(unsafeBytes))))
	if photoCount > 0 {
		lipgloss.Println(labelStyle.Render("  Photos (not audited):") + dimStyle.Render(fmt.Sprintf(" %d, %s", photoCount, formatBytes(photoBytes))))
	}

	if free, err := freeSpace(source); err == nil {
		lipgloss.Println(labelStyle.Render("  Free space now:    ") + valueStyle.Render(formatBytes(free)))
		lipgloss.Println(labelStyle.Render("  Free space after:  ") + successStyle.Render(formatBytes(free + safeBytes)))
	}
	fmt.Println()

	// Plain path list at the end for easy copy/scripting — deletion is the
	// user's call, this tool only ever reports.
	if safeCount > 0 {
		lipgloss.Println(dimStyle.Render("Safe-to-delete paths:"))
		for _, v := range videos {
			if v.safe {
				fmt.Println(v.path)
			}
		}
		fmt.Println()
	}

	return nil
}
