# Running Phase 6 Integration Tests

This guide provides step-by-step instructions for running the VideoTools MCP Server integration tests.

## Prerequisites Checklist

### 1. Test Videos
✅ **Status**: 8/10 videos downloaded (537MB)

Verify videos are present:
```bash
python scripts/verify_test_setup.py
```

Expected output: "8/10 videos available"

**Downloaded videos:**
- short_30s_addition_tutorial.mp4 (5.6MB)
- short_120s_edward_viii.mp4 (6.1MB)
- multi_180s_job_interview.mp4 (92MB)
- multi_300s_cafe_conversation.mp4 (250MB)
- visual_90s_llama_drama_1080p.mp4 (33MB)
- visual_734s_tears_steel_1080p.mp4 (73MB)
- long_883s_david_rose_ted.mp4 (97MB)
- edge_888s_sintel_2048p.mp4 (74MB)

### 2. HuggingFace Authentication

**Check if authenticated:**
```bash
huggingface-cli whoami
```

If not authenticated, login:
```bash
huggingface-cli login
```

You'll need a HuggingFace token with read access for:
- Pyannote audio models (speaker diarization)
- Potentially other models

**Accept model licenses:**
Visit these URLs and accept the terms:
- https://huggingface.co/pyannote/speaker-diarization-3.1
- https://huggingface.co/pyannote/segmentation-3.0

### 3. API Keys (if needed)

Check if `secrets.json` exists with required keys:
```bash
cat secrets.json
```

Should contain:
```json
{
  "anthropic_api_key": "sk-ant-api03-...",
  "openrouter_api_key": "sk-or-v1-...",
  "huggingface_token": "hf_..."
}
```

### 4. Python Environment

Verify UV environment is set up:
```bash
uv sync
```

### 5. Disk Space

Integration tests will:
- Download AI models (~2-3GB on first run)
- Create temporary files during processing
- Generate transcripts and screenshots

**Check available space:**
```bash
df -h .
```

Recommended: At least 5GB free space

---

## Running the Tests

### Quick Start: Error Handling Tests Only

These tests are fast and don't require model loading:

```bash
uv run pytest tests/integration/ -v -k "error or invalid"
```

**Expected**: 3 tests pass in < 5 seconds

---

### Full Integration Test Suite

**Step 1: Run Fast Tests First (Excluding Slow Tests)**

```bash
uv run pytest tests/integration/ -v -m "not slow" --tb=short --timeout=600
```

This will:
- Run 31 tests (excluding 2 marked @pytest.mark.slow)
- Skip 19 stub tests
- Take 10-30 minutes depending on:
  - Whether models are already downloaded
  - Your machine's processing speed (M4 Mac Mini baseline)

**Step 2: Run Slow Tests Separately**

```bash
uv run pytest tests/integration/ -v -m "slow" --tb=short --timeout=1200
```

This will:
- Run 2 slow tests (long video processing)
- Take 5-15 minutes per test

**Step 3: Run All Tests Together**

```bash
uv run pytest tests/integration/ -v --tb=short --timeout=1200
```

---

## Test Categories

### By Tool

**Speaker Diarization Tests:**
```bash
uv run pytest tests/integration/test_speaker_diarization_integration.py -v
```
- 18 tests
- Tests: transcribe_with_speakers, rename_speakers
- Estimated time: 15-25 minutes

**Screenshot Extraction Tests:**
```bash
uv run pytest tests/integration/test_screenshot_extraction_integration.py -v
```
- 12 tests
- Tests: extract_smart_screenshots
- Estimated time: 20-40 minutes (AI model evaluation is slow)

**Workflow Tests:**
```bash
uv run pytest tests/integration/test_cross_tool_workflows.py -v
```
- 3 tests
- Tests: Multi-tool workflows
- Estimated time: 10-20 minutes

### By Test Class

**Run specific test class:**
```bash
uv run pytest tests/integration/test_speaker_diarization_integration.py::TestBasicSpeakerDiarization -v
```

**Run specific test:**
```bash
uv run pytest tests/integration/test_speaker_diarization_integration.py::TestBasicSpeakerDiarization::test_diarize_two_speaker_interview -v
```

---

## Expected First-Run Behavior

### On First Run

**Model Downloads (one-time):**
- Parakeet TDT 0.6B model (~600MB)
- Pyannote speaker diarization models (~500MB)
- Qwen VL 8B model (~4GB compressed, 8GB uncompressed)

**Where models are stored:**
- `~/.cache/huggingface/` (Pyannote, Qwen VL)
- MLX cache for Parakeet

**Progress indication:**
- Models download with progress bars
- First test will be slow while models load
- Subsequent tests reuse loaded models

### Typical Processing Times (M4 Mac Mini)

**Speaker Diarization:**
- Short video (30s): ~30-60s processing
- Medium video (3min): ~2-5 minutes processing
- Long video (15min): ~10-20 minutes processing

**Screenshot Extraction:**
- 90s video: ~5-10 minutes (AI evaluation per frame)
- 12min video: ~20-40 minutes

**RTF (Real-Time Factor) Targets:**
- Transcription: RTF < 0.05 (20x faster than real-time)
- Diarization: RTF < 0.5 (2x faster than real-time)
- Screenshots: ~1-2 fps AI evaluation

---

## Troubleshooting

### Issue: Tests fail with "Model not found"

**Solution:**
```bash
# Re-run model downloads
uv run python -c "from video_tools_mcp.models.parakeet import ParakeetModel; m = ParakeetModel(); m.ensure_loaded()"
uv run python -c "from video_tools_mcp.models.pyannote import PyannoteModel; m = PyannoteModel(); m.ensure_loaded()"
uv run python -c "from video_tools_mcp.models.qwen_vl import QwenVLModel; m = QwenVLModel(); m.load()"
```

### Issue: "401 Unauthorized" for Pyannote

**Solution:**
1. Check HuggingFace authentication: `huggingface-cli whoami`
2. Accept model licenses (see Prerequisites section)
3. Verify token in secrets.json

### Issue: Tests timeout

**Solution:**
Increase timeout for slow tests:
```bash
uv run pytest tests/integration/ -v --timeout=1800
```

### Issue: Out of memory

**Solution:**
- Close other applications
- Run tests one at a time
- Consider using smaller test videos

### Issue: "Video file not found"

**Solution:**
Download test videos:
```bash
python scripts/download_test_videos.py
```

---

## Understanding Test Output

### Passing Test Example
```
tests/integration/test_speaker_diarization_integration.py::TestBasicSpeakerDiarization::test_diarize_two_speaker_interview PASSED [10%]
```

### Skipped Test Example
```
tests/integration/test_transcription_integration.py::TestBasicTranscription::test_transcribe_short_video_srt SKIPPED [20%]
```
(Skipped = stub test waiting for implementation)

### Failed Test Example
```
tests/integration/test_speaker_diarization_integration.py::TestBasicSpeakerDiarization::test_diarize_two_speaker_interview FAILED [10%]
```

Check traceback for:
- Model loading issues
- Video file path issues
- Assertion failures (check expected vs actual values)

---

## Test Coverage Report

Generate coverage report:
```bash
uv run pytest tests/integration/ --cov=video_tools_mcp --cov-report=html
```

View report:
```bash
open htmlcov/index.html
```

---

## Performance Benchmarking

Run only benchmark tests:
```bash
uv run pytest tests/integration/ -v -m "benchmark" --tb=short
```

These tests will output:
- Video duration
- Processing time
- RTF (Real-Time Factor)
- Frames per second (for screenshot extraction)

---

## Continuous Testing Strategy

### Quick Smoke Test (< 5 minutes)
```bash
uv run pytest tests/integration/ -v -k "error or invalid" --timeout=60
```

### Medium Test Suite (15-30 minutes)
```bash
uv run pytest tests/integration/ -v -m "not slow and not benchmark" --timeout=600
```

### Full Test Suite (30-60 minutes)
```bash
uv run pytest tests/integration/ -v --timeout=1200
```

---

## CI/CD Recommendations

If setting up automated testing:

1. **Cache models** between runs:
   - Cache `~/.cache/huggingface/`
   - Cache MLX model directories

2. **Use test video subset**:
   - Start with 3-4 videos for CI
   - Run full suite nightly

3. **Parallel execution**:
   - Run test files in parallel if resources allow
   - `pytest -n auto` with pytest-xdist

4. **Timeout management**:
   - Set generous timeouts for first run (model downloads)
   - Reduce timeouts after models cached

---

## Expected Test Results Summary

### Currently Passing Tests
- Error handling tests: 3/3 ✅
- Invalid path tests: 3/3 ✅

### Tests Requiring Model Loading
- Speaker diarization: 15 tests ⏳
- Screenshot extraction: 12 tests ⏳
- Workflows: 3 tests ⏳

### Skipped Tests (Stub Implementations)
- Basic transcription: 3 tests (waiting for Phase 2)
- Video analysis: 4 tests (waiting for Phase 4)
- Additional stubs: 12 tests

**Total: 52 tests (6 passing, 30 pending model setup, 16 skipped stubs)**

---

## Getting Help

If tests fail unexpectedly:

1. Check this troubleshooting guide
2. Verify prerequisites (videos, auth, models)
3. Run single test with verbose output: `pytest -vvs <test_path>`
4. Check logs in test output
5. Review test code for expected behavior

---

## Next Steps After Tests Pass

1. **Document performance results** in BENCHMARKS.md
2. **Update README.md** with real-world examples
3. **Generate screenshots** from test runs for documentation
4. **Create CHANGELOG.md** for v1.0 release
5. **Tag release** v1.0.0

---

**Last Updated:** 2025-11-15
**Test Suite Version:** Phase 6 - Integration Tests
**Status:** Ready to run with model downloads
