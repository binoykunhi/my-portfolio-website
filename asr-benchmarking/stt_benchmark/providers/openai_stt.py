import os
import time
from openai import OpenAI
from stt_benchmark.providers.base import STTProvider
from stt_benchmark.config import OPENAI_API_KEY

class OpenAIProvider(STTProvider):
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def transcribe(self, audio_path: str, model: str = "whisper-1") -> tuple[str, float, dict]:
        # Get audio duration
        from stt_benchmark.utils.audio_utils import get_audio_duration
        audio_duration = get_audio_duration(audio_path)

        start_time = time.time()
        with open(audio_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                model=model or "whisper-1", 
                file=audio_file
            )
        end_time = time.time()
        
        stt_latency = end_time - start_time
        
        # Build timing info
        timing_info = {
            "provider": "openai",
            "model": model or "whisper-1",
            "audio_duration_sec": audio_duration,
            "upload_time_sec": 0, # Direct API call
            "stt_latency_sec": round(stt_latency, 3),
            "total_pipeline_time_sec": round(stt_latency, 3),
            "timestamps": {
                "stt_call_start": start_time,
                "stt_call_end": end_time
            }
        }
        
        import json
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OpenAI latency breakdown: {json.dumps(timing_info)}")
        
        return transcription.text, stt_latency, timing_info
