"""
Unit tests for configuration module (config/models.py).

Tests cover:
- Configuration model instantiation
- Pydantic validation rules
- Environment variable overrides
- Path expansion for ~ in paths
- load_config() function behavior
"""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from video_tools_mcp.config.models import (
    ParakeetConfig,
    PyannoteConfig,
    QwenVLConfig,
    ProcessingConfig,
    ScreenshotConfig,
    TranscriptionConfig,
    VideoToolsConfig,
    load_config
)


class TestParakeetConfig:
    """Test cases for ParakeetConfig model."""

    def test_default_values(self):
        """Test that ParakeetConfig initializes with correct defaults."""
        config = ParakeetConfig()

        assert config.model_id == "mlx-community/parakeet-tdt-0.6b-v3"
        assert config.chunk_duration == 120.0
        assert config.overlap_duration == 15.0
        assert config.language == "en"

    def test_custom_values(self):
        """Test ParakeetConfig accepts custom values."""
        config = ParakeetConfig(
            model_id="custom-model",
            chunk_duration=60.0,
            overlap_duration=10.0,
            language="es"
        )

        assert config.model_id == "custom-model"
        assert config.chunk_duration == 60.0
        assert config.overlap_duration == 10.0
        assert config.language == "es"

    def test_negative_chunk_duration_raises_error(self):
        """Test that negative chunk_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParakeetConfig(chunk_duration=-10.0)

        assert "Duration must be positive" in str(exc_info.value)

    def test_zero_chunk_duration_raises_error(self):
        """Test that zero chunk_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParakeetConfig(chunk_duration=0.0)

        assert "Duration must be positive" in str(exc_info.value)

    def test_negative_overlap_duration_raises_error(self):
        """Test that negative overlap_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ParakeetConfig(overlap_duration=-5.0)

        assert "Duration must be positive" in str(exc_info.value)


class TestPyannoteConfig:
    """Test cases for PyannoteConfig model."""

    def test_default_values(self):
        """Test that PyannoteConfig initializes with correct defaults."""
        config = PyannoteConfig()

        assert config.model_id == "pyannote/speaker-diarization-3.1"
        assert config.device == "mps"
        assert config.min_duration == 0.5
        assert config.hf_token is None

    def test_custom_values_with_token(self):
        """Test PyannoteConfig accepts custom values including HF token."""
        config = PyannoteConfig(
            model_id="custom-diarization",
            device="cuda",
            min_duration=1.0,
            hf_token="hf_test123"
        )

        assert config.model_id == "custom-diarization"
        assert config.device == "cuda"
        assert config.min_duration == 1.0
        assert config.hf_token == "hf_test123"

    def test_negative_min_duration_raises_error(self):
        """Test that negative min_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PyannoteConfig(min_duration=-0.5)

        assert "Minimum duration must be positive" in str(exc_info.value)

    def test_zero_min_duration_raises_error(self):
        """Test that zero min_duration is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PyannoteConfig(min_duration=0.0)

        assert "Minimum duration must be positive" in str(exc_info.value)


class TestQwenVLConfig:
    """Test cases for QwenVLConfig model."""

    def test_default_values(self):
        """Test that QwenVLConfig initializes with correct defaults."""
        config = QwenVLConfig()

        assert config.model_id == "mlx-community/Qwen2-VL-8B-Instruct-8bit"
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.fps == 1.0

    def test_custom_values(self):
        """Test QwenVLConfig accepts custom values."""
        config = QwenVLConfig(
            model_id="custom-vl-model",
            max_tokens=1024,
            temperature=0.5,
            fps=2.0
        )

        assert config.model_id == "custom-vl-model"
        assert config.max_tokens == 1024
        assert config.temperature == 0.5
        assert config.fps == 2.0

    def test_negative_max_tokens_raises_error(self):
        """Test that negative max_tokens is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QwenVLConfig(max_tokens=-100)

        assert "Max tokens must be positive" in str(exc_info.value)

    def test_zero_max_tokens_raises_error(self):
        """Test that zero max_tokens is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QwenVLConfig(max_tokens=0)

        assert "Max tokens must be positive" in str(exc_info.value)

    def test_temperature_below_range_raises_error(self):
        """Test that temperature below 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QwenVLConfig(temperature=-0.1)

        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)

    def test_temperature_above_range_raises_error(self):
        """Test that temperature above 2.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QwenVLConfig(temperature=2.5)

        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)

    def test_temperature_at_boundaries(self):
        """Test that temperature at 0.0 and 2.0 is accepted."""
        config_min = QwenVLConfig(temperature=0.0)
        config_max = QwenVLConfig(temperature=2.0)

        assert config_min.temperature == 0.0
        assert config_max.temperature == 2.0

    def test_negative_fps_raises_error(self):
        """Test that negative fps is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QwenVLConfig(fps=-1.0)

        assert "FPS must be positive" in str(exc_info.value)


class TestProcessingConfig:
    """Test cases for ProcessingConfig model."""

    def test_default_values(self):
        """Test that ProcessingConfig initializes with correct defaults."""
        config = ProcessingConfig()

        assert config.keep_temp_files is False
        assert config.temp_dir == "/tmp/video-tools"
        assert config.cache_dir is None

    def test_custom_values(self):
        """Test ProcessingConfig accepts custom values."""
        config = ProcessingConfig(
            keep_temp_files=True,
            temp_dir="/custom/temp",
            cache_dir="/custom/cache"
        )

        assert config.keep_temp_files is True
        assert config.temp_dir == "/custom/temp"
        assert config.cache_dir == "/custom/cache"

    def test_path_expansion_with_tilde(self, monkeypatch):
        """Test that ~ is expanded to home directory in paths."""
        # Get actual home directory
        home = str(Path.home())

        config = ProcessingConfig(
            temp_dir="~/temp",
            cache_dir="~/cache"
        )

        assert config.temp_dir == f"{home}/temp"
        assert config.cache_dir == f"{home}/cache"

    def test_path_expansion_with_none(self):
        """Test that None cache_dir is handled correctly."""
        config = ProcessingConfig(cache_dir=None)

        assert config.cache_dir is None


class TestScreenshotConfig:
    """Test cases for ScreenshotConfig model."""

    def test_default_values(self):
        """Test that ScreenshotConfig initializes with correct defaults."""
        config = ScreenshotConfig()

        assert config.default_interval == 5
        assert config.default_similarity == 0.90
        assert config.jpeg_quality == 95

    def test_custom_values(self):
        """Test ScreenshotConfig accepts custom values."""
        config = ScreenshotConfig(
            default_interval=10,
            default_similarity=0.85,
            jpeg_quality=90
        )

        assert config.default_interval == 10
        assert config.default_similarity == 0.85
        assert config.jpeg_quality == 90

    def test_negative_interval_raises_error(self):
        """Test that negative interval is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotConfig(default_interval=-5)

        assert "Interval must be positive" in str(exc_info.value)

    def test_similarity_below_range_raises_error(self):
        """Test that similarity below 0.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotConfig(default_similarity=-0.1)

        assert "Similarity threshold must be between 0.0 and 1.0" in str(exc_info.value)

    def test_similarity_above_range_raises_error(self):
        """Test that similarity above 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotConfig(default_similarity=1.5)

        assert "Similarity threshold must be between 0.0 and 1.0" in str(exc_info.value)

    def test_jpeg_quality_below_range_raises_error(self):
        """Test that JPEG quality below 0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotConfig(jpeg_quality=-10)

        assert "JPEG quality must be between 0 and 100" in str(exc_info.value)

    def test_jpeg_quality_above_range_raises_error(self):
        """Test that JPEG quality above 100 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ScreenshotConfig(jpeg_quality=110)

        assert "JPEG quality must be between 0 and 100" in str(exc_info.value)


class TestTranscriptionConfig:
    """Test cases for TranscriptionConfig model."""

    def test_default_values(self):
        """Test that TranscriptionConfig initializes with correct defaults."""
        config = TranscriptionConfig()

        assert config.default_format == "srt"

    def test_valid_formats(self):
        """Test that all valid formats are accepted."""
        valid_formats = ["srt", "vtt", "txt", "json"]

        for fmt in valid_formats:
            config = TranscriptionConfig(default_format=fmt)
            assert config.default_format == fmt

    def test_invalid_format_raises_error(self):
        """Test that invalid format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TranscriptionConfig(default_format="invalid")

        assert "Format must be one of" in str(exc_info.value)

    def test_format_case_insensitive(self):
        """Test that format is converted to lowercase."""
        config = TranscriptionConfig(default_format="SRT")

        assert config.default_format == "srt"


class TestVideoToolsConfig:
    """Test cases for main VideoToolsConfig model."""

    def test_default_values(self):
        """Test that VideoToolsConfig initializes with all sub-configs."""
        config = VideoToolsConfig()

        # Verify all sub-configs exist with defaults
        assert isinstance(config.parakeet, ParakeetConfig)
        assert isinstance(config.pyannote, PyannoteConfig)
        assert isinstance(config.qwen_vl, QwenVLConfig)
        assert isinstance(config.processing, ProcessingConfig)
        assert isinstance(config.screenshot, ScreenshotConfig)
        assert isinstance(config.transcription, TranscriptionConfig)

    def test_custom_sub_configs(self):
        """Test that VideoToolsConfig accepts custom sub-configs."""
        config = VideoToolsConfig(
            parakeet=ParakeetConfig(language="es"),
            pyannote=PyannoteConfig(device="cuda"),
            processing=ProcessingConfig(keep_temp_files=True)
        )

        assert config.parakeet.language == "es"
        assert config.pyannote.device == "cuda"
        assert config.processing.keep_temp_files is True


class TestLoadConfig:
    """Test cases for load_config() function."""

    def test_load_config_with_defaults(self, clean_env_vars, temp_dir, monkeypatch):
        """Test load_config() with no environment variables uses defaults."""
        # Override temp dir to use test temp dir to avoid creating /tmp/video-tools
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(temp_dir))

        config = load_config()

        # Check defaults are used
        assert config.pyannote.hf_token is None
        assert config.processing.cache_dir is None
        assert config.processing.temp_dir == str(temp_dir)
        assert config.processing.keep_temp_files is False

    def test_load_config_with_env_vars(self, temp_dir, monkeypatch):
        """Test load_config() respects environment variables."""
        # Set environment variables
        test_cache_dir = temp_dir / "cache"
        test_temp_dir = temp_dir / "temp"

        monkeypatch.setenv("HF_TOKEN", "test_hf_token_abc123")
        monkeypatch.setenv("VIDEO_TOOLS_CACHE_DIR", str(test_cache_dir))
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(test_temp_dir))
        monkeypatch.setenv("VIDEO_TOOLS_KEEP_TEMP", "true")

        config = load_config()

        # Check environment overrides are applied
        assert config.pyannote.hf_token == "test_hf_token_abc123"
        assert config.processing.cache_dir == str(test_cache_dir)
        assert config.processing.temp_dir == str(test_temp_dir)
        assert config.processing.keep_temp_files is True

    def test_load_config_creates_cache_dir(self, temp_dir, monkeypatch):
        """Test load_config() creates cache directory if specified."""
        test_cache_dir = temp_dir / "new_cache"
        test_temp_dir = temp_dir / "temp"

        monkeypatch.setenv("VIDEO_TOOLS_CACHE_DIR", str(test_cache_dir))
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(test_temp_dir))

        # Cache dir shouldn't exist yet
        assert not test_cache_dir.exists()

        config = load_config()

        # Cache dir should be created
        assert test_cache_dir.exists()
        assert test_cache_dir.is_dir()

    def test_load_config_creates_temp_dir(self, temp_dir, monkeypatch):
        """Test load_config() creates temp directory."""
        test_temp_dir = temp_dir / "new_temp"

        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(test_temp_dir))

        # Temp dir shouldn't exist yet
        assert not test_temp_dir.exists()

        config = load_config()

        # Temp dir should be created
        assert test_temp_dir.exists()
        assert test_temp_dir.is_dir()

    def test_load_config_keep_temp_false_by_default(self, temp_dir, monkeypatch):
        """Test that keep_temp_files defaults to False."""
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(temp_dir))
        monkeypatch.delenv("VIDEO_TOOLS_KEEP_TEMP", raising=False)

        config = load_config()

        assert config.processing.keep_temp_files is False

    def test_load_config_keep_temp_accepts_true(self, temp_dir, monkeypatch):
        """Test that keep_temp_files can be set to True."""
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(temp_dir))
        monkeypatch.setenv("VIDEO_TOOLS_KEEP_TEMP", "true")

        config = load_config()

        assert config.processing.keep_temp_files is True

    def test_load_config_keep_temp_case_insensitive(self, temp_dir, monkeypatch):
        """Test that keep_temp_files is case-insensitive."""
        monkeypatch.setenv("VIDEO_TOOLS_TEMP_DIR", str(temp_dir))
        monkeypatch.setenv("VIDEO_TOOLS_KEEP_TEMP", "TRUE")

        config = load_config()

        assert config.processing.keep_temp_files is True
