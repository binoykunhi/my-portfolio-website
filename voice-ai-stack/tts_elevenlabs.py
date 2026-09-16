from elevenlabs import ElevenLabs, save
from typing import Generator, Iterator, Union
import numpy as np
import io

class TTSClient:
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
        # Use a standard voice ID, e.g., "Rachel"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM" 

    def synthesize_batch(self, text: str) -> bytes:
        audio = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id="eleven_turbo_v2",
            output_format="pcm_16000"
        )
        # audio is a generator of bytes, we need to consume it for batch
        return b"".join(audio)

    def synthesize_stream(self, text_iterator: Iterator[str]) -> Generator[bytes, None, None]:
        """
        Consumes a text iterator (yielding tokens/chunks), buffers them into sentences,
        and calls the API for each sentence to achieve streaming.
        """
        buffer = ""
        print("DEBUG: TTS synthesize_stream started")
        for token in text_iterator:
            buffer += token
            # Simple heuristic for sentence boundary: punctuation + space or newline
            if any(punct in token for punct in [".", "?", "!", "\n"]):
                # Check if we have a substantial chunk (avoid sending just ".")
                if len(buffer.strip()) > 2:
                    print(f"DEBUG: TTS flushing sentence: '{buffer.strip()[:20]}...'")
                    yield from self._stream_text_chunk(buffer)
                    buffer = ""
        
        # Process remaining buffer
        if buffer.strip():
            print(f"DEBUG: TTS flushing remaining buffer: '{buffer.strip()[:20]}...'")
            yield from self._stream_text_chunk(buffer)
        print("DEBUG: TTS synthesize_stream finished")

    def _stream_text_chunk(self, text: str) -> Generator[bytes, None, None]:
        print(f"DEBUG: TTS calling ElevenLabs API for: '{text[:10]}...'")
        try:
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id="eleven_turbo_v2",
                output_format="pcm_16000"
            )
            chunk_count = 0
            for chunk in audio_stream:
                if chunk:
                    chunk_count += 1
                    yield chunk
            print(f"DEBUG: TTS received {chunk_count} chunks for sentence.")
        except Exception as e:
            print(f"TTS Error for chunk '{text[:20]}...': {e}")
