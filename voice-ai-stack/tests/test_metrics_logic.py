import unittest
import time
from metrics import LatencyTracker, TurnMetrics

class TestMetricsLogic(unittest.TestCase):
    def setUp(self):
        self.tracker = LatencyTracker()

    def test_batch_metrics_calculation(self):
        """Test that batch metrics are calculated correctly from timestamps."""
        self.tracker.start_turn("batch")
        
        # Simulate timeline
        t0 = 100.0
        timestamps = {
            "t_start_speech_capture": t0,
            "t_first_voice_detected": t0 + 0.5,
            "t_end_voice_detected": t0 + 2.0, # Speech duration = 1.5s
            "t_vad_complete": t0 + 2.5,       # VAD silence = 0.5s
            
            "t_stt_batch_request_sent": t0 + 2.6,
            "t_stt_batch_response_received": t0 + 3.0, # STT = 0.4s
            
            "t_llm_request_sent": t0 + 3.1,
            "t_llm_first_token_received": t0 + 3.5,
            "t_llm_all_tokens_received": t0 + 4.1,      # LLM Total = 1.0s
            
            "t_tts_request_sent": t0 + 4.2,
            "t_tts_first_audio_chunk_received": t0 + 4.5,
            "t_tts_all_audio_received": t0 + 5.0, # TTS Total = 0.8s
            
            "t_tts_playback_start": t0 + 5.1, # Perceived = 5.1 - 2.0 = 3.1s
            "t_tts_playback_end": t0 + 8.0
        }
        
        # Inject timestamps
        self.tracker.current_turn.timestamps = timestamps
        self.tracker.compute_metrics()
        m = self.tracker.current_turn.metrics
        
        self.assertAlmostEqual(m["user_speech_duration_ms"], 1500.0)
        self.assertAlmostEqual(m["vad_silence_duration_ms"], 500.0)
        self.assertAlmostEqual(m["stt_batch_processing_latency_ms"], 400.0)
        self.assertAlmostEqual(m["llm_total_generation_latency_ms"], 1000.0)
        self.assertAlmostEqual(m["tts_generation_total_latency_ms"], 800.0)
        self.assertAlmostEqual(m["perceived_latency_ms"], 3100.0)
        self.assertAlmostEqual(m["e2e_latency_ms"], 5100.0)

    def test_streaming_metrics_calculation(self):
        """Test that streaming metrics are calculated correctly."""
        self.tracker.start_turn("streaming")
        
        t0 = 200.0
        timestamps = {
            "t_start_speech_capture": t0,
            "t_first_voice_detected": t0 + 0.5,
            "t_end_voice_detected": t0 + 2.0,
            
            "t_stt_streaming_start": t0 + 0.5, # Overlapping start
            "t_stt_streaming_first_partial": t0 + 0.8,
            "t_stt_streaming_final": t0 + 2.5,   # STT Final Latency = 2.0s
            
            "t_llm_request_sent": t0 + 2.6,
            "t_llm_first_token_received": t0 + 2.8, # LLM TTFT = 0.2s
            "t_llm_all_tokens_received": t0 + 3.6,
            
            "t_tts_request_sent": t0 + 2.9,
            "t_tts_first_audio_chunk_received": t0 + 3.2, # TTS TTFA = 0.3s
            "t_tts_all_audio_received": t0 + 4.0,
            
            "t_tts_playback_start": t0 + 3.3, # Perceived = 3.3 - 2.0 = 1.3s
            "t_tts_playback_end": t0 + 6.0
        }
        
        self.tracker.current_turn.timestamps = timestamps
        self.tracker.compute_metrics()
        m = self.tracker.current_turn.metrics
        
        self.assertAlmostEqual(m["stt_streaming_final_latency_ms"], 2000.0)
        self.assertAlmostEqual(m["llm_time_to_first_token_ms"], 200.0)
        self.assertAlmostEqual(m["tts_time_to_first_audio_chunk_ms"], 300.0)
        self.assertAlmostEqual(m["perceived_latency_ms"], 1300.0)
        self.assertAlmostEqual(m["e2e_latency_ms"], 3300.0)

    def test_wer_calculation(self):
        """Test WER calculation logic."""
        self.tracker.start_turn("batch")
        self.tracker.set_transcript("hello world")
        self.tracker.set_wer("hello world")
        self.assertEqual(self.tracker.current_turn.wer, 0.0)
        
        self.tracker.set_wer("hello")
        self.assertEqual(self.tracker.current_turn.wer, 1.0)
        
        self.tracker.set_wer("hello world folks")
        self.assertAlmostEqual(self.tracker.current_turn.wer, 0.3333333, places=5)

if __name__ == "__main__":
    unittest.main()
