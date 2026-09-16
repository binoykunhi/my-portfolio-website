import os
import time
import tempfile
import numpy as np
import scipy.io.wavfile as wav
from openai import OpenAI
from typing import Generator, Optional

class WhisperClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def _save_to_temp_wav(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        # Normalize float32 audio to int16 if needed, or just save
        if audio_data.dtype == np.float32:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav.write(f.name, sample_rate, audio_data)
            return f.name

    def transcribe_batch(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        temp_file = self._save_to_temp_wav(audio_data, sample_rate)
        try:
            with open(temp_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            return transcript.text
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def transcribe_stream(self, audio_generator: Generator[np.ndarray, None, None], sample_rate: int = 16000) -> Generator[str, None, None]:
        """
        Simulates streaming by accumulating audio and transcribing periodically.
        In a real production app, you'd use a websocket-based streaming STT (like Deepgram or Google).
        Here we accumulate chunks and send to Whisper every X seconds or when silence is detected.
        """
        buffer = []
        buffer_duration = 0.0
        chunk_duration_threshold = 1.0  # Transcribe every 1 second of new audio

        for chunk in audio_generator:
            buffer.append(chunk)
            chunk_len_sec = len(chunk) / sample_rate
            buffer_duration += chunk_len_sec

            if buffer_duration >= chunk_duration_threshold:
                # Transcribe what we have so far
                full_audio = np.concatenate(buffer)
                # We can't easily do partial updates with standard Whisper API without re-sending everything
                # For this playground, we will just yield the *current full transcript* 
                # (re-transcribing the growing buffer is inefficient but correct for "streaming" simulation)
                
                # Optimization: In a real app, we'd use a sliding window or a real streaming API.
                # Here, to keep it responsive but not burn too many tokens/requests, we might only do it 
                # if we have enough new data.
                
                try:
                    text = self.transcribe_batch(full_audio, sample_rate)
                    yield text
                except Exception as e:
                    print(f"Streaming STT error: {e}")
                
                # Reset duration counter to throttle, but keep buffer to build context
                # Actually, if we reset buffer, we lose context. 
                # If we keep buffer, it gets slower. 
                # Let's keep it simple: Re-transcribe full buffer every 1s.
                buffer_duration = 0.0
        
        # Final transcription
        if buffer:
            full_audio = np.concatenate(buffer)
            yield self.transcribe_batch(full_audio, sample_rate)
