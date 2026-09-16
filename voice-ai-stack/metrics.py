import time
import json
import uuid
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Any
from pathlib import Path

@dataclass
class TurnMetrics:
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_mode: str = "unknown"  # "batch", "streaming", "streaming_degraded"
    stt_mode: str = "unknown"
    llm_mode: str = "unknown"
    tts_mode: str = "unknown"
    
    # Raw Timestamps (ms precision stored as float seconds)
    timestamps: Dict[str, float] = field(default_factory=dict)
    
    # Derived Metrics (ms)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Text
    user_transcript_text: Optional[str] = None
    llm_response_text: Optional[str] = None
    
    # Validation
    metrics_valid: bool = True
    validation_errors: list = field(default_factory=list)
    
    # Optional
    accuracy_rating: Optional[int] = None
    wer: Optional[float] = None
    judge_score: Optional[float] = None
    judge_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculates Word Error Rate (WER).
    """
    r = reference.lower().split()
    h = hypothesis.lower().split()
    d = np.zeros((len(r) + 1) * (len(h) + 1), dtype=np.uint8)
    d = d.reshape((len(r) + 1, len(h) + 1))
    
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                sub = d[i - 1][j - 1] + 1
                ins = d[i][j - 1] + 1
                rem = d[i - 1][j] + 1
                d[i][j] = min(sub, ins, rem)
    
    if len(r) == 0:
        return 0.0 if len(h) == 0 else 1.0
        
    return float(d[len(r)][len(h)]) / len(r)

class LatencyTracker:
    def __init__(self):
        self.current_turn: Optional[TurnMetrics] = None
        self.session_turns: list[TurnMetrics] = []
        self.log_file = Path("results.jsonl")

    def start_turn(self, pipeline_mode: str) -> str:
        self.current_turn = TurnMetrics(pipeline_mode=pipeline_mode)
        return self.current_turn.turn_id

    def mark(self, event_name: str):
        if self.current_turn:
            self.current_turn.timestamps[event_name] = time.perf_counter()

    def set_transcript(self, text: str):
        if self.current_turn:
            self.current_turn.user_transcript_text = text

    def set_response(self, text: str):
        if self.current_turn:
            self.current_turn.llm_response_text = text
            
    def set_wer(self, reference: str):
        if self.current_turn and self.current_turn.user_transcript_text:
            self.current_turn.wer = calculate_wer(reference, self.current_turn.user_transcript_text)
            
    def set_judge_score(self, score: float, reason: str):
        if self.current_turn:
            self.current_turn.judge_score = score
            self.current_turn.judge_reason = reason

    def compute_metrics(self):
        if not self.current_turn:
            return

        ts = self.current_turn.timestamps
        m = self.current_turn.metrics
        
        # Helper for ms conversion
        def diff_ms(end_key, start_key):
            if end_key in ts and start_key in ts:
                return (ts[end_key] - ts[start_key]) * 1000.0
            return None

        # --- 1. Audio Capture & VAD ---
        m["user_speech_duration_ms"] = diff_ms("t_end_voice_detected", "t_first_voice_detected")
        m["vad_silence_duration_ms"] = diff_ms("t_vad_complete", "t_end_voice_detected")
        
        # --- 2.1 STT Latency ---
        # A. Common
        m["stt_endpointing_latency_ms"] = diff_ms("t_vad_complete", "t_end_voice_detected")
        
        audio_duration_s = (m.get("user_speech_duration_ms") or 0) / 1000.0
        
        # B. Batch STT
        m["stt_batch_processing_latency_ms"] = diff_ms("t_stt_batch_response_received", "t_stt_batch_request_sent")
        if m.get("stt_batch_processing_latency_ms") and audio_duration_s > 0:
            m["stt_batch_rtf"] = m["stt_batch_processing_latency_ms"] / (audio_duration_s * 1000.0)

        # C. Streaming STT
        m["stt_streaming_partial_latency_ms"] = diff_ms("t_stt_streaming_first_partial", "t_first_voice_detected")
        m["stt_streaming_final_latency_ms"] = diff_ms("t_stt_streaming_final", "t_stt_streaming_start")
        if m.get("stt_streaming_final_latency_ms") and audio_duration_s > 0:
            m["stt_streaming_rtf"] = m["stt_streaming_final_latency_ms"] / (audio_duration_s * 1000.0)

        # --- 2.2 LLM Latency ---
        m["llm_time_to_first_token_ms"] = diff_ms("t_llm_first_token_received", "t_llm_request_sent")
        m["llm_total_generation_latency_ms"] = diff_ms("t_llm_all_tokens_received", "t_llm_request_sent")

        # --- 2.3 TTS Latency ---
        m["tts_time_to_first_audio_chunk_ms"] = diff_ms("t_tts_first_audio_chunk_received", "t_tts_request_sent")
        m["tts_generation_total_latency_ms"] = diff_ms("t_tts_all_audio_received", "t_tts_request_sent")
        m["tts_playback_duration_ms"] = diff_ms("t_tts_playback_end", "t_tts_playback_start")

        # --- 3. Pipeline Latency ---
        m["perceived_latency_ms"] = diff_ms("t_tts_playback_start", "t_end_voice_detected")
        m["e2e_latency_ms"] = diff_ms("t_tts_playback_start", "t_start_speech_capture")

        # --- 5. Validation Rules ---
        self.validate_metrics()

    def validate_metrics(self):
        if not self.current_turn:
            return
            
        m = self.current_turn.metrics
        valid = True
        errors = []
        
        # Ensure all latencies >= 0
        for k, v in m.items():
            if v is not None and v < 0:
                valid = False
                errors.append(f"{k} is negative: {v}")

        # Invariants
        if m.get("llm_time_to_first_token_ms") and m.get("llm_total_generation_latency_ms"):
            if m["llm_time_to_first_token_ms"] > m["llm_total_generation_latency_ms"]:
                valid = False
                errors.append("LLM TTFT > Total Generation")
        
        if m.get("tts_time_to_first_audio_chunk_ms") and m.get("tts_generation_total_latency_ms"):
            if m["tts_time_to_first_audio_chunk_ms"] > m["tts_generation_total_latency_ms"]:
                valid = False
                errors.append("TTS TTFA > Total Generation")
                
        if m.get("e2e_latency_ms") and m.get("perceived_latency_ms"):
            if m["e2e_latency_ms"] < m["perceived_latency_ms"]:
                valid = False
                errors.append("E2E < Perceived Latency")
                
        if m.get("perceived_latency_ms") and m.get("vad_silence_duration_ms"):
            if m["perceived_latency_ms"] < m["vad_silence_duration_ms"]:
                valid = False
                errors.append("Perceived < VAD Silence (Impossible)")

        self.current_turn.metrics_valid = valid
        self.current_turn.validation_errors = errors

    def save_turn(self):
        if self.current_turn:
            self.compute_metrics()
            self.session_turns.append(self.current_turn)
            # Also append to file for persistence if needed, but session is main now
            with open(self.log_file, "a") as f:
                f.write(json.dumps(self.current_turn.to_dict()) + "\n")
            
    def save_session_to_csv(self, filename: str):
        if not self.session_turns:
            return
            
        import csv
        
        # Define headers based on Master Prompt
        headers = [
            "turn_id", "pipeline_mode", "metrics_valid", "validation_errors",
            "user_transcript_text", "llm_response_text", "wer", "judge_score",
            "user_speech_duration_ms", "vad_silence_duration_ms",
            "stt_endpointing_latency_ms",
            "stt_batch_processing_latency_ms", "stt_batch_rtf",
            "stt_streaming_partial_latency_ms", "stt_streaming_final_latency_ms", "stt_streaming_rtf",
            "llm_time_to_first_token_ms", "llm_total_generation_latency_ms",
            "tts_time_to_first_audio_chunk_ms", "tts_generation_total_latency_ms", "tts_playback_duration_ms",
            "perceived_latency_ms", "e2e_latency_ms"
        ]
        
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for turn in self.session_turns:
                m = turn.metrics
                writer.writerow([
                    turn.turn_id,
                    turn.pipeline_mode,
                    turn.metrics_valid,
                    "; ".join(turn.validation_errors),
                    turn.user_transcript_text,
                    turn.llm_response_text,
                    turn.wer,
                    turn.judge_score,
                    m.get("user_speech_duration_ms"),
                    m.get("vad_silence_duration_ms"),
                    m.get("stt_endpointing_latency_ms"),
                    m.get("stt_batch_processing_latency_ms"),
                    m.get("stt_batch_rtf"),
                    m.get("stt_streaming_partial_latency_ms"),
                    m.get("stt_streaming_final_latency_ms"),
                    m.get("stt_streaming_rtf"),
                    m.get("llm_time_to_first_token_ms"),
                    m.get("llm_total_generation_latency_ms"),
                    m.get("tts_time_to_first_audio_chunk_ms"),
                    m.get("tts_generation_total_latency_ms"),
                    m.get("tts_playback_duration_ms"),
                    m.get("perceived_latency_ms"),
                    m.get("e2e_latency_ms")
                ])
