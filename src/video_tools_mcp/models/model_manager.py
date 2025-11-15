"""Abstract base class for managing ML model lifecycle."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ModelManager(ABC):
    """
    Abstract base class for ML model managers.

    Implements singleton pattern to ensure only one instance per model type.
    Manages model lifecycle: loading, unloading, and status tracking.
    """

    # Class-level dictionary to store instances (one per subclass)
    _instances: Dict[type, 'ModelManager'] = {}

    def __new__(cls):
        """Implement singleton pattern - one instance per model class."""
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
            # Initialize state tracking variables
            instance._is_loaded = False
            instance._load_error: Optional[str] = None
            instance._model_id: str = ""
        return cls._instances[cls]

    @property
    def model_id(self) -> str:
        """Get the model identifier."""
        return self._model_id

    @model_id.setter
    def model_id(self, value: str) -> None:
        """Set the model identifier."""
        self._model_id = value

    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded in memory."""
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool) -> None:
        """Set the loaded state."""
        self._is_loaded = value

    @property
    def load_error(self) -> Optional[str]:
        """Get the last load error message, if any."""
        return self._load_error

    @load_error.setter
    def load_error(self, value: Optional[str]) -> None:
        """Set the load error message."""
        self._load_error = value

    @abstractmethod
    def load(self) -> None:
        """
        Load the model into memory.

        Raises:
            Exception: If model loading fails
        """
        pass

    @abstractmethod
    def unload(self) -> None:
        """
        Unload the model from memory to free resources.
        """
        pass

    def status(self) -> Dict[str, Any]:
        """
        Get current model status.

        Returns:
            Dict containing:
                - model_id: The model identifier
                - is_loaded: Whether model is loaded
                - load_error: Error message if loading failed (or None)
        """
        return {
            "model_id": self.model_id,
            "is_loaded": self.is_loaded,
            "load_error": self.load_error
        }

    def ensure_loaded(self) -> None:
        """
        Ensure model is loaded. Load if not already loaded.

        Convenience method that safely loads the model if needed.
        Handles errors gracefully and updates load_error property.
        """
        if self.is_loaded:
            logger.debug(f"Model {self.model_id} already loaded")
            return

        try:
            logger.info(f"Loading model {self.model_id}...")
            self.load()
            self.load_error = None
            logger.info(f"Model {self.model_id} loaded successfully")
        except Exception as e:
            error_msg = f"Failed to load model {self.model_id}: {str(e)}"
            logger.error(error_msg)
            self.load_error = error_msg
            self.is_loaded = False
            raise
