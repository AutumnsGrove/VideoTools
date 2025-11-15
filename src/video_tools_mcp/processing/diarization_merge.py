"""
Diarization merge utilities for combining transcription and speaker diarization results.

This module provides functions to merge speaker diarization data with transcription
segments, using temporal overlap to assign speakers to transcribed text.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def find_speaker_for_segment(
    segment_start: float,
    segment_end: float,
    diarization_segments: List[Dict[str, Any]]
) -> str:
    """
    Find the speaker ID with maximum temporal overlap for a transcription segment.

    Args:
        segment_start: Start time of transcription segment in seconds
        segment_end: End time of transcription segment in seconds
        diarization_segments: List of diarization segments with 'start', 'end', 'speaker'

    Returns:
        Speaker ID string (e.g., "SPEAKER_00") with maximum overlap,
        or "SPEAKER_00" if no overlap found
    """
    max_overlap = 0.0
    best_speaker = "SPEAKER_00"

    for diar_seg in diarization_segments:
        diar_start = diar_seg["start"]
        diar_end = diar_seg["end"]

        # Calculate temporal overlap
        overlap = max(0, min(segment_end, diar_end) - max(segment_start, diar_start))

        if overlap > max_overlap:
            max_overlap = overlap
            best_speaker = diar_seg["speaker"]

    if max_overlap > 0:
        logger.debug(
            f"Segment [{segment_start:.2f}-{segment_end:.2f}] matched to {best_speaker} "
            f"(overlap: {max_overlap:.2f}s)"
        )
    else:
        logger.debug(
            f"Segment [{segment_start:.2f}-{segment_end:.2f}] has no overlap, "
            f"defaulting to {best_speaker}"
        )

    return best_speaker


def merge_transcription_with_diarization(
    transcription_result: Dict[str, Any],
    diarization_result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Merge transcription segments with speaker diarization data.

    Args:
        transcription_result: Dict with 'segments' containing transcription data
                             Each segment has 'start', 'end', 'text'
        diarization_result: Dict with 'segments' containing diarization data
                           Each segment has 'start', 'end', 'speaker'

    Returns:
        List of merged segments with format:
        [{"start": float, "end": float, "text": str, "speaker": str}, ...]
    """
    transcription_segments = transcription_result.get("segments", [])
    diarization_segments = diarization_result.get("segments", [])

    if not transcription_segments:
        logger.warning("No transcription segments found to merge")
        return []

    if not diarization_segments:
        logger.warning("No diarization segments found, all speakers will default to SPEAKER_00")

    merged_segments = []

    for trans_seg in transcription_segments:
        segment_start = trans_seg["start"]
        segment_end = trans_seg["end"]
        text = trans_seg["text"]

        # Find matching speaker using temporal overlap
        speaker = find_speaker_for_segment(
            segment_start,
            segment_end,
            diarization_segments
        )

        merged_segments.append({
            "start": segment_start,
            "end": segment_end,
            "text": text,
            "speaker": speaker
        })

    logger.info(f"Merged {len(merged_segments)} transcription segments with diarization data")
    return merged_segments


def format_speaker_transcript(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add speaker prefixes to transcription text.

    Args:
        segments: List of segments with 'speaker', 'text', 'start', 'end' fields

    Returns:
        New list of segments with speaker-prefixed text:
        Text format: "SPEAKER_00: Hello world"
        All other fields (start, end, speaker) remain unchanged
    """
    formatted_segments = []

    for segment in segments:
        speaker = segment.get("speaker", "SPEAKER_00")
        text = segment.get("text", "")

        # Create new segment with speaker-prefixed text
        formatted_segment = {
            "start": segment["start"],
            "end": segment["end"],
            "text": f"{speaker}: {text}",
            "speaker": speaker
        }

        formatted_segments.append(formatted_segment)

    logger.debug(f"Formatted {len(formatted_segments)} segments with speaker prefixes")
    return formatted_segments
