# Camera Sync (sync_concurrent.py) - Project TODOs

## High Priority - Critical Fixes

- [x] Create TODOS.md file
- [ ] **BLOCKER**: Fix file extension bug in `generate_new_filename()` - hardcoded `.mp4` destroys `.mov`/`.avi`/`.mkv` files
- [ ] Add platform compatibility for `st_birthtime` (macOS-only) - add Linux fallback
- [ ] Add thread-safe counters using `threading.Lock()` for `files_moved` and `skipped`

## High Priority - Performance Optimizations

- [ ] Replace `rglob('*')` with `os.scandir()` for 3-5x faster directory scanning
- [ ] Implement smart worker count: `min(4, os.cpu_count())` instead of hardcoded 4
- [ ] Eliminate redundant sorting - group files by date during collection

## Medium Priority - Robustness

- [ ] Add duplicate detection using MD5 file hashing
- [ ] Implement granular error handling (PermissionError, disk full, etc.)
- [ ] Add resume capability with JSON state file for interrupted syncs
- [ ] Add path validation and disk space checks before starting
- [ ] Implement `--dry-run` mode for safe testing

## Medium Priority - Interface Improvements

- [ ] Replace hardcoded paths with argparse CLI interface
  - Required: `source`, `dest`
  - Optional: `--workers`, `--dry-run`, `--resume`, `--verify`, `--move`
- [ ] Enhance progress reporting with file sizes, MB/s, total transferred
- [ ] Add final summary with duration and average speed

## Low Priority - Code Quality

- [ ] Complete type hints for all method signatures
- [ ] Add comprehensive docstrings (Google style) for all public methods
- [ ] Add class-level docstring explaining overall purpose
- [ ] Optional: Add EXIF date extraction for photos (graceful fallback if PIL not available)

## Future Enhancements

- [ ] Add `--verify` flag to check file integrity after copy using hashes
- [ ] Add `--move` flag to move files instead of copying
- [ ] Consider `multiprocessing.Pool` option for same-disk, CPU-bound scenarios
- [ ] Add support for custom naming patterns via config file

## Testing Checklist

- [ ] Test with 10,000+ files (memory usage validation)
- [ ] Test interruption and resume functionality
- [ ] Test on both macOS and Linux
- [ ] Verify all file extensions preserved correctly
- [ ] Benchmark: confirm 2-3x speed improvement

---
*Last updated: 2025-10-12*
