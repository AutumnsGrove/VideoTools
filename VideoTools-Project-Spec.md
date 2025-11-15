# Video Tools MCP Server - Project Specification

**Version:** 1.0  
**Created:** November 14, 2025  
**Author:** Autumn Brown  
**Repository:** autumnsgrove/video-tools (existing repo, adding MCP server)

-----

## Executive Summary

An MCP (Model Context Protocol) server providing local, privacy-focused video transcription, speaker diarization, and intelligent video analysis tools. Optimized for Apple Silicon (M4 Mac mini, 32GB RAM) with batch processing capabilities for personal vlog archives.

-----

## Core Objectives

1. **Local-first processing** - All models run on-device, no cloud dependencies for core functionality
1. **Privacy-focused** - Personal video content never leaves the machine
1. **MCP-compatible** - Easy integration with AI assistants and agentic workflows
1. **Modular architecture** - Tools can be used independently or in combination
1. **Batch-ready** - Designed for per-video operation but scalable to batch processing

-----

## Technical Stack

### Core Framework

- **Language:** Python 3.11+
- **Package Manager:** UV
- **MCP Framework:** FastMCP
- **Testing:** pytest with test coverage

### ML Frameworks

- **MLX** (Apple’s ML framework) - Parakeet + Qwen VL
- **PyTorch** (with MPS backend) - Pyannote diarization

### Key Dependencies

```toml
[dependencies]
python = ">=3.11"
fastmcp = "^0.2.0"
parakeet-mlx = "^0.4.0"
mlx-vlm = "^0.1.0"
pyannote-audio = "^3.1.0"
torch = "^2.0.0"  # With MPS support
ffmpeg-python = "^0.2.0"
pillow = "^10.0.0"
imagehash = "^4.3.1"
pydantic = "^2.0.0"
```

-----

## Architecture Overview

```
video-tools-mcp/
├── src/
│   ├── video_tools_mcp/
│   │   ├── __init__.py
│   │   ├── server.py                 # FastMCP server entry point
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── parakeet.py          # Parakeet MLX wrapper
│   │   │   ├── pyannote.py          # Pyannote diarization wrapper
│   │   │   ├── qwen_vl.py           # Qwen VL wrapper
│   │   │   └── model_manager.py     # Lazy loading & model lifecycle
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py     # Tools 1-2
│   │   │   ├── analysis.py          # Tools 3-4
│   │   │   └── utilities.py         # Tool 5
│   │   ├── processing/
│   │   │   ├── __init__.py
│   │   │   ├── audio_extraction.py  # Video → audio with ffmpeg
│   │   │   ├── frame_extraction.py  # Video → frames
│   │   │   ├── diarization_merge.py # Merge transcripts + speakers
│   │   │   └── deduplication.py     # pHash-based image dedup
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Model configs (paths, quants)
│   │   │   └── prompts.py           # Default analysis prompts
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py
│   │       └── srt_utils.py         # SRT parsing/writing
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   └── setup_models.py              # Download & verify models
├── pyproject.toml
├── README.md
└── SKILL.md                         # MCP skill documentation
```

-----

## MCP Tools Specification

### Tool 1: `transcribe_video`

**Purpose:** Basic video transcription without speaker identification

**Parameters:**

```python
{
    "video_path": str,              # Required: Path to video file
    "output_format": str,           # Optional: "srt" (default) | "vtt" | "json" | "txt"
    "model": str,                   # Optional: Default "parakeet-tdt-0.6b-v3"
    "language": str                 # Optional: "en" (default), auto-detect not supported
}
```

**Returns:**

```python
{
    "transcript_path": str,         # Path to output file
    "duration": float,              # Video duration in seconds
    "word_count": int,
    "processing_time": float
}
```

**Process:**

1. Extract audio from video (ffmpeg: video → 16kHz mono WAV)
1. Transcribe with Parakeet MLX
1. Generate SRT file with timestamps
1. Save to `{video_path}.srt` (same directory as source)
1. Clean up temporary audio file

-----

### Tool 2: `transcribe_with_speakers`

**Purpose:** Transcription with speaker diarization (multi-speaker support)

**Parameters:**

```python
{
    "video_path": str,              # Required: Path to video file
    "output_format": str,           # Optional: "srt" (default) | "vtt" | "json"
    "num_speakers": int | None,     # Optional: Expected speaker count (None = auto-detect)
    "min_speakers": int,            # Optional: Min speakers (default: 1)
    "max_speakers": int             # Optional: Max speakers (default: 10)
}
```

**Returns:**

```python
{
    "transcript_path": str,         # Path to SRT with speaker labels
    "speakers_detected": int,
    "duration": float,
    "processing_time": float
}
```

**Process:**

1. Extract audio (same as Tool 1)
1. Run Parakeet transcription (word-level timestamps)
1. Run Pyannote diarization (speaker segments with timestamps)
1. Merge transcripts with speaker labels
1. Format: `"Speaker 1: Hello, how are you?"`
1. Save to `{video_path}.speakers.srt`

**Speaker Label Format:**

- Auto-assigned: `Speaker 1`, `Speaker 2`, etc.
- Consistent ordering within a video
- Can be renamed post-processing with Tool 5

-----

### Tool 3: `analyze_video`

**Purpose:** Frame-by-frame analysis with Qwen VL for general video understanding

**Parameters:**

```python
{
    "video_path": str,              # Required: Path to video file
    "analysis_prompt": str,         # Optional: Custom analysis prompt
    "sample_interval": int,         # Optional: Seconds between samples (default: 5)
    "max_frames": int,              # Optional: Max frames to analyze (default: 100)
    "include_ocr": bool             # Optional: Extract text from frames (default: False)
}
```

**Default Prompt:**

```
"Analyze this video frame. Describe: 
1. Main subjects and their activities
2. Scene/location description
3. Notable objects or text visible
4. Emotional tone or atmosphere
Be concise and factual."
```

**Returns:**

```python
{
    "analysis_path": str,           # Path to JSON sidecar file
    "frames_analyzed": int,
    "duration": float,
    "processing_time": float
}
```

**Output Format (JSON):**

```json
{
  "video_path": "/path/to/video.mp4",
  "analyzed_at": "2025-11-14T10:30:00Z",
  "model": "qwen-vl-8b-mlx-8bit",
  "prompt_used": "...",
  "total_frames": 50,
  "frames": [
    {
      "timestamp": 0.0,
      "frame_number": 0,
      "analysis": "Person speaking to camera in well-lit room...",
      "confidence": 0.92,
      "ocr_text": null
    },
    ...
  ]
}
```

**Save Location:** `{video_path}.analysis.json`

-----

### Tool 4: `extract_smart_screenshots`

**Purpose:** AI-driven screenshot extraction with deduplication and auto-captioning

**Parameters:**

```python
{
    "video_path": str,              # Required: Path to video file
    "extraction_prompt": str,       # Optional: Custom prompt for "interesting" moments
    "sample_interval": int,         # Optional: Check every N seconds (default: 5)
    "similarity_threshold": float,  # Optional: pHash similarity % (default: 0.90)
    "max_screenshots": int,         # Optional: Max to extract (default: 50)
    "output_dir": str | None        # Optional: Default = same as video
}
```

**Default Extraction Prompt:**

```
"Evaluate if this frame is worth capturing as a screenshot. 
Capture frames with:
- Clear faces with visible expressions
- Significant scene changes
- Text or important visual information
- Emotionally notable moments
- Unique or memorable compositions

Respond with: CAPTURE or SKIP, followed by a brief reason."
```

**Returns:**

```python
{
    "screenshots": List[str],       # Paths to saved screenshots
    "metadata_path": str,           # Path to JSON metadata file
    "total_extracted": int,
    "duplicates_removed": int,
    "processing_time": float
}
```

**Output Structure:**

```
/path/to/video.mp4
├── video.mp4.screenshots/
│   ├── screenshot_00001_0005s.jpg  # frame number_timestamp
│   ├── screenshot_00045_0225s.jpg
│   └── ...
└── video.mp4.screenshots.json
```

**Metadata Format (JSON):**

```json
{
  "video_path": "/path/to/video.mp4",
  "extracted_at": "2025-11-14T10:30:00Z",
  "total_screenshots": 25,
  "settings": {
    "sample_interval": 5,
    "similarity_threshold": 0.90,
    "model": "qwen-vl-8b-mlx-8bit"
  },
  "screenshots": [
    {
      "filename": "screenshot_00001_0005s.jpg",
      "timestamp": 5.0,
      "frame_number": 150,
      "caption": "Person smiling at camera in outdoor setting",
      "tags": ["portrait", "outdoor", "smiling", "daytime"],
      "phash": "a1b2c3d4e5f6...",
      "capture_reason": "Clear facial expression, good composition"
    },
    ...
  ]
}
```

**Process:**

1. Sample frames at specified interval
1. For each frame:
- Run Qwen VL with extraction prompt
- If “CAPTURE”: check pHash against existing screenshots
- If similarity < threshold: save + generate caption + extract tags
- Store metadata
1. Save all screenshots to subdirectory
1. Write comprehensive JSON metadata file

-----

### Tool 5: `rename_speakers`

**Purpose:** Bulk rename speaker labels in SRT files

**Parameters:**

```python
{
    "srt_path": str,                # Required: Path to SRT file
    "speaker_map": Dict[str, str],  # Required: {"Speaker 1": "Autumn", "Speaker 2": "Alex"}
    "output_path": str | None,      # Optional: Default = overwrite original
    "backup": bool                  # Optional: Create .bak file (default: True)
}
```

**Returns:**

```python
{
    "output_path": str,
    "replacements_made": int,
    "backup_path": str | None
}
```

**Process:**

1. Parse SRT file
1. Replace all instances of old speaker names with new names
1. Validate SRT format integrity
1. Write to output path
1. Create backup if requested

-----

## Model Configuration

### Parakeet MLX

```python
MODEL_ID = "mlx-community/parakeet-tdt-0.6b-v3"
CHUNK_DURATION = 120.0  # 2 minutes
OVERLAP_DURATION = 15.0  # 15 seconds overlap
OUTPUT_FORMAT = "srt"
LANGUAGE = "en"
```

### Pyannote Diarization

```python
MODEL_ID = "pyannote/speaker-diarization-3.1"
DEVICE = "mps"  # Apple Silicon GPU
MIN_DURATION = 0.5  # Minimum segment duration
```

**Setup Requirements:**

- HuggingFace token (free account)
- Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1

### Qwen VL

```python
MODEL_ID = "mlx-community/Qwen2-VL-8B-Instruct-8bit"  # or 16-bit if preferred
MAX_TOKENS = 512
TEMPERATURE = 0.7
FPS = 1.0  # Frame sampling rate for video analysis
```

-----

## Configuration Files

### User Config (Optional)

Users can create `~/.config/video-tools-mcp/config.yaml`:

```yaml
models:
  parakeet:
    model_id: "mlx-community/parakeet-tdt-0.6b-v3"
    chunk_duration: 120
  
  pyannote:
    model_id: "pyannote/speaker-diarization-3.1"
    hf_token: "${HF_TOKEN}"  # From environment variable
  
  qwen_vl:
    model_id: "mlx-community/Qwen2-VL-8B-Instruct-8bit"
    max_tokens: 512

processing:
  keep_temp_files: false
  temp_dir: "/tmp/video-tools"
  
screenshots:
  default_interval: 5
  default_similarity: 0.90
  jpeg_quality: 95
  
transcription:
  default_format: "srt"
```

### Batch Processing Config

For future batch processing (not in v1.0):

```yaml
batch:
  input_directory: "/path/to/videos"
  file_patterns: ["*.mp4", "*.mov", "*.avi"]
  recursive: true
  parallel_jobs: 2  # Conservative for memory
  tools_to_run:
    - "transcribe_with_speakers"
    - "extract_smart_screenshots"
```

-----

## Error Handling

### Model Loading Errors

```python
class ModelLoadError(Exception):
    """Raised when model fails to load"""
    pass
```

**Handling:**

- Lazy load models (only when tool is called)
- Cache loaded models in memory for subsequent calls
- Provide clear error messages with setup instructions
- Graceful degradation (e.g., transcribe without diarization if Pyannote fails)

### File Processing Errors

```python
class VideoProcessingError(Exception):
    """Raised when video processing fails"""
    pass

class AudioExtractionError(Exception):
    """Raised when audio extraction fails"""
    pass
```

**Validation:**

- Check file exists and is readable
- Verify video format is supported (ffmpeg probe)
- Ensure sufficient disk space for output
- Validate output path is writable

### MCP-Specific Errors

- Tool parameter validation via Pydantic
- Comprehensive error messages returned to MCP client
- Non-blocking errors where possible

-----

## Testing Strategy

### Unit Tests

```python
tests/unit/
├── test_audio_extraction.py
├── test_parakeet_wrapper.py
├── test_pyannote_wrapper.py
├── test_qwen_vl_wrapper.py
├── test_diarization_merge.py
├── test_deduplication.py
└── test_srt_utils.py
```

**Coverage Targets:**

- Core processing functions: 90%+
- Model wrappers: 80%+
- Utility functions: 95%+

### Integration Tests

```python
tests/integration/
├── test_transcribe_workflow.py
├── test_diarization_workflow.py
├── test_screenshot_workflow.py
└── test_full_pipeline.py
```

**Test Fixtures:**

- 30-second test video with 2 speakers
- Single-speaker video
- Video with significant scene changes
- Various formats (MP4, MOV, AVI)

### Performance Tests

- Transcription speed: Target 20x real-time on M4
- Memory usage: Peak < 10GB for typical workloads
- Concurrent requests: Handle 2 simultaneous tool calls

-----

## Development Workflow

### Phase 1: Core Infrastructure (Week 1)

- [ ] Project setup with UV
- [ ] FastMCP server skeleton
- [ ] Model manager with lazy loading
- [ ] Audio extraction (ffmpeg wrapper)
- [ ] Basic unit tests

### Phase 2: Transcription Tools (Week 2)

- [ ] Parakeet MLX integration
- [ ] Tool 1: `transcribe_video`
- [ ] SRT generation & validation
- [ ] Integration tests for transcription
- [ ] Performance benchmarking

### Phase 3: Diarization (Week 3)

- [ ] Pyannote integration (PyTorch MPS)
- [ ] Diarization merge logic
- [ ] Tool 2: `transcribe_with_speakers`
- [ ] Tool 5: `rename_speakers`
- [ ] Multi-speaker test cases

### Phase 4: Video Analysis (Week 4)

- [ ] Qwen VL MLX integration
- [ ] Frame extraction pipeline
- [ ] Tool 3: `analyze_video`
- [ ] JSON metadata generation
- [ ] Analysis accuracy testing

### Phase 5: Smart Screenshots (Week 5)

- [ ] pHash-based deduplication
- [ ] AI-driven frame selection
- [ ] Tool 4: `extract_smart_screenshots`
- [ ] Screenshot metadata system
- [ ] End-to-end testing

### Phase 6: Polish & Documentation (Week 6)

- [ ] Comprehensive error handling
- [ ] Configuration system
- [ ] SKILL.md documentation
- [ ] README with examples
- [ ] Performance optimization
- [ ] Release v1.0

-----

## Deployment & Usage

### Installation

```bash
# Clone repository
git clone https://github.com/autumnsgrove/video-tools.git
cd video-tools

# Run setup script (downloads models, installs deps)
uv run scripts/setup_models.py

# Install MCP server
uv pip install -e .
```

### MCP Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "video-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/video-tools",
        "video-tools-mcp"
      ],
      "env": {
        "HF_TOKEN": "hf_xxxxx"
      }
    }
  }
}
```

### Environment Variables

```bash
# Required for Pyannote
export HF_TOKEN="hf_xxxxx"

# Optional overrides
export VIDEO_TOOLS_CACHE_DIR="~/.cache/video-tools"
export VIDEO_TOOLS_CONFIG="~/.config/video-tools-mcp/config.yaml"
```

-----

## Performance Expectations (M4 Mac Mini 32GB)

### Transcription (Parakeet MLX)

- **Speed:** ~20-30x real-time
- **Example:** 1 hour video → ~2-3 minutes processing
- **Memory:** ~2-3GB peak

### Diarization (Pyannote MPS)

- **Speed:** ~2-3x real-time
- **Example:** 1 hour video → ~20-30 minutes processing
- **Memory:** ~4-6GB peak

### Video Analysis (Qwen VL 8B)

- **Speed:** ~2-3 frames/second
- **Example:** 100 frames → ~30-45 seconds
- **Memory:** ~8-10GB peak

### Smart Screenshots

- **Speed:** Depends on interval and video length
- **Example:** 1 hour video (5s interval) → ~10-15 minutes
- **Memory:** ~10-12GB peak (includes Qwen VL)

-----

## Future Enhancements (Post v1.0)

### Planned Features

- [ ] Batch processing CLI tool
- [ ] Web UI for manual video management
- [ ] Speaker embedding extraction for consistent naming across videos
- [ ] Timeline visualization for video analysis
- [ ] Export to video with burned-in captions
- [ ] Integration with video editing tools
- [ ] Cloud provider fallbacks (optional)
- [ ] Streaming transcription for live video

### Model Improvements

- [ ] Support for whisper models as alternative
- [ ] Test Canary/Granite models for comparison
- [ ] Multi-language support (when available)
- [ ] Custom fine-tuned models for personal voice

-----

## Success Criteria

### Functional Requirements ✓

- All 5 tools working as specified
- Accurate transcription (< 5% WER on clear audio)
- Reliable speaker diarization (< 15% DER on 2-speaker videos)
- Smart screenshot extraction captures meaningful moments
- All outputs saved to correct locations

### Performance Requirements ✓

- Transcription faster than 10x real-time
- Memory usage under 16GB for typical operations
- No crashes on videos up to 2 hours
- Handles concurrent tool calls gracefully

### Developer Experience ✓

- Clear documentation and examples
- Easy installation and setup
- Helpful error messages
- Good test coverage (>80%)
- Type hints throughout

-----

## Notes & Considerations

### Hardware Requirements

- **Minimum:** M1 Mac with 16GB RAM
- **Recommended:** M2/M3/M4 with 32GB+ RAM
- **Storage:** ~15GB for models + working space

### Privacy & Data Handling

- All processing happens locally
- No data sent to external services (except model downloads)
- Temporary files cleaned up automatically
- User controls all output locations

### Known Limitations

- English only (Parakeet limitation)
- Speaker diarization accuracy decreases with:
  - Background noise
  - Overlapping speech
  - Similar-sounding voices
- Qwen VL video understanding limited by:
  - Frame sampling (not full temporal context)
  - Model size (8B parameter)

### Dependencies on External Projects

- Parakeet MLX (senstella/parakeet-mlx)
- MLX VLM (Blaizzy/mlx-vlm)
- Pyannote Audio (pyannote/pyannote-audio)

If any upstream project breaks, we may need to:

- Pin specific versions
- Fork and maintain
- Switch to alternatives

-----

## Questions for Review

1. **Tool Design:** Are the 5 tools appropriately scoped? Any missing essential functionality?
1. **Output Formats:** Is SRT as default sufficient, or should we support more formats from the start?
1. **Configuration:** Is YAML config + env vars the right approach, or prefer pure env vars?
1. **Batch Processing:** Should we build batch capabilities in v1.0 or defer to v2.0?
1. **Testing:** Are the coverage targets realistic for the timeline?
1. **Performance:** Are the performance expectations reasonable for M4 32GB?

-----

## Sign-off

This specification will guide the development of video-tools-mcp v1.0. Once approved, development will proceed in phases as outlined above.

**Estimated Timeline:** 6 weeks to v1.0 release  
**Next Steps:** Review, approve spec, begin Phase 1 infrastructure work

-----

**Document Version:** 1.0  
**Last Updated:** November 14, 2025  
**Status:** Draft - Awaiting Approval