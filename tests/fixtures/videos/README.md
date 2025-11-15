# Test Video Fixtures

This directory contains test videos for integration testing of the VideoTools MCP Server.

## Test Video Requirements

For comprehensive testing, we need videos with the following characteristics:

### 1. Short Test Video (30 seconds)
**Purpose**: Quick smoke tests, basic functionality verification
**Requirements**:
- Duration: ~30 seconds
- Content: Single speaker, clear audio
- Resolution: 720p or higher
- Format: MP4 (H.264)
- Use case: Basic transcription, quick turnaround testing

**Suggested source**: Create a simple screen recording with narration

---

### 2. Multi-Speaker Test Video (2-3 minutes)
**Purpose**: Speaker diarization testing
**Requirements**:
- Duration: 2-3 minutes
- Content: 2-3 distinct speakers with alternating dialogue
- Audio: Clear speaker separation
- Format: MP4 (H.264)
- Use case: Testing transcribe_with_speakers, rename_speakers

**Suggested source**: Interview clips, podcast segments

---

### 3. Visual Content Test Video (5 minutes)
**Purpose**: Video analysis and screenshot extraction
**Requirements**:
- Duration: ~5 minutes
- Content: Varied scenes with different visual elements
  - Scene changes
  - Text overlays (for OCR testing)
  - Different objects/people
  - Transitions
- Resolution: 1080p
- Format: MP4 (H.264)
- Use case: Testing analyze_video, extract_smart_screenshots

**Suggested source**: Tutorial videos, presentations with slides

---

### 4. Long-Form Test Video (10-15 minutes)
**Purpose**: Performance testing, edge case handling
**Requirements**:
- Duration: 10-15 minutes
- Content: Mix of speakers and visual content
- Format: MP4 (H.264)
- Use case: Performance benchmarking, memory usage testing

---

### 5. Edge Case Test Videos

#### Poor Audio Quality (1-2 minutes)
- Low bitrate audio
- Background noise
- Muffled speech
- Use case: Robustness testing

#### High-Motion Video (1-2 minutes)
- Fast camera movement
- Action sequences
- Use case: Frame extraction edge cases

#### 4K High-Resolution (1 minute)
- 4K resolution
- Use case: Memory usage, processing time testing

---

## Downloading Test Videos

### Option 1: Free Stock Videos
```bash
# Run the download script (to be created in Phase 6)
python scripts/download_test_videos.py
```

### Option 2: Manual Download
Sources for free test videos:
- **Pexels Videos**: https://www.pexels.com/videos/
- **Pixabay**: https://pixabay.com/videos/
- **Coverr**: https://coverr.co/
- **Videvo**: https://www.videvo.net/

### Option 3: Create Your Own
```bash
# Record a simple test video with ffmpeg
ffmpeg -f avfoundation -i "0:0" -t 30 -vf "scale=1280:720" short_test.mp4

# Or use QuickTime Player on macOS for screen recordings
```

---

## Test Video Naming Convention

Please name test videos according to this pattern:
```
{category}_{duration}_{description}.mp4

Examples:
- short_30s_single_speaker.mp4
- multi_180s_interview.mp4
- visual_300s_tutorial.mp4
- long_900s_presentation.mp4
- edge_120s_poor_audio.mp4
```

---

## Current Test Videos

<!-- Update this section as videos are added -->
- [ ] Short test video (30s)
- [ ] Multi-speaker video (2-3 min)
- [ ] Visual content video (5 min)
- [ ] Long-form video (10-15 min)
- [ ] Poor audio quality video
- [ ] High-motion video
- [ ] 4K video

---

## Usage in Tests

Test videos will be referenced in integration tests like this:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "videos"
SHORT_TEST_VIDEO = FIXTURES_DIR / "short_30s_single_speaker.mp4"
MULTI_SPEAKER_VIDEO = FIXTURES_DIR / "multi_180s_interview.mp4"
```

---

**Note**: Test videos are NOT committed to git due to size. Each developer/CI environment should download or generate test videos locally.
