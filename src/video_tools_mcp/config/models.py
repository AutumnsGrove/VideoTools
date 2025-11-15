"""
Configuration models for video-tools-mcp using Pydantic.

This module defines all configuration classes for the different models
and processing settings used in the video tools MCP server.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ParakeetConfig(BaseModel):
    """Configuration for Parakeet MLX transcription model."""

    model_id: str = Field(
        default="mlx-community/parakeet-tdt-0.6b-v3",
        description="HuggingFace model ID for Parakeet transcription"
    )
    chunk_duration: float = Field(
        default=120.0,
        description="Duration of audio chunks in seconds (2 minutes)"
    )
    overlap_duration: float = Field(
        default=15.0,
        description="Overlap between chunks in seconds"
    )
    language: str = Field(
        default="en",
        description="Language code for transcription"
    )

    @field_validator("chunk_duration", "overlap_duration")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        """Ensure duration values are positive."""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class PyannoteConfig(BaseModel):
    """Configuration for Pyannote speaker diarization model."""

    model_id: str = Field(
        default="pyannote/speaker-diarization-3.1",
        description="HuggingFace model ID for speaker diarization"
    )
    device: str = Field(
        default="mps",
        description="Device to run the model on (mps, cuda, cpu)"
    )
    min_duration: float = Field(
        default=0.5,
        description="Minimum segment duration in seconds"
    )
    hf_token: Optional[str] = Field(
        default=None,
        description="HuggingFace API token (required for pyannote models)"
    )

    @field_validator("min_duration")
    @classmethod
    def validate_min_duration(cls, v: float) -> float:
        """Ensure minimum duration is positive."""
        if v <= 0:
            raise ValueError("Minimum duration must be positive")
        return v


class QwenVLConfig(BaseModel):
    """Configuration for Qwen VL vision-language model."""

    model_id: str = Field(
        default="mlx-community/Qwen2-VL-8B-Instruct-8bit",
        description="HuggingFace model ID for Qwen VL"
    )
    max_tokens: int = Field(
        default=512,
        description="Maximum tokens for model generation"
    )
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for generation"
    )
    fps: float = Field(
        default=1.0,
        description="Frame sampling rate for video analysis (frames per second)"
    )

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Ensure max tokens is positive."""
        if v <= 0:
            raise ValueError("Max tokens must be positive")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v: float) -> float:
        """Ensure FPS is positive."""
        if v <= 0:
            raise ValueError("FPS must be positive")
        return v


class ProcessingConfig(BaseModel):
    """Configuration for general processing settings."""

    keep_temp_files: bool = Field(
        default=False,
        description="Whether to keep temporary files after processing"
    )
    temp_dir: str = Field(
        default="/tmp/video-tools",
        description="Directory for temporary files"
    )
    cache_dir: Optional[str] = Field(
        default=None,
        description="Directory for caching models and intermediate results"
    )

    @field_validator("temp_dir", "cache_dir")
    @classmethod
    def expand_path(cls, v: Optional[str]) -> Optional[str]:
        """Expand ~ in paths to home directory."""
        if v is None:
            return v
        return str(Path(v).expanduser())


class ScreenshotConfig(BaseModel):
    """Configuration for screenshot extraction."""

    default_interval: int = Field(
        default=5,
        description="Default interval in seconds between screenshot checks"
    )
    default_similarity: float = Field(
        default=0.90,
        description="Default similarity threshold for deduplication (0-1)"
    )
    jpeg_quality: int = Field(
        default=95,
        description="JPEG quality for saved screenshots (0-100)"
    )

    @field_validator("default_interval")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        """Ensure interval is positive."""
        if v <= 0:
            raise ValueError("Interval must be positive")
        return v

    @field_validator("default_similarity")
    @classmethod
    def validate_similarity(cls, v: float) -> float:
        """Ensure similarity threshold is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        return v

    @field_validator("jpeg_quality")
    @classmethod
    def validate_quality(cls, v: int) -> int:
        """Ensure JPEG quality is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("JPEG quality must be between 0 and 100")
        return v


class TranscriptionConfig(BaseModel):
    """Configuration for transcription output."""

    default_format: str = Field(
        default="srt",
        description="Default format for transcription output"
    )

    @field_validator("default_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Ensure format is supported."""
        valid_formats = {"srt", "vtt", "txt", "json"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Format must be one of: {valid_formats}")
        return v.lower()


class VideoToolsConfig(BaseModel):
    """Main configuration class that combines all settings."""

    parakeet: ParakeetConfig = Field(default_factory=ParakeetConfig)
    pyannote: PyannoteConfig = Field(default_factory=PyannoteConfig)
    qwen_vl: QwenVLConfig = Field(default_factory=QwenVLConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    screenshot: ScreenshotConfig = Field(default_factory=ScreenshotConfig)
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)


def load_config() -> VideoToolsConfig:
    """
    Load configuration from environment variables with sensible defaults.

    Environment variables:
        HF_TOKEN: HuggingFace API token (required for pyannote)
        VIDEO_TOOLS_CACHE_DIR: Cache directory for models
        VIDEO_TOOLS_TEMP_DIR: Temporary directory for processing
        VIDEO_TOOLS_KEEP_TEMP: Keep temporary files (true/false)

    Returns:
        VideoToolsConfig: Loaded configuration object
    """
    # Load environment variables
    hf_token = os.getenv("HF_TOKEN")
    cache_dir = os.getenv("VIDEO_TOOLS_CACHE_DIR")
    temp_dir = os.getenv("VIDEO_TOOLS_TEMP_DIR", "/tmp/video-tools")
    keep_temp = os.getenv("VIDEO_TOOLS_KEEP_TEMP", "false").lower() == "true"

    # Create configuration
    config = VideoToolsConfig(
        pyannote=PyannoteConfig(hf_token=hf_token),
        processing=ProcessingConfig(
            cache_dir=cache_dir,
            temp_dir=temp_dir,
            keep_temp_files=keep_temp
        )
    )

    # Ensure cache directory exists if specified
    if config.processing.cache_dir:
        cache_path = Path(config.processing.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

    # Ensure temp directory exists
    temp_path = Path(config.processing.temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)

    return config
