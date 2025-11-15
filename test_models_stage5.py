#!/usr/bin/env python3
"""Test script to verify Stage 5 model manager implementation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from video_tools_mcp.models import ModelManager, ParakeetModel, PyannoteModel, QwenVLModel


def test_singleton_pattern():
    """Test that singleton pattern works correctly."""
    print("Testing Singleton Pattern...")

    # Create two instances of ParakeetModel
    parakeet1 = ParakeetModel()
    parakeet2 = ParakeetModel()

    # They should be the same instance
    assert parakeet1 is parakeet2, "Singleton pattern failed for ParakeetModel"
    print("✓ ParakeetModel singleton works")

    # Test for PyannoteModel
    pyannote1 = PyannoteModel()
    pyannote2 = PyannoteModel()
    assert pyannote1 is pyannote2, "Singleton pattern failed for PyannoteModel"
    print("✓ PyannoteModel singleton works")

    # Test for QwenVLModel
    qwen1 = QwenVLModel()
    qwen2 = QwenVLModel()
    assert qwen1 is qwen2, "Singleton pattern failed for QwenVLModel"
    print("✓ QwenVLModel singleton works")

    # Verify different model types are different instances
    assert parakeet1 is not pyannote1, "Different model types should be different instances"
    print("✓ Different model types maintain separate instances")

    print("✓ Singleton pattern test PASSED\n")


def test_model_lifecycle():
    """Test model load/unload lifecycle."""
    print("Testing Model Lifecycle...")

    # Test Parakeet
    parakeet = ParakeetModel()

    # Initial state
    assert not parakeet.is_loaded, "Model should start unloaded"
    assert parakeet.model_id == "mlx-community/parakeet-tdt-0.6b-v3"
    print(f"✓ Parakeet initial state: {parakeet.status()}")

    # Load model (stub)
    parakeet.load()
    assert parakeet.is_loaded, "Model should be loaded after load()"
    print(f"✓ Parakeet after load: {parakeet.status()}")

    # Unload model
    parakeet.unload()
    assert not parakeet.is_loaded, "Model should be unloaded after unload()"
    print(f"✓ Parakeet after unload: {parakeet.status()}")

    print("✓ Model lifecycle test PASSED\n")


def test_ensure_loaded():
    """Test ensure_loaded convenience method."""
    print("Testing ensure_loaded()...")

    pyannote = PyannoteModel()
    pyannote.unload()  # Ensure it starts unloaded

    # Call ensure_loaded
    pyannote.ensure_loaded()
    assert pyannote.is_loaded, "ensure_loaded() should load the model"
    print("✓ ensure_loaded() loads unloaded model")

    # Call again - should not error
    pyannote.ensure_loaded()
    assert pyannote.is_loaded, "ensure_loaded() should keep model loaded"
    print("✓ ensure_loaded() on already loaded model works")

    print("✓ ensure_loaded() test PASSED\n")


def test_stub_methods():
    """Test that stub methods return expected placeholder data."""
    print("Testing Stub Methods...")

    # Test Parakeet transcribe
    parakeet = ParakeetModel()
    result = parakeet.transcribe("test.wav", language="en")
    assert "text" in result, "transcribe() should return dict with 'text'"
    assert "[STUB]" in result["text"], "Stub should indicate placeholder data"
    print(f"✓ Parakeet transcribe stub: {result['text'][:50]}...")

    # Test Pyannote diarize
    pyannote = PyannoteModel()
    result = pyannote.diarize("test.wav", num_speakers=3)
    assert "segments" in result, "diarize() should return dict with 'segments'"
    assert result["num_speakers"] == 3, "num_speakers should match input"
    print(f"✓ Pyannote diarize stub: {result['num_speakers']} speakers")

    # Test Qwen VL analyze_frame
    qwen = QwenVLModel()
    result = qwen.analyze_frame("test.jpg", "What's in this image?")
    assert "analysis" in result, "analyze_frame() should return dict with 'analysis'"
    assert "[STUB]" in result["analysis"], "Stub should indicate placeholder data"
    print(f"✓ Qwen VL analyze stub: {result['analysis'][:50]}...")

    print("✓ Stub methods test PASSED\n")


def test_model_status():
    """Test model status reporting."""
    print("Testing Model Status...")

    qwen = QwenVLModel()
    qwen.unload()

    status = qwen.status()
    assert "model_id" in status, "status() should include model_id"
    assert "is_loaded" in status, "status() should include is_loaded"
    assert "load_error" in status, "status() should include load_error"

    print(f"✓ Status format correct: {status}")

    qwen.load()
    status = qwen.status()
    assert status["is_loaded"], "Status should reflect loaded state"

    print(f"✓ Status reflects model state: {status}")
    print("✓ Model status test PASSED\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Stage 5: Model Manager Framework and Stub Wrappers")
    print("=" * 60)
    print()

    try:
        test_singleton_pattern()
        test_model_lifecycle()
        test_ensure_loaded()
        test_stub_methods()
        test_model_status()

        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print()
        print("Summary:")
        print("- ModelManager base class with singleton pattern ✓")
        print("- ParakeetModel stub implementation ✓")
        print("- PyannoteModel stub implementation ✓")
        print("- QwenVLModel stub implementation ✓")
        print("- Model lifecycle management ✓")
        print("- Stub methods return placeholder data ✓")
        print()
        print("Ready for Phase 2-4 implementation!")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
