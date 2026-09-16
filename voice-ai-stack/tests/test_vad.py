import pytest
import numpy as np
from audio_io import VAD

def test_vad_silence():
    vad = VAD(threshold=0.1, silence_duration=0.5, sample_rate=16000)
    # Silence chunk
    chunk = np.zeros(1024, dtype=np.float32)
    assert vad.process_chunk(chunk) == "silence"

def test_vad_speech_trigger():
    vad = VAD(threshold=0.1, silence_duration=0.5, sample_rate=16000)
    # Loud chunk
    chunk = np.ones(1024, dtype=np.float32)
    assert vad.process_chunk(chunk) == "speech"
    assert vad.is_speaking is True

def test_vad_silence_duration():
    vad = VAD(threshold=0.1, silence_duration=0.1, sample_rate=16000) # 0.1s silence
    
    # 1. Start speech
    chunk_loud = np.ones(1600, dtype=np.float32) # 0.1s at 16k
    vad.process_chunk(chunk_loud)
    assert vad.is_speaking is True
    
    # 2. Silence (not enough)
    chunk_quiet = np.zeros(800, dtype=np.float32) # 0.05s
    assert vad.process_chunk(chunk_quiet) == "silence" # Still speaking state, but returning silence status for chunk?
    # Wait, my VAD implementation returns "silence" if amplitude < threshold, 
    # BUT it checks if silence_duration exceeded to return "speech_end".
    # If not exceeded, it returns "silence" but keeps is_speaking=True?
    # Let's check audio_io.py logic:
    # if amplitude > threshold: return "speech"
    # else: if is_speaking: silence_frames += len; if exceeded: return "speech_end"; return "silence"
    # So yes, it returns "silence" while waiting for timeout.
    
    # 3. More silence (exceeds 0.1s total)
    chunk_quiet_2 = np.zeros(1600, dtype=np.float32) # 0.1s
    # Total silence = 0.05 + 0.1 = 0.15 > 0.1
    assert vad.process_chunk(chunk_quiet_2) == "speech_end"
    assert vad.is_speaking is False
