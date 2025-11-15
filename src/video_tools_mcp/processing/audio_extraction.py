"""
Audio extraction functionality for video processing.

This module provides utilities for:
- Extracting audio from video files to WAV format
- Converting audio to specific sample rates (16kHz for Parakeet)
- Getting audio file information
- Cleaning up temporary audio files
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import ffmpeg

from video_tools_mcp.config import load_config
from video_tools_mcp.utils.file_utils import (
    AudioExtractionError,
    VideoProcessingError,
    generate_temp_filename,
    validate_video_path,
)

# Set up module logger
logger = logging.getLogger(__name__)


def extract_audio(
    video_path: str,
    output_path: Optional[str] = None,
    sample_rate: int = 16000
) -> str:
    """
    Extract audio from video file to WAV format.

    Extracts audio stream from video, converts to mono channel WAV format
    with specified sample rate. Default sample rate of 16kHz is optimized
    for Parakeet transcription model.

    Args:
        video_path: Path to input video file
        output_path: Path for output WAV file. If None, auto-generates
                     temp filename in configured temp directory
        sample_rate: Target sample rate in Hz (default: 16000)

    Returns:
        Path to extracted audio WAV file

    Raises:
        AudioExtractionError: If video validation fails or extraction fails
        VideoProcessingError: If video path is invalid

    Example:
        >>> # Extract with auto-generated filename
        >>> audio_path = extract_audio("/path/to/video.mp4")
        >>> print(f"Audio saved to: {audio_path}")
        Audio saved to: /tmp/video-tools/audio_a1b2c3d4.wav

        >>> # Extract with custom output path
        >>> audio_path = extract_audio(
        ...     "/path/to/video.mp4",
        ...     output_path="/custom/output.wav",
        ...     sample_rate=44100
        ... )
    """
    try:
        # Validate input video file
        if not validate_video_path(video_path):
            raise VideoProcessingError(f"Invalid video file: {video_path}")

        logger.info(f"Starting audio extraction from: {video_path}")

        # Generate output path if not provided
        if output_path is None:
            config = load_config()
            temp_dir = config.processing.temp_dir

            # Ensure temp directory exists
            temp_path = Path(temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)

            output_path = generate_temp_filename("audio", ".wav", temp_dir)
            logger.info(f"Generated temp audio filename: {output_path}")
        else:
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

        # Extract audio using ffmpeg-python
        # - Extract audio stream
        # - Convert to PCM 16-bit WAV format (pcm_s16le codec)
        # - Set sample rate (16kHz default for Parakeet)
        # - Convert to mono (1 channel)
        # - Overwrite output file if it exists
        logger.info(
            f"Extracting audio: sample_rate={sample_rate}Hz, channels=1 (mono)"
        )

        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec='pcm_s16le',  # PCM 16-bit little-endian (WAV format)
            ar=sample_rate,       # Audio sample rate
            ac=1,                 # Audio channels (1 = mono)
            format='wav'          # Output format
        )
        stream = ffmpeg.overwrite_output(stream)

        # Run ffmpeg command
        logger.debug(f"Running ffmpeg command: {' '.join(ffmpeg.compile(stream))}")
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, quiet=True)

        # Verify output file was created
        output_file = Path(output_path)
        if not output_file.exists():
            raise AudioExtractionError(
                f"Audio extraction completed but output file not found: {output_path}"
            )

        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(
            f"Audio extraction successful: {output_path} ({file_size_mb:.2f} MB)"
        )

        return output_path

    except ffmpeg.Error as e:
        # Extract error message from ffmpeg stderr
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg audio extraction error: {error_msg}")
        raise AudioExtractionError(
            f"Failed to extract audio from {video_path}: {error_msg}"
        ) from e

    except (VideoProcessingError, AudioExtractionError):
        # Re-raise our custom exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during audio extraction: {e}")
        raise AudioExtractionError(
            f"Audio extraction failed with unexpected error: {e}"
        ) from e


def get_audio_info(audio_path: str) -> Dict[str, any]:
    """
    Get information about an audio file using ffmpeg probe.

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary containing:
            - duration: Duration in seconds (float)
            - sample_rate: Sample rate in Hz (int)
            - channels: Number of audio channels (int)
            - codec: Audio codec name (str)

    Raises:
        AudioExtractionError: If probe fails or audio file is invalid

    Example:
        >>> info = get_audio_info("/path/to/audio.wav")
        >>> print(f"Duration: {info['duration']:.2f}s")
        >>> print(f"Sample rate: {info['sample_rate']}Hz")
        >>> print(f"Channels: {info['channels']}")
        >>> print(f"Codec: {info['codec']}")
        Duration: 125.50s
        Sample rate: 16000Hz
        Channels: 1
        Codec: pcm_s16le
    """
    try:
        audio_file = Path(audio_path)

        # Check if file exists
        if not audio_file.exists():
            raise AudioExtractionError(f"Audio file not found: {audio_path}")

        if not audio_file.is_file():
            raise AudioExtractionError(f"Path is not a file: {audio_path}")

        logger.info(f"Probing audio file: {audio_path}")

        # Probe audio file
        probe = ffmpeg.probe(audio_path)

        # Extract audio stream information
        audio_streams = [
            s for s in probe.get('streams', [])
            if s.get('codec_type') == 'audio'
        ]

        if not audio_streams:
            raise AudioExtractionError(
                f"No audio stream found in file: {audio_path}"
            )

        # Get first audio stream
        audio_stream = audio_streams[0]

        # Extract information with fallbacks
        duration = None
        if 'duration' in audio_stream:
            duration = float(audio_stream['duration'])
        elif 'format' in probe and 'duration' in probe['format']:
            duration = float(probe['format']['duration'])

        sample_rate = int(audio_stream.get('sample_rate', 0))
        channels = int(audio_stream.get('channels', 0))
        codec = audio_stream.get('codec_name', 'unknown')

        # Build info dictionary
        info = {
            'duration': duration,
            'sample_rate': sample_rate,
            'channels': channels,
            'codec': codec
        }

        logger.info(
            f"Audio info: duration={duration}s, "
            f"sample_rate={sample_rate}Hz, "
            f"channels={channels}, "
            f"codec={codec}"
        )

        return info

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg probe error for {audio_path}: {error_msg}")
        raise AudioExtractionError(
            f"Failed to probe audio file: {error_msg}"
        ) from e

    except AudioExtractionError:
        # Re-raise our custom exception
        raise

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing audio metadata for {audio_path}: {e}")
        raise AudioExtractionError(
            f"Invalid audio metadata: {e}"
        ) from e

    except Exception as e:
        logger.error(f"Unexpected error getting audio info for {audio_path}: {e}")
        raise AudioExtractionError(
            f"Failed to get audio information: {e}"
        ) from e


def cleanup_audio_file(audio_path: str) -> bool:
    """
    Safely delete an audio file.

    Args:
        audio_path: Path to audio file to delete

    Returns:
        True if file was successfully deleted, False if file doesn't exist
        or deletion failed

    Example:
        >>> success = cleanup_audio_file("/tmp/audio_temp.wav")
        >>> if success:
        ...     print("Audio file cleaned up successfully")
        Audio file cleaned up successfully
    """
    try:
        audio_file = Path(audio_path)

        # Check if file exists
        if not audio_file.exists():
            logger.info(f"Audio file doesn't exist, nothing to cleanup: {audio_path}")
            return False

        # Check if it's a file (not directory)
        if not audio_file.is_file():
            logger.warning(f"Path is not a file, skipping cleanup: {audio_path}")
            return False

        # Delete the file
        audio_file.unlink()
        logger.info(f"Successfully deleted audio file: {audio_path}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied deleting audio file {audio_path}: {e}")
        return False

    except OSError as e:
        logger.error(f"OS error deleting audio file {audio_path}: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error deleting audio file {audio_path}: {e}")
        return False
