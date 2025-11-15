"""
Unit tests for MCP server module (server.py).

Tests cover:
- Server module loads without errors
- All 5 tools are registered
- Each tool can be called with valid parameters
- Tool docstrings are present
- Stub tools return correct response format
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Import server module to verify it loads
from video_tools_mcp import server


class TestServerModule:
    """Test cases for server module loading."""

    def test_server_module_imports_successfully(self):
        """Test that server module can be imported without errors."""
        # If we got here, import succeeded
        assert server is not None

    def test_mcp_instance_exists(self):
        """Test that mcp FastMCP instance is created."""
        assert hasattr(server, 'mcp')
        assert server.mcp is not None

    def test_mcp_name_and_version(self):
        """Test that MCP server has correct name and version."""
        assert server.mcp.name == "video-tools"
        # Note: FastMCP may not expose version directly, check if available
        # This test verifies the mcp object is properly configured


class TestToolRegistration:
    """Test cases for tool registration."""

    def test_all_five_tools_are_registered(self):
        """Test that all 5 expected tools are registered."""
        # Get registered tools from FastMCP
        # Note: FastMCP stores tools in _tools or similar attribute
        # We'll verify by checking if the functions have the tool decorator

        # Check that tool functions exist
        assert hasattr(server, 'transcribe_video')
        assert hasattr(server, 'transcribe_with_speakers')
        assert hasattr(server, 'analyze_video')
        assert hasattr(server, 'extract_smart_screenshots')
        assert hasattr(server, 'rename_speakers')

    def test_transcribe_video_has_description(self):
        """Test that transcribe_video has documentation."""
        # FastMCP wraps functions in FunctionTool objects with description attribute
        assert hasattr(server.transcribe_video, 'description')
        assert server.transcribe_video.description is not None
        assert len(server.transcribe_video.description.strip()) > 0

    def test_transcribe_with_speakers_has_description(self):
        """Test that transcribe_with_speakers has documentation."""
        assert hasattr(server.transcribe_with_speakers, 'description')
        assert server.transcribe_with_speakers.description is not None
        assert len(server.transcribe_with_speakers.description.strip()) > 0

    def test_analyze_video_has_description(self):
        """Test that analyze_video has documentation."""
        assert hasattr(server.analyze_video, 'description')
        assert server.analyze_video.description is not None
        assert len(server.analyze_video.description.strip()) > 0

    def test_extract_smart_screenshots_has_description(self):
        """Test that extract_smart_screenshots has documentation."""
        assert hasattr(server.extract_smart_screenshots, 'description')
        assert server.extract_smart_screenshots.description is not None
        assert len(server.extract_smart_screenshots.description.strip()) > 0

    def test_rename_speakers_has_description(self):
        """Test that rename_speakers has documentation."""
        assert hasattr(server.rename_speakers, 'description')
        assert server.rename_speakers.description is not None
        assert len(server.rename_speakers.description.strip()) > 0


class TestTranscribeVideo:
    """Test cases for transcribe_video tool."""

    def test_transcribe_video_basic_call_returns_dict(self):
        """Test that transcribe_video returns expected dict structure."""
        # Access the underlying function from the FunctionTool wrapper
        result = server.transcribe_video.fn("/path/to/video.mp4")

        assert isinstance(result, dict)
        assert "transcript_path" in result
        assert "duration" in result
        assert "word_count" in result
        assert "processing_time" in result

    def test_transcribe_video_custom_parameters(self):
        """Test that transcribe_video accepts custom parameters."""
        result = server.transcribe_video.fn(
            video_path="/path/to/video.mp4",
            output_format="vtt",
            model="custom-model",
            language="es"
        )

        assert isinstance(result, dict)
        # Stub should still return valid response
        assert "transcript_path" in result

    def test_transcribe_video_default_format_is_srt(self):
        """Test that default output format is srt."""
        result = server.transcribe_video.fn("/path/to/video.mp4")

        # Stub returns path with format extension
        assert ".srt" in result["transcript_path"]

    def test_transcribe_video_returns_numeric_values(self):
        """Test that numeric fields are numbers."""
        result = server.transcribe_video.fn("/path/to/video.mp4")

        assert isinstance(result["duration"], (int, float))
        assert isinstance(result["word_count"], int)
        assert isinstance(result["processing_time"], (int, float))


class TestTranscribeWithSpeakers:
    """Test cases for transcribe_with_speakers tool."""

    def test_transcribe_with_speakers_basic_call_returns_dict(self):
        """Test that transcribe_with_speakers returns expected dict structure."""
        result = server.transcribe_with_speakers.fn("/path/to/video.mp4")

        assert isinstance(result, dict)
        assert "transcript_path" in result
        assert "speakers_detected" in result
        assert "duration" in result
        assert "processing_time" in result

    def test_transcribe_with_speakers_with_num_speakers(self):
        """Test that transcribe_with_speakers accepts num_speakers parameter."""
        result = server.transcribe_with_speakers.fn(
            video_path="/path/to/video.mp4",
            num_speakers=3
        )

        assert isinstance(result, dict)
        # Stub returns the num_speakers value
        assert result["speakers_detected"] == 3

    def test_transcribe_with_speakers_auto_detect(self):
        """Test that transcribe_with_speakers supports auto-detect (None)."""
        result = server.transcribe_with_speakers.fn(
            video_path="/path/to/video.mp4",
            num_speakers=None
        )

        assert isinstance(result, dict)
        # Stub defaults to 2 when None
        assert result["speakers_detected"] == 2

    def test_transcribe_with_speakers_min_max_range(self):
        """Test that transcribe_with_speakers accepts min/max speaker range."""
        result = server.transcribe_with_speakers.fn(
            video_path="/path/to/video.mp4",
            min_speakers=1,
            max_speakers=5
        )

        assert isinstance(result, dict)
        assert "speakers_detected" in result


class TestAnalyzeVideo:
    """Test cases for analyze_video tool."""

    def test_analyze_video_basic_call_returns_dict(self):
        """Test that analyze_video returns expected dict structure."""
        result = server.analyze_video.fn("/path/to/video.mp4")

        assert isinstance(result, dict)
        assert "analysis_path" in result
        assert "frames_analyzed" in result
        assert "duration" in result
        assert "processing_time" in result

    def test_analyze_video_custom_prompt(self):
        """Test that analyze_video accepts custom analysis prompt."""
        result = server.analyze_video.fn(
            video_path="/path/to/video.mp4",
            analysis_prompt="Describe the main actions in each frame"
        )

        assert isinstance(result, dict)
        assert "analysis_path" in result

    def test_analyze_video_default_prompt_used_when_none(self):
        """Test that analyze_video uses default prompt when None."""
        result = server.analyze_video.fn(
            video_path="/path/to/video.mp4",
            analysis_prompt=None
        )

        assert isinstance(result, dict)
        # Stub should still return valid response
        assert "frames_analyzed" in result

    def test_analyze_video_sample_interval_parameter(self):
        """Test that analyze_video accepts sample_interval parameter."""
        result = server.analyze_video.fn(
            video_path="/path/to/video.mp4",
            sample_interval=10
        )

        assert isinstance(result, dict)

    def test_analyze_video_max_frames_parameter(self):
        """Test that analyze_video accepts max_frames parameter."""
        result = server.analyze_video.fn(
            video_path="/path/to/video.mp4",
            max_frames=50
        )

        assert isinstance(result, dict)

    def test_analyze_video_include_ocr_parameter(self):
        """Test that analyze_video accepts include_ocr parameter."""
        result = server.analyze_video.fn(
            video_path="/path/to/video.mp4",
            include_ocr=True
        )

        assert isinstance(result, dict)


class TestExtractSmartScreenshots:
    """Test cases for extract_smart_screenshots tool."""

    def test_extract_smart_screenshots_basic_call_returns_dict(self):
        """Test that extract_smart_screenshots returns expected dict structure."""
        result = server.extract_smart_screenshots.fn("/path/to/video.mp4")

        assert isinstance(result, dict)
        assert "screenshots" in result
        assert "metadata_path" in result
        assert "total_extracted" in result
        assert "duplicates_removed" in result
        assert "processing_time" in result

    def test_extract_smart_screenshots_returns_list(self):
        """Test that screenshots field is a list."""
        result = server.extract_smart_screenshots.fn("/path/to/video.mp4")

        assert isinstance(result["screenshots"], list)

    def test_extract_smart_screenshots_custom_prompt(self):
        """Test that extract_smart_screenshots accepts custom extraction prompt."""
        result = server.extract_smart_screenshots.fn(
            video_path="/path/to/video.mp4",
            extraction_prompt="Extract frames showing people speaking"
        )

        assert isinstance(result, dict)
        assert "screenshots" in result

    def test_extract_smart_screenshots_similarity_threshold(self):
        """Test that extract_smart_screenshots accepts similarity_threshold."""
        result = server.extract_smart_screenshots.fn(
            video_path="/path/to/video.mp4",
            similarity_threshold=0.95
        )

        assert isinstance(result, dict)

    def test_extract_smart_screenshots_max_screenshots(self):
        """Test that extract_smart_screenshots accepts max_screenshots."""
        result = server.extract_smart_screenshots.fn(
            video_path="/path/to/video.mp4",
            max_screenshots=100
        )

        assert isinstance(result, dict)

    def test_extract_smart_screenshots_custom_output_dir(self):
        """Test that extract_smart_screenshots accepts output_dir."""
        result = server.extract_smart_screenshots.fn(
            video_path="/path/to/video.mp4",
            output_dir="/custom/output"
        )

        assert isinstance(result, dict)


class TestRenameSpeakers:
    """Test cases for rename_speakers tool."""

    def test_rename_speakers_basic_call_returns_dict(self):
        """Test that rename_speakers returns expected dict structure."""
        speaker_map = {"Speaker 1": "Alice", "Speaker 2": "Bob"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map
        )

        assert isinstance(result, dict)
        assert "output_path" in result
        assert "replacements_made" in result
        assert "backup_path" in result

    def test_rename_speakers_replacements_count(self):
        """Test that replacements_made reflects speaker_map size."""
        speaker_map = {"Speaker 1": "Alice", "Speaker 2": "Bob", "Speaker 3": "Carol"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map
        )

        assert result["replacements_made"] == len(speaker_map)

    def test_rename_speakers_custom_output_path(self):
        """Test that rename_speakers accepts custom output_path."""
        speaker_map = {"Speaker 1": "Alice"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map,
            output_path="/path/to/output.srt"
        )

        assert result["output_path"] == "/path/to/output.srt"

    def test_rename_speakers_default_output_path(self):
        """Test that rename_speakers defaults to overwriting original."""
        speaker_map = {"Speaker 1": "Alice"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map,
            output_path=None
        )

        # Should default to original path
        assert result["output_path"] == "/path/to/subtitles.srt"

    def test_rename_speakers_backup_enabled_by_default(self):
        """Test that backup is created by default."""
        speaker_map = {"Speaker 1": "Alice"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map
        )

        assert result["backup_path"] is not None
        assert ".bak" in result["backup_path"]

    def test_rename_speakers_backup_disabled(self):
        """Test that backup can be disabled."""
        speaker_map = {"Speaker 1": "Alice"}

        result = server.rename_speakers.fn(
            srt_path="/path/to/subtitles.srt",
            speaker_map=speaker_map,
            backup=False
        )

        assert result["backup_path"] is None


class TestPromptImports:
    """Test cases for prompt configuration imports."""

    def test_default_prompts_imported(self):
        """Test that default prompts are imported from config."""
        from video_tools_mcp.config.prompts import (
            DEFAULT_ANALYSIS_PROMPT,
            DEFAULT_SCREENSHOT_EXTRACTION_PROMPT
        )

        # Prompts should be non-empty strings
        assert isinstance(DEFAULT_ANALYSIS_PROMPT, str)
        assert len(DEFAULT_ANALYSIS_PROMPT) > 0

        assert isinstance(DEFAULT_SCREENSHOT_EXTRACTION_PROMPT, str)
        assert len(DEFAULT_SCREENSHOT_EXTRACTION_PROMPT) > 0


class TestServerMain:
    """Test cases for main() function."""

    def test_main_function_exists(self):
        """Test that main() function is defined."""
        assert hasattr(server, 'main')
        assert callable(server.main)

    @patch('video_tools_mcp.server.mcp.run')
    def test_main_calls_mcp_run(self, mock_run):
        """Test that main() calls mcp.run()."""
        # Call main
        server.main()

        # Verify mcp.run was called
        mock_run.assert_called_once()
