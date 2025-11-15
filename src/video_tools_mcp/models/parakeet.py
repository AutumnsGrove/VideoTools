"""Parakeet MLX model for speech transcription."""

import mlx.core as mx
from parakeet_mlx import from_pretrained, ParakeetTDT
from parakeet_mlx.audio import load_audio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from video_tools_mcp.models.model_manager import ModelManager
from video_tools_mcp.config import load_config

logger = logging.getLogger(__name__)


class ParakeetModel(ModelManager):
    """
    Parakeet MLX model for speech transcription.

    Model: mlx-community/parakeet-tdt-0.6b-v3
    Purpose: Fast on-device speech-to-text using Apple Silicon MLX
    """

    def __init__(self):
        """Initialize Parakeet model configuration."""
        super().__init__()

        # Load configuration
        config = load_config()
        self.model_id = config.parakeet.model_id
        self._model = None
        self._processor = None

        # Audio processing settings from config
        self.chunk_duration = config.parakeet.chunk_duration
        self.overlap_duration = config.parakeet.overlap_duration

        logger.debug(f"Initialized ParakeetModel with id: {self.model_id}")

    def load(self) -> None:
        """Load Parakeet model using MLX."""
        if self._is_loaded:
            logger.info(f"Parakeet model already loaded")
            return

        try:
            logger.info(f"Loading Parakeet model: {self.model_id}")

            # Load model using from_pretrained
            self._model = from_pretrained(self.model_id)

            self._is_loaded = True
            self._load_error = None
            logger.info(f"✓ Parakeet model loaded successfully")

        except Exception as e:
            self._is_loaded = False
            self._load_error = str(e)
            logger.error(f"Failed to load Parakeet model: {e}")
            raise

    def unload(self) -> None:
        """Unload model from memory."""
        if not self._is_loaded:
            logger.info("Parakeet model not loaded, nothing to unload")
            return

        logger.info("Unloading Parakeet model")
        self._model = None
        self._processor = None
        self._is_loaded = False
        logger.info("✓ Parakeet model unloaded")

    def transcribe(
        self,
        audio_path: str,
        language: str = "en",
        return_timestamps: bool = True
    ) -> Dict[str, Any]:
        """Transcribe audio file using Parakeet MLX.

        Args:
            audio_path: Path to audio file (WAV, 16kHz mono preferred)
            language: Language code (default: "en")
            return_timestamps: Include word-level timestamps (default: True)

        Returns:
            Dict with:
                - text: Full transcription text
                - segments: List of segments with timestamps
                - language: Language used
                - duration: Audio duration in seconds
        """
        self.ensure_loaded()

        try:
            logger.info(f"Transcribing audio: {audio_path}")

            # Load audio file
            audio_data, sample_rate = load_audio(audio_path)
            logger.debug(f"Audio loaded: {len(audio_data)} samples at {sample_rate}Hz")

            # Run transcription
            result = self._model.transcribe(
                audio_data,
                language=language
            )

            # Extract text and segments
            full_text = result.text if hasattr(result, 'text') else str(result)

            # Build segments list
            segments = []
            if hasattr(result, 'segments') and result.segments:
                for seg in result.segments:
                    segments.append({
                        "start": getattr(seg, 'start', 0.0),
                        "end": getattr(seg, 'end', 0.0),
                        "text": getattr(seg, 'text', ''),
                        "confidence": getattr(seg, 'confidence', 1.0)
                    })
            elif hasattr(result, 'words') and result.words:
                # If we have word-level timestamps
                for word in result.words:
                    segments.append({
                        "start": getattr(word, 'start', 0.0),
                        "end": getattr(word, 'end', 0.0),
                        "text": getattr(word, 'word', ''),
                        "confidence": getattr(word, 'confidence', 1.0)
                    })
            else:
                # No timestamps, create single segment
                segments.append({
                    "start": 0.0,
                    "end": len(audio_data) / sample_rate,
                    "text": full_text,
                    "confidence": 1.0
                })

            duration = len(audio_data) / sample_rate

            logger.info(f"Transcription complete: {len(segments)} segments, {len(full_text)} chars")

            return {
                "text": full_text,
                "segments": segments,
                "language": language,
                "duration": duration
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages.

        Phase 1: STUB - Returns common languages
        Phase 2: TODO - Return actual model capabilities

        Returns:
            List of language codes
        """
        logger.info("[STUB Phase 1] get_supported_languages() stub")

        # TODO Phase 2: Return actual model language support
        # return self._model.supported_languages

        # Phase 1: Common languages placeholder
        return ["en", "es", "fr", "de", "it", "pt", "pl", "ru", "zh", "ja", "ko"]
