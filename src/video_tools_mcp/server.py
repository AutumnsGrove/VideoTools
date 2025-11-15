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
import tempfile
import shutil
import json
from typing import Optional, Dict, Any
from pathlib import Path

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
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    language: str = "en",
    cleanup_temp_files: bool = True
) -> Dict[str, Any]:
    """
    Transcribe video with speaker diarization.

    Args:
        video_path: Path to video file
        output_format: Output format (srt, json, txt)
        num_speakers: Exact number of speakers (if known)
        min_speakers: Minimum number of speakers
        max_speakers: Maximum number of speakers
        language: Language code for transcription
        cleanup_temp_files: Whether to delete temporary files

    Returns:
        {
            "transcript_path": str,
            "speakers_detected": int,
            "duration": float,
            "num_segments": int,
            "speakers": List[str]
        }
    """
    from video_tools_mcp.processing import transcribe_video_file
    from video_tools_mcp.processing.diarization_merge import (
        merge_transcription_with_diarization,
        format_speaker_transcript
    )
    from video_tools_mcp.processing.audio_extraction import extract_audio
    from video_tools_mcp.models.pyannote import PyannoteModel
    from video_tools_mcp.utils.srt_utils import write_srt_file

    logger.info(f"Starting speaker diarization for: {video_path}")

    # 1. Validate video file
    video_path = Path(video_path)
    if not video_path.exists():
        raise ValueError(f"Video file not found: {video_path}")

    # 2. Extract audio (temporary file)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        audio_path = tmp_audio.name

    try:
        extract_audio(str(video_path), audio_path)

        # 3. Run transcription
        logger.info("Running transcription with Parakeet...")
        transcription_result = transcribe_video_file(
            str(video_path),
            language=language,
            cleanup_temp_files=False  # We'll manage cleanup
        )

        # 4. Run diarization
        logger.info("Running speaker diarization with Pyannote...")
        pyannote = PyannoteModel()
        pyannote.ensure_loaded()
        diarization_result = pyannote.diarize(
            audio_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )

        # 5. Merge transcription with diarization
        logger.info("Merging transcription with speaker labels...")
        merged_segments = merge_transcription_with_diarization(
            transcription_result,
            diarization_result
        )

        # 6. Format with speaker prefixes
        formatted_segments = format_speaker_transcript(merged_segments)

        # 7. Generate output file
        output_path = video_path.with_suffix(f".speakers.{output_format}")

        if output_format == "srt":
            write_srt_file(formatted_segments, str(output_path))
        elif output_format == "json":
            with open(output_path, 'w') as f:
                json.dump({
                    "segments": formatted_segments,
                    "speakers": diarization_result["speakers"],
                    "num_speakers": diarization_result["num_speakers"],
                    "duration": transcription_result["duration"]
                }, f, indent=2)
        elif output_format == "txt":
            with open(output_path, 'w') as f:
                for seg in formatted_segments:
                    f.write(f"{seg['text']}\n")

        # 8. Cleanup
        if cleanup_temp_files:
            Path(audio_path).unlink(missing_ok=True)

        logger.info(f"Speaker diarization complete: {output_path}")

        return {
            "transcript_path": str(output_path),
            "speakers_detected": diarization_result["num_speakers"],
            "speakers": diarization_result["speakers"],
            "duration": transcription_result["duration"],
            "num_segments": len(formatted_segments),
            "output_format": output_format
        }

    finally:
        # Ensure cleanup even if errors occur
        if cleanup_temp_files and Path(audio_path).exists():
            Path(audio_path).unlink(missing_ok=True)


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
    speaker_map: Dict[str, str],
    output_path: Optional[str] = None,
    create_backup: bool = True
) -> Dict[str, Any]:
    """
    Rename speakers in an SRT file.

    Args:
        srt_path: Path to SRT file with speaker labels
        speaker_map: Mapping of old to new speaker names (e.g., {"SPEAKER_00": "Alice", "SPEAKER_01": "Bob"})
        output_path: Output path (defaults to overwriting input file)
        create_backup: Whether to create a backup of the original file

    Returns:
        {
            "output_path": str,
            "replacements_made": int,
            "backup_path": Optional[str],
            "speakers_renamed": List[str]
        }
    """
    from video_tools_mcp.utils.srt_utils import parse_srt_file, write_srt_file

    logger.info(f"Renaming speakers in: {srt_path}")

    # 1. Validate input file
    srt_path = Path(srt_path)
    if not srt_path.exists():
        raise ValueError(f"SRT file not found: {srt_path}")

    # 2. Parse SRT file
    segments = parse_srt_file(str(srt_path))

    # 3. Create backup if requested
    backup_path = None
    if create_backup:
        backup_path = str(srt_path) + ".bak"
        shutil.copy(str(srt_path), backup_path)
        logger.info(f"Created backup: {backup_path}")

    # 4. Apply speaker name replacements
    replacements_made = 0
    speakers_renamed = set()

    for segment in segments:
        text = segment["text"]
        for old_name, new_name in speaker_map.items():
            # Match speaker prefix (e.g., "SPEAKER_00: ")
            if text.startswith(f"{old_name}:"):
                segment["text"] = text.replace(f"{old_name}:", f"{new_name}:", 1)
                replacements_made += 1
                speakers_renamed.add(old_name)
                break

    # 5. Write updated SRT file
    output = output_path or str(srt_path)
    write_srt_file(segments, output)

    logger.info(f"Speaker renaming complete: {replacements_made} replacements made")

    return {
        "output_path": output,
        "replacements_made": replacements_made,
        "backup_path": backup_path,
        "speakers_renamed": sorted(list(speakers_renamed))
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
