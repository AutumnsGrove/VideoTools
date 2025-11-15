#!/usr/bin/env python3
"""
Download test videos for integration testing.

This script downloads free stock videos from various sources
to use as test fixtures for the VideoTools MCP Server.

Usage:
    python scripts/download_test_videos.py
    python scripts/download_test_videos.py --skip-existing
    python scripts/download_test_videos.py --video short
"""

import argparse
import subprocess
from pathlib import Path
import sys


# Test video URLs (TODO Phase 6: Find and add actual free stock video URLs)
TEST_VIDEOS = {
    "short": {
        "url": "https://example.com/short_30s_video.mp4",  # TODO: Replace with actual URL
        "filename": "short_30s_single_speaker.mp4",
        "description": "30-second video with single speaker for basic testing",
    },
    "multi_speaker": {
        "url": "https://example.com/interview_180s.mp4",  # TODO: Replace with actual URL
        "filename": "multi_180s_interview.mp4",
        "description": "2-3 minute interview with multiple speakers",
    },
    "visual": {
        "url": "https://example.com/tutorial_300s.mp4",  # TODO: Replace with actual URL
        "filename": "visual_300s_tutorial.mp4",
        "description": "5-minute tutorial with varied visual content",
    },
    "long": {
        "url": "https://example.com/presentation_900s.mp4",  # TODO: Replace with actual URL
        "filename": "long_900s_presentation.mp4",
        "description": "10-15 minute long-form video for performance testing",
    },
}


def download_video(url: str, output_path: Path) -> bool:
    """
    Download a video using curl or wget.

    Args:
        url: Video URL
        output_path: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Downloading: {output_path.name}")
        print(f"  from: {url}")

        # Try curl first (available on macOS by default)
        result = subprocess.run(
            ["curl", "-L", "-o", str(output_path), url],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"  ✓ Downloaded successfully")
            return True
        else:
            print(f"  ✗ Download failed: {result.stderr}")
            return False

    except FileNotFoundError:
        # If curl not found, try wget
        try:
            subprocess.run(
                ["wget", "-O", str(output_path), url],
                check=True,
            )
            print(f"  ✓ Downloaded successfully")
            return True
        except FileNotFoundError:
            print("  ✗ Neither curl nor wget found. Please install one.")
            return False
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download test videos for VideoTools integration testing"
    )
    parser.add_argument(
        "--video",
        choices=list(TEST_VIDEOS.keys()),
        help="Download specific video only",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip videos that already exist",
    )
    args = parser.parse_args()

    # Determine output directory
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir.parent / "tests" / "fixtures" / "videos"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("VideoTools Test Video Downloader")
    print("=" * 60)
    print(f"Output directory: {fixtures_dir}")
    print()

    # Determine which videos to download
    if args.video:
        videos_to_download = {args.video: TEST_VIDEOS[args.video]}
    else:
        videos_to_download = TEST_VIDEOS

    # Download videos
    success_count = 0
    skip_count = 0
    fail_count = 0

    for video_id, info in videos_to_download.items():
        output_path = fixtures_dir / info["filename"]

        # Check if already exists
        if output_path.exists():
            if args.skip_existing:
                print(f"Skipping {info['filename']} (already exists)")
                skip_count += 1
                continue
            else:
                print(f"Overwriting existing {info['filename']}")

        # Download
        if download_video(info["url"], output_path):
            success_count += 1
        else:
            fail_count += 1

        print()

    # Summary
    print("=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"✓ Successful: {success_count}")
    if skip_count > 0:
        print(f"⊘ Skipped: {skip_count}")
    if fail_count > 0:
        print(f"✗ Failed: {fail_count}")
    print()

    if fail_count > 0:
        print("Some downloads failed. You may need to manually download videos.")
        print("See tests/fixtures/videos/README.md for alternative sources.")
        sys.exit(1)
    else:
        print("All test videos ready!")
        print("Run integration tests with: pytest tests/integration/ -v")
        sys.exit(0)


if __name__ == "__main__":
    main()
