"""Configuration management for video tools."""

from .models import (
    ParakeetConfig,
    PyannoteConfig,
    QwenVLConfig,
    ProcessingConfig,
    ScreenshotConfig,
    TranscriptionConfig,
    VideoToolsConfig,
    load_config,
)
from .prompts import (
    DEFAULT_ANALYSIS_PROMPT,
    DEFAULT_SCREENSHOT_EXTRACTION_PROMPT,
    DETAILED_ANALYSIS_PROMPT,
    TECHNICAL_ANALYSIS_PROMPT,
    OCR_FOCUSED_PROMPT,
    ACCESSIBILITY_PROMPT,
    PRESENTATION_SCREENSHOT_PROMPT,
    TUTORIAL_SCREENSHOT_PROMPT,
    SOCIAL_MEDIA_SCREENSHOT_PROMPT,
)

__all__ = [
    # Configuration models
    "ParakeetConfig",
    "PyannoteConfig",
    "QwenVLConfig",
    "ProcessingConfig",
    "ScreenshotConfig",
    "TranscriptionConfig",
    "VideoToolsConfig",
    "load_config",
    # Default prompts
    "DEFAULT_ANALYSIS_PROMPT",
    "DEFAULT_SCREENSHOT_EXTRACTION_PROMPT",
    # Alternative prompts
    "DETAILED_ANALYSIS_PROMPT",
    "TECHNICAL_ANALYSIS_PROMPT",
    "OCR_FOCUSED_PROMPT",
    "ACCESSIBILITY_PROMPT",
    "PRESENTATION_SCREENSHOT_PROMPT",
    "TUTORIAL_SCREENSHOT_PROMPT",
    "SOCIAL_MEDIA_SCREENSHOT_PROMPT",
]
