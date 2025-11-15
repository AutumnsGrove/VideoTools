# Development Documentation

## Architecture Overview

Video Tools MCP Server is built with a modular, extensible architecture that prioritizes testability, maintainability, and clean separation of concerns.

### Core Design Principles

1. **Separation of Concerns**: Models, processing logic, and server code are isolated
2. **Dependency Injection**: Configuration passed explicitly, no global state
3. **Singleton Pattern**: Model managers load once and persist across requests
4. **Lazy Loading**: Models initialize only when first needed
5. **Comprehensive Testing**: 95% coverage with fast unit tests

### Directory Structure

```
VideoTools/
├── src/video_tools_mcp/          # Main package
│   ├── __init__.py               # Package initialization
│   ├── server.py                 # MCP server entry point (FastMCP)
│   │
│   ├── models/                   # AI model wrappers
│   │   ├── __init__.py           # Model exports
│   │   ├── model_manager.py      # Abstract base class with singleton
│   │   ├── parakeet.py           # Parakeet TDT transcription (stub)
│   │   ├── pyannote.py           # Pyannote diarization (stub)
│   │   └── qwen_vl.py            # Qwen VL vision-language model (stub)
│   │
│   ├── processing/               # Core processing logic
│   │   ├── __init__.py
│   │   └── audio_extraction.py   # FFmpeg-based audio extraction
│   │
│   ├── config/                   # Configuration system
│   │   ├── __init__.py
│   │   ├── models.py             # Pydantic config models
│   │   └── prompts.py            # Default analysis prompts
│   │
│   ├── tools/                    # Future: tool implementations
│   │   └── __init__.py           # (Empty in Phase 1)
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       └── file_utils.py         # File operations and validation
│
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest fixtures and configuration
│   ├── unit/                     # Unit tests (162 tests, 95% coverage)
│   │   ├── test_audio_extraction.py
│   │   ├── test_config.py
│   │   ├── test_file_utils.py
│   │   ├── test_model_managers.py
│   │   └── test_server.py
│   └── fixtures/                 # Test data (Phase 2+)
│
├── scripts/                      # Utility scripts
├── pyproject.toml                # Project configuration
├── .env.example                  # Environment variable template
└── README.md                     # User documentation
```

## Phase 1 Implementation Details

### Configuration System (`config/models.py`)

**Pydantic-based Configuration**

The configuration system uses Pydantic models for type-safe, validated configuration:

```python
class VideoToolsConfig(BaseModel):
    """Main configuration model with validation"""

    # Environment variables
    hf_token: Optional[str] = Field(default=None, alias="HF_TOKEN")
    cache_dir: Path = Field(default=Path("~/.cache/video-tools"))
    log_level: str = Field(default="INFO")

    # Model configurations
    parakeet_config: ParakeetConfig = Field(default_factory=ParakeetConfig)
    pyannote_config: PyannoteConfig = Field(default_factory=PyannoteConfig)
    qwen_vl_config: QwenVLConfig = Field(default_factory=QwenVLConfig)

    # Validators
    @field_validator("cache_dir")
    def expand_cache_dir(cls, v: Path) -> Path:
        """Expand ~ in paths"""
        return Path(str(v).replace("~", str(Path.home())))
```

**Features:**
- Environment variable support via `.env` files
- Path expansion for `~` (home directory)
- Nested configuration for each model
- Type validation with Pydantic
- Default values for all settings

**Loading Configuration:**

```python
from video_tools_mcp.config import load_config

config = load_config()  # Auto-loads from environment
```

### Model Manager System (`models/model_manager.py`)

**Abstract Base Class with Singleton Pattern**

The `ModelManager` base class provides a consistent interface for all AI models:

```python
class ModelManager(ABC):
    """
    Abstract base class for all model managers.
    Implements singleton pattern and lazy loading.
    """

    _instances = {}  # Singleton storage

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance per model type"""
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    @abstractmethod
    def load_model(self) -> Any:
        """Load the model (lazy loading)"""
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unload model to free memory"""
        pass

    def is_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self._model is not None
```

**Key Features:**
- **Singleton**: Only one instance per model type
- **Lazy Loading**: Models load on first use
- **Memory Management**: Explicit unload for memory control
- **Consistent Interface**: All models follow same pattern

**Example Usage:**

```python
# Phase 2+ example
from video_tools_mcp.models import ParakeetManager

manager = ParakeetManager(config.parakeet_config)
manager.load_model()  # Load when needed
result = manager.transcribe(audio_path)
manager.unload_model()  # Free memory
```

### Audio Extraction (`processing/audio_extraction.py`)

**FFmpeg-Based Audio Processing**

The audio extraction module provides robust video-to-audio conversion:

```python
class AudioExtractor:
    """Extract audio from video files using FFmpeg"""

    def extract_audio(
        self,
        video_path: Path,
        output_path: Optional[Path] = None,
        sample_rate: int = 16000,
        channels: int = 1
    ) -> Path:
        """
        Extract audio from video file.

        Optimized for Parakeet TDT:
        - 16kHz sample rate
        - Mono channel
        - WAV format
        """
```

**Features:**
- FFmpeg integration via `ffmpeg-python`
- Optimized settings for ASR (16kHz mono)
- Temporary file management
- Duration extraction
- Comprehensive error handling

**Technical Details:**
- **Sample Rate**: 16kHz (Parakeet optimal)
- **Channels**: 1 (mono)
- **Format**: WAV (uncompressed for quality)
- **Codec**: PCM S16LE

### MCP Server (`server.py`)

**FastMCP Framework Integration**

The server implements 5 MCP tools using the FastMCP framework:

```python
from fastmcp import FastMCP

mcp = FastMCP("video-tools", version="0.1.0")

@mcp.tool()
def transcribe_video(
    video_path: str,
    output_format: str = "srt",
    model: str = "parakeet-tdt-0.6b-v3",
    language: str = "en"
) -> dict:
    """Basic transcription without speaker ID"""
    # Phase 1: Stub implementation
    # Phase 2: Real implementation
```

**Phase 1 Tools (Stubs):**
1. `transcribe_video` - Basic transcription
2. `transcribe_with_speakers` - Speaker diarization
3. `analyze_video` - Frame-by-frame analysis
4. `extract_smart_screenshots` - AI screenshot extraction
5. `rename_speakers` - Speaker label renaming

**FastMCP Features Used:**
- Automatic parameter validation (Pydantic)
- JSON-RPC protocol handling
- Tool registration with decorators
- Built-in logging

### File Utils (`utils/file_utils.py`)

**Robust File Operations**

Utility functions for file handling with comprehensive validation:

```python
def validate_video_file(path: Path) -> bool:
    """Validate video file exists and has valid extension"""

def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if needed"""

def get_safe_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility"""
```

**Features:**
- Video file validation
- Directory creation with parents
- Safe filename generation
- Path expansion
- Extension checking

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone https://github.com/autumnsgrove/video-tools.git
cd VideoTools

# 2. Install UV package manager (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# 5. Install dev dependencies
uv sync --extra dev

# 6. Set up environment variables
cp .env.example .env
# Edit .env with your settings
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/unit/ -v --cov=src/video_tools_mcp --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_audio_extraction.py -v

# Run tests matching pattern
uv run pytest tests/unit/ -k "test_config" -v

# Run with verbose output
uv run pytest tests/unit/ -vv

# View coverage report
open htmlcov/index.html  # macOS
```

### Code Style and Linting

```bash
# Format code with Black
uv run black src/ tests/

# Check style
uv run black --check src/ tests/

# Run Ruff linter
uv run ruff check src/ tests/

# Run type checker
uv run mypy src/
```

**Style Configuration:**
- **Black**: Line length 100, Python 3.11 target
- **Ruff**: E, F, I, N, W, UP rules enabled
- **MyPy**: Strict typing, ignore missing imports

### Pre-commit Workflow

Before committing code:

1. **Run tests**: Ensure all tests pass
2. **Format code**: Run Black on modified files
3. **Check linting**: Run Ruff to catch issues
4. **Verify coverage**: Check coverage hasn't dropped
5. **Update docs**: Update docstrings if needed

```bash
# One-liner for pre-commit checks
uv run black src/ tests/ && uv run ruff check src/ tests/ && uv run pytest tests/unit/ -v
```

## Testing Strategy

### Unit Testing Philosophy

**Phase 1: Fast, Isolated Unit Tests**

All Phase 1 tests are pure unit tests with mocked dependencies:

- **No External Dependencies**: All FFmpeg, file I/O, models are mocked
- **Fast Execution**: 162 tests run in ~1.6 seconds
- **High Coverage**: 95% code coverage
- **Deterministic**: Same results every time

**Example Test Structure:**

```python
# tests/unit/test_audio_extraction.py
def test_extract_audio_success(audio_extractor, mock_ffmpeg, tmp_path):
    """Test successful audio extraction"""
    video_path = tmp_path / "test.mp4"
    video_path.touch()

    # Mock ffmpeg output
    mock_ffmpeg.probe.return_value = {"format": {"duration": "120.5"}}

    # Test extraction
    result = audio_extractor.extract_audio(video_path)

    # Assertions
    assert result.exists()
    assert result.suffix == ".wav"
    mock_ffmpeg.input.assert_called_once()
```

### Test Fixtures (`tests/conftest.py`)

Pytest fixtures provide reusable test components:

```python
@pytest.fixture
def config():
    """Test configuration"""
    return VideoToolsConfig(
        hf_token="test_token",
        cache_dir=Path("/tmp/test_cache"),
        log_level="DEBUG"
    )

@pytest.fixture
def audio_extractor(config):
    """Audio extractor instance"""
    return AudioExtractor(config)
```

### Coverage Breakdown

**Phase 1 Coverage (95% overall):**

| Module | Coverage | Notes |
|--------|----------|-------|
| `config/models.py` | 100% | Full configuration coverage |
| `config/prompts.py` | 100% | All prompts tested |
| `models/model_manager.py` | 96% | Singleton pattern covered |
| `models/parakeet.py` | 100% | Stub implementation |
| `models/pyannote.py` | 100% | Stub implementation |
| `models/qwen_vl.py` | 100% | Stub implementation |
| `processing/audio_extraction.py` | 87% | Core paths covered, edge cases mocked |
| `utils/file_utils.py` | 89% | Main functions covered |
| `server.py` | 98% | All tools tested |

**Uncovered Lines:**
- Error handling paths requiring real FFmpeg failures
- Edge cases in file operations
- Main entry point (tested manually)

## Phase 2-6 Roadmap

### Phase 2: Transcription (Week 2)

**Goals:**
- Integrate Parakeet TDT MLX for real transcription
- Implement audio chunking for long videos
- Support multiple output formats (SRT, VTT, JSON, TXT)

**Implementation Steps:**

1. **Install Parakeet MLX**
   ```bash
   pip install parakeet-mlx
   ```

2. **Implement `ParakeetManager.load_model()`**
   ```python
   def load_model(self):
       from parakeet_mlx import ParakeetTDT
       self._model = ParakeetTDT(self.config.model_name)
   ```

3. **Implement `transcribe_video` Tool**
   - Extract audio with `AudioExtractor`
   - Chunk audio for long videos (30-second chunks)
   - Run Parakeet on each chunk
   - Merge results and format as SRT/VTT/JSON

4. **Add Integration Tests**
   - Test with real 30-second video
   - Verify SRT formatting
   - Benchmark performance

**Expected Performance:**
- 20-30x real-time on M4 Mac mini
- 1 hour video → 2-3 minutes processing

### Phase 3: Speaker Diarization (Week 3)

**Goals:**
- Add Pyannote Audio for speaker identification
- Merge transcription with speaker labels
- Implement speaker renaming utility

**Implementation Steps:**

1. **Install Pyannote Audio**
   ```bash
   pip install pyannote-audio
   ```

2. **Implement `PyannoteManager.load_model()`**
   ```python
   def load_model(self):
       from pyannote.audio import Pipeline
       self._pipeline = Pipeline.from_pretrained(
           "pyannote/speaker-diarization-3.1",
           use_auth_token=self.config.hf_token
       )
   ```

3. **Implement `transcribe_with_speakers` Tool**
   - Run Parakeet transcription
   - Run Pyannote diarization
   - Align transcript with speaker segments
   - Format with speaker labels

4. **Implement `rename_speakers` Tool**
   - Parse SRT file
   - Replace speaker labels using map
   - Create backup before overwriting

**Expected Performance:**
- 2-3x real-time on M4 Mac mini
- 1 hour video → 20-30 minutes processing

### Phase 4: Video Analysis (Week 4)

**Goals:**
- Integrate Qwen VL MLX for frame analysis
- Support custom analysis prompts
- Optional OCR integration

**Implementation Steps:**

1. **Install MLX VLM**
   ```bash
   pip install mlx-vlm
   ```

2. **Implement `QwenVLManager.load_model()`**
   ```python
   def load_model(self):
       from mlx_vlm import load
       self._model, self._processor = load(self.config.model_name)
   ```

3. **Implement Frame Extraction**
   - Use FFmpeg to extract frames at intervals
   - Store frames temporarily

4. **Implement `analyze_video` Tool**
   - Extract frames every N seconds
   - Run Qwen VL on each frame with prompt
   - Aggregate results into JSON report
   - Optionally run OCR (pytesseract)

**Expected Performance:**
- 2-3 frames/second
- 5-minute video → ~2 minutes analysis

### Phase 5: Smart Screenshots (Week 5)

**Goals:**
- AI-driven screenshot selection
- pHash-based deduplication
- Auto-captioning

**Implementation Steps:**

1. **Install pHash Library**
   ```bash
   pip install imagehash pillow
   ```

2. **Implement Deduplication**
   ```python
   def is_duplicate(frame1, frame2, threshold=0.90):
       hash1 = imagehash.phash(frame1)
       hash2 = imagehash.phash(frame2)
       similarity = 1 - (hash1 - hash2) / 64.0
       return similarity > threshold
   ```

3. **Implement `extract_smart_screenshots` Tool**
   - Extract frames at intervals
   - Compute pHash for each frame
   - Skip duplicates above threshold
   - Use Qwen VL to decide: keep/skip with reasoning
   - Generate captions for kept frames
   - Save with metadata JSON

**Expected Performance:**
- 1-2 frames/second
- 10-minute video → 5-10 meaningful screenshots

### Phase 6: Polish & Release (Week 6)

**Goals:**
- Performance optimization
- Comprehensive documentation
- Release v1.0.0

**Tasks:**

1. **Performance Optimization**
   - Profile code to find bottlenecks
   - Optimize frame extraction
   - Add caching for repeated operations
   - Benchmark on various hardware

2. **Documentation**
   - Create SKILL.md for MCP protocol
   - Add user guides and tutorials
   - Document API with examples
   - Create video demonstrations

3. **Release Preparation**
   - Final testing on clean install
   - Update version to 1.0.0
   - Tag release on GitHub
   - Publish announcement

## Contributing

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Run tests and linting**
   ```bash
   uv run pytest tests/unit/ -v
   uv run black src/ tests/
   uv run ruff check src/ tests/
   ```

5. **Commit with conventional commits**
   ```bash
   git commit -m "feat: Add new screenshot deduplication"
   ```

6. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

**Python Style:**
- Follow PEP 8
- Use type hints for all function signatures
- Write docstrings (Google style)
- Keep functions small and focused
- Use meaningful variable names

**Docstring Example:**

```python
def extract_audio(
    self,
    video_path: Path,
    output_path: Optional[Path] = None,
    sample_rate: int = 16000,
    channels: int = 1
) -> Path:
    """
    Extract audio from video file.

    Args:
        video_path: Path to input video file
        output_path: Path for output audio file (default: auto-generate)
        sample_rate: Audio sample rate in Hz (default: 16000)
        channels: Number of audio channels (default: 1 for mono)

    Returns:
        Path to extracted audio file

    Raises:
        FileNotFoundError: If video file doesn't exist
        FFmpegError: If FFmpeg extraction fails
    """
```

**Testing Guidelines:**
- Write tests for all new functionality
- Aim for >90% coverage
- Use descriptive test names
- Test both success and error paths
- Use fixtures for common setup

### Pull Request Process

1. **Ensure tests pass**: All tests must pass before review
2. **Update documentation**: README and DEVELOPMENT.md if needed
3. **Add changelog entry**: Document changes in commit message
4. **Request review**: Assign to maintainers
5. **Address feedback**: Make requested changes
6. **Merge**: Squash and merge after approval

## Development Tips

### Debugging

**Enable Debug Logging:**

```python
# In .env file
VIDEO_TOOLS_LOG_LEVEL=DEBUG
```

**Interactive Debugging:**

```bash
# Use pytest with -s flag to see print statements
uv run pytest tests/unit/ -s -v

# Use pdb for breakpoints
import pdb; pdb.set_trace()
```

### Performance Profiling

**Profile Code:**

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Management

**Monitor Model Memory:**

```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024**2:.1f} MB")
```

### Common Issues

**Issue: FFmpeg not found**

```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**Issue: HuggingFace authentication failed**

```bash
# Set token in .env
echo "HF_TOKEN=your_token_here" >> .env

# Or set environment variable
export HF_TOKEN=your_token_here
```

**Issue: Tests failing on CI**

- Ensure all dependencies in `pyproject.toml`
- Check Python version (3.11+ required)
- Verify mocks are platform-agnostic

## Resources

### Documentation

- **FastMCP**: https://github.com/jlowin/fastmcp
- **Parakeet MLX**: https://github.com/JosefAlbers/parakeet-mlx
- **Pyannote Audio**: https://github.com/pyannote/pyannote-audio
- **MLX VLM**: https://github.com/Blaizzy/mlx-vlm
- **Pydantic**: https://docs.pydantic.dev/

### Community

- **Issues**: https://github.com/autumnsgrove/video-tools/issues
- **Discussions**: https://github.com/autumnsgrove/video-tools/discussions
- **MCP Community**: https://modelcontextprotocol.io/

---

**Last Updated**: Phase 1 Complete (2025-11-15)
**Next Update**: Phase 2 (Transcription implementation)
