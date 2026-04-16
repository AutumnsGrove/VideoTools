package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	lipgloss "charm.land/lipgloss/v2"
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

	barFillStyleCompress = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#BD93F9"))

	dividerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#BD93F9"))

	copiedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#50FA7B")).
			Bold(true)

	skippedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFB86C"))

	compressStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#BD93F9")).
			Bold(true)

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#BD93F9"))
)

func timestamp() string {
	return dimStyle.Render(time.Now().Format("2006-01-02 15:04:05"))
}

// renderBar draws a filled bar of width chars at the given fill ratio.
func renderBar(fillStyle, emptyStyle lipgloss.Style, ratio float64, width int) string {
	if ratio < 0 {
		ratio = 0
	}
	if ratio > 1 {
		ratio = 1
	}
	filled := int(ratio * float64(width))
	if filled > width {
		filled = width
	}
	return fillStyle.Render(strings.Repeat("█", filled)) +
		emptyStyle.Render(strings.Repeat("░", width-filled))
}

// renderSyncProgressBar renders the copy-phase progress bar.
func renderSyncProgressBar(current, total int, width int, elapsed time.Duration) string {
	pct := 0.0
	if total > 0 {
		pct = float64(current) / float64(total)
	}

	bar := renderBar(barFillStyle, barEmptyStyle, pct, width)
	pctStr := fmt.Sprintf("%3.0f%%", pct*100)

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

// formatBytes renders a byte count in human-readable form.
func formatBytes(n int64) string {
	const (
		kb = 1024.0
		mb = kb * 1024
		gb = mb * 1024
	)
	f := float64(n)
	switch {
	case f >= gb:
		return fmt.Sprintf("%.2f GB", f/gb)
	case f >= mb:
		return fmt.Sprintf("%.1f MB", f/mb)
	case f >= kb:
		return fmt.Sprintf("%.1f KB", f/kb)
	}
	return fmt.Sprintf("%d B", n)
}

// formatMBps renders a MB/s throughput value.
func formatMBps(bytesPerSec float64) string {
	return fmt.Sprintf("%.1f MB/s", bytesPerSec/(1024*1024))
}

// shortPath trims the leading destination base so compression lines stay readable.
func shortPath(path string, maxLen int) string {
	if len(path) <= maxLen {
		return path
	}
	base := filepath.Base(path)
	if len(base) >= maxLen {
		return base
	}
	return "…" + path[len(path)-maxLen+1:]
}

// renderCompressLine draws a single-line status for the currently compressing file.
//
//	[3/23] video-004-2026-04-12.mp4 · compressing 63% █████░░░ · 2.1 GB · 84.3 MB/s
func renderCompressLine(idx, total int, filename string, origSize int64, stage string, pct, mbps float64, barWidth int) string {
	bar := renderBar(barFillStyleCompress, barEmptyStyle, pct, barWidth)
	pctStr := fmt.Sprintf("%3.0f%%", pct*100)

	mbpsStr := "-- MB/s"
	if mbps > 0 {
		mbpsStr = formatMBps(mbps)
	}

	return fmt.Sprintf("%s %s %s %s %s %s %s %s %s",
		dimStyle.Render(fmt.Sprintf("[%d/%d]", idx, total)),
		valueStyle.Render(filename),
		dimStyle.Render("·"),
		compressStyle.Render(stage),
		headerStyle.Render(pctStr),
		bar,
		dimStyle.Render("·"),
		dimStyle.Render(formatBytes(origSize)),
		dimStyle.Render(mbpsStr),
	)
}

