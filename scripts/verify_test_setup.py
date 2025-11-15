#!/usr/bin/env python3
"""
Verify test setup and video availability for VideoTools integration testing.

Usage:
    python scripts/verify_test_setup.py
"""

import sys
from pathlib import Path

# Add tests to path so we can import conftest
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

try:
    from conftest import (
        videos_available,
        any_videos_available,
        all_videos_available,
        FIXTURES_DIR,
        SHORT_TUTORIAL,
        MULTI_SPEAKER_2,
        VISUAL_SHORT,
        LONG_PRESENTATION,
    )
except ImportError as e:
    print(f"❌ Error importing conftest: {e}")
    print("   Make sure pytest is installed: uv pip install pytest")
    sys.exit(1)


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def main():
    """Main verification function."""
    print_header("VideoTools Test Setup Verification")

    # Check fixtures directory
    print(f"\n📁 Fixtures Directory: {FIXTURES_DIR}")
    if FIXTURES_DIR.exists():
        print("   ✓ Directory exists")
    else:
        print("   ✗ Directory not found")
        print(f"   Creating: {FIXTURES_DIR}")
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Check video availability
    print_header("Test Video Availability")

    status = videos_available()
    available_count = sum(status.values())
    total_count = len(status)

    print(f"\n📊 Status: {available_count}/{total_count} videos available\n")

    # Group by category
    categories = {
        "Single Speaker": [
            "short_tutorial",
            "short_history",
            "medium_ted_talk",
            "long_tutorial",
        ],
        "Multi-Speaker": ["multi_speaker_2", "multi_speaker_3"],
        "Visual Content": ["visual_short", "visual_effects"],
        "Long-Form/Edge": ["long_presentation", "edge_4k"],
    }

    for category, video_names in categories.items():
        print(f"  {category}:")
        for video_name in video_names:
            if video_name in status:
                symbol = "✓" if status[video_name] else "✗"
                print(f"    {symbol} {video_name}")
        print()

    # Overall status
    print_header("Test Readiness")

    if all_videos_available():
        print("\n✅ ALL videos available - Full test suite ready!")
    elif any_videos_available():
        print(f"\n⚠️  PARTIAL videos available ({available_count}/{total_count})")
        print("   Some integration tests will be skipped")
    else:
        print("\n❌ NO videos available")
        print("   All integration tests will be skipped")

    # Download instructions
    if not all_videos_available():
        print_header("Download Instructions")
        print("\nTo download all test videos (~700 MB):")
        print("  python scripts/download_test_videos.py\n")
        print("To download specific videos:")
        print("  python scripts/download_test_videos.py --video short_tutorial")
        print("  python scripts/download_test_videos.py --video interview_2speaker")
        print("  python scripts/download_test_videos.py --video visual_short\n")

    # Test command suggestions
    print_header("Running Tests")

    if any_videos_available():
        print("\nYou can now run integration tests:")
        print("  pytest tests/integration/ -v")
        print("  pytest tests/integration/ -v -m requires_videos")
        print("\nRun only tests with available videos:")
        print("  pytest tests/integration/ -v --tb=short")
    else:
        print("\nDownload videos first, then run:")
        print("  pytest tests/integration/ -v")

    print("\nRun unit tests (no videos needed):")
    print("  pytest tests/unit/ -v")
    print("  pytest tests/ -v -m 'not requires_videos'")

    # Environment check
    print_header("Environment Check")

    # Check for pytest
    try:
        import pytest
        print(f"  ✓ pytest installed (version {pytest.__version__})")
    except ImportError:
        print("  ✗ pytest not installed")
        print("    Install with: uv pip install pytest")

    # Check for key dependencies
    dependencies = [
        ("ffmpeg-python", "ffmpeg"),
        ("mlx", "mlx"),
        ("mlx-vlm", "mlx_vlm"),
    ]

    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name} installed")
        except ImportError:
            print(f"  ✗ {package_name} not installed")

    print()
    print_header("Setup Complete")

    if all_videos_available():
        print("\n🎉 Your test environment is fully ready!")
        return 0
    elif any_videos_available():
        print(f"\n⚠️  Test environment partially ready ({available_count}/{total_count} videos)")
        return 0
    else:
        print("\n📥 Download test videos to enable integration tests")
        return 1


if __name__ == "__main__":
    sys.exit(main())
