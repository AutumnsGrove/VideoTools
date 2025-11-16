"""Pyannote model for speaker diarization."""

import gc
import logging
import os
import torch
from typing import Dict, Any, Optional
from video_tools_mcp.models.model_manager import ModelManager
from video_tools_mcp.config import load_config

logger = logging.getLogger(__name__)


class PyannoteModel(ModelManager):
    """
    Pyannote model for speaker diarization.

    Model: pyannote/speaker-diarization-3.1
    Purpose: Identify "who spoke when" in audio recordings
    Requires: HuggingFace token with pyannote model access

    Note: Requires accepting the model's user agreement on HuggingFace
    """

    def __init__(self):
        """Initialize Pyannote model configuration."""
        super().__init__()
        self.model_id = "pyannote/speaker-diarization-3.1"
        self._pipeline = None

        # Load configuration
        config = load_config()
        self._model_config = config.pyannote

        # Get HuggingFace token from config
        self._hf_token = config.pyannote.hf_token
        if not self._hf_token:
            logger.warning("No HuggingFace token found in config. Pyannote requires authentication.")

        logger.debug(f"Initialized PyannoteModel with id: {self.model_id}")

    def load(self) -> None:
        """
        Load Pyannote diarization pipeline.

        Validates HuggingFace token, loads the pipeline, and configures device.

        Raises:
            ValueError: If HuggingFace token is missing
        """
        if self.is_loaded:
            return

        logger.info(f"Loading Pyannote model: {self.model_id}")

        from pyannote.audio import Pipeline
        import json
        from pathlib import Path

        # Load HF token from secrets.json, environment, or config (in that order)
        hf_token = None

        # 1. Try secrets.json first (project root)
        secrets_path = Path(__file__).parent.parent.parent.parent / "secrets.json"
        if secrets_path.exists():
            try:
                with open(secrets_path) as f:
                    secrets = json.load(f)
                    hf_token = secrets.get("hf_token")
                    if hf_token and hf_token != "PASTE_YOUR_HUGGINGFACE_TOKEN_HERE":
                        logger.info("Using HF token from secrets.json")
            except Exception as e:
                logger.warning(f"Failed to load secrets.json: {e}")

        # 2. Fallback to environment variable
        if not hf_token:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                logger.info("Using HF token from environment variable")

        # 3. Final fallback to config
        if not hf_token:
            hf_token = self._hf_token
            if hf_token:
                logger.info("Using HF token from config")

        if not hf_token:
            raise ValueError(
                "HuggingFace token required for Pyannote. Please either:\n"
                "1. Add 'hf_token' to secrets.json in project root, OR\n"
                "2. Set HF_TOKEN environment variable, OR\n"
                "3. Add hf_token to config/models.json"
            )

        # Load pipeline with token (newer pyannote uses 'token' not 'use_auth_token')
        self._pipeline = Pipeline.from_pretrained(
            self.model_id,
            token=hf_token
        )

        # Set device (mps for Apple Silicon, cuda for NVIDIA, cpu fallback)
        device = self._model_config.device
        self._pipeline.to(torch.device(device))

        self.is_loaded = True
        logger.info(f"Pyannote model loaded successfully on device: {device}")

    def unload(self) -> None:
        """Unload model and free memory."""
        if not self.is_loaded:
            return

        logger.info("Unloading Pyannote model")
        self._pipeline = None

        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()

        gc.collect()
        self.is_loaded = False
        logger.info("Pyannote model unloaded successfully")

    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform speaker diarization on audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers

        Returns:
            Dict containing:
                - segments: List of speaker segments with timestamps
                - speakers: List of unique speaker IDs
                - num_speakers: Total number of speakers detected

        Example result:
            {
                "segments": [
                    {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"},
                    {"start": 2.7, "end": 5.2, "speaker": "SPEAKER_01"}
                ],
                "speakers": ["SPEAKER_00", "SPEAKER_01"],
                "num_speakers": 2
            }
        """
        self.ensure_loaded()

        logger.info(f"Performing diarization on: {audio_path}")

        # Pre-load audio using soundfile to avoid torchcodec dependency
        # Pyannote accepts audio as {'waveform': tensor, 'sample_rate': int}
        import soundfile as sf
        import numpy as np

        # Load audio with soundfile (returns numpy array)
        audio_data, sample_rate = sf.read(audio_path)

        # Convert to torch tensor and ensure shape is (channels, samples)
        waveform = torch.from_numpy(audio_data).float()
        if waveform.ndim == 1:
            # Mono audio - add channel dimension
            waveform = waveform.unsqueeze(0)
        else:
            # Stereo/multi-channel - transpose to (channels, samples)
            waveform = waveform.T

        audio_dict = {
            "waveform": waveform,
            "sample_rate": sample_rate
        }

        # Run diarization with pre-loaded audio
        diarization = self._pipeline(
            audio_dict,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )

        # Convert pyannote 4.0 output to our format
        # Pyannote 4.0 returns DiarizeOutput object with serialize() method
        serialized = diarization.serialize()

        # Use 'diarization' key (non-overlapping segments)
        segments = serialized.get('diarization', [])

        # Extract unique speakers
        speakers = set(seg['speaker'] for seg in segments)

        result = {
            "segments": segments,  # Already in correct format with start, end, speaker
            "speakers": sorted(list(speakers)),
            "num_speakers": len(speakers)
        }

        logger.info(f"Diarization complete: {result['num_speakers']} speakers, {len(segments)} segments")
        return result

    def verify_token(self) -> bool:
        """
        Verify HuggingFace token is available.

        Returns:
            True if token is available, False otherwise
        """
        token = os.getenv("HF_TOKEN") or self._hf_token
        if not token:
            logger.warning("HF_TOKEN not found in environment variables or config")
            return False
        return True
