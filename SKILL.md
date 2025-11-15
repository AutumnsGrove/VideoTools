# VideoTools MCP Server - Skill Definition

**Status**: Template - To be completed in Phase 6

---

## Overview

VideoTools is a Model Context Protocol (MCP) server that provides AI-powered video processing capabilities including transcription, speaker diarization, video analysis, and intelligent screenshot extraction.

**Version**: 0.1.0 (Pre-release)
**Protocol**: MCP (Model Context Protocol)
**Platform**: macOS (Apple Silicon optimized)

---

## Capabilities

### 1. Video Transcription (`transcribe_video`)

**Description**: Transcribe audio from video files to text with timestamps.

**Input Parameters**:
- `video_path` (string, required): Path to video file
- `output_format` (string, optional): Output format - "srt", "json", or "txt" (default: "srt")
- `model` (string, optional): Parakeet model variant (default: "parakeet-tdt-0.6b-v3")
- `language` (string, optional): Language code (default: "en")

**Output**:
```json
{
  "transcript_path": "/path/to/output.srt",
  "duration": 120.5,
  "word_count": 245,
  "processing_time": 6.3
}
```

**Use Cases**:
- Generate subtitles for videos
- Create searchable text transcripts
- Extract dialogue for content analysis
- Accessibility (closed captions)

**Performance**: ~20-30x real-time on M4 Mac mini

---

### 2. Speaker Diarization (`transcribe_with_speakers`)

**Description**: Transcribe video with speaker identification and labeling.

**Input Parameters**:
- `video_path` (string, required): Path to video file
- `output_format` (string, optional): Output format (default: "srt")
- `num_speakers` (int, optional): Expected number of speakers
- `min_speakers` (int, optional): Minimum speakers to detect
- `max_speakers` (int, optional): Maximum speakers to detect

**Output**:
```json
{
  "transcript_path": "/path/to/output.srt",
  "speakers_detected": ["SPEAKER_00", "SPEAKER_01"],
  "num_speakers": 2,
  "duration": 180.0,
  "processing_time": 45.2
}
```

**Use Cases**:
- Meeting transcriptions with speaker labels
- Interview processing
- Podcast episode transcripts
- Multi-speaker content analysis

**Requirements**: HuggingFace token for Pyannote model access

**Performance**: ~2-3x real-time on M4 Mac mini

---

### 3. Speaker Renaming (`rename_speakers`)

**Description**: Rename speaker labels in SRT files with human-readable names.

**Input Parameters**:
- `srt_path` (string, required): Path to SRT file with speaker labels
- `speaker_map` (object, required): Mapping of old to new names
  ```json
  {
    "SPEAKER_00": "Alice",
    "SPEAKER_01": "Bob"
  }
  ```
- `output_path` (string, optional): Output path (default: overwrite original)
- `backup` (bool, optional): Create backup before overwriting (default: true)

**Output**:
```json
{
  "output_path": "/path/to/renamed.srt",
  "replacements_made": 15,
  "backup_path": "/path/to/renamed.srt.backup"
}
```

**Use Cases**:
- Post-processing diarization output
- Preparing transcripts for publication
- Named speaker identification

---

### 4. Video Analysis (`analyze_video`)

**Description**: AI-powered frame-by-frame video analysis using vision-language models.

**Input Parameters**:
- `video_path` (string, required): Path to video file
- `analysis_prompt` (string, optional): Custom analysis instruction
- `sample_interval` (int, optional): Seconds between frames (default: 5)
- `max_frames` (int, optional): Maximum frames to analyze (default: 100)
- `include_ocr` (bool, optional): Include text extraction (default: false)

**Output**:
```json
{
  "analysis_path": "/path/to/analysis.json",
  "frames_analyzed": 60,
  "duration": 300.0,
  "processing_time": 150.2
}
```

**Analysis JSON Structure**:
```json
{
  "frames": [
    {
      "frame_number": 0,
      "timestamp": 0.0,
      "analysis": "A person standing in front of a whiteboard...",
      "confidence": 0.85,
      "tokens_used": 42
    }
  ],
  "summary": {
    "total_frames": 60,
    "successful_analyses": 60,
    "average_confidence": 0.87
  }
}
```

**Use Cases**:
- Content moderation
- Scene understanding
- Visual content indexing
- Video summarization
- Text extraction from slides/presentations

**Model**: Qwen2-VL-8B-Instruct (MLX optimized)

**Performance**: ~2-3 frames/second on M4 Mac mini

---

### 5. Smart Screenshot Extraction (`extract_smart_screenshots`)

**Description**: AI-driven screenshot extraction with deduplication and auto-captioning.

**Input Parameters**:
- `video_path` (string, required): Path to video file
- `extraction_prompt` (string, optional): Custom selection criteria
- `sample_interval` (int, optional): Seconds between samples (default: 5)
- `similarity_threshold` (float, optional): pHash similarity 0-1 (default: 0.90)
- `max_screenshots` (int, optional): Maximum screenshots to extract (default: 50)
- `output_dir` (string, optional): Output directory (default: {video}_screenshots/)

**Output**:
```json
{
  "screenshots": ["/path/to/screenshot_00001.jpg", "..."],
  "metadata_path": "/path/to/metadata.json",
  "total_extracted": 12,
  "duplicates_removed": 8,
  "processing_time": 95.3
}
```

**Metadata JSON Structure**:
```json
{
  "screenshots": [
    {
      "filename": "screenshot_00001.jpg",
      "path": "/path/to/screenshot_00001.jpg",
      "timestamp": 15.2,
      "caption": "Person presenting slides with technical diagram",
      "ai_reasoning": "KEEP - Contains informative visual content with technical details",
      "confidence": 0.88
    }
  ]
}
```

**Use Cases**:
- Automatic thumbnail generation
- Key moment extraction
- Presentation slide extraction
- Video preview generation
- Content cataloging

**Features**:
- pHash-based deduplication (removes similar frames)
- AI evaluation (keeps only meaningful frames)
- Automatic captioning for each screenshot
- High-quality JPEG output (quality=95)

**Performance**: ~1-2 frames/second effective processing rate

---

## Installation

<!-- TODO Phase 6: Add detailed installation instructions -->

```bash
# Clone repository
git clone https://github.com/your-username/VideoTools.git
cd VideoTools

# Install with UV
uv sync --extra all

# Set up HuggingFace token for speaker diarization
# Create secrets.json with your HF token
```

---

## Configuration

<!-- TODO Phase 6: Add configuration details -->

### Environment Variables
### Secrets Management
### Model Downloads

---

## Usage Examples

<!-- TODO Phase 6: Add detailed usage examples for each tool -->

### Example 1: Basic Transcription
### Example 2: Multi-Speaker Interview
### Example 3: Video Analysis
### Example 4: Screenshot Extraction

---

## Performance Characteristics

<!-- TODO Phase 6: Add actual benchmark results -->

| Tool | Processing Speed | Memory Usage | Model Size |
|------|-----------------|--------------|------------|
| transcribe_video | ~20-30x RT | TBD | TBD |
| transcribe_with_speakers | ~2-3x RT | TBD | TBD |
| analyze_video | ~2-3 fps | TBD | TBD |
| extract_smart_screenshots | ~1-2 fps | TBD | TBD |

**Platform**: M4 Mac mini, macOS Sonoma

---

## Limitations

- **Platform**: Currently optimized for Apple Silicon (MLX backend)
- **HuggingFace Token**: Required for speaker diarization
- **Model Downloads**: First run downloads models (can be large)
- **Processing Time**: Long videos may require significant processing time
- **GPU**: Requires Apple MPS (Metal Performance Shaders) for optimal performance

---

## Troubleshooting

<!-- TODO Phase 6: Add common issues and solutions -->

---

## Contributing

<!-- TODO Phase 6: Add contribution guidelines -->

---

## License

MIT

---

**Last Updated**: Phase 6 Template (2025-11-15)
