# Video Tools MCP Server - Phase 4 & 5 Planning

**Created**: 2025-11-15
**Session**: Phase 3 → Phase 4/5 Transition
**Status**: Ready for Implementation

---

## 🎯 Overview

Phase 3 (Speaker Diarization) is **95% complete** but blocked by Pyannote dependency issues. Moving forward with Phase 4 (Video Analysis) and Phase 5 (Smart Screenshots) which are independent and high-value features.

---

## 📋 Phase 4: Video Analysis with Qwen VL

### Objective
Analyze video content using Qwen VL vision-language model to extract scenes, objects, activities, and generate descriptive metadata.

### Requirements

#### 1. Model Selection & Setup
- **Model**: Use MLX-community Qwen VL model from HuggingFace
- **Quantization**: **MUST be 8-bit** (per user requirement)
- **Implementation**: Create `models/qwen_vl.py` with model manager pattern
- **Model Download Stage**: Ensure explicit download step before first use

**Recommended Model**:
- `mlx-community/Qwen2-VL-7B-Instruct-8bit` or
- `mlx-community/Qwen2-VL-2B-Instruct-8bit` (smaller, faster)

#### 2. Frame Extraction
**File**: `src/video_tools_mcp/processing/frame_extraction.py`

**Functions Needed**:
```python
def extract_frames_uniform(
    video_path: str,
    num_frames: int = 10,
    output_dir: Optional[str] = None
) -> List[str]:
    """Extract N evenly-spaced frames from video."""
    # Use ffmpeg or opencv to extract frames
    # Return list of frame paths
    pass

def extract_frames_by_time(
    video_path: str,
    timestamps: List[float],
    output_dir: Optional[str] = None
) -> List[str]:
    """Extract frames at specific timestamps."""
    pass

def extract_keyframes(
    video_path: str,
    threshold: float = 0.4,
    output_dir: Optional[str] = None
) -> List[str]:
    """Extract keyframes using scene detection."""
    # Use ffmpeg scene detection
    pass
```

#### 3. Video Analysis
**File**: `src/video_tools_mcp/processing/video_analysis.py`

**Functions Needed**:
```python
def analyze_frame(
    frame_path: str,
    model: QwenVLModel,
    prompt: str = "Describe this image in detail."
) -> Dict[str, Any]:
    """Analyze a single frame with Qwen VL."""
    # Return: description, objects, activities, etc.
    pass

def analyze_video(
    video_path: str,
    num_frames: int = 10,
    extraction_method: str = "uniform"
) -> Dict[str, Any]:
    """
    Analyze entire video by sampling frames.

    Returns:
        {
            "video_path": str,
            "duration": float,
            "frames_analyzed": int,
            "scenes": [
                {
                    "timestamp": float,
                    "frame_path": str,
                    "description": str,
                    "objects": List[str],
                    "activities": List[str],
                    "confidence": float
                },
                ...
            ],
            "summary": str,
            "metadata": {...}
        }
    """
    pass
```

#### 4. MCP Tool Integration
**File**: `src/video_tools_mcp/server.py`

**New Tool**: `analyze_video`
```python
@mcp.tool()
def analyze_video(
    video_path: str,
    num_frames: int = 10,
    extraction_method: str = "uniform",  # uniform, keyframes, timestamps
    output_format: str = "json",
    save_frames: bool = False
) -> Dict[str, Any]:
    """
    Analyze video content using Qwen VL vision model.

    Args:
        video_path: Path to video file
        num_frames: Number of frames to analyze (default: 10)
        extraction_method: How to extract frames (uniform, keyframes, timestamps)
        output_format: json or markdown
        save_frames: Whether to save extracted frames

    Returns:
        Analysis results with scene descriptions and metadata
    """
    pass
```

#### 5. Output Format Examples

**JSON Output**:
```json
{
  "video_path": "/path/to/video.mp4",
  "duration": 120.5,
  "frames_analyzed": 10,
  "scenes": [
    {
      "timestamp": 0.0,
      "frame_path": "/tmp/frame_0000.jpg",
      "description": "A person sitting at a desk working on a laptop",
      "objects": ["person", "laptop", "desk", "chair"],
      "activities": ["working", "typing"],
      "confidence": 0.92
    },
    {
      "timestamp": 12.05,
      "description": "Same person now standing and gesturing",
      "objects": ["person", "desk", "whiteboard"],
      "activities": ["presenting", "gesturing"],
      "confidence": 0.88
    }
  ],
  "summary": "Video shows a person working at a desk, then presenting ideas at a whiteboard.",
  "metadata": {
    "resolution": "1920x1080",
    "fps": 30,
    "codec": "h264"
  }
}
```

**Markdown Output**:
```markdown
# Video Analysis: video.mp4

**Duration**: 2:00.5
**Frames Analyzed**: 10
**Resolution**: 1920x1080

## Scenes

### Scene 1 (0:00)
A person sitting at a desk working on a laptop

**Objects**: person, laptop, desk, chair
**Activities**: working, typing

### Scene 2 (0:12)
Same person now standing and gesturing

**Objects**: person, desk, whiteboard
**Activities**: presenting, gesturing

## Summary
Video shows a person working at a desk, then presenting ideas at a whiteboard.
```

### Testing Strategy
1. Test frame extraction with various video formats
2. Test Qwen VL model loading and inference
3. Test analysis on short video (~30 seconds)
4. Verify JSON and markdown output formats
5. Test edge cases (very long videos, corrupted frames, etc.)

### Estimated Time
**3-4 hours**

---

## 🖼️ Phase 5: Smart Screenshots

### Objective
Extract meaningful, non-duplicate screenshots from videos using perceptual hashing (pHash) and AI-driven selection.

### Requirements

#### 1. pHash Implementation
**File**: `src/video_tools_mcp/utils/phash.py`

**Functions Needed**:
```python
def calculate_phash(image_path: str) -> str:
    """Calculate perceptual hash of an image."""
    # Use imagehash library or custom implementation
    pass

def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two pHashes."""
    pass

def is_duplicate(
    image_path1: str,
    image_path2: str,
    threshold: int = 5
) -> bool:
    """Check if two images are perceptually similar."""
    pass
```

**Dependencies**: `pip install imagehash pillow`

#### 2. Smart Screenshot Extraction
**File**: `src/video_tools_mcp/processing/smart_screenshots.py`

**Functions Needed**:
```python
def extract_all_frames(
    video_path: str,
    fps: float = 1.0,  # 1 frame per second
    output_dir: Optional[str] = None
) -> List[str]:
    """Extract frames at specified FPS."""
    pass

def deduplicate_frames(
    frame_paths: List[str],
    threshold: int = 5
) -> List[str]:
    """
    Remove duplicate/similar frames using pHash.

    Args:
        frame_paths: List of frame image paths
        threshold: Max Hamming distance for duplicates (0-64)

    Returns:
        List of unique frame paths
    """
    pass

def score_frames(
    frame_paths: List[str],
    model: QwenVLModel,
    criteria: str = "interesting"  # interesting, clear, informative
) -> List[Tuple[str, float]]:
    """
    Score frames using AI model for quality/interest.

    Returns:
        List of (frame_path, score) tuples sorted by score
    """
    pass

def select_best_frames(
    frame_paths: List[str],
    num_screenshots: int = 10,
    dedup_threshold: int = 5,
    use_ai_scoring: bool = True
) -> List[Dict[str, Any]]:
    """
    Select best N screenshots from video.

    Process:
    1. Deduplicate using pHash
    2. (Optional) Score with AI for quality
    3. Select top N frames
    4. (Optional) Auto-caption with Qwen VL

    Returns:
        [
            {
                "frame_path": str,
                "timestamp": float,
                "phash": str,
                "score": float,
                "caption": str
            },
            ...
        ]
    """
    pass
```

#### 3. MCP Tool Integration
**File**: `src/video_tools_mcp/server.py`

**New Tool**: `extract_smart_screenshots`
```python
@mcp.tool()
def extract_smart_screenshots(
    video_path: str,
    num_screenshots: int = 10,
    fps: float = 1.0,
    dedup_threshold: int = 5,
    use_ai_selection: bool = True,
    auto_caption: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract smart screenshots from video with deduplication and AI selection.

    Args:
        video_path: Path to video file
        num_screenshots: Number of screenshots to extract (default: 10)
        fps: Frames per second to sample (default: 1.0)
        dedup_threshold: pHash similarity threshold (0-64, default: 5)
        use_ai_selection: Use Qwen VL to score frame quality (default: True)
        auto_caption: Generate captions for screenshots (default: True)
        output_dir: Where to save screenshots (default: video_dir/screenshots/)

    Returns:
        {
            "screenshots": [
                {
                    "path": str,
                    "timestamp": float,
                    "caption": str,
                    "score": float
                },
                ...
            ],
            "total_frames_extracted": int,
            "duplicates_removed": int,
            "processing_time": float
        }
    """
    pass
```

#### 4. Screenshot Naming Convention
```
video-name_screenshot_001_00m15s.jpg  # Frame at 0:15
video-name_screenshot_002_01m30s.jpg  # Frame at 1:30
video-name_screenshot_003_05m42s.jpg  # Frame at 5:42
```

### Testing Strategy
1. Test pHash calculation and duplicate detection
2. Test frame extraction at various FPS rates
3. Test deduplication on video with repeated scenes
4. Test AI scoring and selection
5. Test auto-captioning integration
6. Verify output naming and organization

### Estimated Time
**3-4 hours**

---

## 🔄 Implementation Order

### Session 1: Phase 4 Foundation (2-3 hours)
1. Create `models/qwen_vl.py` with MLX-community 8-bit model
2. Implement frame extraction (`processing/frame_extraction.py`)
3. Test frame extraction on sample video
4. **Git Commit**: "feat: Add Qwen VL model and frame extraction"

### Session 2: Phase 4 Analysis (1-2 hours)
1. Implement `processing/video_analysis.py`
2. Add `analyze_video` MCP tool to `server.py`
3. Test full video analysis pipeline
4. **Git Commit**: "feat: Complete Phase 4 - Video analysis with Qwen VL"

### Session 3: Phase 5 Deduplication (2 hours)
1. Install imagehash dependency: `uv add imagehash pillow`
2. Implement `utils/phash.py`
3. Implement deduplication in `processing/smart_screenshots.py`
4. Test deduplication on sample video
5. **Git Commit**: "feat: Add pHash-based frame deduplication"

### Session 4: Phase 5 Smart Selection (1-2 hours)
1. Implement AI scoring and frame selection
2. Add `extract_smart_screenshots` MCP tool
3. Integration testing
4. **Git Commit**: "feat: Complete Phase 5 - Smart screenshots with AI selection"

---

## 📦 Dependencies to Add

```bash
# Phase 4
uv add pillow opencv-python  # Frame extraction

# Phase 5
uv add imagehash  # pHash deduplication

# Qwen VL (check MLX-community for exact package name)
# May be included in mlx-vlm or similar
```

---

## 🎯 Success Criteria

### Phase 4: Video Analysis
- [ ] Qwen VL 8-bit model loads successfully
- [ ] Can extract frames from video (uniform, keyframe, timestamp methods)
- [ ] Can analyze frames with Qwen VL
- [ ] `analyze_video` tool returns structured JSON/markdown
- [ ] Works on videos of various lengths (10s to 10min+)

### Phase 5: Smart Screenshots
- [ ] pHash accurately detects duplicate frames
- [ ] Deduplication removes similar frames (threshold configurable)
- [ ] AI scoring ranks frames by quality/interest
- [ ] Auto-captioning generates accurate descriptions
- [ ] `extract_smart_screenshots` tool returns best N frames
- [ ] Screenshots saved with meaningful names and timestamps

---

## 🚧 Known Challenges & Solutions

### Challenge 1: Qwen VL Model Selection
**Problem**: Many Qwen VL variants exist
**Solution**: Use `mlx-community/Qwen2-VL-2B-Instruct-8bit` for speed, or `7B-8bit` for accuracy

### Challenge 2: Frame Extraction Performance
**Problem**: Extracting many frames can be slow
**Solution**: Use ffmpeg for fast batch extraction, cache frames in temp directory

### Challenge 3: pHash Threshold Tuning
**Problem**: Optimal threshold varies by video content
**Solution**: Default to 5, make configurable, provide examples in docs

### Challenge 4: AI Scoring Cost
**Problem**: Running Qwen VL on every frame is expensive
**Solution**: Only score after deduplication (reduces candidate set significantly)

---

## 📝 Files to Create/Modify

### New Files (Phase 4)
- `src/video_tools_mcp/models/qwen_vl.py`
- `src/video_tools_mcp/processing/frame_extraction.py`
- `src/video_tools_mcp/processing/video_analysis.py`

### New Files (Phase 5)
- `src/video_tools_mcp/utils/phash.py`
- `src/video_tools_mcp/processing/smart_screenshots.py`

### Files to Modify
- `src/video_tools_mcp/server.py` (add 2 new MCP tools)
- `src/video_tools_mcp/config/models.py` (add QwenVLConfig)
- `pyproject.toml` (add dependencies)
- `TODOS.md` (track progress)

---

## 🔗 References

### Qwen VL
- MLX Community: https://huggingface.co/mlx-community
- Qwen VL Docs: https://github.com/QwenLM/Qwen-VL
- MLX VLM: https://github.com/Blaizzy/mlx-vlm

### pHash
- imagehash library: https://github.com/JohannesBuchner/imagehash
- Perceptual Hashing: https://www.phash.org/

### Frame Extraction
- ffmpeg scene detection: https://ffmpeg.org/ffmpeg-filters.html#select_002c-aselect
- OpenCV video capture: https://docs.opencv.org/

---

## 💡 Future Enhancements (Post Phase 5)

1. **Real-time Video Processing**: Stream analysis for live videos
2. **Multi-modal Search**: Search videos by description
3. **Clip Extraction**: Auto-extract interesting clips based on AI analysis
4. **Thumbnail Generation**: Create representative thumbnails
5. **Scene Boundary Detection**: Automatic scene segmentation
6. **Object Tracking**: Track specific objects across frames

---

**Ready to Start**: Phase 4, Session 1 - Qwen VL Model & Frame Extraction
**Next Command**: Review this plan and begin implementation!
