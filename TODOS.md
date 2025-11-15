# Video Tools MCP Server - Development TODOs

**Last Updated**: 2025-11-15 01:30 AM
**Current Status**: Phase 2 Complete, Phase 3 In Progress

---

## 🎯 Current Progress Summary

### ✅ COMPLETED - Phase 1: Core Infrastructure
- [x] Project structure with UV and pyproject.toml
- [x] Configuration system (Pydantic models, environment variables)
- [x] File utilities (validation, temp files, disk space)
- [x] Audio extraction (ffmpeg-python, 16kHz mono WAV)
- [x] Model manager framework (singleton pattern, lazy loading)
- [x] FastMCP server with 5 stub tools registered
- [x] Unit test suite (162 tests, 95% coverage)
- [x] Documentation (README.md, DEVELOPMENT.md)

**Commits**:
- `84c7cfc` - Phase 1 complete

---

### ✅ COMPLETED - Phase 2: Video Transcription
- [x] Parakeet MLX dependencies installed (parakeet-mlx, mlx, numpy, scipy)
- [x] Parakeet model loading in `models/parakeet.py`
- [x] Audio chunking for long videos (120s chunks, 15s overlap)
- [x] Chunk transcription merging with overlap handling
- [x] SRT generation and parsing utilities (`utils/srt_utils.py`)
- [x] Transcription pipeline (`processing/transcription.py`)
- [x] Updated `transcribe_video` tool in server.py (fully functional)
- [x] Multi-format output support (SRT, JSON, TXT)

**Commits**:
- `7b541e0` - Parakeet model implementation
- `abcbbef` - Transcription pipeline and SRT utilities

**Status**: ~90% Complete
**Missing**: Integration tests, performance benchmarking

---

### 🔄 IN PROGRESS - Phase 3: Speaker Diarization

#### ✅ Completed So Far
- [x] Pyannote dependencies installed (pyannote-audio, torch)
- [x] PyTorch with MPS backend verified (GPU acceleration)
- [x] Pyannote model loading in `models/pyannote.py`
- [x] Diarization implementation with speaker detection

#### ❌ Still Needed (Tomorrow's Tasks)
- [ ] **Create `processing/diarization_merge.py`** (agents claimed but didn't create)
  - [ ] `merge_transcription_with_diarization()` function
  - [ ] `find_speaker_for_segment()` with overlap matching
  - [ ] `format_speaker_transcript()` for readable output
  - [ ] Export functions in `processing/__init__.py`

- [ ] **Update `transcribe_with_speakers` tool in server.py**
  - [ ] Replace stub with real implementation
  - [ ] Orchestrate: transcription → diarization → merge
  - [ ] Generate speaker-labeled SRT files
  - [ ] Return speaker statistics

- [ ] **Implement `rename_speakers` tool in server.py**
  - [ ] Load SRT file with `parse_srt_file()`
  - [ ] Apply speaker name mapping (dict)
  - [ ] Create backup if requested
  - [ ] Write updated SRT file

- [ ] **Integration testing**
  - [ ] Test with sample video (2 speakers)
  - [ ] Verify speaker labels are accurate
  - [ ] Test rename_speakers tool

**Status**: ~40% Complete
**Estimated Time**: 2-3 hours to complete

---

## 🛠️ Development Workflow Guidelines

### ⚡ When to Use Direct Tools (Write/Edit/Read)

**Use Write/Edit for**:
- Creating new files (always more reliable than agents)
- Updating existing files with specific changes
- Small, focused code additions (<200 lines)
- When you need guaranteed file creation

**Examples**:
```bash
# Creating a new module
Write tool → src/video_tools_mcp/processing/diarization_merge.py

# Updating server.py to add real implementation
Edit tool → Replace stub function with real code
```

### 🤖 When to Use Subagents (house-coder, etc.)

**Use house-coder for**:
- Small, surgical updates to existing files
- Quick bug fixes or import additions
- When you want a summary without full file context
- Exploratory code analysis

**Use house-research for**:
- Searching across 20+ files
- Finding patterns in codebase
- Locating TODO/FIXME comments

**Use house-planner for**:
- Breaking down complex features
- Planning multi-file changes
- Creating implementation strategies

**⚠️ IMPORTANT**: Always verify subagent outputs!
- Agents may claim to create files without actually writing them
- Check filesystem with `ls` or `Bash` tool after agent completes
- If file doesn't exist, use Write tool directly

### 📋 Recommended Workflow for Tomorrow

1. **Create diarization_merge.py** (Use Write tool directly)
2. **Update server.py** (Use Edit tool for transcribe_with_speakers)
3. **Test imports** (Use Bash tool: `uv run python -c "from video_tools_mcp.processing import merge_transcription_with_diarization"`)
4. **Commit working code** (Git workflow)
5. **Test with sample video** (Integration testing)

---

## 📝 Detailed Next Steps for Phase 3

### Step 1: Create Diarization Merge Module (30 mins)

**File**: `src/video_tools_mcp/processing/diarization_merge.py`

**Functions needed**:
```python
def find_speaker_for_segment(segment_start, segment_end, diarization_segments):
    """Find speaker with max temporal overlap."""
    # Use overlap calculation to match speakers
    pass

def merge_transcription_with_diarization(transcription_result, diarization_result):
    """Merge Parakeet transcription with Pyannote speaker labels."""
    # For each transcription segment, find best matching speaker
    # Return merged segments with speaker labels
    pass

def format_speaker_transcript(segments):
    """Format as: SPEAKER_00: Text here..."""
    pass
```

**Test imports**:
```bash
uv run python -c "from video_tools_mcp.processing.diarization_merge import merge_transcription_with_diarization"
```

---

### Step 2: Update transcribe_with_speakers Tool (45 mins)

**File**: `src/video_tools_mcp/server.py`

**Implementation**:
```python
@mcp.tool()
def transcribe_with_speakers(video_path, output_format="srt", ...):
    # 1. Extract audio
    # 2. Run Parakeet transcription
    # 3. Run Pyannote diarization
    # 4. Merge results with diarization_merge
    # 5. Generate speaker-labeled SRT
    # 6. Return stats (speakers_detected, transcript_path, etc.)
    pass
```

---

### Step 3: Implement rename_speakers Tool (20 mins)

**File**: `src/video_tools_mcp/server.py`

**Implementation**:
```python
@mcp.tool()
def rename_speakers(srt_path, speaker_map, output_path=None, backup=True):
    # 1. Parse SRT with parse_srt_file()
    # 2. Replace speaker names in text
    # 3. Create backup if requested
    # 4. Write updated SRT
    # 5. Return output_path, replacements_made, backup_path
    pass
```

---

### Step 4: Test & Validate (30 mins)

**Integration test checklist**:
- [ ] Create 30-second test video with 2 speakers
- [ ] Run `transcribe_with_speakers` tool
- [ ] Verify speaker labels in output SRT
- [ ] Test `rename_speakers` with {"SPEAKER_00": "Alice", "SPEAKER_01": "Bob"}
- [ ] Verify renamed SRT is correct

---

## 🎯 Success Criteria for Phase 3 Completion

### Functional Requirements
- [ ] `transcribe_with_speakers` tool returns speaker-labeled transcripts
- [ ] Speaker detection is reasonably accurate (>70% DER on clear audio)
- [ ] `rename_speakers` tool successfully renames speakers in SRT files
- [ ] All Phase 3 code committed to git

### Technical Requirements
- [ ] All files actually exist on disk (not just agent claims)
- [ ] Imports work without errors
- [ ] Code passes syntax checks
- [ ] Logging integrated throughout

### Output Requirements
- [ ] SRT files have speaker labels: "SPEAKER_00: Hello there"
- [ ] Speaker statistics returned (speakers_detected, num_speakers)
- [ ] Backup files created when requested

---

## 🚀 Future Phases (Post Phase 3)

### Phase 4: Video Analysis (Qwen VL)
- Qwen VL model loading
- Frame extraction from video
- `analyze_video` tool implementation
- JSON metadata generation

### Phase 5: Smart Screenshots
- pHash-based deduplication
- AI-driven frame selection
- `extract_smart_screenshots` tool
- Auto-captioning with Qwen VL

### Phase 6: Polish & Optimization
- Performance benchmarking (all phases)
- Integration tests for all tools
- Documentation updates
- SKILL.md for MCP server
- Release v1.0

---

## 📚 Key File Locations

### Models
- `src/video_tools_mcp/models/parakeet.py` - Transcription (✅ complete)
- `src/video_tools_mcp/models/pyannote.py` - Diarization (✅ complete)
- `src/video_tools_mcp/models/qwen_vl.py` - Vision (stub)

### Processing
- `src/video_tools_mcp/processing/audio_extraction.py` - FFmpeg wrapper (✅ complete)
- `src/video_tools_mcp/processing/transcription.py` - Chunking pipeline (✅ complete)
- `src/video_tools_mcp/processing/diarization_merge.py` - Merge logic (❌ need to create)

### Utilities
- `src/video_tools_mcp/utils/file_utils.py` - File operations (✅ complete)
- `src/video_tools_mcp/utils/srt_utils.py` - SRT generation (✅ complete)

### Server
- `src/video_tools_mcp/server.py` - MCP tools (1/5 complete, 4 stubs)

---

## 🔍 Known Issues & Limitations

### House-Coder Agent Issue
**Problem**: Agents return summaries claiming files were created, but files don't actually exist on disk.

**Solution**:
- Always verify with `ls` or Bash commands after agent completes
- Use Write/Edit tools directly for file creation
- Use agents only for planning, research, or code analysis

### Current Blockers
- None! All dependencies installed, models configured

### Testing Gaps
- No integration tests yet (need test videos)
- Performance benchmarks not run
- Multi-speaker accuracy not validated

---

## 💾 Git Status

**Branch**: master
**Commits ahead of origin**: 3
**Working tree**: Clean ✅

**Recent commits**:
1. `84c7cfc` - Phase 1: Core infrastructure
2. `7b541e0` - Phase 2: Parakeet model
3. `abcbbef` - Phase 2: Transcription pipeline

**Ready to push**: Yes (all work committed)

---

## 🎬 Quick Start for Tomorrow

```bash
# 1. Navigate to project
cd /Users/mini/Documents/VideoTools

# 2. Activate environment (uv handles this)
uv run python -c "print('Environment ready')"

# 3. Check current status
git status
ls -la src/video_tools_mcp/processing/

# 4. Create missing file
# Use Write tool to create diarization_merge.py

# 5. Update server.py
# Use Edit tool to update transcribe_with_speakers

# 6. Test imports
uv run python -c "from video_tools_mcp.processing import merge_transcription_with_diarization"

# 7. Commit progress
git add .
git commit -m "feat: Complete Phase 3 - Speaker diarization"
```

---

**End of TODO List**
Ready to resume development! 🚀
