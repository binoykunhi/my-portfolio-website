import os
import time
from deepgram import DeepgramClient
from stt_benchmark.providers.base import STTProvider
from stt_benchmark.config import DEEPGRAM_API_KEY

class DeepgramProvider(STTProvider):
    def __init__(self):
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is not set")
        self.client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    def transcribe(self, audio_path: str, model: str = "nova-2") -> tuple[str, float, dict]:
        # Get audio duration
        from stt_benchmark.utils.audio_utils import get_audio_duration
        audio_duration = get_audio_duration(audio_path)

        with open(audio_path, "rb") as audio_file:
            buffer_data = audio_file.read()

        start_time = time.time()
        response = self.client.listen.v1.media.transcribe_file(
            request=buffer_data, 
            model=model, 
            smart_format=True
        )
        end_time = time.time()
        
        stt_latency = end_time - start_time
        
        # Build timing info
        timing_info = {
            "provider": "deepgram",
            "model": model or "nova-2",
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
        logger.info(f"Deepgram latency breakdown: {json.dumps(timing_info)}")
        
        return response.results.channels[0].alternatives[0].transcript, stt_latency, timing_info
