package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"syscall"

	lipgloss "charm.land/lipgloss/v2"
)

// pruneBatchSize is how many files we hand to Finder per AppleScript call.
// Keeps the script string small and the Finder round-trip responsive.
const pruneBatchSize = 100

// pruneMaxListed caps how many queued paths we echo back before summarizing.
const pruneMaxListed = 40

// pruneItem is one verified source file queued for the trash.
type pruneItem struct {
	src    string
	dst    string
	size   int64
	status verifyStatus
}

// prunable reports whether a verification status means the source file is
// safe to remove from the card. Only an exact copy (PASS) or a copy we
// compressed ourselves (COMPRESSED) qualify. MISSING, EMPTY, CORRUPT and
// TRUNCATED never do.
func prunable(status verifyStatus) bool {
	return status == verifyPass || status == verifyCompressed
}

// buildPrunePlan turns verification results into a delete queue, re-checking
// the filesystem at plan time so nothing is queued on stale information.
func buildPrunePlan(audit verifyAudit, sourceRoot string) []pruneItem {
	root := filepath.Clean(sourceRoot)
	seen := make(map[string]bool, len(audit.results))
	var items []pruneItem

	for _, r := range audit.results {
		if !prunable(r.status) {
			continue
		}
		src := filepath.Clean(r.src)
		// Never touch anything outside the source tree.
		if src != root && !strings.HasPrefix(src, root+string(filepath.Separator)) {
			continue
		}
		if seen[src] {
			continue
		}

		srcInfo, err := os.Stat(src)
		if err != nil || srcInfo.Size() == 0 {
			continue
		}
		dstInfo, err := os.Stat(r.dst)
		if err != nil || dstInfo.Size() == 0 {
			continue
		}
		// Last-moment integrity re-check against what the audit saw.
		if r.status == verifyPass && dstInfo.Size() != srcInfo.Size() {
			continue
		}
		if r.status == verifyCompressed && !isVideoPath(r.dst) {
			continue
		}

		seen[src] = true
		items = append(items, pruneItem{
			src:    src,
			dst:    r.dst,
			size:   srcInfo.Size(),
			status: r.status,
		})
	}

	// Largest first so the space math reads naturally.
	sort.Slice(items, func(i, j int) bool {
		if items[i].size != items[j].size {
			return items[i].size > items[j].size
		}
		return items[i].src < items[j].src
	})
	return items
}

// deviceID returns the filesystem device number for path. Two paths on the
// same device are on the same volume — exactly the case we refuse to prune.
func deviceID(path string) (uint64, error) {
	var st syscall.Stat_t
	if err := syscall.Stat(path, &st); err != nil {
		return 0, err
	}
	return uint64(st.Dev), nil
}

// runPrune verifies every source file against the external drive, then moves
// the files that came back PASS/COMPRESSED to the Trash in one batch. Files
// that fail verification are left alone on the card.
func runPrune(cfg config, workers int, dryRun, assumeYes bool) error {
	divider := dividerStyle.Render(strings.Repeat("━", 70))

	if _, err := os.Stat(cfg.Source); err != nil {
		return fmt.Errorf("source path does not exist: %s", cfg.Source)
	}
	if _, err := os.Stat(cfg.Destination); err != nil {
		return fmt.Errorf("destination path does not exist (external drive mounted?): %s", cfg.Destination)
	}

	srcDev, err := deviceID(cfg.Source)
	if err != nil {
		return fmt.Errorf("cannot stat source volume: %w", err)
	}
	dstDev, err := deviceID(cfg.Destination)
	if err != nil {
		return fmt.Errorf("cannot stat destination volume: %w", err)
	}
	if srcDev == dstDev {
		return fmt.Errorf("source and destination are on the same volume — refusing to prune (%s)", cfg.Destination)
	}

	// Full verification pipeline. Only its PASS/COMPRESSED results feed the
	// delete queue; failures are reported and kept.
	audit, err := runVerify(cfg, workers)
	if err != nil {
		return err
	}

	items := buildPrunePlan(audit, cfg.Source)

	fmt.Println()
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Prune Queue") + " " +
		dimStyle.Render("(verified on the external drive, safe to remove from card)"))
	lipgloss.Println(divider)

	if len(items) == 0 {
		lipgloss.Println("  " + dimStyle.Render("(nothing verified — nothing to prune)"))
		fmt.Println()
		if audit.fail > 0 {
			lipgloss.Println(warnStyle.Render(fmt.Sprintf(
				"%d file(s) did not verify. Run 'camera-sync' to re-sync them first.", audit.fail)))
			fmt.Println()
		}
		return nil
	}

	var total int64
	for i, it := range items {
		total += it.size
		if i >= pruneMaxListed {
			continue
		}
		tag := successStyle.Render("✓")
		if it.status == verifyCompressed {
			tag = copiedStyle.Render("✓")
		}
		lipgloss.Println("  " + tag + " " +
			valueStyle.Render(fmt.Sprintf("%-10s", formatBytes(it.size))) + " " +
			dimStyle.Render(filepath.Base(it.src)) + " " +
			dimStyle.Render("→") + " " + dimStyle.Render(it.dst))
	}
	if len(items) > pruneMaxListed {
		lipgloss.Println("  " + dimStyle.Render(fmt.Sprintf("… and %d more", len(items)-pruneMaxListed)))
	}
	fmt.Println()

	lipgloss.Println(labelStyle.Render("  Queued:        ") +
		valueStyle.Render(fmt.Sprintf("%d file(s), %s", len(items), formatBytes(total))))
	if audit.fail > 0 {
		lipgloss.Println(labelStyle.Render("  Kept:          ") +
			warnStyle.Render(fmt.Sprintf("%d file(s) failed verification", audit.fail)))
	}
	if free, err := freeSpace(cfg.Source); err == nil {
		lipgloss.Println(labelStyle.Render("  Free space now:  ") + valueStyle.Render(formatBytes(free)))
		lipgloss.Println(labelStyle.Render("  After emptying Trash: ") + successStyle.Render(formatBytes(free+total)))
	}
	fmt.Println()

	if dryRun {
		lipgloss.Println(infoStyle.Render("Dry run — nothing was moved. Re-run without --dry-run to prune."))
		fmt.Println()
		return nil
	}

	if !assumeYes {
		if !promptYesNo(fmt.Sprintf("Move %d file(s) (%s) to the Trash?", len(items), formatBytes(total)), false) {
			lipgloss.Println(dimStyle.Render("Nothing moved."))
			fmt.Println()
			return nil
		}
	}

	fmt.Println()
	lipgloss.Println(headerStyle.Render("Moving to Trash") + " " + dimStyle.Render(fmt.Sprintf("(%d file(s))", len(items))))
	fmt.Println()

	paths := make([]string, len(items))
	for i, it := range items {
		paths[i] = it.src
	}
	if err := trashPaths(paths); err != nil {
		return err
	}

	// Confirm each source file actually left the card.
	var leftover []pruneItem
	for _, it := range items {
		if _, err := os.Stat(it.src); err == nil {
			leftover = append(leftover, it)
		}
	}
	removed := len(items) - len(leftover)
	var removedBytes int64
	for _, it := range items {
		removedBytes += it.size
	}
	for _, it := range leftover {
		removedBytes -= it.size
	}

	fmt.Println()
	lipgloss.Println(divider)
	lipgloss.Println(headerStyle.Render("Prune complete"))
	lipgloss.Println(divider)
	lipgloss.Println(labelStyle.Render("  Trashed:  ") + successStyle.Render(fmt.Sprintf("%d file(s), %s", removed, formatBytes(removedBytes))))
	if len(leftover) > 0 {
		lipgloss.Println(labelStyle.Render("  Failed:   ") + errorStyle.Render(fmt.Sprintf("%d file(s) still on the card", len(leftover))))
		for _, it := range leftover {
			lipgloss.Println("    " + dimStyle.Render(it.src))
		}
	}
	if audit.fail > 0 {
		lipgloss.Println(labelStyle.Render("  Kept:     ") + warnStyle.Render(fmt.Sprintf("%d file(s) that did not verify", audit.fail)))
	}
	if free, err := freeSpace(cfg.Source); err == nil {
		lipgloss.Println(labelStyle.Render("  Free space: ") + valueStyle.Render(formatBytes(free)))
	}
	fmt.Println()
	lipgloss.Println(dimStyle.Render("Empty the Trash to reclaim the space."))
	fmt.Println()

	if len(leftover) > 0 {
		return fmt.Errorf("%d file(s) could not be moved to the Trash", len(leftover))
	}
	return nil
}

// trashPaths moves the given files to the macOS Trash. On macOS this goes
// through Finder, which puts files on the correct per-volume .Trashes folder
// (so card contents don't land on the internal disk) and keeps "Put Back"
// metadata. Elsewhere it falls back to the `trash` CLI if installed.
func trashPaths(paths []string) error {
	if len(paths) == 0 {
		return nil
	}

	if runtime.GOOS == "darwin" {
		return trashViaFinder(paths)
	}
	if bin, err := exec.LookPath("trash"); err == nil {
		for start := 0; start < len(paths); start += pruneBatchSize {
			end := start + pruneBatchSize
			if end > len(paths) {
				end = len(paths)
			}
			cmd := exec.Command(bin, paths[start:end]...)
			if out, err := cmd.CombinedOutput(); err != nil {
				return fmt.Errorf("trash failed: %v: %s", err, strings.TrimSpace(string(out)))
			}
		}
		return nil
	}
	return fmt.Errorf("no trash mechanism available on %s (install the 'trash' CLI)", runtime.GOOS)
}

// trashViaFinder hands each batch of paths to Finder in a single
// "delete {...}" call, so the whole batch moves at once.
func trashViaFinder(paths []string) error {
	for start := 0; start < len(paths); start += pruneBatchSize {
		end := start + pruneBatchSize
		if end > len(paths) {
			end = len(paths)
		}

		items := make([]string, 0, end-start)
		for _, p := range paths[start:end] {
			items = append(items, `POSIX file "`+appleScriptEscape(p)+`"`)
		}
		script := `tell application "Finder" to delete {` + strings.Join(items, ", ") + `}`

		cmd := exec.Command("osascript", "-e", script)
		if out, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("Finder could not move files to the Trash: %v: %s",
				err, strings.TrimSpace(string(out)))
		}
	}
	return nil
}

// appleScriptEscape escapes a string for embedding in an AppleScript literal.
func appleScriptEscape(s string) string {
	s = strings.ReplaceAll(s, `\`, `\\`)
	return strings.ReplaceAll(s, `"`, `\"`)
}
