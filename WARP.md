# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Commands

### Core VideoTools Utilities

```bash
# File Verifier - Parse file paths and check existence
python file_verifier.py
# Web interface opens at http://localhost:7861

# Camera Sync - Synchronize DCIM files to date-based folders
python sync.py
# Configure paths in main() function before running

# Video Combiner - Concatenate videos with smart grouping
python video_combiner.py
# Requires input_dir, output_dir parameters in VideoCombiner class

# Video Analyzer - AI-powered video content analysis
python video_analyzer.py
# Requires PyTorch, Transformers, and Qwen2.5-VL model
```

### Video Compressor (Subdirectory)

```bash
cd "Video Compressor"

# Web Interface (Recommended)
python GradioVideoCompression.py
# Opens at http://localhost:7869

# CLI - Single file with dry run (ALWAYS TEST FIRST)
python VideoCompression.py --single "/path/to/video.mp4" --dry-run

# CLI - Multiple files
python VideoCompression.py video1.mp4 video2.mp4 video3.mp4 --dry-run

# CLI - From file list
python VideoCompression.py --files files.txt --dry-run

# Test suite
python test_compression.py
```

### Configuration & Setup

```bash
# Check FFmpeg installation
which ffmpeg
/opt/homebrew/bin/ffmpeg  # Update config.json with this path

# Install core dependencies
pip install gradio pathlib humanize

# Install Video Analyzer dependencies
pip install torch transformers qwen-vl-utils
pip install flash-attn --no-build-isolation
```

## Architecture Overview

### Two-Tier Structure

1. **Core VideoTools** (repository root): Standalone utilities for video workflow tasks
2. **Video Compressor** (subdirectory): Separate repository for advanced compression with safety protocols

### Main Classes and Components

**VideoCompressor** (`Video Compressor/VideoCompression.py`):
- Core compression engine with 7-step safety protocol
- Hardware acceleration detection (Apple VideoToolbox)
- Enhanced logging with rotation and cleanup
- Methods: `process_file()`, `build_ffmpeg_command()`, `detect_hardware_acceleration()`

**CameraSync** (`sync.py`):
- Intelligent file synchronization for DCIM folders
- Date-based folder organization with progress tracking
- Methods: `sync_files()`, `get_video_files()`, `create_date_folder()`

**VideoCombiner** (`video_combiner.py`):
- Professional video concatenation with quality analysis
- Smart grouping by date/time, metadata preservation
- Methods: `combine_videos()`, `_prepare_video()`, `_get_video_metadata()`

**File Verifier** (`file_verifier.py`):
- Gradio web interface for batch file existence verification
- Smart path parsing (space-separated and newline-separated)
- Functions: `parse_file_paths()`, `verify_files()`, `format_*_section()`

### Gradio Web Interfaces

All major tools include modern Gradio UIs with:
- Real-time progress tracking
- Interactive configuration
- Inter font and neutral color themes
- Copy-paste ready outputs

### Logging Architecture

- Rotating log files with configurable size limits
- Dual-level logging: console (INFO) and file (DEBUG)
- Automatic cleanup of old logs (default: keep 5 most recent)
- Session tracking with timestamps

## Configuration & Safety

### Video Compressor Configuration (`config.json`)

**Critical Settings:**
```json
{
  "ffmpeg_path": "/opt/homebrew/bin/ffmpeg",
  "compression_settings": {
    "enable_hardware_acceleration": true,
    "video_codec": "libx265",
    "preset": "medium",
    "crf": 23,
    "target_bitrate_reduction": 0.5
  },
  "safety_settings": {
    "min_free_space_gb": 15,
    "verify_integrity": true,
    "create_backup_hash": true,
    "max_retries": 3
  }
}
```

**Large File Handling:**
- `use_same_filesystem`: true (creates temp on same drive as source)
- `hash_chunk_size_mb`: 5 (for integrity verification)
- `threshold_gb`: 10 (triggers enhanced monitoring)

### 7-Step Safety Protocol

1. **Pre-flight Checks**: Verify file exists, check disk space
2. **Hash Calculation**: Create integrity hash of original
3. **Compress to Temp**: Create compressed copy in temp location
4. **Verify Compressed**: Test playability and metadata
5. **Move to Final**: Move compressed file to target location
6. **Final Verification**: Verify moved file integrity
7. **Delete Original**: Only after ALL verifications pass

### Hardware Acceleration

**Apple Silicon Detection:**
- Auto-detects VideoToolbox availability
- Falls back to software encoding if unavailable
- Configurable via `enable_hardware_acceleration` setting
- Test with: `python test_compression.py` (hardware acceleration test)

**Quality Parameters:**
- VideoToolbox: uses `q:v` quality parameter
- Software: uses `crf` parameter
- 10-bit preservation when supported

## Development Workflow

### Repository Structure

- **Main VideoTools**: Single git repository for core utilities
- **Video Compressor**: Independent subdirectory (separate git repo per .gitignore)
- Keep Video Compressor changes isolated from main repo commits

### Configuration-Driven Development

- Most tuning via JSON config files, no code changes needed
- `config.json` for Video Compressor settings
- Temporary config creation for UI-driven changes (`temp_config.json`)

### Testing & Validation

```bash
# Always test compression with dry run first
cd "Video Compressor"
python VideoCompression.py --single test_video.mp4 --dry-run

# Run full test suite
python test_compression.py

# Hardware acceleration validation
python -c "from VideoCompression import VideoCompressor; c=VideoCompressor(); print(c.detect_hardware_acceleration())"
```

### Log Management

- Logs stored in `./logs/` with automatic rotation
- Check recent activity: `ls -la logs/`
- View real-time compression logs: `tail -f logs/video_compression_*.log`
- Cleanup happens automatically based on `max_log_files` setting

### Code Style Standards

- **Modern Python**: Type hints, pathlib, f-strings throughout
- **Class-based architecture**: Each major component is a standalone class
- **Comprehensive error handling**: Try/catch blocks with detailed logging
- **Progress indicators**: Real-time feedback for long-running operations
- **Gradio UIs**: Consistent theming with Inter font and neutral colors

### Development Tips

- Each tool designed to run independently without complex setup
- Hot reload Gradio interfaces: Ctrl+C and restart Python script
- Use `--dry-run` extensively before actual processing
- Monitor disk space during large file operations
- Check Video Compressor logs for detailed compression progress

### Dependencies Management

**Core Tools:**
```bash
pip install gradio pathlib humanize
```

**Video Analyzer (AI-powered):**
```bash
pip install torch transformers qwen-vl-utils
pip install flash-attn --no-build-isolation
```

**System Requirements:**
- FFmpeg installed and configured in `config.json`
- Python 3.8+ with type hint support
- Sufficient disk space (2.5x original file size for compression)
