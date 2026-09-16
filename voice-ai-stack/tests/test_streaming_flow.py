import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
from metrics import LatencyTracker
from pipelines import VoicePipeline

class MockAudioCapture:
    def __init__(self):
        self.q = []
    
    def stream_until_silence(self, vad, metrics):
        # Simulate yielding 3 chunks of speech then silence
        metrics.mark("t_start_speech_capture")
        time.sleep(0.1)
        metrics.mark("t_first_voice_detected")
        yield np.zeros(1024, dtype=np.float32)
        time.sleep(0.1)
        yield np.zeros(1024, dtype=np.float32)
        time.sleep(0.1)
        metrics.mark("t_end_voice_detected")
        yield np.zeros(1024, dtype=np.float32)
        metrics.mark("t_vad_complete")

class MockSTT:
    def transcribe_stream(self, audio_stream):
        # Consume audio
        for _ in audio_stream:
            pass
        # Yield transcripts
        yield "Hello"
        yield "Hello world"

class MockLLM:
    def generate_stream(self, transcript):
        yield "Hi"
        yield " there"

class MockTTS:
    def synthesize_stream(self, token_stream):
        for _ in token_stream:
            pass
        yield b'audio1'
        yield b'audio2'

class MockPlayer:
    def play_stream(self, audio_stream, metrics):
        first = True
        for _ in audio_stream:
            if first:
                metrics.mark("t_playback_start_stream")
                first = False
        metrics.mark("t_playback_end_stream")

class TestStreamingFlow(unittest.TestCase):
    def test_streaming_metrics_population(self):
        """
        Simulates a full streaming turn to verify all metrics are populated.
        """
        tracker = LatencyTracker()
        
        # Manually assemble a pipeline-like flow
        capture = MockAudioCapture()
        stt = MockSTT()
        llm = MockLLM()
        tts = MockTTS()
        player = MockPlayer()
        
        # 1. Capture
        audio_stream = capture.stream_until_silence(None, tracker)
        
        # 2. STT
        tracker.mark("t_stt_stream_start")
        transcript_stream = stt.transcribe_stream(audio_stream)
        
        final_transcript = ""
        for text in transcript_stream:
            final_transcript = text
        tracker.mark("t_stt_stream_final")
        tracker.set_transcript(final_transcript)
        
        # 3. LLM
        tracker.mark("t_llm_stream_start")
        def llm_wrapper(gen):
            first = True
            for token in gen:
                if first:
                    tracker.mark("t_llm_stream_first_token")
                    first = False
                yield token
            tracker.mark("t_llm_stream_complete")
            
        token_stream = llm.generate_stream(final_transcript)
        wrapped_token_stream = llm_wrapper(token_stream)
        
        # 4. TTS
        tracker.mark("t_tts_stream_start")
        def tts_wrapper(gen):
            first = True
            for chunk in gen:
                if first:
                    tracker.mark("t_tts_first_audio_stream")
                    first = False
                yield chunk
                
        audio_stream = tts.synthesize_stream(wrapped_token_stream)
        wrapped_audio_stream = tts_wrapper(audio_stream)
        
        # 5. Playback
        player.play_stream(wrapped_audio_stream, tracker)
        
        # Verify Metrics
        tracker.current_turn = tracker.current_turn or tracker.start_turn("streaming") # Ensure turn exists if not started
        # Actually start_turn should be called first
        
        # Let's redo with proper start
        tracker = LatencyTracker()
        tracker.start_turn("streaming")
        
        # Re-run flow logic (copy-paste from above essentially)
        # ... (simplified for brevity in test execution)
        
        # Let's just check if the keys exist in a populated tracker
        # We need to run the flow again with the NEW tracker
        
        # 1. Capture
        audio_stream = capture.stream_until_silence(None, tracker)
        
        # 2. STT
        tracker.mark("t_stt_stream_start")
        transcript_stream = stt.transcribe_stream(audio_stream)
        for text in transcript_stream: pass
        tracker.mark("t_stt_stream_final")
        
        # 3. LLM
        tracker.mark("t_llm_stream_start")
        token_stream = llm.generate_stream("text")
        # wrapper logic
        first_token = True
        def l_wrap():
            nonlocal first_token
            for t in token_stream:
                if first_token:
                    tracker.mark("t_llm_stream_first_token")
                    first_token = False
                yield t
            tracker.mark("t_llm_stream_complete")
            
        # 4. TTS
        tracker.mark("t_tts_stream_start")
        audio_gen = tts.synthesize_stream(l_wrap())
        first_audio = True
        def t_wrap():
            nonlocal first_audio
            for c in audio_gen:
                if first_audio:
                    tracker.mark("t_tts_first_audio_stream")
                    first_audio = False
                yield c
                
        # 5. Playback
        player.play_stream(t_wrap(), tracker)
        
        tracker.compute_metrics()
        m = tracker.current_turn.metrics
        ts = tracker.current_turn.timestamps
        
        print("Timestamps:", ts.keys())
        print("Metrics:", m)
        
        required_metrics = [
            "stt_duration_stream",
            "llm_time_to_first_token_stream",
            "tts_time_to_first_audio_stream",
            "perceived_latency_stream",
            "e2e_latency_stream"
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, m, f"Metric {metric} is missing")
            self.assertIsNotNone(m[metric])
            self.assertGreater(m[metric], 0)

if __name__ == "__main__":
    unittest.main()
