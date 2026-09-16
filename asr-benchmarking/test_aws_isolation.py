import os
import sys
import logging
import traceback
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

# Add parent dir to path so we can import stt_benchmark
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from stt_benchmark.providers.aws_stt import AWSTranscribeProvider
    from stt_benchmark.config import AWS_REGION, S3_BUCKET_NAME

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    print("=== AWS Configuration Check ===")
    print(f"AWS_ACCESS_KEY_ID: {'*' * 4 + AWS_ACCESS_KEY_ID[-4:] if AWS_ACCESS_KEY_ID else 'None'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'Set' if AWS_SECRET_ACCESS_KEY else 'None'}")
    print(f"AWS_REGION: {AWS_REGION}")
    print(f"S3_BUCKET_NAME: {S3_BUCKET_NAME}")
    print("===============================")

    print("\nInitializing AWS Provider...")
    provider = AWSTranscribeProvider()
    
    audio_file = "test.wav"
    if not os.path.exists(audio_file):
        print(f"Error: {audio_file} not found.")
        sys.exit(1)
        
    print(f"\nStarting transcription of {audio_file}...")
    transcript, latency, timing = provider.transcribe(audio_file, file_format='wav')
    
    print("\n=== Success! ===")
    print(f"Transcript: {transcript[:100]}...")
    print(f"Latency: {latency}s")
    print(f"Timing Info: {timing}")

except Exception as e:
    print("\n=== AWS Test Failed ===")
    print(f"Error: {str(e)}")
    traceback.print_exc()
