"""
Unit tests for file utility functions (utils/file_utils.py).

Tests cover:
- Video path validation
- Directory creation
- Video duration extraction
- Disk space checking
- Temporary filename generation
- Temporary file cleanup
"""

import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import ffmpeg

from video_tools_mcp.utils.file_utils import (
    validate_video_path,
    ensure_output_directory,
    get_video_duration,
    check_disk_space,
    generate_temp_filename,
    cleanup_temp_files,
    VideoProcessingError,
    AudioExtractionError
)


class TestValidateVideoPath:
    """Test cases for validate_video_path() function."""

    def test_validate_video_path_valid_file_returns_true(self, mock_video_path):
        """Test that a valid video file path returns True."""
        result = validate_video_path(mock_video_path)

        assert result is True

    def test_validate_video_path_missing_file_returns_false(self, temp_dir):
        """Test that a non-existent file path returns False."""
        missing_path = str(temp_dir / "missing_video.mp4")

        result = validate_video_path(missing_path)

        assert result is False

    def test_validate_video_path_directory_returns_false(self, temp_dir):
        """Test that a directory path returns False."""
        result = validate_video_path(str(temp_dir))

        assert result is False

    def test_validate_video_path_invalid_extension_returns_false(self, temp_dir):
        """Test that a non-video file extension returns False."""
        text_file = temp_dir / "document.txt"
        text_file.touch()

        result = validate_video_path(str(text_file))

        assert result is False

    def test_validate_video_path_accepts_all_video_extensions(self, sample_video_files):
        """Test that all supported video extensions are accepted."""
        for ext, file_path in sample_video_files.items():
            result = validate_video_path(file_path)
            assert result is True, f"Extension .{ext} should be valid"

    def test_validate_video_path_case_insensitive_extension(self, temp_dir):
        """Test that video extension check is case-insensitive."""
        video_upper = temp_dir / "video.MP4"
        video_upper.touch()

        result = validate_video_path(str(video_upper))

        assert result is True


class TestEnsureOutputDirectory:
    """Test cases for ensure_output_directory() function."""

    def test_ensure_output_directory_creates_new_directory(self, temp_dir):
        """Test that new directory is created successfully."""
        new_dir = temp_dir / "output" / "nested" / "directory"

        # Directory shouldn't exist yet
        assert not new_dir.exists()

        ensure_output_directory(str(new_dir))

        # Directory should now exist
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_output_directory_existing_directory_succeeds(self, temp_dir):
        """Test that function succeeds if directory already exists."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        # Should not raise error
        ensure_output_directory(str(existing_dir))

        assert existing_dir.exists()

    def test_ensure_output_directory_file_exists_raises_error(self, temp_dir):
        """Test that ValueError or OSError is raised if path is an existing file."""
        file_path = temp_dir / "file.txt"
        file_path.touch()

        # The function raises OSError which wraps the original ValueError
        with pytest.raises((ValueError, OSError)) as exc_info:
            ensure_output_directory(str(file_path))

        error_msg = str(exc_info.value)
        assert "not a directory" in error_msg or "Failed to create directory" in error_msg


class TestGetVideoDuration:
    """Test cases for get_video_duration() function."""

    def test_get_video_duration_from_format(self):
        """Test extracting duration from format section of probe."""
        mock_probe_result = {
            'format': {
                'duration': '125.50'
            },
            'streams': []
        }

        with patch('ffmpeg.probe', return_value=mock_probe_result):
            duration = get_video_duration("/path/to/video.mp4")

        assert duration == 125.50

    def test_get_video_duration_from_stream(self):
        """Test extracting duration from video stream when format doesn't have it."""
        mock_probe_result = {
            'format': {},
            'streams': [
                {
                    'codec_type': 'video',
                    'duration': '90.25'
                }
            ]
        }

        with patch('ffmpeg.probe', return_value=mock_probe_result):
            duration = get_video_duration("/path/to/video.mp4")

        assert duration == 90.25

    def test_get_video_duration_no_duration_raises_error(self):
        """Test that VideoProcessingError is raised when no duration found."""
        mock_probe_result = {
            'format': {},
            'streams': []
        }

        with patch('ffmpeg.probe', return_value=mock_probe_result):
            with pytest.raises(VideoProcessingError) as exc_info:
                get_video_duration("/path/to/video.mp4")

        assert "Could not determine video duration" in str(exc_info.value)

    def test_get_video_duration_ffmpeg_error_raises_error(self):
        """Test that FFmpeg errors are properly handled."""
        # Mock ffmpeg.Error with stderr
        mock_error = ffmpeg.Error('ffmpeg', 'stdout', b'Error reading file')
        mock_error.stderr = b'Error reading file'

        with patch('ffmpeg.probe', side_effect=mock_error):
            with pytest.raises(VideoProcessingError) as exc_info:
                get_video_duration("/path/to/video.mp4")

        assert "Failed to probe video" in str(exc_info.value)


class TestCheckDiskSpace:
    """Test cases for check_disk_space() function."""

    def test_check_disk_space_sufficient_space_returns_true(self, temp_dir):
        """Test that True is returned when sufficient space is available."""
        # Request very small amount (0.001 GB = 1 MB)
        result = check_disk_space(str(temp_dir), required_gb=0.001)

        assert result is True

    def test_check_disk_space_insufficient_space_returns_false(self, temp_dir):
        """Test that False is returned when insufficient space."""
        # Mock disk_usage to return low free space
        mock_usage = MagicMock()
        mock_usage.free = 1024 * 1024 * 100  # 100 MB in bytes

        with patch('shutil.disk_usage', return_value=mock_usage):
            # Request 1 GB, but only 100 MB available
            result = check_disk_space(str(temp_dir), required_gb=1.0)

        assert result is False

    def test_check_disk_space_file_path_uses_parent(self, temp_dir):
        """Test that file paths use parent directory for check."""
        test_file = temp_dir / "video.mp4"
        test_file.touch()

        # Should check parent directory, not fail
        result = check_disk_space(str(test_file), required_gb=0.001)

        assert result is True

    def test_check_disk_space_error_returns_false(self):
        """Test that errors during check return False for safety."""
        with patch('shutil.disk_usage', side_effect=OSError("Disk error")):
            result = check_disk_space("/invalid/path", required_gb=1.0)

        assert result is False


class TestGenerateTempFilename:
    """Test cases for generate_temp_filename() function."""

    def test_generate_temp_filename_basic(self):
        """Test generating temp filename without directory."""
        filename = generate_temp_filename("audio", ".wav")

        # Check format: prefix_uniqueid.suffix
        assert filename.startswith("audio_")
        assert filename.endswith(".wav")
        # Should have 8-character unique ID
        assert len(filename) == len("audio_") + 8 + len(".wav")

    def test_generate_temp_filename_with_directory(self, temp_dir):
        """Test generating temp filename with directory path."""
        full_path = generate_temp_filename("video", ".mp4", str(temp_dir))

        # Check it's a full path
        path = Path(full_path)
        assert path.parent == temp_dir
        assert path.name.startswith("video_")
        assert path.name.endswith(".mp4")

    def test_generate_temp_filename_adds_dot_to_suffix(self):
        """Test that suffix without dot gets dot prepended."""
        filename = generate_temp_filename("test", "txt")

        assert filename.endswith(".txt")

    def test_generate_temp_filename_unique_ids(self):
        """Test that multiple calls generate unique filenames."""
        filenames = set()

        for _ in range(10):
            filename = generate_temp_filename("test", ".tmp")
            filenames.add(filename)

        # All filenames should be unique
        assert len(filenames) == 10

    def test_generate_temp_filename_exception_fallback(self):
        """Test fallback to timestamp-based name on error."""
        # Mock uuid4 to raise exception
        with patch('uuid.uuid4', side_effect=Exception("UUID error")):
            filename = generate_temp_filename("test", ".tmp")

            # Should still return a valid filename using timestamp
            assert filename.startswith("test_")
            assert filename.endswith(".tmp")


class TestCleanupTempFiles:
    """Test cases for cleanup_temp_files() function."""

    def test_cleanup_temp_files_removes_old_files(self, temp_dir):
        """Test that old files are deleted."""
        # Create test files with old timestamps
        old_file1 = temp_dir / "old_file1.tmp"
        old_file2 = temp_dir / "old_file2.tmp"
        old_file1.touch()
        old_file2.touch()

        # Set modification time to 48 hours ago
        old_time = time.time() - (48 * 3600)
        os.utime(old_file1, (old_time, old_time))
        os.utime(old_file2, (old_time, old_time))

        # Run cleanup for files older than 24 hours
        count = cleanup_temp_files(str(temp_dir), max_age_hours=24)

        # Both old files should be deleted
        assert count == 2
        assert not old_file1.exists()
        assert not old_file2.exists()

    def test_cleanup_temp_files_keeps_recent_files(self, temp_dir):
        """Test that recent files are kept."""
        # Create recent file
        recent_file = temp_dir / "recent_file.tmp"
        recent_file.touch()

        # Run cleanup for files older than 24 hours
        count = cleanup_temp_files(str(temp_dir), max_age_hours=24)

        # Recent file should still exist
        assert count == 0
        assert recent_file.exists()

    def test_cleanup_temp_files_mixed_ages(self, temp_dir):
        """Test cleanup with mix of old and recent files."""
        # Create old file
        old_file = temp_dir / "old_file.tmp"
        old_file.touch()
        old_time = time.time() - (48 * 3600)
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        recent_file = temp_dir / "recent_file.tmp"
        recent_file.touch()

        # Run cleanup
        count = cleanup_temp_files(str(temp_dir), max_age_hours=24)

        # Only old file should be deleted
        assert count == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_temp_files_nonexistent_directory_returns_zero(self, temp_dir):
        """Test that cleanup returns 0 for non-existent directory."""
        missing_dir = temp_dir / "missing"

        count = cleanup_temp_files(str(missing_dir), max_age_hours=24)

        assert count == 0

    def test_cleanup_temp_files_ignores_subdirectories(self, temp_dir):
        """Test that subdirectories are not deleted."""
        # Create old subdirectory
        old_subdir = temp_dir / "old_subdir"
        old_subdir.mkdir()
        old_time = time.time() - (48 * 3600)
        os.utime(old_subdir, (old_time, old_time))

        # Run cleanup
        count = cleanup_temp_files(str(temp_dir), max_age_hours=24)

        # Directory should still exist (only files are deleted)
        assert count == 0
        assert old_subdir.exists()

    def test_cleanup_temp_files_continues_on_individual_error(self, temp_dir):
        """Test that cleanup continues even if one file deletion fails."""
        # Create test files
        file1 = temp_dir / "file1.tmp"
        file2 = temp_dir / "file2.tmp"
        file1.touch()
        file2.touch()

        # Make both files old
        old_time = time.time() - (48 * 3600)
        os.utime(file1, (old_time, old_time))
        os.utime(file2, (old_time, old_time))

        # Mock unlink to fail for first file but succeed for second
        original_unlink = Path.unlink
        call_count = [0]

        def mock_unlink(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Mock permission denied")
            return original_unlink(self, *args, **kwargs)

        with patch.object(Path, 'unlink', mock_unlink):
            count = cleanup_temp_files(str(temp_dir), max_age_hours=24)

        # Should have tried to delete both but only succeeded with one
        assert count == 1


class TestExceptions:
    """Test custom exception classes."""

    def test_video_processing_error_can_be_raised(self):
        """Test that VideoProcessingError can be raised and caught."""
        with pytest.raises(VideoProcessingError) as exc_info:
            raise VideoProcessingError("Test error message")

        assert "Test error message" in str(exc_info.value)

    def test_audio_extraction_error_can_be_raised(self):
        """Test that AudioExtractionError can be raised and caught."""
        with pytest.raises(AudioExtractionError) as exc_info:
            raise AudioExtractionError("Test audio error")

        assert "Test audio error" in str(exc_info.value)
