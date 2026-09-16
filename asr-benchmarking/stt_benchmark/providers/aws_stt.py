
import time
import boto3
import requests
import uuid
import json
import logging
from stt_benchmark.providers.base import STTProvider
from stt_benchmark.utils.storage import upload_to_s3
from stt_benchmark.utils.audio_utils import get_audio_duration
from stt_benchmark.config import S3_BUCKET_NAME, AWS_REGION

logger = logging.getLogger(__name__)

class AWSTranscribeProvider(STTProvider):
    def __init__(self):
        self.client = boto3.client('transcribe', region_name=AWS_REGION)

    def transcribe(self, audio_path: str, model: str = None, file_format: str = 'mp3') -> tuple[str, float, dict]:
        if not S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME not set")

        # Get audio duration for logging
        audio_duration = get_audio_duration(audio_path)

        job_name = f"transcribe-job-{uuid.uuid4()}"
        
        # Upload phase (NOT counted in STT latency)
        t_upload_start = time.time()
        s3_uri = upload_to_s3(S3_BUCKET_NAME, audio_path)
        t_upload_end = time.time()
        upload_time = t_upload_end - t_upload_start
        
        # STT call phase (START latency measurement AFTER upload)
        t_stt_call_start = time.time()
        
        self.client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat=file_format,
            LanguageCode='en-US'
        )

        while True:
            status = self.client.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)

        t_stt_call_end = time.time()
        # END latency measurement
        
        stt_latency = t_stt_call_end - t_stt_call_start
        total_pipeline_time = t_stt_call_end - t_upload_start

        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            # Use requests to fetch the transcript, as it handles SSL certificates better than urllib
            response = requests.get(transcript_uri)
            response.raise_for_status()
            data = response.json()
            
            # Calculate latency from server-side timestamps if available
            job = status['TranscriptionJob']
            server_stt_latency = None
            if 'StartTime' in job and 'CompletionTime' in job:
                server_stt_latency = (job['CompletionTime'] - job['StartTime']).total_seconds()
                # Prefer server-side timing if available
                stt_latency = server_stt_latency
            
            # Build timing info for logging
            timing_info = {
                "provider": "aws_transcribe",
                "model": model or "default",
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
            
            if server_stt_latency is not None:
                timing_info["server_stt_latency_sec"] = round(server_stt_latency, 3)
            
            logger.info(f"AWS Transcribe latency breakdown: {json.dumps(timing_info)}")
                
            return data['results']['transcripts'][0]['transcript'], stt_latency, timing_info
        else:
            raise Exception(f"AWS Transcribe failed: {status['TranscriptionJob']['FailureReason']}")

