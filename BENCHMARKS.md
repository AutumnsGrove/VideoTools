# Performance Benchmarks - VideoTools MCP Server

**Status**: Phase 6 Template - To be populated with actual measurements

---

## Test Environment

**Hardware**: M4 Mac mini (2024)
**CPU**: Apple M4 (10 cores)
**GPU**: Apple M4 GPU (10 cores)
**RAM**: 16GB unified memory
**Storage**: SSD
**OS**: macOS Sonoma 14.x

---

## Benchmark Methodology

### Test Videos

| ID | Name | Duration | Resolution | Size | Speakers | Notes |
|----|------|----------|------------|------|----------|-------|
| TV1 | short_30s_single_speaker.mp4 | 30s | 720p | ~5MB | 1 | Basic test |
| TV2 | multi_180s_interview.mp4 | 3min | 1080p | ~20MB | 2-3 | Diarization test |
| TV3 | visual_300s_tutorial.mp4 | 5min | 1080p | ~40MB | 1 | Visual analysis |
| TV4 | long_900s_presentation.mp4 | 15min | 1080p | ~100MB | 2 | Performance test |

### Measurement Tools

- **Time**: Python `time.time()` for wall-clock time
- **Memory**: `psutil` for peak memory usage
- **Profiling**: `cProfile` for detailed analysis
- **Iterations**: 3 runs per test, median reported

---

## Tool 1: `transcribe_video` (Phase 2)

### Performance Targets

- **Speed**: 20-30x real-time (1 minute video → 2-3 seconds processing)
- **Memory**: <2GB peak usage
- **Accuracy**: WER <10% on clean audio

### Benchmark Results

<!-- TODO Phase 6: Fill in actual measurements -->

| Test Video | Duration | Processing Time | Real-Time Factor | Memory (MB) | WER % |
|------------|----------|----------------|------------------|-------------|-------|
| TV1 (30s) | 30s | TBD | TBD | TBD | TBD |
| TV2 (3min) | 180s | TBD | TBD | TBD | TBD |
| TV3 (5min) | 300s | TBD | TBD | TBD | TBD |
| TV4 (15min) | 900s | TBD | TBD | TBD | TBD |

**Notes**:
- Real-Time Factor (RTF) = Processing Time / Video Duration
- Lower RTF is better (0.05 = 20x real-time)
- WER = Word Error Rate (requires reference transcripts)

---

## Tool 2: `transcribe_with_speakers` (Phase 3)

### Performance Targets

- **Speed**: 2-3x real-time (1 minute video → 30-45 seconds processing)
- **Memory**: <4GB peak usage
- **Accuracy**: DER <15% on clear multi-speaker audio

### Benchmark Results

<!-- TODO Phase 6: Fill in actual measurements -->

| Test Video | Duration | Processing Time | Real-Time Factor | Memory (MB) | Speakers Detected | DER % |
|------------|----------|----------------|------------------|-------------|-------------------|-------|
| TV2 (3min) | 180s | TBD | TBD | TBD | TBD | TBD |
| TV4 (15min) | 900s | TBD | TBD | TBD | TBD | TBD |

**Notes**:
- DER = Diarization Error Rate (requires reference labels)
- Includes both transcription + diarization time
- Speaker detection accuracy varies with audio quality

---

## Tool 3: `analyze_video` (Phase 4)

### Performance Targets

- **Speed**: 2-3 frames/second
- **Memory**: <6GB peak usage
- **Quality**: Meaningful frame descriptions

### Benchmark Results

<!-- TODO Phase 6: Fill in actual measurements -->

| Test Video | Frames Analyzed | Processing Time | FPS | Memory (MB) | Tokens/Frame (avg) |
|------------|----------------|----------------|-----|-------------|--------------------|
| TV1 (6 frames) | 6 | TBD | TBD | TBD | TBD |
| TV3 (60 frames) | 60 | TBD | TBD | TBD | TBD |
| TV4 (180 frames) | 180 | TBD | TBD | TBD | TBD |

**Notes**:
- FPS = Frames analyzed per second
- Sample interval: 5 seconds between frames
- Includes frame extraction + Qwen VL inference time

---

## Tool 4: `extract_smart_screenshots` (Phase 5)

### Performance Targets

- **Speed**: 1-2 effective frames/second (after deduplication)
- **Memory**: <6GB peak usage
- **Quality**: 5-10 meaningful screenshots per 10-minute video

### Benchmark Results

<!-- TODO Phase 6: Fill in actual measurements -->

| Test Video | Frames Extracted | Duplicates Removed | Screenshots Kept | Processing Time | Effective FPS |
|------------|-----------------|-------------------|------------------|----------------|---------------|
| TV3 (5min) | TBD | TBD | TBD | TBD | TBD |
| TV4 (15min) | TBD | TBD | TBD | TBD | TBD |

**Notes**:
- Effective FPS = Frames evaluated / Processing time
- Deduplication typically removes 20-40% of frames
- AI evaluation adds ~0.5s per unique frame

---

## Combined Workflow Performance

### Full Pipeline Test

**Scenario**: Process a 5-minute interview video with all tools

<!-- TODO Phase 6: Measure full pipeline -->

| Step | Tool | Time (s) | Memory (MB) |
|------|------|----------|-------------|
| 1. Basic transcription | transcribe_video | TBD | TBD |
| 2. Speaker diarization | transcribe_with_speakers | TBD | TBD |
| 3. Rename speakers | rename_speakers | TBD | TBD |
| 4. Video analysis | analyze_video | TBD | TBD |
| 5. Screenshot extraction | extract_smart_screenshots | TBD | TBD |
| **Total** | - | **TBD** | **TBD (peak)** |

---

## Memory Usage Profile

### Peak Memory by Tool

<!-- TODO Phase 6: Measure memory usage -->

```
transcribe_video:              [████░░░░░░] TBD MB
transcribe_with_speakers:     [████████░░] TBD MB
analyze_video:                 [██████████] TBD MB
extract_smart_screenshots:    [██████████] TBD MB
```

### Memory Timeline

<!-- TODO Phase 6: Profile memory over time -->

```
Memory (GB)
    8 │                    ╭─╮
    7 │                ╭───╯ ╰───╮
    6 │            ╭───╯         ╰───╮
    5 │        ╭───╯                 ╰───╮
    4 │    ╭───╯                         ╰───╮
    3 │╭───╯                                 ╰───╮
    2 │╯                                         ╰───
    1 │
    0 └────────────────────────────────────────────
      0s   30s  60s  90s 120s 150s 180s 210s 240s
```

---

## Model Loading Times

### First Load (Cold Start)

<!-- TODO Phase 6: Measure model load times -->

| Model | Load Time | Disk Size | Memory Size |
|-------|-----------|-----------|-------------|
| Parakeet TDT | TBD | TBD | TBD |
| Pyannote Speaker Diarization | TBD | TBD | TBD |
| Qwen2-VL-8B-Instruct | TBD | TBD | TBD |

### Subsequent Loads (Warm Start)

Models are cached in memory after first load. Subsequent calls should be near-instantaneous.

---

## Optimization Opportunities

<!-- TODO Phase 6: Identify bottlenecks -->

### Potential Improvements

1. **Batch Processing**
   - Current: Sequential frame processing
   - Proposed: Batch Qwen VL inference
   - Expected gain: 20-30% faster video analysis

2. **Parallel Pipelines**
   - Current: Single-threaded model inference
   - Proposed: Parallel transcription + diarization
   - Expected gain: 30-40% faster for multi-tool workflows

3. **Frame Caching**
   - Current: Extract frames twice for analysis + screenshots
   - Proposed: Shared frame cache
   - Expected gain: 15-20% faster when using both tools

---

## Comparison with Alternatives

<!-- TODO Phase 6: Compare with other solutions -->

### Transcription Speed

| Tool | RTF (lower is better) | Notes |
|------|-----------------------|-------|
| VideoTools (Parakeet MLX) | TBD | Apple Silicon optimized |
| Whisper.cpp | ~0.5 | CPU-based |
| Whisper Large (GPU) | ~0.3 | NVIDIA GPU required |
| Cloud APIs (AssemblyAI, etc.) | ~1.0 | Network latency included |

### Diarization Accuracy

| Tool | DER (lower is better) | Notes |
|------|-----------------------|-------|
| VideoTools (Pyannote) | TBD | State-of-the-art model |
| Pyannote (CPU) | ~12-15% | Benchmark reference |
| Cloud APIs | ~10-12% | Proprietary models |

---

## Stress Testing

### Long Video Tests

<!-- TODO Phase 6: Test with very long videos -->

| Duration | Tools Used | Status | Notes |
|----------|-----------|--------|-------|
| 30 minutes | All | TBD | - |
| 1 hour | All | TBD | - |
| 2 hours | transcribe_video only | TBD | - |

### High-Resolution Tests

<!-- TODO Phase 6: Test with 4K videos -->

| Resolution | Tools Used | Status | Notes |
|------------|-----------|--------|-------|
| 1080p | All | TBD | Standard resolution |
| 4K | analyze_video, screenshots | TBD | Memory intensive |

---

## Conclusion

<!-- TODO Phase 6: Write summary after benchmarking -->

### Summary
- Overall performance meets/exceeds targets: ✅/❌
- Memory usage within acceptable limits: ✅/❌
- Optimization needed for: [list areas]

### Recommendations
- [ ] Recommendation 1
- [ ] Recommendation 2
- [ ] Recommendation 3

---

**Last Updated**: Phase 6 Template (2025-11-15)

**Run Benchmarks**:
```bash
pytest tests/integration/ -v -m benchmark
```
