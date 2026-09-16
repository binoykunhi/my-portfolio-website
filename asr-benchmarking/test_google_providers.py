#!/usr/bin/env python3
"""
Test script to verify Google ASR providers can be initialized correctly
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Google ASR Provider Configuration Test")
print("=" * 60)

# Check environment variables
print("\n1. Checking Environment Variables:")
print("-" * 60)

google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
google_project = os.getenv("GOOGLE_CLOUD_PROJECT")
gcs_bucket = os.getenv("GCS_BUCKET_NAME")

print(f"GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
print(f"  - File exists: {os.path.exists(google_creds) if google_creds else False}")
print(f"GOOGLE_CLOUD_PROJECT: {google_project}")
print(f"GCS_BUCKET_NAME: {gcs_bucket}")

# Test Google V1 Provider
print("\n2. Testing Google V1 Provider:")
print("-" * 60)
try:
    from stt_benchmark.providers.google_stt import GoogleV1Provider
    provider_v1 = GoogleV1Provider()
    print("✅ Google V1 Provider initialized successfully")
except Exception as e:
    print(f"❌ Google V1 Provider failed: {str(e)}")

# Test Google V2 Provider
print("\n3. Testing Google V2 Provider:")
print("-" * 60)
try:
    from stt_benchmark.providers.google_stt import GoogleV2Provider
    provider_v2 = GoogleV2Provider()
    print("✅ Google V2 Provider initialized successfully")
    print(f"   Project ID: {provider_v2.project_id}")
except Exception as e:
    print(f"❌ Google V2 Provider failed: {str(e)}")

# Test GCS Upload
print("\n4. Testing GCS Bucket Access:")
print("-" * 60)
try:
    from google.cloud import storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket)
    
    # Check if bucket exists
    if bucket.exists():
        print(f"✅ GCS Bucket '{gcs_bucket}' is accessible")
    else:
        print(f"⚠️  GCS Bucket '{gcs_bucket}' does not exist")
        print("   You may need to create it in Google Cloud Console")
except Exception as e:
    print(f"❌ GCS Bucket access failed: {str(e)}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
