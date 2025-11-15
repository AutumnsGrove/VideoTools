"""
Integration tests for transcription tools (Phase 2 & 3).

These tests require actual video files in tests/fixtures/videos/
and will test the complete transcription pipeline end-to-end.

Run with: pytest tests/integration/test_transcription_integration.py -v
"""

import pytest
from pathlib import Path
import json

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "videos"
SHORT_VIDEO = FIXTURES_DIR / "short_30s_single_speaker.mp4"
MULTI_SPEAKER_VIDEO = FIXTURES_DIR / "multi_180s_interview.mp4"


@pytest.fixture
def check_test_videos():
    """Ensure test videos are available."""
    if not SHORT_VIDEO.exists():
        pytest.skip(f"Test video not found: {SHORT_VIDEO}. Run scripts/download_test_videos.py")
    if not MULTI_SPEAKER_VIDEO.exists():
        pytest.skip(f"Test video not found: {MULTI_SPEAKER_VIDEO}. Run scripts/download_test_videos.py")


class TestBasicTranscription:
    """Test transcribe_video tool (Phase 2)."""

    def test_transcribe_short_video_srt(self, check_test_videos):
        """Test basic transcription with SRT output."""
        # TODO Phase 6: Implement
        # - Call transcribe_video tool with SHORT_VIDEO
        # - Verify SRT file is created
        # - Parse SRT and validate format
        # - Check that transcript is not empty
        # - Verify timestamps are sequential
        pytest.skip("TODO: Implement in Phase 6")

    def test_transcribe_short_video_json(self, check_test_videos):
        """Test basic transcription with JSON output."""
        # TODO Phase 6: Implement
        # - Call transcribe_video with output_format="json"
        # - Load and validate JSON structure
        # - Check for required fields: segments, duration, etc.
        pytest.skip("TODO: Implement in Phase 6")

    def test_transcribe_short_video_txt(self, check_test_videos):
        """Test basic transcription with plain text output."""
        # TODO Phase 6: Implement
        # - Call transcribe_video with output_format="txt"
        # - Verify text file contains transcript
        # - Check for reasonable word count
        pytest.skip("TODO: Implement in Phase 6")


class TestSpeakerDiarization:
    """Test transcribe_with_speakers tool (Phase 3)."""

    def test_transcribe_with_speakers_basic(self, check_test_videos):
        """Test speaker diarization on multi-speaker video."""
        # TODO Phase 6: Implement
        # - Call transcribe_with_speakers with MULTI_SPEAKER_VIDEO
        # - Verify speaker labels are present (SPEAKER_00, SPEAKER_01, etc.)
        # - Check that num_speakers is reasonable (2-4 for test video)
        # - Validate SRT format with speaker prefixes
        pytest.skip("TODO: Implement in Phase 6")

    def test_transcribe_with_speakers_num_speakers(self, check_test_videos):
        """Test with explicit num_speakers parameter."""
        # TODO Phase 6: Implement
        # - Call with num_speakers=2
        # - Verify exactly 2 speakers detected
        pytest.skip("TODO: Implement in Phase 6")

    def test_rename_speakers_tool(self, check_test_videos):
        """Test rename_speakers tool."""
        # TODO Phase 6: Implement
        # - First transcribe with speakers
        # - Then rename SPEAKER_00 -> "Alice", SPEAKER_01 -> "Bob"
        # - Verify renamed SRT has correct names
        # - Check that backup was created
        pytest.skip("TODO: Implement in Phase 6")


class TestPerformanceBenchmarks:
    """Benchmark transcription performance."""

    def test_transcription_speed(self, check_test_videos):
        """Measure transcription processing speed."""
        # TODO Phase 6: Implement
        # - Transcribe SHORT_VIDEO and measure time
        # - Calculate real-time factor (processing_time / video_duration)
        # - Assert RTF < 0.1 (10x faster than real-time on M4)
        # - Log results for benchmarking documentation
        pytest.skip("TODO: Implement in Phase 6")

    def test_diarization_speed(self, check_test_videos):
        """Measure diarization processing speed."""
        # TODO Phase 6: Implement
        # - Process MULTI_SPEAKER_VIDEO with speakers
        # - Measure total processing time
        # - Log results for documentation
        pytest.skip("TODO: Implement in Phase 6")


# TODO Phase 6: Add more edge case tests
# - Very long video (10+ minutes)
# - Poor audio quality
# - Multiple overlapping speakers
# - Video with no speech
# - Video with music/background noise
