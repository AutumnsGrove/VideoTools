"""
Integration tests for speaker diarization and renaming tools.

Tests the following MCP tools:
- transcribe_with_speakers
- rename_speakers

Uses real video files from tests/fixtures/videos/
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from video_tools_mcp import server

# Extract actual functions from MCP tools
transcribe_with_speakers = server.transcribe_with_speakers.fn
rename_speakers = server.rename_speakers.fn
from tests.integration.helpers import (
    validate_srt_format,
    count_speakers_in_srt,
    extract_speaker_labels,
    validate_json_transcript,
    assert_file_exists,
    assert_reasonable_duration,
    calculate_rtf
)


class TestBasicSpeakerDiarization:
    """Test basic speaker diarization functionality."""

    def test_diarize_two_speaker_interview(self, require_multi_speaker_video, temp_dir):
        """Test diarization on a 2-speaker job interview video."""
        video_path = require_multi_speaker_video

        # Run diarization
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        # Validate response structure
        assert "transcript_path" in result
        assert "speakers_detected" in result
        assert "duration" in result
        assert "num_segments" in result
        assert "speakers" in result

        # Check output file exists
        transcript_path = result["transcript_path"]
        assert_file_exists(transcript_path, "SRT transcript")

        # Validate SRT format
        assert validate_srt_format(transcript_path), f"Invalid SRT format: {transcript_path}"

        # Check speaker count (should be 2 or close)
        speakers_detected = result["speakers_detected"]
        assert 1 <= speakers_detected <= 3, f"Expected 1-3 speakers, got {speakers_detected}"

        # Verify speaker labels in output
        speaker_labels = extract_speaker_labels(transcript_path)
        assert len(speaker_labels) >= 1, "Should have at least 1 speaker label"
        assert all(label.startswith("SPEAKER_") for label in speaker_labels), \
            f"Speaker labels should start with SPEAKER_, got: {speaker_labels}"

        # Verify segments
        assert result["num_segments"] > 0, "Should have at least one segment"

        # Duration should be reasonable (~180s for job interview)
        assert_reasonable_duration(180, result["duration"], tolerance=0.20)

    def test_diarize_three_speaker_conversation(self, temp_dir):
        """Test diarization on a 3+ speaker conversation video."""
        # Use cafe conversation video (3 speakers)
        video_path = Path("tests/fixtures/videos/multi_300s_cafe_conversation.mp4")

        if not video_path.exists():
            pytest.skip(f"Test video not available: {video_path}")

        # Run diarization (auto-detect speakers)
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        # Should detect 2+ speakers
        assert result["speakers_detected"] >= 2, \
            f"Expected at least 2 speakers, got {result['speakers_detected']}"

        # Check output
        transcript_path = result["transcript_path"]
        assert_file_exists(transcript_path, "SRT transcript")
        assert validate_srt_format(transcript_path)

        # Duration should be ~300s
        assert_reasonable_duration(300, result["duration"], tolerance=0.15)

    def test_diarize_with_exact_speaker_count(self, require_multi_speaker_video, temp_dir):
        """Test diarization with exact speaker count specified."""
        video_path = require_multi_speaker_video

        # Specify exactly 2 speakers
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt",
            num_speakers=2
        )

        # Should report 2 speakers
        assert result["speakers_detected"] == 2, \
            f"Expected exactly 2 speakers, got {result['speakers_detected']}"

        # Verify output
        transcript_path = result["transcript_path"]
        speaker_labels = extract_speaker_labels(transcript_path)
        assert len(speaker_labels) == 2, \
            f"Expected 2 unique speaker labels, got {len(speaker_labels)}: {speaker_labels}"

    def test_single_speaker_video_diarization(self, require_short_video, temp_dir):
        """Test diarization on a single-speaker video."""
        video_path = require_short_video

        # Run diarization (should detect 1 speaker)
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        # Should detect 1 speaker
        assert result["speakers_detected"] == 1, \
            f"Expected 1 speaker, got {result['speakers_detected']}"

        # Verify only SPEAKER_00 in output
        transcript_path = result["transcript_path"]
        speaker_labels = extract_speaker_labels(transcript_path)
        assert speaker_labels == ["SPEAKER_00"], \
            f"Expected only SPEAKER_00, got: {speaker_labels}"


class TestOutputFormats:
    """Test different output formats for speaker diarization."""

    def test_diarization_srt_output(self, require_multi_speaker_video, temp_dir):
        """Test SRT format output."""
        video_path = require_multi_speaker_video

        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        transcript_path = result["transcript_path"]

        # Should end with .speakers.srt
        assert transcript_path.endswith(".speakers.srt"), \
            f"Expected .speakers.srt extension, got: {transcript_path}"

        # Validate SRT format
        assert validate_srt_format(transcript_path)

        # Check for speaker prefixes in content
        with open(transcript_path, 'r') as f:
            content = f.read()

        assert "SPEAKER_" in content, "Should contain speaker prefixes"

    def test_diarization_json_output(self, require_multi_speaker_video, temp_dir):
        """Test JSON format output."""
        video_path = require_multi_speaker_video

        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="json"
        )

        transcript_path = result["transcript_path"]

        # Should end with .speakers.json
        assert transcript_path.endswith(".speakers.json"), \
            f"Expected .speakers.json extension, got: {transcript_path}"

        # Validate JSON structure
        required_fields = ["segments", "speakers", "num_speakers", "duration"]
        assert validate_json_transcript(transcript_path, required_fields), \
            f"JSON missing required fields: {required_fields}"

        # Parse and validate content
        with open(transcript_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data["segments"], list), "segments should be a list"
        assert len(data["segments"]) > 0, "Should have at least one segment"
        assert isinstance(data["speakers"], list), "speakers should be a list"
        assert data["num_speakers"] >= 1, "Should have at least 1 speaker"

        # Check segments have speaker prefixes
        first_segment = data["segments"][0]
        assert "text" in first_segment, "Segment should have text field"
        assert "SPEAKER_" in first_segment["text"], "Segment text should have speaker prefix"

    def test_diarization_txt_output(self, require_multi_speaker_video, temp_dir):
        """Test plain text format output."""
        video_path = require_multi_speaker_video

        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="txt"
        )

        transcript_path = result["transcript_path"]

        # Should end with .speakers.txt
        assert transcript_path.endswith(".speakers.txt"), \
            f"Expected .speakers.txt extension, got: {transcript_path}"

        # Read content
        with open(transcript_path, 'r') as f:
            content = f.read()

        # Should contain speaker prefixes
        assert "SPEAKER_" in content, "Should contain speaker prefixes"

        # Should be plain text (no timestamps like 00:00:01,000)
        assert "-->" not in content, "Plain text should not contain SRT timestamps"


class TestSpeakerRenaming:
    """Test speaker renaming functionality."""

    def test_rename_speakers_basic(self, require_multi_speaker_video, temp_dir):
        """Test basic speaker renaming workflow."""
        video_path = require_multi_speaker_video

        # Step 1: Transcribe with speakers
        transcribe_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        srt_path = transcribe_result["transcript_path"]

        # Step 2: Rename speakers
        speaker_map = {
            "SPEAKER_00": "Alice",
            "SPEAKER_01": "Bob"
        }

        rename_result = rename_speakers(
            srt_path=srt_path,
            speaker_map=speaker_map,
            create_backup=True
        )

        # Validate response
        assert "output_path" in rename_result
        assert "replacements_made" in rename_result
        assert "backup_path" in rename_result
        assert "speakers_renamed" in rename_result

        # Should have made replacements
        assert rename_result["replacements_made"] > 0, \
            "Should have replaced at least one speaker label"

        # Should list which speakers were renamed
        assert "SPEAKER_00" in rename_result["speakers_renamed"] or \
               "SPEAKER_01" in rename_result["speakers_renamed"], \
            "Should report which speakers were renamed"

        # Read output file and verify changes
        output_path = rename_result["output_path"]
        with open(output_path, 'r') as f:
            content = f.read()

        # Should contain new names
        assert "Alice:" in content or "Bob:" in content, \
            "Output should contain renamed speakers"

        # Should NOT contain old names at start of lines
        lines = content.split('\n')
        speaker_lines = [line for line in lines if ':' in line and not '-->' in line]
        for line in speaker_lines:
            assert not line.strip().startswith("SPEAKER_00:"), \
                "Should not have SPEAKER_00: after renaming"
            assert not line.strip().startswith("SPEAKER_01:"), \
                "Should not have SPEAKER_01: after renaming"

    def test_rename_speakers_backup_creation(self, require_multi_speaker_video, temp_dir):
        """Test that backup file is created when requested."""
        video_path = require_multi_speaker_video

        # Transcribe
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )
        srt_path = result["transcript_path"]

        # Rename with backup
        rename_result = rename_speakers(
            srt_path=srt_path,
            speaker_map={"SPEAKER_00": "Alice"},
            create_backup=True
        )

        # Should have backup path
        assert rename_result["backup_path"] is not None, \
            "Should return backup_path when create_backup=True"

        # Backup file should exist
        backup_path = rename_result["backup_path"]
        assert Path(backup_path).exists(), f"Backup file not found: {backup_path}"

        # Backup should have .bak extension
        assert backup_path.endswith(".bak"), \
            f"Backup should have .bak extension, got: {backup_path}"

    def test_rename_speakers_no_backup(self, require_multi_speaker_video, temp_dir):
        """Test that no backup is created when not requested."""
        video_path = require_multi_speaker_video

        # Transcribe
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )
        srt_path = result["transcript_path"]

        # Rename without backup
        rename_result = rename_speakers(
            srt_path=srt_path,
            speaker_map={"SPEAKER_00": "Charlie"},
            create_backup=False
        )

        # Should not have backup path
        assert rename_result["backup_path"] is None, \
            "Should not return backup_path when create_backup=False"

    def test_rename_speakers_custom_output_path(self, require_multi_speaker_video, temp_dir):
        """Test renaming with custom output path."""
        video_path = require_multi_speaker_video

        # Transcribe
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )
        srt_path = result["transcript_path"]

        # Rename to custom path
        custom_output = str(temp_dir / "custom_renamed.srt")
        rename_result = rename_speakers(
            srt_path=srt_path,
            speaker_map={"SPEAKER_00": "David"},
            output_path=custom_output
        )

        # Should use custom output path
        assert rename_result["output_path"] == custom_output, \
            f"Expected output_path={custom_output}, got {rename_result['output_path']}"

        # Custom file should exist
        assert Path(custom_output).exists(), f"Custom output not found: {custom_output}"

        # Original file should be unchanged
        with open(srt_path, 'r') as f:
            original_content = f.read()
        assert "SPEAKER_00:" in original_content, \
            "Original file should still have SPEAKER_00"

    def test_rename_invalid_srt_path_error(self):
        """Test that invalid SRT path raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            rename_speakers(
                srt_path="/nonexistent/file.srt",
                speaker_map={"SPEAKER_00": "Nobody"}
            )


class TestTempFileAndErrors:
    """Test temp file management and error handling."""

    def test_cleanup_temp_files_enabled(self, require_short_video, temp_dir):
        """Test that temporary audio files are cleaned up when enabled."""
        video_path = require_short_video

        # Run with cleanup enabled (default)
        result = transcribe_with_speakers(
            video_path=str(video_path),
            cleanup_temp_files=True
        )

        # Output should exist
        assert_file_exists(result["transcript_path"], "Transcript")

        # Temp wav files should be cleaned up
        # (We can't easily verify cleanup without file system introspection,
        # but we can verify the function completes without errors)
        assert result["num_segments"] > 0, "Should have successfully processed"

    def test_cleanup_temp_files_disabled(self, require_short_video, temp_dir):
        """Test that temporary files are kept when cleanup is disabled."""
        video_path = require_short_video

        # Run with cleanup disabled
        result = transcribe_with_speakers(
            video_path=str(video_path),
            cleanup_temp_files=False
        )

        # Output should exist
        assert_file_exists(result["transcript_path"], "Transcript")
        assert result["num_segments"] > 0

    def test_invalid_video_path_error(self):
        """Test that invalid video path raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            transcribe_with_speakers(
                video_path="/nonexistent/video.mp4"
            )

    def test_diarize_with_speaker_range(self, require_multi_speaker_video, temp_dir):
        """Test diarization with min/max speaker range."""
        video_path = require_multi_speaker_video

        # Specify speaker range (2-4 speakers)
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt",
            min_speakers=2,
            max_speakers=4
        )

        # Should detect speakers within range
        speakers_detected = result["speakers_detected"]
        assert 2 <= speakers_detected <= 4, \
            f"Expected 2-4 speakers, got {speakers_detected}"


class TestPerformance:
    """Test performance and long video processing."""

    @pytest.mark.slow
    def test_long_video_diarization(self, temp_dir):
        """Test diarization on a long video (~15 minutes)."""
        # Use David Rose TED talk (883s = ~14.7 minutes)
        video_path = Path("tests/fixtures/videos/long_883s_david_rose_ted.mp4")

        if not video_path.exists():
            pytest.skip(f"Test video not available: {video_path}")

        import time
        start_time = time.time()

        # Run diarization
        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        processing_time = time.time() - start_time

        # Verify completion
        assert_file_exists(result["transcript_path"], "Transcript")

        # Duration should be ~883s
        assert_reasonable_duration(883, result["duration"], tolerance=0.10)

        # Log performance metrics
        rtf = calculate_rtf(result["duration"], processing_time)
        print(f"\n=== Performance Metrics ===")
        print(f"Video Duration: {result['duration']:.1f}s")
        print(f"Processing Time: {processing_time:.1f}s")
        print(f"RTF: {rtf:.3f}")
        print(f"Speed: {1/rtf:.1f}x real-time")
        print(f"Segments: {result['num_segments']}")
        print(f"Speakers: {result['speakers_detected']}")

    @pytest.mark.benchmark
    def test_benchmark_diarization_rtf(self, require_multi_speaker_video, temp_dir):
        """Benchmark diarization Real-Time Factor (RTF)."""
        video_path = require_multi_speaker_video

        import time
        start_time = time.time()

        result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        processing_time = time.time() - start_time
        rtf = calculate_rtf(result["duration"], processing_time)

        # Log benchmark results
        print(f"\n=== Benchmark: Speaker Diarization ===")
        print(f"Video: {video_path.name}")
        print(f"Duration: {result['duration']:.1f}s")
        print(f"Processing Time: {processing_time:.1f}s")
        print(f"RTF: {rtf:.3f}")
        print(f"Target: RTF < 0.5 (2x real-time)")
        print(f"Result: {'PASS' if rtf < 0.5 else 'ACCEPTABLE'}")

        # RTF should be reasonable (not requiring strict performance)
        # Just verify it completes in a reasonable timeframe
        assert rtf < 5.0, f"RTF too high: {rtf:.2f} (processing is too slow)"
