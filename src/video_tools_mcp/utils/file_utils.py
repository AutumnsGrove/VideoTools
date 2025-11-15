"""
File utility functions for video processing operations.

This module provides utilities for:
- Video file validation
- Directory management
- Video duration extraction
- Disk space checks
- Temporary file management
"""

import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

import ffmpeg

# Set up module logger
logger = logging.getLogger(__name__)


# Custom Exceptions
class VideoProcessingError(Exception):
    """Raised when video processing operations fail."""
    pass


class AudioExtractionError(Exception):
    """Raised when audio extraction operations fail."""
    pass


def validate_video_path(path: str) -> bool:
    """
    Validate that a path points to a readable video file.

    Args:
        path: Path to video file to validate

    Returns:
        True if path is valid video file, False otherwise

    Example:
        >>> validate_video_path("/path/to/video.mp4")
        True
        >>> validate_video_path("/path/to/missing.mp4")
        False
    """
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}

    try:
        file_path = Path(path)

        # Check if file exists
        if not file_path.exists():
            logger.warning(f"File does not exist: {path}")
            return False

        # Check if it's a regular file (not directory)
        if not file_path.is_file():
            logger.warning(f"Path is not a regular file: {path}")
            return False

        # Check if file is readable
        if not file_path.stat().st_mode & 0o400:
            logger.warning(f"File is not readable: {path}")
            return False

        # Check for valid video extension
        if file_path.suffix.lower() not in video_extensions:
            logger.warning(f"File does not have a valid video extension: {path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating video path {path}: {e}")
        return False


def ensure_output_directory(path: str) -> None:
    """
    Create directory if it doesn't exist, including parent directories.

    Args:
        path: Directory path to create

    Raises:
        ValueError: If path exists but is not a directory
        OSError: If directory cannot be created (permissions issue)

    Example:
        >>> ensure_output_directory("/path/to/output/folder")
        >>> # Directory created if it didn't exist
    """
    dir_path = Path(path)

    try:
        # Check if path exists but is not a directory
        if dir_path.exists() and not dir_path.is_dir():
            raise ValueError(f"Path exists but is not a directory: {path}")

        # Create directory with parents if needed
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {path}")

    except PermissionError as e:
        logger.error(f"Permission denied creating directory {path}: {e}")
        raise OSError(f"Cannot create directory due to permissions: {path}") from e
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise OSError(f"Failed to create directory: {path}") from e


def get_video_duration(video_path: str) -> float:
    """
    Extract video duration in seconds using ffmpeg probe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds as float

    Raises:
        VideoProcessingError: If probe fails or duration cannot be determined

    Example:
        >>> duration = get_video_duration("/path/to/video.mp4")
        >>> print(f"Video is {duration:.2f} seconds long")
        Video is 125.50 seconds long
    """
    try:
        probe = ffmpeg.probe(video_path)

        # Try to get duration from format section first
        if 'format' in probe and 'duration' in probe['format']:
            duration = float(probe['format']['duration'])
            logger.info(f"Video duration: {duration:.2f}s for {video_path}")
            return duration

        # Fallback: try to get from first video stream
        video_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
        if video_streams and 'duration' in video_streams[0]:
            duration = float(video_streams[0]['duration'])
            logger.info(f"Video duration from stream: {duration:.2f}s for {video_path}")
            return duration

        # No duration found
        logger.error(f"No duration information found in video: {video_path}")
        raise VideoProcessingError(f"Could not determine video duration: {video_path}")

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg probe error for {video_path}: {error_msg}")
        raise VideoProcessingError(f"Failed to probe video: {error_msg}") from e
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing video metadata for {video_path}: {e}")
        raise VideoProcessingError(f"Invalid video metadata: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting video duration for {video_path}: {e}")
        raise VideoProcessingError(f"Failed to get video duration: {e}") from e


def check_disk_space(path: str, required_gb: float) -> bool:
    """
    Check if sufficient disk space is available at given path.

    Args:
        path: Directory path to check (file paths will use parent directory)
        required_gb: Required space in gigabytes

    Returns:
        True if available space >= required_gb, False otherwise

    Example:
        >>> if check_disk_space("/tmp", 5.0):
        ...     print("Sufficient space for 5GB output")
        Sufficient space for 5GB output
    """
    try:
        check_path = Path(path)

        # If path is a file, use its parent directory
        if check_path.is_file():
            check_path = check_path.parent

        # Get disk usage statistics
        usage = shutil.disk_usage(check_path)
        available_gb = usage.free / (1024 ** 3)  # Convert bytes to GB

        has_space = available_gb >= required_gb

        if has_space:
            logger.info(f"Sufficient disk space: {available_gb:.2f}GB available, {required_gb:.2f}GB required")
        else:
            logger.warning(f"Insufficient disk space: {available_gb:.2f}GB available, {required_gb:.2f}GB required")

        return has_space

    except Exception as e:
        logger.error(f"Error checking disk space at {path}: {e}")
        # Return False on error to be safe
        return False


def generate_temp_filename(
    prefix: str,
    suffix: str,
    temp_dir: Optional[str] = None
) -> str:
    """
    Generate unique temporary filename with optional directory path.

    Args:
        prefix: Filename prefix (e.g., "audio", "video")
        suffix: File extension including dot (e.g., ".wav", ".mp4")
        temp_dir: Optional directory path to prepend to filename

    Returns:
        Full path if temp_dir specified, otherwise just filename

    Example:
        >>> filename = generate_temp_filename("audio", ".wav")
        >>> # Returns: audio_a1b2c3d4.wav
        >>>
        >>> full_path = generate_temp_filename("audio", ".wav", "/tmp")
        >>> # Returns: /tmp/audio_a1b2c3d4.wav
    """
    try:
        # Generate unique identifier using uuid4
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]

        # Ensure suffix starts with dot
        if not suffix.startswith('.'):
            suffix = f".{suffix}"

        # Construct filename
        filename = f"{prefix}_{unique_id}{suffix}"

        # Return full path if temp_dir specified
        if temp_dir:
            temp_path = Path(temp_dir)
            full_path = temp_path / filename
            return str(full_path)

        return filename

    except Exception as e:
        logger.error(f"Error generating temp filename: {e}")
        # Fallback to timestamp-based name
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}{suffix}"
        if temp_dir:
            return str(Path(temp_dir) / filename)
        return filename


def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Delete temporary files older than specified age.

    Args:
        directory: Directory containing temporary files
        max_age_hours: Maximum age of files to keep (default: 24 hours)

    Returns:
        Number of files deleted

    Example:
        >>> count = cleanup_temp_files("/tmp/video_processing", max_age_hours=12)
        >>> print(f"Cleaned up {count} old temporary files")
        Cleaned up 5 old temporary files
    """
    deleted_count = 0

    try:
        dir_path = Path(directory)

        # Skip if directory doesn't exist
        if not dir_path.exists():
            logger.info(f"Directory does not exist, skipping cleanup: {directory}")
            return 0

        if not dir_path.is_dir():
            logger.warning(f"Path is not a directory, skipping cleanup: {directory}")
            return 0

        # Calculate cutoff time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cutoff_time = current_time - max_age_seconds

        # Iterate through files in directory
        for file_path in dir_path.iterdir():
            try:
                # Skip directories
                if not file_path.is_file():
                    continue

                # Check file age
                file_mtime = file_path.stat().st_mtime

                if file_mtime < cutoff_time:
                    # Delete old file
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old temporary file: {file_path}")

            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                # Continue with other files even if one fails
                continue

        logger.info(f"Cleanup completed: {deleted_count} files deleted from {directory}")
        return deleted_count

    except Exception as e:
        logger.error(f"Error during temp file cleanup in {directory}: {e}")
        return deleted_count
