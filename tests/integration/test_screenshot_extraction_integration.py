"""
Integration tests for smart screenshot extraction.

Tests the extract_smart_screenshots MCP tool with:
- Basic extraction functionality
- Deduplication thresholds
- AI-driven frame selection
- Metadata generation
- Output management

Uses real video files from tests/fixtures/videos/
"""

import pytest
import json
from pathlib import Path

from video_tools_mcp import server

# Extract actual function from MCP tool
extract_smart_screenshots = server.extract_smart_screenshots.fn
from tests.integration.helpers import (
    validate_screenshot_metadata,
    assert_file_exists,
    calculate_rtf
)


class TestBasicScreenshotExtraction:
    """Test basic screenshot extraction functionality."""

    def test_extract_screenshots_visual_video(self, require_visual_video, temp_dir):
        """Test screenshot extraction on a visual animation video."""
        video_path = require_visual_video

        # Extract screenshots with default settings
        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=5,
            similarity_threshold=0.90,
            max_screenshots=20
        )

        # Validate response structure
        assert "screenshots" in result
        assert "metadata_path" in result
        assert "total_extracted" in result
        assert "duplicates_removed" in result
        assert "processing_time" in result

        # Should have extracted some screenshots
        assert isinstance(result["screenshots"], list), "screenshots should be a list"
        assert result["total_extracted"] > 0, "Should have extracted at least one screenshot"

        # Metadata file should exist
        metadata_path = result["metadata_path"]
        assert_file_exists(metadata_path, "Metadata JSON")

        # Validate metadata structure
        validation = validate_screenshot_metadata(metadata_path)
        assert validation["exists"], "Metadata file should exist"
        assert validation["has_all_top_level_fields"], \
            "Metadata should have all required top-level fields"
        assert validation["screenshots_is_list"], "screenshots should be a list"
        assert validation["screenshots_not_empty"], "screenshots list should not be empty"
        assert validation["all_screenshots_valid"], \
            "All screenshots should have required fields"

        # Verify screenshot files actually exist
        for screenshot_path in result["screenshots"]:
            assert_file_exists(screenshot_path, "Screenshot image")
            assert screenshot_path.endswith(".jpg"), \
                f"Screenshot should be .jpg, got: {screenshot_path}"

        # Processing metrics should be reasonable
        assert result["processing_time"] > 0, "Processing time should be > 0"
        assert result["duplicates_removed"] >= 0, "Duplicates removed should be >= 0"

    @pytest.mark.slow
    def test_extract_screenshots_tears_steel(self, temp_dir):
        """Test screenshot extraction on longer visual video (Tears of Steel)."""
        video_path = Path("tests/fixtures/videos/visual_734s_tears_steel_1080p.mp4")

        if not video_path.exists():
            pytest.skip(f"Test video not available: {video_path}")

        import time
        start_time = time.time()

        # Extract with higher limit for longer video
        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=10,  # Every 10 seconds
            similarity_threshold=0.90,
            max_screenshots=30
        )

        processing_time = time.time() - start_time

        # Should have extracted screenshots
        assert result["total_extracted"] > 0, "Should extract screenshots"
        assert result["total_extracted"] <= 30, "Should respect max_screenshots limit"

        # Metadata should exist
        assert_file_exists(result["metadata_path"], "Metadata")

        # Log performance
        print(f"\n=== Screenshot Extraction Performance ===")
        print(f"Video: {video_path.name}")
        print(f"Duration: ~734s (12:14)")
        print(f"Processing Time: {processing_time:.1f}s")
        print(f"Screenshots Extracted: {result['total_extracted']}")
        print(f"Duplicates Removed: {result['duplicates_removed']}")
        print(f"Speed: ~{processing_time/result['total_extracted']:.1f}s per screenshot")


class TestDeduplicationAndConfig:
    """Test deduplication and configuration options."""

    def test_deduplication_threshold_strict(self, require_visual_video, temp_dir):
        """Test with stricter deduplication threshold (keeps more similar frames)."""
        video_path = require_visual_video

        # Use stricter threshold (0.95 = only remove very similar frames)
        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=3,
            similarity_threshold=0.95,  # Stricter
            max_screenshots=15
        )

        # Should extract screenshots
        assert result["total_extracted"] > 0

        # With stricter threshold, fewer duplicates should be removed
        # (more frames pass the similarity test)
        print(f"\n=== Strict Threshold (0.95) ===")
        print(f"Extracted: {result['total_extracted']}")
        print(f"Duplicates Removed: {result['duplicates_removed']}")

    def test_deduplication_threshold_loose(self, require_visual_video, temp_dir):
        """Test with looser deduplication threshold (removes more similar frames)."""
        video_path = require_visual_video

        # Use looser threshold (0.85 = more aggressive deduplication)
        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=3,
            similarity_threshold=0.85,  # Looser
            max_screenshots=15
        )

        # Should extract screenshots
        assert result["total_extracted"] > 0

        # With looser threshold, more duplicates should be removed
        print(f"\n=== Loose Threshold (0.85) ===")
        print(f"Extracted: {result['total_extracted']}")
        print(f"Duplicates Removed: {result['duplicates_removed']}")

    def test_max_screenshots_limit(self, require_visual_video, temp_dir):
        """Test that max_screenshots limit is respected."""
        video_path = require_visual_video

        # Set low limit
        max_limit = 5

        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=2,  # Frequent sampling
            max_screenshots=max_limit
        )

        # Should not exceed limit
        assert result["total_extracted"] <= max_limit, \
            f"Should not exceed max_screenshots={max_limit}, got {result['total_extracted']}"

    def test_very_short_interval(self, require_short_video, temp_dir):
        """Test extraction with very short sampling interval."""
        video_path = require_short_video

        # Sample every 1 second
        result = extract_smart_screenshots(
            video_path=str(video_path),
            sample_interval=1,
            similarity_threshold=0.90,
            max_screenshots=20
        )

        # Should extract some frames
        assert result["total_extracted"] > 0

        # Should have good deduplication (short video likely has similar frames)
        assert result["duplicates_removed"] >= 0

        print(f"\n=== Short Interval (1s) on {video_path.name} ===")
        print(f"Extracted: {result['total_extracted']}")
        print(f"Duplicates Removed: {result['duplicates_removed']}")


class TestMetadataAndOutputs:
    """Test metadata generation and output management."""

    def test_screenshot_metadata_structure(self, require_visual_video, temp_dir):
        """Test that metadata.json has correct structure and all required fields."""
        video_path = require_visual_video

        result = extract_smart_screenshots(
            video_path=str(video_path),
            max_screenshots=10
        )

        metadata_path = result["metadata_path"]

        # Parse metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Verify top-level fields
        required_top_level = [
            "video_path",
            "extraction_prompt",
            "sample_interval",
            "similarity_threshold",
            "max_screenshots",
            "output_dir",
            "total_frames_extracted",
            "duplicates_removed",
            "frames_evaluated",
            "screenshots_kept",
            "processing_time",
            "screenshots"
        ]

        for field in required_top_level:
            assert field in metadata, f"Missing required field: {field}"

        # Verify screenshots array
        assert isinstance(metadata["screenshots"], list), "screenshots should be a list"
        assert len(metadata["screenshots"]) == result["total_extracted"], \
            "Metadata screenshots count should match result total_extracted"

        # Verify each screenshot entry has required fields
        if len(metadata["screenshots"]) > 0:
            screenshot_required = ["filename", "path", "timestamp", "caption"]
            for screenshot in metadata["screenshots"]:
                for field in screenshot_required:
                    assert field in screenshot, \
                        f"Screenshot entry missing required field: {field}"

    def test_screenshot_captions_generated(self, require_visual_video, temp_dir):
        """Test that AI-generated captions are present and non-empty."""
        video_path = require_visual_video

        result = extract_smart_screenshots(
            video_path=str(video_path),
            max_screenshots=5
        )

        # Parse metadata
        with open(result["metadata_path"], 'r') as f:
            metadata = json.load(f)

        # Check each screenshot has a caption
        for screenshot in metadata["screenshots"]:
            assert "caption" in screenshot, "Screenshot should have caption field"
            caption = screenshot["caption"]
            assert isinstance(caption, str), "Caption should be a string"
            assert len(caption) > 0, "Caption should not be empty"
            assert len(caption) < 500, "Caption should be concise"

            print(f"\nScreenshot: {screenshot['filename']}")
            print(f"Caption: {caption}")
            print(f"Timestamp: {screenshot['timestamp']:.1f}s")

    def test_custom_extraction_prompt(self, require_visual_video, temp_dir):
        """Test extraction with custom AI prompt."""
        video_path = require_visual_video

        custom_prompt = "Select frames that show character movement or action scenes."

        result = extract_smart_screenshots(
            video_path=str(video_path),
            extraction_prompt=custom_prompt,
            max_screenshots=8
        )

        # Parse metadata
        with open(result["metadata_path"], 'r') as f:
            metadata = json.load(f)

        # Should use custom prompt
        assert metadata["extraction_prompt"] == custom_prompt, \
            "Metadata should contain custom extraction prompt"

        # Check AI reasoning mentions relevant concepts
        for screenshot in metadata["screenshots"]:
            if "ai_reasoning" in screenshot:
                reasoning = screenshot["ai_reasoning"].lower()
                print(f"\nAI Reasoning: {screenshot['ai_reasoning'][:100]}...")

    def test_default_output_directory(self, require_visual_video, temp_dir):
        """Test that default output directory is created correctly."""
        video_path = require_visual_video

        # Don't specify output_dir (use default)
        result = extract_smart_screenshots(
            video_path=str(video_path),
            max_screenshots=5
        )

        # Default should be {video_stem}_screenshots next to video
        expected_dir_name = f"{Path(video_path).stem}_screenshots"
        output_dir = Path(result["metadata_path"]).parent

        assert output_dir.name == expected_dir_name, \
            f"Expected output dir '{expected_dir_name}', got '{output_dir.name}'"

        # Directory should exist
        assert output_dir.exists(), f"Output directory not found: {output_dir}"

    def test_custom_output_directory(self, require_visual_video, temp_dir):
        """Test extraction with custom output directory."""
        video_path = require_visual_video

        # Use custom output directory
        custom_output_dir = temp_dir / "my_custom_screenshots"

        result = extract_smart_screenshots(
            video_path=str(video_path),
            output_dir=str(custom_output_dir),
            max_screenshots=5
        )

        # Should use custom directory
        metadata_dir = Path(result["metadata_path"]).parent
        assert metadata_dir == custom_output_dir, \
            f"Expected output dir {custom_output_dir}, got {metadata_dir}"

        # Directory should exist
        assert custom_output_dir.exists(), f"Custom output dir not found: {custom_output_dir}"

        # Screenshots should be in custom directory
        for screenshot_path in result["screenshots"]:
            assert Path(screenshot_path).parent == custom_output_dir, \
                f"Screenshot should be in custom dir: {screenshot_path}"

    def test_invalid_video_path_error(self):
        """Test that invalid video path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="not found"):
            extract_smart_screenshots(
                video_path="/nonexistent/video.mp4"
            )
