"""
Video transcription processing with chunking support.

This module provides utilities for:
- Transcribing video files with automatic audio extraction
- Chunking long audio files for processing
- Merging chunk transcriptions with overlap handling
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

from parakeet_mlx.audio import load_audio
from video_tools_mcp.models.parakeet import ParakeetModel
from video_tools_mcp.config import load_config
from video_tools_mcp.processing.audio_extraction import extract_audio, cleanup_audio_file
from video_tools_mcp.utils.file_utils import validate_video_path, VideoProcessingError

# Set up module logger
logger = logging.getLogger(__name__)


def chunk_audio(
    audio_data: np.ndarray,
    sample_rate: int,
    chunk_duration: float = 120.0,
    overlap_duration: float = 15.0
) -> List[Tuple[np.ndarray, float, float]]:
    """Split audio into overlapping chunks for processing.

    Args:
        audio_data: Audio samples as numpy array
        sample_rate: Audio sample rate (Hz)
        chunk_duration: Duration of each chunk in seconds (default: 120.0)
        overlap_duration: Overlap between chunks in seconds (default: 15.0)

    Returns:
        List of tuples: (chunk_data, start_time, end_time)

    Example:
        >>> audio_data, sr = load_audio("video.mp4")
        >>> chunks = chunk_audio(audio_data, sr, chunk_duration=60.0, overlap_duration=10.0)
        >>> len(chunks)
        5
    """
    total_duration = len(audio_data) / sample_rate

    # If audio is shorter than chunk duration, return as single chunk
    if total_duration <= chunk_duration:
        return [(audio_data, 0.0, total_duration)]

    chunk_samples = int(chunk_duration * sample_rate)
    overlap_samples = int(overlap_duration * sample_rate)
    stride_samples = chunk_samples - overlap_samples

    chunks = []
    start_sample = 0

    while start_sample < len(audio_data):
        end_sample = min(start_sample + chunk_samples, len(audio_data))
        chunk_data = audio_data[start_sample:end_sample]

        start_time = start_sample / sample_rate
        end_time = end_sample / sample_rate

        chunks.append((chunk_data, start_time, end_time))

        # Move to next chunk
        start_sample += stride_samples

        # Stop if we've passed the end
        if end_sample >= len(audio_data):
            break

    logger.info(f"Audio split into {len(chunks)} chunks ({total_duration:.1f}s total)")
    return chunks


def merge_chunk_transcriptions(
    chunk_results: List[Dict[str, Any]],
    overlap_duration: float = 15.0
) -> Dict[str, Any]:
    """Merge transcriptions from overlapping chunks.

    Args:
        chunk_results: List of transcription results from each chunk
        overlap_duration: Overlap duration used for chunking

    Returns:
        Merged transcription result with adjusted timestamps

    Example:
        >>> chunk_results = [
        ...     {"text": "Hello world", "segments": [...], "chunk_start_time": 0.0},
        ...     {"text": "More text", "segments": [...], "chunk_start_time": 105.0}
        ... ]
        >>> result = merge_chunk_transcriptions(chunk_results, overlap_duration=15.0)
    """
    if not chunk_results:
        return {"text": "", "segments": [], "language": "en", "duration": 0.0}

    if len(chunk_results) == 1:
        return chunk_results[0]

    # Merge strategy: Use full text from each chunk except in overlap regions
    # In overlap regions, prefer the chunk where the segment is earlier
    merged_segments = []
    full_text_parts = []

    for i, chunk_result in enumerate(chunk_results):
        # Skip if no segments
        if not chunk_result.get('segments'):
            continue

        chunk_offset = chunk_result.get('chunk_start_time', 0.0)

        for segment in chunk_result['segments']:
            # Adjust segment timestamps by chunk offset
            adjusted_segment = segment.copy()
            adjusted_segment['start'] += chunk_offset
            adjusted_segment['end'] += chunk_offset

            # Skip segments in overlap region (except for the last chunk)
            if i < len(chunk_results) - 1:  # Not the last chunk
                chunk_duration = chunk_result.get('chunk_end_time', 0) - chunk_offset
                if adjusted_segment['start'] > (chunk_offset + chunk_duration - overlap_duration):
                    continue  # Skip overlap region

            merged_segments.append(adjusted_segment)
            full_text_parts.append(segment.get('text', ''))

    # Sort segments by start time
    merged_segments.sort(key=lambda s: s['start'])

    total_duration = max([s['end'] for s in merged_segments]) if merged_segments else 0.0

    return {
        "text": " ".join(full_text_parts),
        "segments": merged_segments,
        "language": chunk_results[0].get('language', 'en'),
        "duration": total_duration
    }


def transcribe_video_file(
    video_path: str,
    language: str = "en",
    cleanup: bool = True
) -> Dict[str, Any]:
    """Transcribe a video file with automatic chunking for long videos.

    Args:
        video_path: Path to video file
        language: Language code (default: "en")
        cleanup: Clean up temporary audio file after transcription (default: True)

    Returns:
        Dict with:
            - text: Full transcription text
            - segments: List of segments with timestamps
            - language: Language used
            - duration: Total duration in seconds
            - chunks_processed: Number of chunks processed

    Raises:
        VideoProcessingError: If video file is invalid or processing fails

    Example:
        >>> result = transcribe_video_file("video.mp4", language="en")
        >>> print(result['text'])
        'Full transcription text...'
        >>> print(f"Duration: {result['duration']:.1f}s")
        Duration: 300.5s
    """
    # Validate video file
    if not validate_video_path(video_path):
        raise VideoProcessingError(f"Invalid video file: {video_path}")

    # Load configuration
    config = load_config()
    chunk_duration = config.parakeet.chunk_duration
    overlap_duration = config.parakeet.overlap_duration

    # Extract audio
    logger.info(f"Extracting audio from video: {video_path}")
    audio_path = extract_audio(video_path)

    try:
        # Load Parakeet model
        model = ParakeetModel()
        model.ensure_loaded()

        # Transcribe audio (Parakeet handles chunking internally)
        logger.info(f"Transcribing audio with Parakeet (chunking: {chunk_duration}s, overlap: {overlap_duration}s)")
        result = model.transcribe(
            audio_path,
            language=language,
            chunk_duration=chunk_duration,
            overlap_duration=overlap_duration
        )

        logger.info(f"Transcription complete: {result['duration']:.1f}s, {len(result['segments'])} segments")

        return result

    finally:
        # Clean up temporary audio file
        if cleanup:
            cleanup_audio_file(audio_path)
