import os
import sys
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

load_dotenv()

from stt_benchmark.providers.assemblyai_stt import AssemblyAIProvider
from stt_benchmark.providers.google_stt import GoogleV2Provider

def test_providers():
    print("Testing AssemblyAI...")
    try:
        aai = AssemblyAIProvider()
        print("AssemblyAI initialized.")
        if os.path.exists("test.mp3"):
            print("Transcribing test.mp3 with AssemblyAI...")
            transcript, latency = aai.transcribe("test.mp3")
            print(f"AssemblyAI Result: {transcript[:50]}... (Latency: {latency:.2f}s)")
        else:
            print("test.mp3 not found, skipping transcription.")
    except Exception as e:
        print(f"AssemblyAI Failed: {e}")

    print("\nTesting Google V2...")
    try:
        g2 = GoogleV2Provider()
        print("Google V2 initialized.")
        if os.path.exists("test.mp3"):
             print("Transcribing test.mp3 with Google V2...")
             transcript, latency = g2.transcribe("test.mp3", model="chirp")
             print(f"Google V2 Result: {transcript[:50]}... (Latency: {latency:.2f}s)")
    except Exception as e:
        print(f"Google V2 Failed: {e}")

if __name__ == "__main__":
    test_providers()
