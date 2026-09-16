import os
import time
import assemblyai as aai
from stt_benchmark.providers.base import STTProvider
from stt_benchmark.config import ASSEMBLYAI_API_KEY

class AssemblyAIProvider(STTProvider):
    def __init__(self):
        if not ASSEMBLYAI_API_KEY:
            raise ValueError("ASSEMBLYAI_API_KEY is not set")
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        self.transcriber = aai.Transcriber()

    def transcribe(self, audio_path: str, model: str = None) -> tuple[str, float, dict]:
        # Get audio duration
        from stt_benchmark.utils.audio_utils import get_audio_duration
        audio_duration = get_audio_duration(audio_path)

        # 1. Upload phase
        t_upload_start = time.time()
        upload_url = self.transcriber.upload_file(audio_path)
        t_upload_end = time.time()
        upload_time = t_upload_end - t_upload_start

        # 2. Transcription phase (Engine Latency)
        t_stt_start = time.time()
        config = aai.TranscriptionConfig(speech_model=model) if model else None
        
        # Create a new transcriber instance to ensure clean state if needed, 
        # though reusing self.transcriber is usually fine. 
        # We use the URL from the upload step.
        transcript = self.transcriber.transcribe(upload_url, config=config)
        t_stt_end = time.time()
        
        stt_latency = t_stt_end - t_stt_start
        total_pipeline_time = t_stt_end - t_upload_start

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(transcript.error)

        # Build timing info
        timing_info = {
            "provider": "assemblyai",
            "model": model or "default",
            "audio_duration_sec": audio_duration,
            "upload_time_sec": round(upload_time, 3),
            "stt_latency_sec": round(stt_latency, 3),
            "total_pipeline_time_sec": round(total_pipeline_time, 3),
            "timestamps": {
                "upload_start": t_upload_start,
                "upload_end": t_upload_end,
                "stt_call_start": t_stt_start,
                "stt_call_end": t_stt_end
            }
        }
        
        import json
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"AssemblyAI latency breakdown: {json.dumps(timing_info)}")
            
        return transcript.text, stt_latency, timing_info
