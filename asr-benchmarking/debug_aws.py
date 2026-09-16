import boto3
from botocore.exceptions import ClientError
import ssl

print(f"SSL version: {ssl.OPENSSL_VERSION}")

from dotenv import load_dotenv
import os

load_dotenv()

print(f"AWS_ACCESS_KEY_ID present: {bool(os.getenv('AWS_ACCESS_KEY_ID'))}")
print(f"AWS_REGION: {os.getenv('AWS_REGION')}")

try:
    # Test S3
    s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    print("Listing S3 buckets...")
    s3.list_buckets()
    print("S3 connection successful")
    
    # Test Transcribe
    transcribe = boto3.client('transcribe', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    print("Checking Transcribe...")
    transcribe.list_transcription_jobs(MaxResults=1)
    print("Transcribe connection successful")

except Exception as e:
    print(f"AWS Error: {e}")
