#!/usr/bin/env python3
"""
End-to-end test for Google ASR providers using the API server
Tests all three Google providers with a test audio file
"""
import os
import sys
import requests
import json
from pathlib import Path

# Configuration
API_URL = "http://localhost:5000"
TEST_AUDIO = "test.mp3"

def test_google_providers():
    """Test all Google ASR providers through the API"""
    
    print("=" * 70)
    print("Google ASR End-to-End Test")
    print("=" * 70)
    
    # Check if API is running
    print("\n1. Checking API Server...")
    print("-" * 70)
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server is running")
        else:
            print("❌ API Server returned unexpected status:", response.status_code)
            return
    except requests.exceptions.ConnectionError:
        print("❌ API Server is not running!")
        print("   Please start it with: ./start_experiments.sh")
        return
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return
    
    # Check if test audio exists
    print("\n2. Checking Test Audio File...")
    print("-" * 70)
    if not os.path.exists(TEST_AUDIO):
        print(f"❌ Test audio file '{TEST_AUDIO}' not found")
        print("   Creating a dummy audio file...")
        # Create a minimal valid MP3 file
        os.system("python3 create_dummy_audio.py")
        if not os.path.exists(TEST_AUDIO):
            print("❌ Failed to create test audio")
            return
    print(f"✅ Test audio file found: {TEST_AUDIO}")
    
    # Test each Google provider
    providers_to_test = [
        ("google-v1", "Google V1"),
        ("google-v2-chirp2", "Google V2 Chirp 2"),
        ("google-v2-chirp3", "Google V2 Chirp 3")
    ]
    
    print("\n3. Testing Google ASR Providers...")
    print("-" * 70)
    
    for provider_key, provider_name in providers_to_test:
        print(f"\nTesting {provider_name}...")
        
        try:
            with open(TEST_AUDIO, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {'providers': json.dumps([provider_key])}
                
                response = requests.post(
                    f"{API_URL}/api/asr/benchmark",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'results' in result and len(result['results']) > 0:
                        provider_result = result['results'][0]
                        transcript = provider_result.get('transcript', '')
                        latency = provider_result.get('latency', 0)
                        
                        if transcript.startswith("ERROR:"):
                            print(f"  ❌ {provider_name}: {transcript}")
                        else:
                            print(f"  ✅ {provider_name}: Success")
                            print(f"     Transcript: {transcript[:100]}...")
                            print(f"     Latency: {latency:.2f}s")
                    else:
                        print(f"  ⚠️  {provider_name}: No results returned")
                else:
                    print(f"  ❌ {provider_name}: API returned status {response.status_code}")
                    print(f"     Error: {response.text}")
        
        except requests.exceptions.Timeout:
            print(f"  ⚠️  {provider_name}: Request timed out (may still be processing)")
        except Exception as e:
            print(f"  ❌ {provider_name}: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
    print("\nNote: If you see timeout errors, the providers may still be working")
    print("but taking longer than expected. Check the API server logs for details.")

if __name__ == "__main__":
    test_google_providers()
