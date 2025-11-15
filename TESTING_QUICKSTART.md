# Testing Quick Start Guide

Quick reference for running tests in VideoTools MCP Server.

## Prerequisites

```bash
# Install dependencies
uv sync --extra all

# Verify test setup
uv run python scripts/verify_test_setup.py
```

## Download Test Videos

Integration tests require video files (~700 MB total):

```bash
# Download all 10 test videos
python scripts/download_test_videos.py

# Download specific videos
python scripts/download_test_videos.py --video short_tutorial
python scripts/download_test_videos.py --video interview_2speaker
python scripts/download_test_videos.py --video visual_short

# Skip already downloaded
python scripts/download_test_videos.py --skip-existing
```

**Note**: Test videos are NOT committed to git. Each developer must download locally.

---

## Running Tests

### Unit Tests (No videos needed)
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/test_file_utils.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=video_tools_mcp --cov-report=html
```

### Integration Tests (Requires videos)
```bash
# Run all integration tests (skips tests if videos missing)
uv run pytest tests/integration/ -v

# Run only tests with available videos
uv run pytest tests/integration/ -v --tb=short

# Run tests marked as requiring videos
uv run pytest tests/integration/ -v -m requires_videos
```

### All Tests
```bash
# Run everything
uv run pytest tests/ -v

# Run tests in parallel (faster)
uv run pytest tests/ -v -n auto

# Run without videos (unit tests only)
uv run pytest tests/ -v -m 'not requires_videos'
```

### Specific Tool Tests
```bash
# Transcription tests
uv run pytest tests/integration/test_transcription_integration.py -v

# Video analysis tests
uv run pytest tests/integration/test_video_analysis_integration.py -v
```

---

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.requires_videos` - Needs test videos downloaded
- `@pytest.mark.slow` - Takes >5 seconds to run
- `@pytest.mark.benchmark` - Performance benchmarking test

```bash
# Run only slow tests
uv run pytest -v -m slow

# Skip slow tests
uv run pytest -v -m "not slow"

# Run benchmarks
uv run pytest -v -m benchmark
```

---

## Test Fixtures

### Unit Test Fixtures (Always Available)

```python
def test_example(temp_dir, mock_video_path):
    # temp_dir: Temporary directory (auto-cleaned)
    # mock_video_path: Empty .mp4 file for testing
    pass
```

Available fixtures:
- `temp_dir` - Temporary directory
- `mock_video_path` - Empty video file
- `mock_audio_path` - Empty audio file
- `mock_srt_path` - Sample SRT file
- `mock_env_vars` - Mocked environment variables
- `sample_video_files` - Multiple format video files

### Integration Test Fixtures (Requires Videos)

```python
def test_real_video(require_short_video):
    # require_short_video: Path to short test video (or skip if missing)
    video_path = require_short_video
    # Test with real video...
```

Available fixtures:
- `require_short_video` - Short tutorial video (~60s)
- `require_multi_speaker_video` - Multi-speaker interview
- `require_visual_video` - Visual content video
- `require_any_video` - Any available test video

---

## Video Availability Check

Before running integration tests:

```bash
# Check which videos are downloaded
uv run python scripts/verify_test_setup.py

# Example output:
# ✓ short_tutorial
# ✗ multi_speaker_2
# ✗ visual_short
```

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (no external deps)
│   ├── test_file_utils.py
│   ├── test_srt_utils.py
│   └── test_config.py
├── integration/             # Integration tests (require videos)
│   ├── test_transcription_integration.py
│   └── test_video_analysis_integration.py
└── fixtures/
    └── videos/              # Test videos (gitignored)
        ├── README.md
        └── *.mp4 files
```

---

## Common Test Scenarios

### 1. Quick Smoke Test (No Downloads)
```bash
# Run unit tests only
uv run pytest tests/unit/ -v
```

### 2. Full Integration Test (After Downloads)
```bash
# Download videos first
python scripts/download_test_videos.py

# Run all tests
uv run pytest tests/ -v
```

### 3. Test Specific Tool
```bash
# Just transcription
uv run pytest tests/integration/test_transcription_integration.py::TestBasicTranscription -v
```

### 4. Performance Benchmarking
```bash
# Run benchmarks only
uv run pytest tests/ -v -m benchmark --durations=10
```

---

## Troubleshooting

### Tests are being skipped
```
SKIPPED: Test video not found
```
**Solution**: Download test videos
```bash
python scripts/download_test_videos.py
```

### Import errors
```
ModuleNotFoundError: No module named 'pytest'
```
**Solution**: Use `uv run` to run in project environment
```bash
uv run pytest tests/ -v
```

### FFmpeg not found
```
FileNotFoundError: ffmpeg
```
**Solution**: Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Linux
apt-get install ffmpeg
```

---

## CI/CD Integration

For continuous integration, add test video download step:

```yaml
# .github/workflows/test.yml
- name: Download test videos
  run: python scripts/download_test_videos.py

- name: Run tests
  run: uv run pytest tests/ -v --cov
```

**Note**: May want to cache test videos to speed up CI runs.

---

## Next Steps

1. **Download videos**: `python scripts/download_test_videos.py`
2. **Verify setup**: `uv run python scripts/verify_test_setup.py`
3. **Run tests**: `uv run pytest tests/ -v`
4. **Check coverage**: `uv run pytest tests/ --cov=video_tools_mcp --cov-report=html`
5. **View results**: `open htmlcov/index.html`

---

**Last Updated**: 2025-11-15
**Phase**: 6.1 - Test Infrastructure Setup
