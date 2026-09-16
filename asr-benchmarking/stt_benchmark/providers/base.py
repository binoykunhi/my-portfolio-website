from abc import ABC, abstractmethod

class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    def transcribe(self, audio_path: str, model: str = None) -> tuple[str, float]:
        """
        Transcribe the given audio file.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            str: The transcribed text.
        """
        pass
