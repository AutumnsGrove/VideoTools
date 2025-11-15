"""
Unit tests for model manager and model classes.

Tests cover:
- ModelManager base class (singleton pattern, lifecycle)
- ParakeetModel stub implementation
- PyannoteModel stub implementation
- QwenVLModel stub implementation
- Status tracking and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from video_tools_mcp.models.model_manager import ModelManager
from video_tools_mcp.models.parakeet import ParakeetModel
from video_tools_mcp.models.pyannote import PyannoteModel
from video_tools_mcp.models.qwen_vl import QwenVLModel


class TestModelManagerSingleton:
    """Test cases for ModelManager singleton pattern."""

    def test_singleton_same_class_returns_same_instance(self):
        """Test that multiple instantiations of same model return same instance."""
        # Create two instances of ParakeetModel
        instance1 = ParakeetModel()
        instance2 = ParakeetModel()

        # Should be the exact same object
        assert instance1 is instance2

    def test_singleton_different_classes_return_different_instances(self):
        """Test that different model classes have separate instances."""
        parakeet = ParakeetModel()
        pyannote = PyannoteModel()
        qwen = QwenVLModel()

        # All should be different instances
        assert parakeet is not pyannote
        assert parakeet is not qwen
        assert pyannote is not qwen

    def test_singleton_state_persists_across_instantiations(self):
        """Test that state changes persist across instantiations."""
        # Create first instance and modify state
        instance1 = ParakeetModel()
        instance1.load()

        # Create second instance
        instance2 = ParakeetModel()

        # State should be the same
        assert instance2.is_loaded is True

        # Cleanup
        instance1.unload()


class TestModelManagerLifecycle:
    """Test cases for ModelManager lifecycle methods."""

    def test_model_manager_initial_state(self):
        """Test that new model starts in unloaded state."""
        model = ParakeetModel()

        # Reset state for test (since singleton persists)
        model.is_loaded = False
        model.load_error = None

        assert model.is_loaded is False
        assert model.load_error is None

    def test_ensure_loaded_calls_load_when_not_loaded(self):
        """Test that ensure_loaded() loads unloaded model."""
        model = ParakeetModel()
        model.is_loaded = False

        # Mock the load method
        with patch.object(model, 'load') as mock_load:
            model.ensure_loaded()

            mock_load.assert_called_once()

    def test_ensure_loaded_skips_load_when_already_loaded(self):
        """Test that ensure_loaded() skips loading for already loaded model."""
        model = ParakeetModel()
        model.is_loaded = True

        # Mock the load method
        with patch.object(model, 'load') as mock_load:
            model.ensure_loaded()

            mock_load.assert_not_called()

    def test_ensure_loaded_handles_load_error(self):
        """Test that ensure_loaded() properly handles load errors."""
        model = ParakeetModel()
        model.is_loaded = False

        # Mock load to raise exception
        with patch.object(model, 'load', side_effect=RuntimeError("Load failed")):
            with pytest.raises(RuntimeError):
                model.ensure_loaded()

            # Error message should be recorded
            assert model.load_error is not None
            assert "Load failed" in model.load_error
            assert model.is_loaded is False

    def test_status_returns_correct_state(self):
        """Test that status() returns current model state."""
        model = ParakeetModel()
        model.is_loaded = False
        model.load_error = None
        model.model_id = "test-model"

        status = model.status()

        assert status["model_id"] == "test-model"
        assert status["is_loaded"] is False
        assert status["load_error"] is None

    def test_status_includes_error_when_present(self):
        """Test that status() includes error message when set."""
        model = ParakeetModel()
        model.load_error = "Test error message"

        status = model.status()

        assert status["load_error"] == "Test error message"


class TestParakeetModel:
    """Test cases for ParakeetModel stub implementation."""

    def test_parakeet_model_initialization(self):
        """Test that ParakeetModel initializes with correct defaults."""
        model = ParakeetModel()

        assert model.model_id == "mlx-community/parakeet-tdt-0.6b-v3"

    def test_parakeet_load_sets_loaded_flag(self):
        """Test that load() sets is_loaded to True."""
        model = ParakeetModel()
        model.is_loaded = False

        model.load()

        assert model.is_loaded is True

    def test_parakeet_unload_clears_loaded_flag(self):
        """Test that unload() sets is_loaded to False."""
        model = ParakeetModel()
        model.is_loaded = True

        model.unload()

        assert model.is_loaded is False

    def test_parakeet_transcribe_returns_stub_data(self):
        """Test that transcribe() returns placeholder data in Phase 1."""
        model = ParakeetModel()

        result = model.transcribe("/path/to/audio.wav", language="en")

        # Verify stub response structure
        assert "text" in result
        assert "segments" in result
        assert "language" in result
        assert "duration" in result

        # Verify language is passed through
        assert result["language"] == "en"

        # Verify segments structure
        assert len(result["segments"]) > 0
        assert "start" in result["segments"][0]
        assert "end" in result["segments"][0]
        assert "text" in result["segments"][0]

    def test_parakeet_transcribe_custom_language(self):
        """Test that transcribe() accepts custom language parameter."""
        model = ParakeetModel()

        result = model.transcribe("/path/to/audio.wav", language="es")

        assert result["language"] == "es"

    def test_parakeet_get_supported_languages_returns_list(self):
        """Test that get_supported_languages() returns list of languages."""
        model = ParakeetModel()

        languages = model.get_supported_languages()

        # Should return list of language codes
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
        assert "es" in languages


class TestPyannoteModel:
    """Test cases for PyannoteModel stub implementation."""

    def test_pyannote_model_initialization(self):
        """Test that PyannoteModel initializes with correct defaults."""
        model = PyannoteModel()

        assert model.model_id == "pyannote/speaker-diarization-3.1"

    def test_pyannote_load_sets_loaded_flag(self):
        """Test that load() sets is_loaded to True."""
        model = PyannoteModel()
        model.is_loaded = False

        model.load()

        assert model.is_loaded is True

    def test_pyannote_unload_clears_loaded_flag(self):
        """Test that unload() sets is_loaded to False."""
        model = PyannoteModel()
        model.is_loaded = True

        model.unload()

        assert model.is_loaded is False

    def test_pyannote_diarize_returns_stub_data(self):
        """Test that diarize() returns placeholder data in Phase 1."""
        model = PyannoteModel()

        result = model.diarize("/path/to/audio.wav")

        # Verify stub response structure
        assert "segments" in result
        assert "speakers" in result
        assert "num_speakers" in result

        # Verify default 2 speakers
        assert result["num_speakers"] == 2

        # Verify segments structure
        assert len(result["segments"]) > 0
        assert "start" in result["segments"][0]
        assert "end" in result["segments"][0]
        assert "speaker" in result["segments"][0]

    def test_pyannote_diarize_respects_num_speakers(self):
        """Test that diarize() uses num_speakers parameter."""
        model = PyannoteModel()

        result = model.diarize("/path/to/audio.wav", num_speakers=3)

        assert result["num_speakers"] == 3
        assert len(result["speakers"]) == 3

    def test_pyannote_diarize_with_speaker_range(self):
        """Test that diarize() accepts min/max speaker parameters."""
        model = PyannoteModel()

        # Should not raise error
        result = model.diarize(
            "/path/to/audio.wav",
            min_speakers=1,
            max_speakers=5
        )

        # Stub should still return data
        assert "num_speakers" in result

    def test_pyannote_verify_token_with_token(self):
        """Test that verify_token() returns True when token exists."""
        # Mock config to have a token
        with patch('video_tools_mcp.models.pyannote.load_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.pyannote.hf_token = "test_token_123"
            mock_config.return_value = mock_cfg

            # Create new instance with mocked config
            PyannoteModel._instances = {}  # Clear singleton
            model = PyannoteModel()

            result = model.verify_token()

            assert result is True

    def test_pyannote_verify_token_without_token(self):
        """Test that verify_token() returns False when token is None."""
        # Mock config to have no token
        with patch('video_tools_mcp.models.pyannote.load_config') as mock_config:
            mock_cfg = MagicMock()
            mock_cfg.pyannote.hf_token = None
            mock_config.return_value = mock_cfg

            # Clear singleton and create new instance
            PyannoteModel._instances = {}
            model = PyannoteModel()

            result = model.verify_token()

            assert result is False


class TestQwenVLModel:
    """Test cases for QwenVLModel stub implementation."""

    def test_qwen_vl_model_initialization(self):
        """Test that QwenVLModel initializes with correct defaults."""
        model = QwenVLModel()

        assert model.model_id == "mlx-community/Qwen2-VL-8B-Instruct-8bit"

    def test_qwen_vl_load_sets_loaded_flag(self):
        """Test that load() sets is_loaded to True."""
        model = QwenVLModel()
        model.is_loaded = False

        model.load()

        assert model.is_loaded is True

    def test_qwen_vl_unload_clears_loaded_flag(self):
        """Test that unload() sets is_loaded to False."""
        model = QwenVLModel()
        model.is_loaded = True

        model.unload()

        assert model.is_loaded is False

    def test_qwen_vl_analyze_frame_returns_stub_data(self):
        """Test that analyze_frame() returns placeholder data in Phase 1."""
        model = QwenVLModel()

        result = model.analyze_frame(
            "/path/to/frame.jpg",
            prompt="Describe this image"
        )

        # Verify stub response structure
        assert "analysis" in result
        assert "confidence" in result
        assert "tokens_used" in result

        # Stub should include prompt in response
        assert "Describe this image" in result["analysis"]

    def test_qwen_vl_analyze_frame_custom_parameters(self):
        """Test that analyze_frame() accepts custom max_tokens and temperature."""
        model = QwenVLModel()

        # Should not raise error
        result = model.analyze_frame(
            "/path/to/frame.jpg",
            prompt="Test prompt",
            max_tokens=1024,
            temperature=0.5
        )

        # Stub should still return data
        assert "analysis" in result

    def test_qwen_vl_analyze_frames_batch_returns_list(self):
        """Test that analyze_frames_batch() returns list of results."""
        model = QwenVLModel()

        image_paths = ["/frame1.jpg", "/frame2.jpg", "/frame3.jpg"]
        results = model.analyze_frames_batch(
            image_paths,
            prompt="Describe the scene"
        )

        # Should return list with same length as input
        assert isinstance(results, list)
        assert len(results) == len(image_paths)

        # Each result should have expected structure
        for result in results:
            assert "analysis" in result
            assert "confidence" in result
            assert "tokens_used" in result

    def test_qwen_vl_get_model_capabilities_returns_dict(self):
        """Test that get_model_capabilities() returns capability info."""
        model = QwenVLModel()

        capabilities = model.get_model_capabilities()

        # Verify expected fields
        assert "max_image_size" in capabilities
        assert "supported_formats" in capabilities
        assert "context_window" in capabilities
        assert "features" in capabilities

        # Verify types
        assert isinstance(capabilities["supported_formats"], list)
        assert isinstance(capabilities["context_window"], int)
        assert isinstance(capabilities["features"], list)


class TestModelManagerProperties:
    """Test cases for ModelManager property accessors."""

    def test_model_id_getter(self):
        """Test that model_id property can be retrieved."""
        model = ParakeetModel()
        model._model_id = "test-model-id"

        assert model.model_id == "test-model-id"

    def test_model_id_setter(self):
        """Test that model_id property can be set."""
        model = ParakeetModel()

        model.model_id = "new-model-id"

        assert model._model_id == "new-model-id"

    def test_is_loaded_getter(self):
        """Test that is_loaded property can be retrieved."""
        model = ParakeetModel()
        model._is_loaded = True

        assert model.is_loaded is True

    def test_is_loaded_setter(self):
        """Test that is_loaded property can be set."""
        model = ParakeetModel()

        model.is_loaded = False

        assert model._is_loaded is False

    def test_load_error_getter(self):
        """Test that load_error property can be retrieved."""
        model = ParakeetModel()
        model._load_error = "Test error"

        assert model.load_error == "Test error"

    def test_load_error_setter(self):
        """Test that load_error property can be set."""
        model = ParakeetModel()

        model.load_error = "New error"

        assert model._load_error == "New error"
