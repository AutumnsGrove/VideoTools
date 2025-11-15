"""
Unit tests for audio extraction module (processing/audio_extraction.py).

Tests cover:
- Audio extraction from video files
- Audio file information retrieval
- Audio file cleanup
- Error handling for various failure scenarios

Note: All ffmpeg operations are mocked to avoid requiring real video files.
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest
import ffmpeg

from video_tools_mcp.processing.audio_extraction import (
    extract_audio,
    get_audio_info,
    cleanup_audio_file
)
from video_tools_mcp.utils.file_utils import (
    AudioExtractionError,
    VideoProcessingError
)


class TestExtractAudio:
    """Test cases for extract_audio() function."""

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg')
    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    @patch('video_tools_mcp.processing.audio_extraction.load_config')
    def test_extract_audio_valid_video_creates_wav_file(
        self, mock_load_config, mock_validate, mock_ffmpeg, temp_dir
    ):
        """Test that audio extraction succeeds with valid video file."""
        # Setup mocks
        mock_validate.return_value = True

        # Mock config
        mock_config = MagicMock()
        mock_config.processing.temp_dir = str(temp_dir)
        mock_load_config.return_value = mock_config

        # Mock ffmpeg chain
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.overwrite_output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Create output file to simulate successful extraction
        with patch('video_tools_mcp.processing.audio_extraction.generate_temp_filename') as mock_gen:
            output_path = str(temp_dir / "audio_test.wav")
            mock_gen.return_value = output_path

            # Create the file that ffmpeg would create
            Path(output_path).touch()

            result = extract_audio("/path/to/video.mp4")

        # Verify result
        assert result == output_path
        assert Path(output_path).exists()

        # Verify ffmpeg was called correctly
        mock_ffmpeg.input.assert_called_once_with("/path/to/video.mp4")
        mock_ffmpeg.run.assert_called_once()

    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    def test_extract_audio_invalid_video_raises_error(self, mock_validate):
        """Test that invalid video path raises VideoProcessingError."""
        mock_validate.return_value = False

        with pytest.raises(VideoProcessingError) as exc_info:
            extract_audio("/path/to/invalid.mp4")

        assert "Invalid video file" in str(exc_info.value)

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg')
    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    def test_extract_audio_custom_output_path(
        self, mock_validate, mock_ffmpeg, temp_dir
    ):
        """Test that custom output path is respected."""
        mock_validate.return_value = True

        # Mock ffmpeg chain
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.overwrite_output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Custom output path
        custom_output = str(temp_dir / "custom_audio.wav")

        # Create the output file
        Path(custom_output).touch()

        result = extract_audio(
            "/path/to/video.mp4",
            output_path=custom_output
        )

        assert result == custom_output
        assert Path(custom_output).exists()

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg')
    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    @patch('video_tools_mcp.processing.audio_extraction.load_config')
    def test_extract_audio_custom_sample_rate(
        self, mock_load_config, mock_validate, mock_ffmpeg, temp_dir
    ):
        """Test that custom sample rate is passed to ffmpeg."""
        mock_validate.return_value = True

        # Mock config
        mock_config = MagicMock()
        mock_config.processing.temp_dir = str(temp_dir)
        mock_load_config.return_value = mock_config

        # Mock ffmpeg chain
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.overwrite_output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Create output file
        with patch('video_tools_mcp.processing.audio_extraction.generate_temp_filename') as mock_gen:
            output_path = str(temp_dir / "audio_test.wav")
            mock_gen.return_value = output_path
            Path(output_path).touch()

            extract_audio("/path/to/video.mp4", sample_rate=44100)

        # Verify ffmpeg.output was called with custom sample rate
        output_call = mock_ffmpeg.output.call_args
        assert output_call[1]['ar'] == 44100

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg')
    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    @patch('video_tools_mcp.processing.audio_extraction.load_config')
    def test_extract_audio_ffmpeg_error_raises_audio_extraction_error(
        self, mock_load_config, mock_validate, mock_ffmpeg
    ):
        """Test that FFmpeg errors are wrapped in AudioExtractionError."""
        mock_validate.return_value = True

        # Mock config
        mock_config = MagicMock()
        mock_config.processing.temp_dir = "/tmp"
        mock_load_config.return_value = mock_config

        # Mock ffmpeg to raise error
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.overwrite_output.return_value = mock_stream

        # Create a custom exception class for mocking ffmpeg.Error
        class FakeFFmpegError(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.stderr = b'FFmpeg error occurred'

        # Create mock ffmpeg error instance
        mock_error = FakeFFmpegError('FFmpeg error occurred')
        mock_ffmpeg.run.side_effect = mock_error
        # Also mock ffmpeg.Error class for the except clause
        mock_ffmpeg.Error = FakeFFmpegError

        with pytest.raises(AudioExtractionError) as exc_info:
            extract_audio("/path/to/video.mp4")

        assert "Failed to extract audio" in str(exc_info.value) or "Audio extraction failed" in str(exc_info.value)

    @patch('video_tools_mcp.processing.audio_extraction.Path')
    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg')
    @patch('video_tools_mcp.processing.audio_extraction.validate_video_path')
    @patch('video_tools_mcp.processing.audio_extraction.load_config')
    def test_extract_audio_missing_output_raises_error(
        self, mock_load_config, mock_validate, mock_ffmpeg, mock_path_class, temp_dir
    ):
        """Test that error is raised if output file is not created."""
        mock_validate.return_value = True

        # Mock config
        mock_config = MagicMock()
        mock_config.processing.temp_dir = str(temp_dir)
        mock_load_config.return_value = mock_config

        # Mock ffmpeg chain
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.overwrite_output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Create a custom exception class that doesn't conflict with AudioExtractionError
        class FakeFFmpegError(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.stderr = None

        # Mock ffmpeg.Error class with something that won't catch our AudioExtractionError
        mock_ffmpeg.Error = FakeFFmpegError

        # Mock Path to return a non-existent file
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = False  # File doesn't exist
        mock_path_class.return_value = mock_output_path

        # Don't create output file (simulating ffmpeg failure without error)
        with patch('video_tools_mcp.processing.audio_extraction.generate_temp_filename') as mock_gen:
            output_path = str(temp_dir / "audio_test.wav")
            mock_gen.return_value = output_path

            # Don't create the file

            with pytest.raises(AudioExtractionError) as exc_info:
                extract_audio("/path/to/video.mp4")

        assert "output file not found" in str(exc_info.value)


class TestGetAudioInfo:
    """Test cases for get_audio_info() function."""

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg.probe')
    def test_get_audio_info_returns_correct_data(self, mock_probe, mock_audio_path):
        """Test that audio info is correctly extracted from probe."""
        # Mock probe result
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'audio',
                    'duration': '125.50',
                    'sample_rate': '16000',
                    'channels': 1,
                    'codec_name': 'pcm_s16le'
                }
            ]
        }

        info = get_audio_info(mock_audio_path)

        assert info['duration'] == 125.50
        assert info['sample_rate'] == 16000
        assert info['channels'] == 1
        assert info['codec'] == 'pcm_s16le'

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg.probe')
    def test_get_audio_info_duration_from_format(self, mock_probe, mock_audio_path):
        """Test that duration can be extracted from format section."""
        # Mock probe result with duration in format instead of stream
        mock_probe.return_value = {
            'format': {
                'duration': '90.25'
            },
            'streams': [
                {
                    'codec_type': 'audio',
                    'sample_rate': '16000',
                    'channels': 1,
                    'codec_name': 'pcm_s16le'
                }
            ]
        }

        info = get_audio_info(mock_audio_path)

        assert info['duration'] == 90.25

    def test_get_audio_info_missing_file_raises_error(self, temp_dir):
        """Test that missing audio file raises AudioExtractionError."""
        missing_path = str(temp_dir / "missing_audio.wav")

        with pytest.raises(AudioExtractionError) as exc_info:
            get_audio_info(missing_path)

        assert "not found" in str(exc_info.value)

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg.probe')
    def test_get_audio_info_no_audio_stream_raises_error(self, mock_probe, mock_audio_path):
        """Test that error is raised when no audio stream is found."""
        # Mock probe result with no audio streams
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'video'
                }
            ]
        }

        with pytest.raises(AudioExtractionError) as exc_info:
            get_audio_info(mock_audio_path)

        assert "No audio stream found" in str(exc_info.value)

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg.probe')
    def test_get_audio_info_ffmpeg_error_raises_audio_extraction_error(
        self, mock_probe, mock_audio_path
    ):
        """Test that FFmpeg probe errors are wrapped properly."""
        # Create mock ffmpeg error
        mock_error = ffmpeg.Error('ffprobe', 'stdout', b'Probe error')
        mock_error.stderr = b'Probe error'
        mock_probe.side_effect = mock_error

        with pytest.raises(AudioExtractionError) as exc_info:
            get_audio_info(mock_audio_path)

        assert "Failed to probe audio file" in str(exc_info.value)

    @patch('video_tools_mcp.processing.audio_extraction.ffmpeg.probe')
    def test_get_audio_info_handles_missing_fields(self, mock_probe, mock_audio_path):
        """Test that missing optional fields are handled gracefully."""
        # Mock probe result with minimal data
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'audio'
                    # Missing: duration, sample_rate, channels, codec_name
                }
            ]
        }

        info = get_audio_info(mock_audio_path)

        # Should return defaults for missing fields
        assert info['duration'] is None
        assert info['sample_rate'] == 0
        assert info['channels'] == 0
        assert info['codec'] == 'unknown'


class TestCleanupAudioFile:
    """Test cases for cleanup_audio_file() function."""

    def test_cleanup_audio_file_deletes_existing_file(self, temp_dir):
        """Test that existing audio file is successfully deleted."""
        audio_file = temp_dir / "test_audio.wav"
        audio_file.touch()

        assert audio_file.exists()

        result = cleanup_audio_file(str(audio_file))

        assert result is True
        assert not audio_file.exists()

    def test_cleanup_audio_file_missing_file_returns_false(self, temp_dir):
        """Test that cleanup returns False for missing file."""
        missing_file = temp_dir / "missing_audio.wav"

        result = cleanup_audio_file(str(missing_file))

        assert result is False

    def test_cleanup_audio_file_directory_returns_false(self, temp_dir):
        """Test that cleanup returns False if path is a directory."""
        result = cleanup_audio_file(str(temp_dir))

        assert result is False

    def test_cleanup_audio_file_permission_error_returns_false(self, temp_dir):
        """Test that permission errors are handled gracefully."""
        audio_file = temp_dir / "test_audio.wav"
        audio_file.touch()

        # Mock unlink to raise PermissionError
        with patch.object(Path, 'unlink', side_effect=PermissionError("Access denied")):
            result = cleanup_audio_file(str(audio_file))

        assert result is False

    def test_cleanup_audio_file_os_error_returns_false(self, temp_dir):
        """Test that OS errors are handled gracefully."""
        audio_file = temp_dir / "test_audio.wav"
        audio_file.touch()

        # Mock unlink to raise OSError
        with patch.object(Path, 'unlink', side_effect=OSError("Disk error")):
            result = cleanup_audio_file(str(audio_file))

        assert result is False
