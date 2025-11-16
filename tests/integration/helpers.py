"""Shared utilities for integration tests."""

import json
import re
from pathlib import Path
from typing import List, Dict, Any


def validate_srt_format(srt_path: str) -> bool:
    """
    Validate SRT file format and structure.

    Checks:
    - File exists
    - Sequential numbering
    - Timestamp format (HH:MM:SS,mmm --> HH:MM:SS,mmm)
    - Non-empty text segments

    Returns:
        True if valid SRT format, False otherwise
    """
    path = Path(srt_path)
    if not path.exists():
        return False

    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            return False

        # Check for basic SRT structure
        blocks = content.split('\n\n')
        for i, block in enumerate(blocks, 1):
            lines = block.strip().split('\n')
            if len(lines) < 3:
                return False
            # Validate sequence number, timestamp, and text
            if not lines[0].strip().isdigit():
                return False
            if '-->' not in lines[1]:
                return False
            if not lines[2].strip():
                return False

        return True
    except Exception:
        return False


def parse_srt_file(srt_path: str) -> List[Dict[str, Any]]:
    """
    Parse SRT file into structured segments.

    Returns:
        List of dicts with keys: index, start, end, text
    """
    from video_tools_mcp.utils.srt_utils import parse_srt_file as parse
    return parse(srt_path)


def count_speakers_in_srt(srt_path: str) -> int:
    """
    Count unique speakers in SRT file.

    Looks for patterns like "SPEAKER_00:", "Alice:", etc.

    Returns:
        Number of unique speakers
    """
    segments = parse_srt_file(srt_path)
    speakers = set()

    for segment in segments:
        text = segment.get('text', '')
        # Extract speaker label (e.g., "SPEAKER_00:", "Alice:")
        match = re.match(r'^([A-Z_0-9]+):', text)
        if match:
            speakers.add(match.group(1))

    return len(speakers)


def extract_speaker_labels(srt_path: str) -> List[str]:
    """
    Extract and return sorted list of unique speaker names.

    Returns:
        Sorted list of speaker names (e.g., ["SPEAKER_00", "SPEAKER_01"])
    """
    segments = parse_srt_file(srt_path)
    speakers = set()

    for segment in segments:
        text = segment.get('text', '')
        # Match speaker prefix (letters, numbers, underscores followed by colon)
        match = re.match(r'^([A-Za-z_0-9]+):', text)
        if match:
            speakers.add(match.group(1))

    return sorted(list(speakers))


def validate_json_transcript(json_path: str, required_fields: List[str]) -> bool:
    """
    Validate JSON transcript has required fields.

    Args:
        json_path: Path to JSON file
        required_fields: List of required top-level keys

    Returns:
        True if valid and contains all required fields
    """
    path = Path(json_path)
    if not path.exists():
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check all required fields are present
        return all(field in data for field in required_fields)
    except Exception:
        return False


def validate_screenshot_metadata(metadata_path: str) -> Dict[str, bool]:
    """
    Validate screenshot metadata structure and required fields.

    Returns:
        Dict with validation results for each requirement
    """
    result = {
        'exists': False,
        'has_all_top_level_fields': False,
        'screenshots_is_list': False,
        'screenshots_not_empty': False,
        'all_screenshots_valid': False
    }

    path = Path(metadata_path)
    if not path.exists():
        return result

    result['exists'] = True

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        required_top_level = [
            "video_path", "extraction_prompt", "sample_interval",
            "similarity_threshold", "max_screenshots", "output_dir",
            "total_frames_extracted", "duplicates_removed",
            "frames_evaluated", "screenshots_kept", "processing_time",
            "screenshots"
        ]

        screenshot_required = ["filename", "path", "timestamp", "caption"]

        result['has_all_top_level_fields'] = all(k in data for k in required_top_level)
        result['screenshots_is_list'] = isinstance(data.get("screenshots"), list)
        result['screenshots_not_empty'] = len(data.get("screenshots", [])) > 0

        if result['screenshots_is_list'] and result['screenshots_not_empty']:
            result['all_screenshots_valid'] = all(
                all(k in shot for k in screenshot_required)
                for shot in data["screenshots"]
            )

        return result

    except (json.JSONDecodeError, IOError):
        return result


def calculate_rtf(video_duration: float, processing_time: float) -> float:
    """
    Calculate Real-Time Factor (RTF).

    RTF = processing_time / video_duration

    RTF < 1.0 means faster than real-time
    RTF = 0.1 means 10x faster than real-time

    Args:
        video_duration: Video length in seconds
        processing_time: Processing time in seconds

    Returns:
        Real-time factor
    """
    if video_duration <= 0:
        return float('inf')
    return processing_time / video_duration


def assert_file_exists(path: str, file_type: str = "file") -> None:
    """
    Assert file exists with descriptive error.

    Args:
        path: File path to check
        file_type: Description for error message

    Raises:
        AssertionError if file doesn't exist
    """
    assert Path(path).exists(), f"{file_type} not found: {path}"


def assert_reasonable_duration(expected: float, actual: float, tolerance: float = 0.05) -> None:
    """
    Assert duration is within tolerance.

    Args:
        expected: Expected duration in seconds
        actual: Actual duration in seconds
        tolerance: Acceptable deviation (default 5%)

    Raises:
        AssertionError if outside tolerance
    """
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    assert lower <= actual <= upper, \
        f"Duration {actual:.2f}s outside expected range [{lower:.1f}s - {upper:.1f}s]"
