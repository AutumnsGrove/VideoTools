# Video Scanner

A concurrent video file analyzer that scans directories for large video files and generates markdown reports.

## Features

- 🚀 **Concurrent Processing** - Multi-threaded directory scanning
- 📊 **UV-Style Progress** - Clean, minimal progress display without terminal flooding
- ⚙️ **Configurable** - Adjustable size thresholds and settings
- 📝 **Markdown Output** - Generates reports with file lists and copy-paste ready paths
- 🎬 **Video Focused** - Supports .mp4 and .mov files
- 🔍 **Smart Filtering** - Only includes files above specified size threshold

## Quick Start

```bash
# Scan a directory with default settings (1GB threshold)
python scanner.py /path/to/video/directory

# Use custom size threshold
python scanner.py /path/to/videos -s 2.5

# Custom output file
python scanner.py /path/to/videos -o my_video_report.md

# Use custom config
python scanner.py /path/to/videos -c my_config.json
```

## Configuration

Edit `config.json` to customize:

```json
{
  "size_threshold_gb": 1.0,
  "supported_extensions": [".mp4", ".mov"],
  "output_filename": "video_scan_results.md",
  "max_workers": 4,
  "progress_update_interval": 0.1,
  "scan_hidden_dirs": false
}
```

## Output

The tool generates a markdown report containing:

1. **Summary** - Total files found, size threshold, total size
2. **File List** - Videos sorted by size with details
3. **Copy-Paste Paths** - Ready-to-use file paths for scripts

## Example Output

```markdown
# Video File Scan Report

**Generated:** 2025-01-15 14:30:22  
**Size Threshold:** 1.0GB  
**Total Files Found:** 12  
**Total Size:** 45.7GB  

## Video Files (Sorted by Size)

- **large_video.mp4** (8.2GB)
- **project_final.mov** (6.1GB)
- **backup_footage.mp4** (4.8GB)

## File Paths (Copy/Paste Ready)

```
/path/to/large_video.mp4
/path/to/project_final.mov
/path/to/backup_footage.mp4
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)