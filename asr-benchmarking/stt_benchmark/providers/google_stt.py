import os
import time
import json
import logging
from google.cloud import speech
from google.cloud import speech_v2
from stt_benchmark.providers.base import STTProvider
from stt_benchmark.utils.storage import upload_to_gcs
from stt_benchmark.utils.audio_utils import get_audio_duration
from stt_benchmark.config import GCS_BUCKET_NAME

logger = logging.getLogger(__name__)

class GoogleV1Provider(STTProvider):
    def __init__(self):
        # Check for required environment variables
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Please set it to the path of your Google Cloud service account JSON key file.")
        if not GCS_BUCKET_NAME:
            raise ValueError("GCS_BUCKET_NAME not set in config. Google providers require a GCS bucket for audio storage.")
        
        try:
            self.client = speech.SpeechClient()
        except Exception as e:
            raise ValueError(f"Failed to initialize Google V1 client: {str(e)}. Check your credentials and project setup.")

    def transcribe(self, audio_path: str, model: str = "default") -> tuple[str, float, dict]:
        # Get audio duration for logging
        audio_duration = get_audio_duration(audio_path)
        
        # Upload phase (NOT counted in STT latency)
        t_upload_start = time.time()
        gcs_uri = upload_to_gcs(GCS_BUCKET_NAME, audio_path, os.path.basename(audio_path))
        t_upload_end = time.time()
        upload_time = t_upload_end - t_upload_start
        
        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3, # Assuming MP3 for now, should detect
            sample_rate_hertz=16000,
            language_code="en-US",
            model=model
        )

        # STT call phase (START latency measurement AFTER upload)
        t_stt_call_start = time.time()
        operation = self.client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=300)
        t_stt_call_end = time.time()
        # END latency measurement
        
        stt_latency = t_stt_call_end - t_stt_call_start
        total_pipeline_time = t_stt_call_end - t_upload_start

        # Build timing info for logging
        timing_info = {
            "provider": "google_v1",
            "model": model,
            "audio_duration_sec": audio_duration,
            "upload_time_sec": round(upload_time, 3),
            "stt_latency_sec": round(stt_latency, 3),
            "total_pipeline_time_sec": round(total_pipeline_time, 3),
            "timestamps": {
                "upload_start": t_upload_start,
                "upload_end": t_upload_end,
                "stt_call_start": t_stt_call_start,
                "stt_call_end": t_stt_call_end
            }
        }
        
        logger.info(f"Google V1 latency breakdown: {json.dumps(timing_info)}")

        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        return transcript.strip(), stt_latency, timing_info

class GoogleV2Provider(STTProvider):
    def __init__(self):
        # Check for required environment variables
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set. Please set it to the path of your Google Cloud service account JSON key file.")
        if not GCS_BUCKET_NAME:
            raise ValueError("GCS_BUCKET_NAME not set in config. Google providers require a GCS bucket for audio storage.")
        
        try:
            self.client = speech_v2.SpeechClient()
            # V2 requires project ID in the parent path
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not self.project_id:
                # Try to get from default credentials
                import google.auth
                _, self.project_id = google.auth.default()
            if not self.project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set and could not be inferred from credentials.")
        except Exception as e:
            raise ValueError(f"Failed to initialize Google V2 client: {str(e)}. Check your credentials and project setup.")

    def transcribe(self, audio_path: str, model: str = "chirp") -> tuple[str, float, dict]:
        # Get audio duration for logging
        audio_duration = get_audio_duration(audio_path)
        
        # Upload phase (NOT counted in STT latency)
        t_upload_start = time.time()
        gcs_uri = upload_to_gcs(GCS_BUCKET_NAME, audio_path, os.path.basename(audio_path))
        t_upload_end = time.time()
        upload_time = t_upload_end - t_upload_start
        
        # Chirp models require specific regions.
        if model in ["chirp", "chirp2", "chirp3"]:
            location = "us-central1"
            api_endpoint = f"{location}-speech.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}
            client = speech_v2.SpeechClient(client_options=client_options)
            
            # Map user-friendly names to actual model IDs
            if model in ["chirp2", "chirp3"]:
                # Fallback to 'chirp' as 'chirp-2' is not available/found in this project/region
                model_id = "chirp" 
            else:
                model_id = model
        else:
            location = "global"
            client = self.client
            model_id = model
        
        request = speech_v2.BatchRecognizeRequest(
            recognizer=f"projects/{self.project_id}/locations/{location}/recognizers/_",
            config=speech_v2.RecognitionConfig(
                auto_decoding_config=speech_v2.AutoDetectDecodingConfig(),
                language_codes=["en-US"],
                model=model_id,
            ),
            files=[speech_v2.BatchRecognizeFileMetadata(uri=gcs_uri)],
            recognition_output_config=speech_v2.RecognitionOutputConfig(
                inline_response_config=speech_v2.InlineOutputConfig()
            )
        )

        # STT call phase (START latency measurement AFTER upload)
        t_stt_call_start = time.time()
        operation = client.batch_recognize(request=request)
        response = operation.result(timeout=300)
        t_stt_call_end = time.time()
        # END latency measurement
        
        stt_latency = t_stt_call_end - t_stt_call_start
        total_pipeline_time = t_stt_call_end - t_upload_start

        # Build timing info for logging
        timing_info = {
            "provider": "google_v2",
            "model": model,
            "audio_duration_sec": audio_duration,
            "upload_time_sec": round(upload_time, 3),
            "stt_latency_sec": round(stt_latency, 3),
            "total_pipeline_time_sec": round(total_pipeline_time, 3),
            "timestamps": {
                "upload_start": t_upload_start,
                "upload_end": t_upload_end,
                "stt_call_start": t_stt_call_start,
                "stt_call_end": t_stt_call_end
            }
        }
        
        logger.info(f"Google V2 ({model}) latency breakdown: {json.dumps(timing_info)}")

        # Process results
        transcript = ""
        for result in response.results[gcs_uri].transcript.results:
             transcript += result.alternatives[0].transcript + " "
        
        return transcript.strip(), stt_latency, timing_info
