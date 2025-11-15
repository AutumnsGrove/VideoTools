"""
Frame extraction from video files using FFmpeg.

This module provides utilities for extracting frames from video files at regular
intervals or specific timestamps. Frames are saved as JPEG images with metadata.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
import ffmpeg
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FrameMetadata:
    """Metadata for an extracted frame."""

    frame_path: Path
    timestamp: float  # Timestamp in seconds
    frame_number: int  # Sequential frame number (0-indexed)


class FrameExtractor:
    """Extract frames from video files using FFmpeg."""

    def __init__(self, quality: int = 90):
        """
        Initialize frame extractor.

        Args:
            quality: JPEG quality (1-100, higher is better). Default: 90
        """
        self.quality = quality
        logger.info(f"Initialized FrameExtractor with quality={quality}")

    def extract_frames_at_interval(
        self,
        video_path: Path,
        output_dir: Optional[Path] = None,
        sample_interval: float = 1.0,
        max_frames: Optional[int] = None,
    ) -> List[FrameMetadata]:
        """
        Extract frames from video at regular time intervals.

        Args:
            video_path: Path to input video file
            output_dir: Directory to save extracted frames (default: temp directory)
            sample_interval: Time between frames in seconds (default: 1.0)
            max_frames: Maximum number of frames to extract (default: None = all)

        Returns:
            List of FrameMetadata objects with frame paths and metadata

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If FFmpeg extraction fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="video_frames_"))
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Extracting frames from {video_path} "
            f"(interval={sample_interval}s, max_frames={max_frames})"
        )

        # Get video duration
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe["format"]["duration"])
            logger.debug(f"Video duration: {duration:.2f}s")
        except Exception as e:
            raise RuntimeError(f"Failed to probe video: {e}")

        # Calculate frame timestamps
        timestamps = []
        current_time = 0.0
        while current_time < duration:
            timestamps.append(current_time)
            if max_frames and len(timestamps) >= max_frames:
                break
            current_time += sample_interval

        logger.info(f"Extracting {len(timestamps)} frames")

        # Extract frames
        frames = []
        for idx, timestamp in enumerate(timestamps):
            try:
                frame_path = output_dir / f"frame_{idx:06d}.jpg"

                # Use FFmpeg to extract single frame at timestamp
                (
                    ffmpeg.input(str(video_path), ss=timestamp)
                    .output(
                        str(frame_path),
                        vframes=1,
                        **{"q:v": self.quality},
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )

                frames.append(
                    FrameMetadata(
                        frame_path=frame_path,
                        timestamp=timestamp,
                        frame_number=idx,
                    )
                )

                if (idx + 1) % 10 == 0:
                    logger.debug(f"Extracted {idx + 1}/{len(timestamps)} frames")

            except ffmpeg.Error as e:
                logger.warning(f"Failed to extract frame at {timestamp:.2f}s: {e.stderr}")
                continue

        logger.info(f"Successfully extracted {len(frames)} frames to {output_dir}")
        return frames

    def extract_specific_frames(
        self,
        video_path: Path,
        timestamps: List[float],
        output_dir: Optional[Path] = None,
    ) -> List[FrameMetadata]:
        """
        Extract frames at specific timestamps.

        Args:
            video_path: Path to input video file
            timestamps: List of timestamps (in seconds) to extract
            output_dir: Directory to save extracted frames (default: temp directory)

        Returns:
            List of FrameMetadata objects with frame paths and metadata

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If FFmpeg extraction fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="video_frames_"))
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {len(timestamps)} specific frames from {video_path}")

        # Extract frames
        frames = []
        for idx, timestamp in enumerate(timestamps):
            try:
                frame_path = output_dir / f"frame_{idx:06d}_t{timestamp:.2f}.jpg"

                # Use FFmpeg to extract single frame at timestamp
                (
                    ffmpeg.input(str(video_path), ss=timestamp)
                    .output(
                        str(frame_path),
                        vframes=1,
                        **{"q:v": self.quality},
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )

                frames.append(
                    FrameMetadata(
                        frame_path=frame_path,
                        timestamp=timestamp,
                        frame_number=idx,
                    )
                )

            except ffmpeg.Error as e:
                logger.warning(f"Failed to extract frame at {timestamp:.2f}s: {e.stderr}")
                continue

        logger.info(f"Successfully extracted {len(frames)} frames to {output_dir}")
        return frames

    def get_frame_count(self, video_path: Path) -> int:
        """
        Get total number of frames in video.

        Args:
            video_path: Path to video file

        Returns:
            Total frame count

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If FFmpeg probe fails
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )

            if not video_stream:
                raise RuntimeError("No video stream found")

            # Try to get frame count from stream
            if "nb_frames" in video_stream:
                return int(video_stream["nb_frames"])

            # Fallback: calculate from duration and frame rate
            duration = float(probe["format"]["duration"])
            fps_str = video_stream.get("r_frame_rate", "30/1")
            fps_num, fps_den = map(int, fps_str.split("/"))
            fps = fps_num / fps_den

            estimated_frames = int(duration * fps)
            logger.debug(
                f"Estimated {estimated_frames} frames "
                f"(duration={duration:.2f}s, fps={fps:.2f})"
            )
            return estimated_frames

        except Exception as e:
            raise RuntimeError(f"Failed to get frame count: {e}")
