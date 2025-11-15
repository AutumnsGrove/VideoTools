# Test Video Collection Summary

**Status**: Ready to download
**Total Videos**: 10
**Total Size**: ~700 MB
**License**: All Creative Commons or Public Domain

---

## Quick Download

### Download All Videos
```bash
python scripts/download_test_videos.py
```

### Download Specific Video
```bash
python scripts/download_test_videos.py --video short_tutorial
```

### Skip Already Downloaded
```bash
python scripts/download_test_videos.py --skip-existing
```

---

## Video Breakdown

| Category | Count | Total Size | Duration Range |
|----------|-------|------------|----------------|
| Single Speaker | 4 | ~73 MB | 60s - 11min |
| Multi-Speaker | 2 | ~342 MB | 3min - 5min |
| Visual Content | 2 | ~106 MB | 90s - 12min |
| Long-Form/Edge | 2 | ~171 MB | 14min - 15min |
| **TOTAL** | **10** | **~700 MB** | **60s - 15min** |

---

## Test Coverage

### Duration Coverage
- ✅ **Short** (< 2min): 3 videos
- ✅ **Medium** (2-6min): 3 videos
- ✅ **Long** (10-15min): 4 videos

### Speaker Coverage
- ✅ **Single speaker**: 4 videos
- ✅ **Two speakers**: 1 video
- ✅ **Three+ speakers**: 2 videos
- ✅ **No dialogue** (visual only): 1 video

### Resolution Coverage
- ✅ **480p**: 2 videos (TED talks)
- ✅ **720p+**: Most videos
- ✅ **1080p**: 2 videos (Blender films)
- ✅ **2048p** (4K): 1 video (Sintel)

### Content Type Coverage
- ✅ Educational tutorials (Khan Academy)
- ✅ Professional presentations (TED Talks)
- ✅ Interviews & conversations
- ✅ Animated historical narration
- ✅ Cinematic content (Blender films)

---

## Video Details

### 1. short_30s_addition_tutorial.mp4
- **Source**: Khan Academy
- **Duration**: ~60s
- **Size**: 5.6 MB
- **Speakers**: 1
- **Purpose**: Quick smoke tests, basic transcription

### 2. short_120s_edward_viii.mp4
- **Source**: History Matters
- **Duration**: ~120s
- **Size**: 6.1 MB
- **Speakers**: 1
- **Purpose**: Short animated narration, clear audio quality

### 3. medium_357s_clayton_cameron_ted.mp4
- **Source**: TED Talk
- **Duration**: 5:57 (357s)
- **Size**: 42.3 MB
- **Resolution**: 480p
- **Speakers**: 1
- **Purpose**: Medium-length professional presentation

### 4. long_663s_big_bang_tutorial.mp4
- **Source**: Khan Academy
- **Duration**: 11:03 (663s)
- **Size**: 19.6 MB
- **Speakers**: 1
- **Purpose**: Long-form educational content

### 5. multi_180s_job_interview.mp4
- **Source**: Archive.org
- **Duration**: ~3min (180s)
- **Size**: 92.4 MB
- **Speakers**: 2+
- **Purpose**: Speaker diarization with interview format

### 6. multi_300s_cafe_conversation.mp4
- **Source**: Timothy Leary Archives
- **Duration**: ~5min (300s)
- **Size**: 249.6 MB
- **Speakers**: 3
- **Purpose**: Natural multi-speaker conversation

### 7. visual_90s_llama_drama_1080p.mp4
- **Source**: Caminandes (Blender Foundation)
- **Duration**: 90s
- **Size**: 33.5 MB
- **Resolution**: 1080p
- **Speakers**: 0 (animated short)
- **Purpose**: Visual content analysis, scene detection

### 8. visual_734s_tears_steel_1080p.mp4
- **Source**: Blender Foundation
- **Duration**: 12:14 (734s)
- **Size**: 72.6 MB
- **Resolution**: 1080p
- **Speakers**: 3 (dialogue in film)
- **Purpose**: Visual effects, scene changes, multi-speaker

### 9. long_883s_david_rose_ted.mp4
- **Source**: TED Talk
- **Duration**: 14:43 (883s)
- **Size**: 97.2 MB
- **Resolution**: 480p
- **Speakers**: 1
- **Purpose**: Long-form presentation, performance testing

### 10. edge_888s_sintel_2048p.mp4
- **Source**: Blender Foundation
- **Duration**: 14:48 (888s)
- **Size**: 73.8 MB
- **Resolution**: 2048p
- **Speakers**: 2 (dialogue in film)
- **Purpose**: 4K/high-resolution testing, memory usage

---

## Download Instructions

The download script (`scripts/download_test_videos.py`) uses `curl` to download videos directly from:
- Archive.org (Khan Academy, historical content, conversations)
- TED.com (official TED download API)
- Blender Foundation (official Blender film releases)

All videos are freely licensed and legal to download for testing purposes.

---

## Next Steps After Download

1. **Verify downloads**: Check all 10 videos downloaded successfully
2. **Run quick test**: Test transcription on short video
3. **Implement integration tests**: Create pytest test suite
4. **Run benchmarks**: Measure performance on each category
5. **Document results**: Update README and BENCHMARKS.md

---

**Generated**: 2025-11-15
**Last Updated**: 2025-11-15
