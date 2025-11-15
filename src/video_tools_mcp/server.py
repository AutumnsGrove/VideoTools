"""
Video Tools MCP Server - Main FastMCP server implementation.

This server provides AI-powered video processing tools via MCP protocol:
- Basic transcription (no speaker ID)
- Speaker diarization transcription
- Frame-by-frame video analysis
- Smart screenshot extraction with deduplication
- Speaker label renaming utilities

Phase 1: Stub implementations for protocol testing
Phase 2+: Real integrations with Parakeet, Qwen VL, etc.
"""

import logging
from typing import Optional

from fastmcp import FastMCP
from video_tools_mcp.config.prompts import (
    DEFAULT_ANALYSIS_PROMPT,
    DEFAULT_SCREENSHOT_EXTRACTION_PROMPT
)

# Set up module logger
logger = logging.getLogger(__name__)

# Initialize FastMCP application
mcp = FastMCP(
    "video-tools",
    version="0.1.0"
)


@mcp.tool()
def transcribe_video(
    video_path: str,
    output_format: str = "srt",
    model: str = "parakeet-tdt-0.6b-v3",
    language: str = "en"
) -> dict:
    """
    Basic video transcription without speaker identification.

    Args:
        video_path: Path to video file
        output_format: Output format (srt/vtt/json/txt)
        model: Model to use (default: parakeet-tdt-0.6b-v3)
        language: Language code (default: en)

    Returns:
        Dict with transcript_path, duration, word_count, processing_time
    """
    # STUB Phase 1
    logger.info(f"[STUB] transcribe_video called with: {video_path}")
    logger.info(f"  format={output_format}, model={model}, language={language}")

    # TODO Phase 2: Integrate with transcribe_simple.py
    # - Extract audio from video
    # - Run Parakeet TDT model
    # - Format output as requested (SRT/VTT/JSON/TXT)

    return {
        "transcript_path": f"{video_path}.{output_format}",
        "duration": 120.5,
        "word_count": 350,
        "processing_time": 5.2
    }


@mcp.tool()
def transcribe_with_speakers(
    video_path: str,
    output_format: str = "srt",
    num_speakers: Optional[int] = None,
    min_speakers: int = 1,
    max_speakers: int = 10
) -> dict:
    """
    Transcription with speaker diarization (multi-speaker support).

    Args:
        video_path: Path to video file
        output_format: Output format (srt/vtt/json)
        num_speakers: Expected speaker count (None = auto-detect)
        min_speakers: Minimum speakers (default: 1)
        max_speakers: Maximum speakers (default: 10)

    Returns:
        Dict with transcript_path, speakers_detected, duration, processing_time
    """
    # STUB Phase 1
    logger.info(f"[STUB] transcribe_with_speakers called with: {video_path}")
    logger.info(f"  num_speakers={num_speakers}, min={min_speakers}, max={max_speakers}")

    # TODO Phase 2: Integrate with transcribe_speaker_diarization.py
    # - Extract audio from video
    # - Run Parakeet TDT + diarization model
    # - Cluster speakers (auto-detect or use num_speakers)
    # - Format with speaker labels

    return {
        "transcript_path": f"{video_path}.speakers.{output_format}",
        "speakers_detected": num_speakers or 2,
        "duration": 120.5,
        "processing_time": 45.3
    }


@mcp.tool()
def analyze_video(
    video_path: str,
    analysis_prompt: Optional[str] = None,
    sample_interval: int = 5,
    max_frames: int = 100,
    include_ocr: bool = False
) -> dict:
    """
    Frame-by-frame analysis with Qwen VL for video understanding.

    Args:
        video_path: Path to video file
        analysis_prompt: Custom analysis prompt (uses default if None)
        sample_interval: Seconds between samples (default: 5)
        max_frames: Maximum frames to analyze (default: 100)
        include_ocr: Extract text from frames (default: False)

    Returns:
        Dict with analysis_path, frames_analyzed, duration, processing_time
    """
    # STUB Phase 1
    logger.info(f"[STUB] analyze_video called with: {video_path}")
    logger.info(f"  interval={sample_interval}s, max_frames={max_frames}, ocr={include_ocr}")

    # Use default prompt if not provided
    prompt = analysis_prompt or DEFAULT_ANALYSIS_PROMPT
    logger.info(f"  Using analysis prompt: {prompt[:50]}...")

    # TODO Phase 2: Integrate with analyze_video.py
    # - Sample frames at intervals
    # - Run Qwen VL on each frame with prompt
    # - Optionally run OCR (pytesseract/PaddleOCR)
    # - Aggregate results into JSON report

    return {
        "analysis_path": f"{video_path}.analysis.json",
        "frames_analyzed": 50,
        "duration": 300.0,
        "processing_time": 125.7
    }


@mcp.tool()
def extract_smart_screenshots(
    video_path: str,
    extraction_prompt: Optional[str] = None,
    sample_interval: int = 5,
    similarity_threshold: float = 0.90,
    max_screenshots: int = 50,
    output_dir: Optional[str] = None
) -> dict:
    """
    AI-driven screenshot extraction with deduplication and auto-captioning.

    Args:
        video_path: Path to video file
        extraction_prompt: Custom extraction prompt
        sample_interval: Check every N seconds (default: 5)
        similarity_threshold: pHash similarity % (default: 0.90)
        max_screenshots: Maximum to extract (default: 50)
        output_dir: Output directory (default: same as video)

    Returns:
        Dict with screenshots list, metadata_path, total_extracted, duplicates_removed, processing_time
    """
    # STUB Phase 1
    logger.info(f"[STUB] extract_smart_screenshots called with: {video_path}")
    logger.info(f"  interval={sample_interval}s, threshold={similarity_threshold}, max={max_screenshots}")

    # Use default prompt if not provided
    prompt = extraction_prompt or DEFAULT_SCREENSHOT_EXTRACTION_PROMPT
    logger.info(f"  Using extraction prompt: {prompt[:50]}...")

    # TODO Phase 2: Integrate with screenshot_extraction.py
    # - Sample frames at intervals
    # - Compute pHash for deduplication
    # - Run Qwen VL to decide: keep/skip with reasoning
    # - Generate captions for kept frames
    # - Save with metadata JSON

    return {
        "screenshots": [f"{video_path}.screenshots/screenshot_00001.jpg"],
        "metadata_path": f"{video_path}.screenshots.json",
        "total_extracted": 25,
        "duplicates_removed": 5,
        "processing_time": 180.4
    }


@mcp.tool()
def rename_speakers(
    srt_path: str,
    speaker_map: dict,
    output_path: Optional[str] = None,
    backup: bool = True
) -> dict:
    """
    Bulk rename speaker labels in SRT files.

    Args:
        srt_path: Path to SRT file
        speaker_map: Dict mapping old names to new (e.g., {"Speaker 1": "Autumn"})
        output_path: Output path (default: overwrite original)
        backup: Create .bak file (default: True)

    Returns:
        Dict with output_path, replacements_made, backup_path
    """
    # STUB Phase 1
    logger.info(f"[STUB] rename_speakers called with: {srt_path}")
    logger.info(f"  speaker_map={speaker_map}, backup={backup}")

    # TODO Phase 2: Implement real SRT renaming
    # - Parse SRT file
    # - Replace speaker labels using speaker_map
    # - Save to output_path (or overwrite)
    # - Create backup if requested

    backup_path = f"{srt_path}.bak" if backup else None

    return {
        "output_path": output_path or srt_path,
        "replacements_made": len(speaker_map),
        "backup_path": backup_path
    }


def main():
    """Main entry point for video-tools MCP server."""
    import sys

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting video-tools MCP server...")
    logger.info("Server: video-tools v0.1.0")
    logger.info("Phase 1: Stub tools registered (5 tools available)")
    logger.info("")
    logger.info("Available tools:")
    logger.info("  1. transcribe_video - Basic transcription (no speakers)")
    logger.info("  2. transcribe_with_speakers - Speaker diarization")
    logger.info("  3. analyze_video - Frame-by-frame analysis")
    logger.info("  4. extract_smart_screenshots - AI-driven screenshot extraction")
    logger.info("  5. rename_speakers - Bulk rename speaker labels")
    logger.info("")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
