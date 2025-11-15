"""
SRT subtitle file generation and parsing utilities.

This module provides utilities for:
- Converting transcription segments to SRT format
- Writing SRT files with proper formatting
- Parsing existing SRT files
- Timestamp conversion (seconds ↔ HH:MM:SS,mmm)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import timedelta

# Set up module logger
logger = logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string (e.g., "00:01:23,456")

    Example:
        >>> format_timestamp(83.456)
        '00:01:23,456'
    """
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    milliseconds = int((seconds - total_seconds) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def parse_timestamp(timestamp_str: str) -> float:
    """Parse SRT timestamp to seconds.

    Args:
        timestamp_str: Timestamp in format "HH:MM:SS,mmm"

    Returns:
        Time in seconds

    Example:
        >>> parse_timestamp("00:01:23,456")
        83.456
    """
    # Format: HH:MM:SS,mmm
    time_part, ms_part = timestamp_str.split(',')
    hours, minutes, seconds = map(int, time_part.split(':'))
    milliseconds = int(ms_part)

    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds


def generate_srt(segments: List[Dict[str, Any]]) -> str:
    """Generate SRT subtitle content from transcription segments.

    Args:
        segments: List of segments with 'start', 'end', and 'text' fields

    Returns:
        SRT formatted string

    Example:
        >>> segments = [
        ...     {"start": 0.0, "end": 2.5, "text": "Hello world"},
        ...     {"start": 2.7, "end": 5.0, "text": "This is a test"}
        ... ]
        >>> srt = generate_srt(segments)
    """
    if not segments:
        return ""

    srt_lines = []

    for i, segment in enumerate(segments, start=1):
        # Subtitle number
        srt_lines.append(str(i))

        # Timestamp line
        start_time = format_timestamp(segment.get('start', 0.0))
        end_time = format_timestamp(segment.get('end', 0.0))
        srt_lines.append(f"{start_time} --> {end_time}")

        # Text content
        text = segment.get('text', '').strip()
        if text:
            srt_lines.append(text)
        else:
            srt_lines.append("")  # Empty subtitle

        # Blank line between subtitles
        srt_lines.append("")

    return "\n".join(srt_lines)


def write_srt_file(
    segments: List[Dict[str, Any]],
    output_path: str,
    encoding: str = "utf-8"
) -> str:
    """Write transcription segments to SRT file.

    Args:
        segments: List of segments with timestamps and text
        output_path: Path to output SRT file
        encoding: File encoding (default: "utf-8")

    Returns:
        Path to created SRT file

    Raises:
        IOError: If file cannot be written
    """
    logger.info(f"Writing SRT file: {output_path}")

    srt_content = generate_srt(segments)

    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding=encoding) as f:
            f.write(srt_content)

        logger.info(f"✓ SRT file written: {output_path} ({len(segments)} segments)")
        return str(output_file)

    except Exception as e:
        logger.error(f"Failed to write SRT file: {e}")
        raise IOError(f"Failed to write SRT file: {e}")


def parse_srt_file(srt_path: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Parse an SRT file into segments.

    Args:
        srt_path: Path to SRT file
        encoding: File encoding (default: "utf-8")

    Returns:
        List of segments with 'start', 'end', and 'text' fields

    Raises:
        IOError: If file cannot be read
        ValueError: If SRT format is invalid
    """
    logger.info(f"Parsing SRT file: {srt_path}")

    try:
        with open(srt_path, 'r', encoding=encoding) as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read SRT file: {e}")
        raise IOError(f"Failed to read SRT file: {e}")

    # Split into subtitle blocks (separated by blank lines)
    blocks = content.strip().split('\n\n')
    segments = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue  # Skip invalid blocks

        # Parse timestamp line (format: "00:01:23,456 --> 00:01:25,789")
        try:
            timestamp_line = lines[1]
            start_str, end_str = timestamp_line.split(' --> ')

            start_time = parse_timestamp(start_str)
            end_time = parse_timestamp(end_str)

            # Text is everything after the timestamp line
            text = '\n'.join(lines[2:])

            segments.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })
        except Exception as e:
            logger.warning(f"Skipping malformed subtitle block: {e}")
            continue

    logger.info(f"Parsed {len(segments)} segments from SRT file")
    return segments
