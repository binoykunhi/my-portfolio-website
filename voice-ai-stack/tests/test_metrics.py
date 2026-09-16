import pytest
import time
from metrics import LatencyTracker

def test_latency_tracker_batch_metrics():
    tracker = LatencyTracker()
    tracker.start_turn("batch")
    
    # Simulate timestamps
    tracker.current_turn.timestamps = {
        "t_start_speech_capture": 100.0,
        "t_first_voice_detected": 100.5,
        "t_end_voice_detected": 102.5,
        "t_vad_complete": 104.5,
        "t_stt_start_batch": 104.6,
        "t_stt_end_batch": 105.6,
        "t_llm_start_batch": 105.7,
        "t_llm_end_batch": 106.7,
        "t_tts_start_batch": 106.8,
        "t_tts_audio_ready_batch": 107.8,
        "t_playback_start_batch": 108.0,
        "t_playback_end_batch": 110.0
    }
    
    tracker.compute_metrics()
    m = tracker.current_turn.metrics
    
    assert m["user_speech_duration"] == 2.0
    assert m["vad_silence_duration"] == 2.0
    assert m["stt_duration_batch"] == 1.0
    assert m["llm_duration_batch"] == 1.0
    assert m["tts_synthesis_duration_batch"] == 1.0
    assert m["playback_duration_batch"] == 2.0
    assert m["perceived_latency_batch"] == 108.0 - 102.5 # 5.5s
    assert m["e2e_latency_batch"] == 108.0 - 100.0 # 8.0s

def test_latency_tracker_streaming_metrics():
    tracker = LatencyTracker()
    tracker.start_turn("streaming")
    
    tracker.current_turn.timestamps = {
        "t_start_speech_capture": 100.0,
        "t_first_voice_detected": 100.5,
        "t_end_voice_detected": 102.5,
        "t_stt_stream_start": 100.1,
        "t_stt_stream_final": 102.6,
        "t_llm_stream_start": 102.7,
        "t_llm_stream_first_token": 102.9,
        "t_llm_stream_complete": 103.5,
        "t_tts_stream_start": 103.0,
        "t_tts_first_audio_stream": 103.2,
        "t_playback_start_stream": 103.3,
        "t_playback_end_stream": 105.3
    }
    
    tracker.compute_metrics()
    m = tracker.current_turn.metrics
    
    assert m["stt_duration_stream"] == pytest.approx(2.5)
    assert m["llm_time_to_first_token_stream"] == pytest.approx(0.2)
    assert m["llm_duration_stream"] == pytest.approx(0.8)
    assert m["tts_time_to_first_audio_stream"] == pytest.approx(0.2)
    assert m["perceived_latency_stream"] == pytest.approx(0.8)
