# Testing Guide - VideoTools MCP Server

**Status**: Phase 6 Framework - To be completed during testing phase

---

## Overview

This document describes the testing strategy and procedures for the VideoTools MCP Server, covering unit tests, integration tests, and performance benchmarking.

---

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and shared fixtures
├── unit/                       # Unit tests (Phase 1-5) - ✅ Complete
│   ├── test_audio_extraction.py
│   ├── test_config.py
│   ├── test_file_utils.py
│   ├── test_model_managers.py
│   └── test_server.py
├── integration/                # Integration tests (Phase 6) - 📋 Framework ready
│   ├── test_transcription_integration.py
│   └── test_video_analysis_integration.py
└── fixtures/
    └── videos/                 # Test video files
        └── README.md           # Test video requirements
```

---

## Prerequisites

### 1. Test Videos

Download or create test videos before running integration tests:

```bash
# Option 1: Run download script (Phase 6 TODO: implement)
python scripts/download_test_videos.py

# Option 2: Create your own test videos
# See tests/fixtures/videos/README.md for requirements
```

**Required test videos**:
- Short video (30s) - Basic functionality
- Multi-speaker video (2-3 min) - Speaker diarization
- Visual content video (5 min) - Video analysis
- Long video (10-15 min) - Performance testing

### 2. Dependencies

```bash
# Install all dependencies including test tools
uv sync --extra all --extra dev
```

### 3. API Keys / Secrets

For speaker diarization tests, ensure `secrets.json` contains your HuggingFace token:

```json
{
  "hf_token": "your_huggingface_token_here"
}
```

---

## Running Tests

### Unit Tests (Fast, No Dependencies)

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage report
pytest tests/unit/ -v --cov=src/video_tools_mcp --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py -v

# View coverage report
open htmlcov/index.html
```

**Expected results**:
- ✅ 162 tests pass
- ✅ ~95% code coverage
- ⏱️ ~1-2 seconds total runtime

---

### Integration Tests (Slow, Requires Videos)

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test class
pytest tests/integration/test_transcription_integration.py::TestBasicTranscription -v

# Run with detailed output
pytest tests/integration/ -v -s

# Skip slow tests
pytest tests/integration/ -v -m "not slow"
```

**Expected results** (Phase 6 TODO: verify):
- ✅ All integration tests pass
- ⏱️ ~5-10 minutes total runtime (depends on test videos)
- 📊 Performance metrics logged

---

### Performance Benchmarking

```bash
# Run benchmark tests only
pytest tests/integration/ -v -m benchmark

# Run benchmarks and save results
pytest tests/integration/ -v -m benchmark --benchmark-save=results

# Compare benchmark results
pytest-benchmark compare
```

**Metrics to track** (Phase 6 TODO: implement):
- Transcription speed (real-time factor)
- Diarization processing time
- Video analysis frames per second
- Screenshot extraction speed
- Memory usage per tool
- Model loading times

---

## Test Categories

### 1. Smoke Tests

Quick sanity checks to verify basic functionality:

```bash
pytest tests/integration/ -v -m smoke
```

**Coverage**:
- [ ] Each tool can be called without errors
- [ ] Output files are created
- [ ] Basic format validation

---

### 2. Functional Tests

Comprehensive feature testing:

```bash
pytest tests/integration/ -v -m functional
```

**Coverage**:
- [ ] All input parameters work correctly
- [ ] Output formats (SRT, JSON, TXT) are valid
- [ ] Speaker detection works
- [ ] Frame analysis produces reasonable results
- [ ] Screenshot deduplication works

---

### 3. Edge Case Tests

Handling of unusual inputs:

```bash
pytest tests/integration/ -v -m edge_case
```

**Test cases**:
- [ ] Very long videos (>1 hour)
- [ ] Very short videos (<10 seconds)
- [ ] Poor audio quality
- [ ] High-resolution 4K video
- [ ] Video with no speech
- [ ] Video with multiple overlapping speakers
- [ ] Corrupted/invalid video files

---

### 4. Performance Tests

Benchmarking and optimization validation:

```bash
pytest tests/integration/ -v -m performance
```

**Metrics**:
- [ ] Transcription: <0.05 RTF on M4 Mac mini
- [ ] Diarization: <0.5 RTF on M4 Mac mini
- [ ] Video analysis: 2-3 fps
- [ ] Screenshot extraction: 1-2 effective fps
- [ ] Memory usage: <8GB for typical videos

---

## Writing New Tests

### Integration Test Template

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "videos"

class TestNewFeature:
    """Test description."""

    def test_basic_functionality(self):
        """Test basic case."""
        # Arrange
        video_path = FIXTURES_DIR / "test_video.mp4"

        # Act
        result = call_tool(video_path)

        # Assert
        assert result["status"] == "success"
        assert Path(result["output_path"]).exists()
```

### Test Markers

Mark tests with pytest markers for selective running:

```python
@pytest.mark.smoke
def test_quick_check():
    """Quick smoke test."""
    pass

@pytest.mark.slow
def test_long_video():
    """Test with 10-minute video."""
    pass

@pytest.mark.benchmark
def test_performance():
    """Performance benchmark test."""
    pass

@pytest.mark.edge_case
def test_corrupted_input():
    """Test error handling."""
    pass
```

---

## Continuous Integration

<!-- TODO Phase 6: Set up CI/CD -->

### GitHub Actions Workflow

```yaml
# TODO: Create .github/workflows/test.yml
# - Run unit tests on every push
# - Run integration tests on pull requests
# - Generate coverage reports
# - Upload artifacts
```

---

## Test Data Management

### Test Video Storage

- ❌ **Do NOT commit** test videos to git (too large)
- ✅ **Do commit** test video metadata and download scripts
- ✅ **Do document** test video requirements in `tests/fixtures/videos/README.md`

### Test Outputs

Integration tests should clean up after themselves:

```python
import tempfile
import shutil

def test_with_cleanup():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Test code here
        pass
    finally:
        shutil.rmtree(temp_dir)
```

---

## Troubleshooting Tests

### Common Issues

**Issue**: Test videos not found
```bash
# Solution: Download test videos
python scripts/download_test_videos.py
```

**Issue**: HuggingFace token not configured
```bash
# Solution: Create secrets.json with HF token
echo '{"hf_token": "your_token"}' > secrets.json
```

**Issue**: FFmpeg not found
```bash
# Solution: Install FFmpeg
brew install ffmpeg  # macOS
```

**Issue**: Tests timeout
```bash
# Solution: Increase pytest timeout
pytest --timeout=600  # 10 minutes
```

---

## Test Coverage Goals

### Phase 6 Targets

- **Unit tests**: ✅ 95% (achieved in Phase 1-5)
- **Integration tests**: 🎯 80% of user workflows
- **Edge cases**: 🎯 Major error paths covered
- **Performance**: 🎯 All tools benchmarked

---

## Reporting Bugs

When reporting test failures, include:

1. Test command used
2. Full error output
3. System information (macOS version, hardware)
4. Test video characteristics
5. Logs from `logs/` directory (if applicable)

---

**Last Updated**: Phase 6 Framework (2025-11-15)
