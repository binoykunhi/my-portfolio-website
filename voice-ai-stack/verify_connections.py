import os
import time
import numpy as np
from dotenv import load_dotenv
from rich.console import Console
from unittest.mock import MagicMock, patch

from stt_whisper import WhisperClient
from llm_client import LLMClient
from tts_elevenlabs import TTSClient
from pipelines import VoicePipeline
from audio_io import VAD

load_dotenv()
console = Console()

def verify_components():
    console.print("[bold blue]Verifying Individual Components (Real API Calls)...[/bold blue]")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    
    if not openai_key or not elevenlabs_key:
        console.print("[red]Missing API keys in .env[/red]")
        return False

    # 1. Verify LLM (Cheapest/Fastest)
    try:
        console.print("1. Testing LLM (OpenAI)... ", end="")
        llm = LLMClient(openai_key)
        response = llm.generate_batch("Say 'test' in one word.")
        console.print(f"[green]OK[/green] (Response: {response})")
    except Exception as e:
        console.print(f"[red]FAILED[/red]: {e}")
        return False

    # 2. Verify TTS (ElevenLabs)
    try:
        console.print("2. Testing TTS (ElevenLabs)... ", end="")
        tts = TTSClient(elevenlabs_key)
        audio_bytes = tts.synthesize_batch("Test.")
        if len(audio_bytes) > 0:
            console.print(f"[green]OK[/green] ({len(audio_bytes)} bytes)")
        else:
            console.print("[red]FAILED[/red]: Received empty audio")
            return False
    except Exception as e:
        console.print(f"[red]FAILED[/red]: {e}")
        return False

    # 3. Verify STT (Whisper)
    try:
        console.print("3. Testing STT (Whisper)... ", end="")
        stt = WhisperClient(openai_key)
        # Generate 1 second of silence/noise
        dummy_audio = np.random.uniform(-0.1, 0.1, 16000).astype(np.float32)
        transcript = stt.transcribe_batch(dummy_audio)
        console.print(f"[green]OK[/green] (Transcript: '{transcript}')")
    except Exception as e:
        console.print(f"[red]FAILED[/red]: {e}")
        return False

    return True

def verify_pipeline_logic():
    console.print("\n[bold blue]Verifying Pipeline Logic (Mocked Audio Input, Real APIs)...[/bold blue]")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    pipeline = VoicePipeline(openai_key, elevenlabs_key)
    
    # Mock AudioCapture to return a sequence: Silence -> Speech -> Silence
    # This triggers the VAD logic to capture, then sends to Real STT -> Real LLM -> Real TTS
    
    # We need to mock capture_until_silence to return a buffer directly 
    # because mocking the threading/queue logic of AudioCapture is complex and flaky in a script.
    # However, to test "connections", we want to test the ORCHESTRATION.
    
    # Let's mock `audio_capture.capture_until_silence` to return the dummy audio we used above.
    dummy_audio = np.random.uniform(-0.1, 0.1, 32000).astype(np.float32) # 2 seconds
    
    # Patch the capture method on the instance
    pipeline.audio_capture.capture_until_silence = MagicMock(return_value=dummy_audio)
    
    # Patch AudioPlayer to not actually play sound (we can't hear it), but verify it received data
    pipeline.audio_player.play = MagicMock()
    
    console.print("Running Batch Turn...")
    try:
        pipeline.run_batch_turn()
        console.print("[green]Batch Turn Completed Successfully[/green]")
        pipeline.audio_player.play.assert_called_once()
    except Exception as e:
        console.print(f"[red]Batch Turn Failed[/red]: {e}")
        return False

    return True

if __name__ == "__main__":
    if verify_components():
        if verify_pipeline_logic():
            console.print("\n[bold green]ALL SYSTEMS GO: End-to-End Connections Verified.[/bold green]")
        else:
            console.print("\n[bold red]Pipeline Logic Verification Failed.[/bold red]")
    else:
        console.print("\n[bold red]Component Verification Failed.[/bold red]")
