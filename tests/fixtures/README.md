# Test Fixtures

## Overview

This directory contains test data for integration and end-to-end testing of the Video Tools MCP Server.

**Phase 1 Note**: Currently not needed. All Phase 1 tests use mocks and don't require real video files.

**Phase 2+**: Starting in Phase 2, we'll add real video files here for integration testing of transcription, diarization, and video analysis features.

## Required Test Files (Phase 2+)

### Video Files

You'll need to add the following test video files to this directory before running integration tests:

#### 1. `test_30s.mp4`
- **Purpose**: Single speaker transcription testing
- **Duration**: 30 seconds
- **Content**: Clear speech, single speaker, minimal background noise
- **Size**: < 5MB
- **Format**: MP4 (H.264 video, AAC audio)
- **Resolution**: 720p or higher

#### 2. `test_30s_2speakers.mp4`
- **Purpose**: Speaker diarization testing
- **Duration**: 30 seconds
- **Content**: Two distinct speakers alternating, clear speech
- **Size**: < 5MB
- **Format**: MP4 (H.264 video, AAC audio)
- **Resolution**: 720p or higher

#### 3. `test_scene_changes.mp4`
- **Purpose**: Video analysis and screenshot extraction testing
- **Duration**: 30-60 seconds
- **Content**: Multiple scene transitions, varied content
- **Size**: < 10MB
- **Format**: MP4 (H.264 video, AAC audio)
- **Resolution**: 720p or higher

### Audio Files (Optional)

#### 4. `test_audio.wav`
- **Purpose**: Direct audio transcription testing (bypass video extraction)
- **Duration**: 30 seconds
- **Format**: WAV, 16kHz mono, PCM S16LE
- **Size**: < 2MB

## Creating Test Files

### Option 1: Extract from Existing Videos

Use FFmpeg to extract 30-second clips from longer videos:

```bash
# Extract 30 seconds starting at 1:00
ffmpeg -i input.mp4 -ss 00:01:00 -t 30 -c copy test_30s.mp4

# Extract with re-encoding (ensures compatibility)
ffmpeg -i input.mp4 -ss 00:01:00 -t 30 \
  -c:v libx264 -c:a aac -b:a 128k \
  test_30s.mp4

# Create 16kHz mono WAV from video
ffmpeg -i test_30s.mp4 -ar 16000 -ac 1 test_audio.wav
```

### Option 2: Download Free Test Videos

Free test videos are available from:

- **Sample Videos**: https://sample-videos.com/
- **Test Videos UK**: https://test-videos.co.uk/
- **Pexels**: https://www.pexels.com/videos/ (short clips)

**Requirements for downloaded videos:**
- Clear speech with minimal background noise
- Good audio quality (no distortion)
- Standard codecs (H.264 video, AAC audio)
- Reasonable file size (< 10MB per file)

### Option 3: Record Your Own

Use any screen recording or video capture tool:

```bash
# macOS: Use QuickTime Player
# File → New Screen Recording
# Record 30 seconds of speech
# Export as MP4

# Linux: Use ffmpeg with webcam
ffmpeg -f v4l2 -i /dev/video0 -t 30 test_30s.mp4

# Windows: Use OBS Studio or built-in Game Bar
# Win+G → Record 30 seconds → Export as MP4
```

## File Specifications

### Video Requirements

- **Container**: MP4, MOV, or AVI
- **Video Codec**: H.264, H.265, or VP9
- **Audio Codec**: AAC, MP3, or PCM
- **Duration**: 30-60 seconds (keep short for fast tests)
- **File Size**: < 10MB per file (smaller is better for CI/CD)
- **Resolution**: 720p or higher (but 1080p is fine)
- **Frame Rate**: 24-60 fps

### Audio Requirements (for direct audio files)

- **Format**: WAV (uncompressed)
- **Sample Rate**: 16kHz (Parakeet optimal)
- **Channels**: 1 (mono)
- **Bit Depth**: 16-bit
- **Duration**: 30 seconds
- **File Size**: < 2MB

### Content Requirements

**For Transcription Tests:**
- Clear, understandable speech
- Minimal background noise
- Standard English (or specify language)
- Natural speaking pace

**For Diarization Tests:**
- Two or more distinct speakers
- Clear speaker changes (not overlapping)
- Each speaker talks for at least 5 seconds
- Minimal crosstalk

**For Video Analysis Tests:**
- Varied visual content
- Scene transitions (cuts, fades)
- Different lighting conditions
- Text or objects to identify

## Integration Test Usage

Once you've added test files, integration tests will use them like this:

```python
# tests/integration/test_transcription.py
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_VIDEO = FIXTURES_DIR / "test_30s.mp4"

@pytest.mark.integration
def test_transcribe_real_video():
    """Test transcription with real video file"""
    assert TEST_VIDEO.exists(), "Test video not found. See tests/fixtures/README.md"

    result = transcribe_video(str(TEST_VIDEO))

    assert result["transcript_path"].endswith(".srt")
    assert result["duration"] > 0
    assert result["word_count"] > 0
```

## Git Ignore

**Important**: Test video files should NOT be committed to git due to their size.

The `.gitignore` already includes:

```gitignore
# Test fixtures (large binary files)
tests/fixtures/*.mp4
tests/fixtures/*.mov
tests/fixtures/*.avi
tests/fixtures/*.wav
tests/fixtures/*.mp3

# Keep the README
!tests/fixtures/README.md
```

This means you need to add test files locally, but they won't be pushed to the repository.

## Continuous Integration (CI)

For CI/CD pipelines (GitHub Actions, etc.), you have two options:

### Option 1: Download Test Files in CI

```yaml
# .github/workflows/test.yml
- name: Download test fixtures
  run: |
    wget -O tests/fixtures/test_30s.mp4 \
      https://example.com/test-videos/test_30s.mp4
```

### Option 2: Use Git LFS

For larger projects, use Git Large File Storage:

```bash
# Install Git LFS
git lfs install

# Track video files
git lfs track "tests/fixtures/*.mp4"
git lfs track "tests/fixtures/*.mov"

# Add and commit
git add .gitattributes tests/fixtures/
git commit -m "Add test fixtures with Git LFS"
```

## Troubleshooting

### Test file not found

```bash
# Check if files exist
ls -lh tests/fixtures/

# If missing, add them as described above
```

### FFmpeg errors during tests

```bash
# Verify FFmpeg installation
ffmpeg -version

# Test video file integrity
ffmpeg -v error -i tests/fixtures/test_30s.mp4 -f null -

# Re-encode if corrupted
ffmpeg -i tests/fixtures/test_30s.mp4 -c:v libx264 -c:a aac \
  tests/fixtures/test_30s_fixed.mp4
```

### Tests skipped

Integration tests are marked with `@pytest.mark.integration` and may be skipped if:

1. Test files are missing (expected in Phase 1)
2. Models not installed (expected before Phase 2)
3. Running unit tests only (`pytest tests/unit/`)

To run integration tests (Phase 2+):

```bash
# Run all tests including integration
uv run pytest tests/ -v

# Run only integration tests
uv run pytest tests/integration/ -v
```

## Phase-by-Phase Test File Needs

### Phase 1: Core Infrastructure ✅
- **Files Needed**: None (all tests use mocks)
- **Status**: Complete

### Phase 2: Transcription
- **Files Needed**: `test_30s.mp4`, `test_audio.wav`
- **Purpose**: Test Parakeet transcription with real audio

### Phase 3: Speaker Diarization
- **Files Needed**: `test_30s_2speakers.mp4`
- **Purpose**: Test speaker identification and labeling

### Phase 4: Video Analysis
- **Files Needed**: `test_scene_changes.mp4`
- **Purpose**: Test frame extraction and Qwen VL analysis

### Phase 5: Smart Screenshots
- **Files Needed**: `test_scene_changes.mp4` (reuse from Phase 4)
- **Purpose**: Test screenshot extraction and deduplication

## Contributing Test Files

If you create high-quality test files that you can share:

1. **Ensure you have rights** to share the content
2. **Keep files small** (< 5MB preferred)
3. **Document the content** (what's being said, what's shown)
4. **Upload to public hosting** (Google Drive, Dropbox, etc.)
5. **Share the link** in an issue or PR

## Example Test File Documentation

When adding test files, document them like this:

```markdown
### test_30s.mp4
- **Duration**: 30 seconds
- **Speaker**: Single male voice
- **Content**: Reading of a technical article about AI
- **Language**: English (US accent)
- **Audio Quality**: Clean studio recording, no background noise
- **Video Content**: Static screen capture of text
- **Expected Word Count**: ~75 words
- **Expected Transcript**: "Artificial intelligence has transformed..."
```

This helps others understand what results to expect from tests.

---

**Last Updated**: Phase 1 Complete (2025-11-15)
**Status**: No test files required until Phase 2
**Next Update**: Phase 2 (Add test_30s.mp4 and test_audio.wav)
