"""
Pytest configuration and shared fixtures for video-tools-mcp tests.

This module provides common fixtures used across unit and integration tests:
- Temporary directory management
- Mock video files
- Environment variable mocking
- Configuration fixtures
"""

import os
import tempfile
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for tests.

    Automatically cleaned up after test completion.

    Yields:
        Path: Temporary directory path

    Example:
        >>> def test_file_creation(temp_dir):
        ...     test_file = temp_dir / "test.txt"
        ...     test_file.write_text("hello")
        ...     assert test_file.exists()
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_video_path(temp_dir):
    """
    Create a mock video file for testing.

    Creates an empty .mp4 file in temp directory.
    Note: This is just an empty file with video extension,
    not a real video file with encoded data.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        str: Path to mock video file

    Example:
        >>> def test_video_processing(mock_video_path):
        ...     assert Path(mock_video_path).exists()
        ...     assert mock_video_path.endswith(".mp4")
    """
    video_file = temp_dir / "test_video.mp4"
    video_file.touch()  # Create empty file
    return str(video_file)


@pytest.fixture
def mock_audio_path(temp_dir):
    """
    Create a mock audio file for testing.

    Creates an empty .wav file in temp directory.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        str: Path to mock audio file
    """
    audio_file = temp_dir / "test_audio.wav"
    audio_file.touch()  # Create empty file
    return str(audio_file)


@pytest.fixture
def mock_srt_path(temp_dir):
    """
    Create a mock SRT subtitle file for testing.

    Creates a simple SRT file with speaker labels.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        str: Path to mock SRT file
    """
    srt_file = temp_dir / "test_subtitles.srt"
    srt_content = """1
00:00:00,000 --> 00:00:05,000
Speaker 1: Hello, this is a test.

2
00:00:05,000 --> 00:00:10,000
Speaker 2: Yes, I agree.

3
00:00:10,000 --> 00:00:15,000
Speaker 1: Great, let's continue.
"""
    srt_file.write_text(srt_content)
    return str(srt_file)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Mock environment variables for testing configuration.

    Sets test values for common environment variables used
    by the video-tools-mcp configuration system.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Dict[str, str]: Dictionary of mocked environment variables

    Example:
        >>> def test_config_loading(mock_env_vars):
        ...     assert os.getenv("HF_TOKEN") == "test_token_123"
        ...     assert os.getenv("VIDEO_TOOLS_CACHE_DIR") == "/tmp/test_cache"
    """
    env_vars = {
        "HF_TOKEN": "test_token_123",
        "VIDEO_TOOLS_CACHE_DIR": "/tmp/test_cache",
        "VIDEO_TOOLS_TEMP_DIR": "/tmp/test_temp",
        "VIDEO_TOOLS_KEEP_TEMP": "true"
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def clean_env_vars(monkeypatch):
    """
    Remove all video-tools environment variables for clean testing.

    Useful for testing default configuration behavior without
    environment variable overrides.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Example:
        >>> def test_default_config(clean_env_vars):
        ...     # No env vars set, should use defaults
        ...     config = load_config()
        ...     assert config.processing.temp_dir == "/tmp/video-tools"
    """
    env_vars_to_remove = [
        "HF_TOKEN",
        "VIDEO_TOOLS_CACHE_DIR",
        "VIDEO_TOOLS_TEMP_DIR",
        "VIDEO_TOOLS_KEEP_TEMP"
    ]

    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def sample_video_files(temp_dir):
    """
    Create multiple sample video files with different extensions.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Dict[str, str]: Dictionary mapping extension to file path

    Example:
        >>> def test_multi_format(sample_video_files):
        ...     assert "mp4" in sample_video_files
        ...     assert Path(sample_video_files["mp4"]).exists()
    """
    extensions = ["mp4", "mov", "avi", "mkv", "webm"]
    files = {}

    for ext in extensions:
        file_path = temp_dir / f"test_video.{ext}"
        file_path.touch()
        files[ext] = str(file_path)

    return files


@pytest.fixture
def mock_config_dict():
    """
    Return a dictionary representing a complete VideoToolsConfig.

    Useful for testing configuration loading and validation.

    Returns:
        Dict: Configuration dictionary
    """
    return {
        "parakeet": {
            "model_id": "mlx-community/parakeet-tdt-0.6b-v3",
            "chunk_duration": 120.0,
            "overlap_duration": 15.0,
            "language": "en"
        },
        "pyannote": {
            "model_id": "pyannote/speaker-diarization-3.1",
            "device": "mps",
            "min_duration": 0.5,
            "hf_token": "test_token"
        },
        "qwen_vl": {
            "model_id": "mlx-community/Qwen2-VL-8B-Instruct-8bit",
            "max_tokens": 512,
            "temperature": 0.7,
            "fps": 1.0
        },
        "processing": {
            "keep_temp_files": False,
            "temp_dir": "/tmp/video-tools",
            "cache_dir": None
        },
        "screenshot": {
            "default_interval": 5,
            "default_similarity": 0.90,
            "jpeg_quality": 95
        },
        "transcription": {
            "default_format": "srt"
        }
    }


# ============================================
# Integration Test Fixtures (Phase 6)
# ============================================

# Test video paths - these match the download script filenames
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "videos"

# Single speaker videos
SHORT_TUTORIAL = FIXTURES_DIR / "short_30s_addition_tutorial.mp4"
SHORT_HISTORY = FIXTURES_DIR / "short_120s_edward_viii.mp4"
MEDIUM_TED_TALK = FIXTURES_DIR / "medium_357s_clayton_cameron_ted.mp4"
LONG_TUTORIAL = FIXTURES_DIR / "long_663s_big_bang_tutorial.mp4"

# Multi-speaker videos
MULTI_SPEAKER_2 = FIXTURES_DIR / "multi_180s_job_interview.mp4"
MULTI_SPEAKER_3 = FIXTURES_DIR / "multi_300s_cafe_conversation.mp4"

# Visual content videos
VISUAL_SHORT = FIXTURES_DIR / "visual_90s_llama_drama_1080p.mp4"
VISUAL_EFFECTS = FIXTURES_DIR / "visual_734s_tears_steel_1080p.mp4"

# Long-form & edge case videos
LONG_PRESENTATION = FIXTURES_DIR / "long_883s_david_rose_ted.mp4"
EDGE_4K = FIXTURES_DIR / "edge_888s_sintel_2048p.mp4"


def videos_available() -> Dict[str, bool]:
    """Check which test videos are available."""
    return {
        "short_tutorial": SHORT_TUTORIAL.exists(),
        "short_history": SHORT_HISTORY.exists(),
        "medium_ted_talk": MEDIUM_TED_TALK.exists(),
        "long_tutorial": LONG_TUTORIAL.exists(),
        "multi_speaker_2": MULTI_SPEAKER_2.exists(),
        "multi_speaker_3": MULTI_SPEAKER_3.exists(),
        "visual_short": VISUAL_SHORT.exists(),
        "visual_effects": VISUAL_EFFECTS.exists(),
        "long_presentation": LONG_PRESENTATION.exists(),
        "edge_4k": EDGE_4K.exists(),
    }


def any_videos_available() -> bool:
    """Check if at least one test video is available."""
    return any(videos_available().values())


def all_videos_available() -> bool:
    """Check if all test videos are available."""
    return all(videos_available().values())


@pytest.fixture
def require_short_video():
    """Fixture that requires a short test video."""
    if not SHORT_TUTORIAL.exists():
        pytest.skip(
            f"Short test video not found: {SHORT_TUTORIAL.name}. "
            "Download with: python scripts/download_test_videos.py --video short_tutorial"
        )
    return SHORT_TUTORIAL


@pytest.fixture
def require_multi_speaker_video():
    """Fixture that requires a multi-speaker video."""
    if not MULTI_SPEAKER_2.exists():
        pytest.skip(
            f"Multi-speaker video not found: {MULTI_SPEAKER_2.name}. "
            "Download with: python scripts/download_test_videos.py --video interview_2speaker"
        )
    return MULTI_SPEAKER_2


@pytest.fixture
def require_visual_video():
    """Fixture that requires a visual content video."""
    if not VISUAL_SHORT.exists():
        pytest.skip(
            f"Visual test video not found: {VISUAL_SHORT.name}. "
            "Download with: python scripts/download_test_videos.py --video visual_short"
        )
    return VISUAL_SHORT


@pytest.fixture
def require_any_video():
    """Fixture that requires at least one test video."""
    if not any_videos_available():
        pytest.skip(
            "No test videos found. Download with: python scripts/download_test_videos.py"
        )
    # Return the first available video
    for video_path in [SHORT_TUTORIAL, SHORT_HISTORY, MEDIUM_TED_TALK, VISUAL_SHORT]:
        if video_path.exists():
            return video_path
    pytest.skip("No test videos found")


def pytest_configure(config):
    """Pytest configuration hook."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "requires_videos: mark test as requiring test videos"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>5 seconds)"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as performance benchmark"
    )
