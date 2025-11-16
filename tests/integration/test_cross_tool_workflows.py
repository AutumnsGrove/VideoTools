"""
Integration tests for multi-tool workflows.

Tests realistic use cases that combine multiple MCP tools:
- Transcribe with speakers + rename speakers
- Multiple output format conversions
- Full processing pipeline

Uses real video files from tests/fixtures/videos/
"""

import pytest
from pathlib import Path

from video_tools_mcp import server

# Extract actual functions from MCP tools
transcribe_with_speakers = server.transcribe_with_speakers.fn
rename_speakers = server.rename_speakers.fn
extract_smart_screenshots = server.extract_smart_screenshots.fn
from tests.integration.helpers import (
    extract_speaker_labels,
    assert_file_exists,
    validate_screenshot_metadata
)


class TestMultiToolWorkflows:
    """Test workflows that combine multiple tools."""

    def test_workflow_transcribe_and_rename(self, require_multi_speaker_video, temp_dir):
        """
        Test complete workflow: transcribe with speakers -> rename speakers.

        This simulates a real user workflow:
        1. User transcribes a video with speaker diarization
        2. User renames the generic SPEAKER_XX labels to actual names
        """
        video_path = require_multi_speaker_video

        # Step 1: Transcribe with speaker diarization
        print("\n=== Step 1: Transcribe with Speakers ===")
        transcribe_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )

        transcript_path = transcribe_result["transcript_path"]
        assert_file_exists(transcript_path, "Initial transcript")

        # Verify generic speaker labels
        initial_speakers = extract_speaker_labels(transcript_path)
        print(f"Initial speakers: {initial_speakers}")
        assert all(label.startswith("SPEAKER_") for label in initial_speakers), \
            "Should have generic SPEAKER_XX labels"

        # Step 2: Rename speakers to real names
        print("\n=== Step 2: Rename Speakers ===")
        speaker_map = {
            "SPEAKER_00": "Alice",
            "SPEAKER_01": "Bob"
        }

        rename_result = rename_speakers(
            srt_path=transcript_path,
            speaker_map=speaker_map,
            create_backup=True
        )

        renamed_path = rename_result["output_path"]
        assert_file_exists(renamed_path, "Renamed transcript")

        # Verify changes
        print(f"Replacements made: {rename_result['replacements_made']}")
        print(f"Speakers renamed: {rename_result['speakers_renamed']}")
        assert rename_result["replacements_made"] > 0, "Should have made replacements"

        # Read final output and verify
        with open(renamed_path, 'r') as f:
            final_content = f.read()

        # Should contain new names
        assert "Alice:" in final_content or "Bob:" in final_content, \
            "Final transcript should contain renamed speakers"

        # Should NOT contain generic labels at start of lines
        lines = [line for line in final_content.split('\n') if ':' in line and '-->' not in line]
        speaker_prefixes = [line.split(':')[0].strip() for line in lines if line.strip()]
        generic_prefixes = [p for p in speaker_prefixes if p.startswith("SPEAKER_")]

        print(f"\nFinal speaker prefixes (first 10): {speaker_prefixes[:10]}")
        assert len(generic_prefixes) == 0, \
            f"Should not have SPEAKER_XX prefixes after renaming, found: {generic_prefixes[:5]}"

        # Backup should exist
        assert rename_result["backup_path"] is not None, "Should have backup"
        assert Path(rename_result["backup_path"]).exists(), "Backup file should exist"

        print("\n=== Workflow Complete ===")
        print(f"✓ Transcribed with {transcribe_result['speakers_detected']} speakers")
        print(f"✓ Renamed {len(rename_result['speakers_renamed'])} speaker labels")
        print(f"✓ Output: {renamed_path}")

    def test_workflow_transcribe_multiple_formats(self, require_multi_speaker_video, temp_dir):
        """
        Test workflow: generate transcript in multiple formats.

        This simulates a user who wants transcripts in different formats:
        - SRT for subtitle files
        - JSON for programmatic access
        - TXT for reading/editing
        """
        video_path = require_multi_speaker_video

        print("\n=== Generating Multiple Format Outputs ===")

        # Generate SRT
        print("Generating SRT...")
        srt_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )
        srt_path = srt_result["transcript_path"]
        assert_file_exists(srt_path, "SRT transcript")
        assert srt_path.endswith(".speakers.srt")

        # Generate JSON
        print("Generating JSON...")
        json_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="json"
        )
        json_path = json_result["transcript_path"]
        assert_file_exists(json_path, "JSON transcript")
        assert json_path.endswith(".speakers.json")

        # Generate TXT
        print("Generating TXT...")
        txt_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="txt"
        )
        txt_path = txt_result["transcript_path"]
        assert_file_exists(txt_path, "TXT transcript")
        assert txt_path.endswith(".speakers.txt")

        # Verify consistency across formats
        print("\n=== Verifying Consistency ===")

        # All should have same speaker count
        assert srt_result["speakers_detected"] == json_result["speakers_detected"], \
            "SRT and JSON should report same speaker count"
        assert json_result["speakers_detected"] == txt_result["speakers_detected"], \
            "JSON and TXT should report same speaker count"

        # All should have same duration
        assert abs(srt_result["duration"] - json_result["duration"]) < 1.0, \
            "Duration should be consistent across formats"

        # All should have same speakers list
        assert srt_result["speakers"] == json_result["speakers"], \
            "Speaker lists should match across formats"

        print(f"✓ Generated 3 formats: SRT, JSON, TXT")
        print(f"✓ Speakers detected: {srt_result['speakers_detected']}")
        print(f"✓ Duration: {srt_result['duration']:.1f}s")
        print(f"✓ All formats consistent")

    def test_workflow_full_pipeline(self, require_multi_speaker_video, temp_dir):
        """
        Test complete pipeline: transcribe + rename + extract screenshots.

        This simulates a user who wants:
        1. Transcription with speaker labels
        2. Renamed speakers
        3. Key screenshots from the video

        A realistic "process my video completely" workflow.
        """
        video_path = require_multi_speaker_video

        print("\n=== Full Processing Pipeline ===")

        # Step 1: Transcribe with speakers
        print("\nStep 1: Transcribing video with speaker diarization...")
        transcribe_result = transcribe_with_speakers(
            video_path=str(video_path),
            output_format="srt"
        )
        assert_file_exists(transcribe_result["transcript_path"], "Transcript")
        print(f"✓ Transcribed: {transcribe_result['speakers_detected']} speakers, " \
              f"{transcribe_result['num_segments']} segments")

        # Step 2: Rename speakers
        print("\nStep 2: Renaming speakers to real names...")
        rename_result = rename_speakers(
            srt_path=transcribe_result["transcript_path"],
            speaker_map={"SPEAKER_00": "Interviewer", "SPEAKER_01": "Candidate"},
            create_backup=True
        )
        assert_file_exists(rename_result["output_path"], "Renamed transcript")
        print(f"✓ Renamed: {rename_result['replacements_made']} replacements, " \
              f"{len(rename_result['speakers_renamed'])} speakers")

        # Step 3: Extract key screenshots
        print("\nStep 3: Extracting key screenshots...")
        screenshot_result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=10,  # Every 10 seconds
            max_screenshots=10
        )
        assert screenshot_result["total_extracted"] > 0, "Should extract screenshots"
        assert_file_exists(screenshot_result["metadata_path"], "Screenshot metadata")
        print(f"✓ Screenshots: {screenshot_result['total_extracted']} extracted, " \
              f"{screenshot_result['duplicates_removed']} duplicates removed")

        # Verify all outputs exist
        print("\n=== Pipeline Complete ===")
        print(f"✓ Transcript: {rename_result['output_path']}")
        print(f"✓ Screenshots: {len(screenshot_result['screenshots'])} files")
        print(f"✓ Metadata: {screenshot_result['metadata_path']}")
        print(f"✓ Backup: {rename_result['backup_path']}")

        # Verify screenshot metadata is valid
        validation = validate_screenshot_metadata(screenshot_result["metadata_path"])
        assert validation["exists"], "Metadata should exist"
        assert validation["has_all_top_level_fields"], "Metadata should be complete"

        print("\n✅ Full pipeline executed successfully!")
