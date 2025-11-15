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


# Test video URLs - All Creative Commons or Public Domain licensed
# Last Updated: 2025-11-15
TEST_VIDEOS = {
    # ========================================
    # CATEGORY A: Single Speaker Videos
    # ========================================
    "short_tutorial": {
        "url": "https://archive.org/download/AddingTwoDigitNumbers_201307/Basic%20Addition%20Video.mp4",
        "filename": "short_30s_addition_tutorial.mp4",
        "description": "Khan Academy basic addition tutorial (~30-60s, single speaker)",
        "duration": "~60s",
        "speakers": 1,
        "size": "5.6 MB",
    },
    "short_history_1": {
        "url": "https://archive.org/download/10TenMinuteHistoryThOfEthOfTheBantary/Ten%20Minute%20History/The%20Interwar%20Period%201918-1939/03-Edward%20VIII%20and%20the%20Abdication%20Crisis%20-%20History%20Matters.mp4",
        "filename": "short_120s_edward_viii.mp4",
        "description": "History Matters: Edward VIII Abdication (~2min, animated narration)",
        "duration": "~120s",
        "speakers": 1,
        "size": "6.1 MB",
    },
    "medium_ted_talk": {
        "url": "http://download.ted.com/talks/ClaytonCameron_2013Y-480p.mp4?apikey=TEDDOWNLOAD",
        "filename": "medium_357s_clayton_cameron_ted.mp4",
        "description": "Clayton Cameron TED Talk (5:57, single speaker presentation)",
        "duration": "357s",
        "speakers": 1,
        "size": "42.3 MB",
    },
    "long_tutorial": {
        "url": "https://archive.org/download/Big_Bang_Tutorial_/Big_Bang_Tutorial_.mp4",
        "filename": "long_663s_big_bang_tutorial.mp4",
        "description": "Khan Academy Big Bang tutorial (11:03, educational narration)",
        "duration": "663s",
        "speakers": 1,
        "size": "19.6 MB",
    },

    # ========================================
    # CATEGORY B: Multi-Speaker Videos
    # ========================================
    "interview_2speaker": {
        "url": "https://archive.org/download/video-job-interview/video%20job%20interview.mp4",
        "filename": "multi_180s_job_interview.mp4",
        "description": "Video job interview (~3min, 2+ speakers)",
        "duration": "~180s",
        "speakers": 2,
        "size": "92.4 MB",
    },
    "interview_3speaker": {
        "url": "https://archive.org/download/Timothy_Leary_Archives_174-a/174-a_512kb.mp4",
        "filename": "multi_300s_cafe_conversation.mp4",
        "description": "Timothy Leary cafe conversation (~5min, 3 speakers)",
        "duration": "~300s",
        "speakers": 3,
        "size": "249.6 MB",
    },

    # ========================================
    # CATEGORY C: Visual Content Videos
    # ========================================
    "visual_short": {
        "url": "https://archive.org/download/Caminandes1LlamaDrama/01_llama_drama_1080p.mp4",
        "filename": "visual_90s_llama_drama_1080p.mp4",
        "description": "Caminandes: Llama Drama (90s, animated film, 1080p)",
        "duration": "90s",
        "speakers": 0,
        "size": "33.5 MB",
        "resolution": "1080p",
    },
    "visual_effects": {
        "url": "https://archive.org/download/Tears-of-Steel/tears_of_steel_1080p.mp4",
        "filename": "visual_734s_tears_steel_1080p.mp4",
        "description": "Tears of Steel (12:14, Blender film with dialogue, 1080p)",
        "duration": "734s",
        "speakers": 3,
        "size": "72.6 MB",
        "resolution": "1080p",
    },

    # ========================================
    # CATEGORY D: Long-Form & Edge Cases
    # ========================================
    "long_presentation": {
        "url": "http://download.ted.com/talks/DavidSRose_2007U-480p.mp4",
        "filename": "long_883s_david_rose_ted.mp4",
        "description": "David S. Rose TED Talk (14:43, startup pitch presentation)",
        "duration": "883s",
        "speakers": 1,
        "size": "97.2 MB",
    },
    "edge_4k": {
        "url": "https://archive.org/download/Sintel/sintel-2048-stereo_512kb.mp4",
        "filename": "edge_888s_sintel_2048p.mp4",
        "description": "Sintel (14:48, Blender film, 2048p for 4K testing)",
        "duration": "888s",
        "speakers": 2,
        "size": "73.8 MB",
        "resolution": "2048p",
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
