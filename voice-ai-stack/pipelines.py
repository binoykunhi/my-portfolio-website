import time
import numpy as np
from rich.console import Console
from rich.status import Status

from metrics import LatencyTracker
from audio_io import AudioCapture, AudioPlayer, VAD
from stt_whisper import WhisperClient
from llm_client import LLMClient
from tts_elevenlabs import TTSClient

console = Console()

class VoicePipeline:
    def __init__(self, openai_key: str, elevenlabs_key: str):
        self.metrics = LatencyTracker()
        self.audio_capture = AudioCapture()
        self.audio_player = AudioPlayer()
        self.vad = VAD()
        
        self.stt = WhisperClient(openai_key)
        self.llm = LLMClient(openai_key)
        self.tts = TTSClient(elevenlabs_key)

    def calibrate(self):
        """
        Calibrates VAD threshold based on ambient noise.
        """
        console.print("[yellow]Calibrating microphone... Please remain silent for 2 seconds.[/yellow]")
        noise_floor = self.audio_capture.measure_noise_floor(duration=2.0)
        
        # Heuristic: Threshold = noise_floor * 3.0, but clamped to reasonable bounds
        # Minimum 0.01 to avoid triggering on breathing/very quiet noise
        # Maximum 0.2 to avoid being deaf
        new_threshold = max(0.01, noise_floor * 3.0)
        new_threshold = min(0.2, new_threshold)
        
        self.vad.threshold = new_threshold
        console.print(f"[green]Calibration complete.[/green]")
        console.print(f"Noise Floor: {noise_floor:.5f}")
        console.print(f"New VAD Threshold: [bold]{new_threshold:.5f}[/bold]")

    def run_batch_turn(self):
        turn_id = self.metrics.start_turn("batch")
        console.print(f"[bold blue]Starting Batch Turn (ID: {turn_id})[/bold blue]")
        
        # 1. Capture
        console.print("[yellow]Listening... (Speak now)[/yellow]")
        audio_data = self.audio_capture.capture_until_silence(self.vad, self.metrics)
        console.print("[green]Capture complete.[/green]")
        
        # 2. STT
        self.metrics.mark("t_stt_batch_request_sent")
        with console.status("Transcribing (Batch)..."):
            transcript = self.stt.transcribe_batch(audio_data)
        self.metrics.mark("t_stt_batch_response_received")
        self.metrics.set_transcript(transcript)
        console.print(f"[bold]Transcript:[/bold] {transcript}")
        
        # 3. LLM
        self.metrics.mark("t_llm_request_sent")
        with console.status("Generating Response (Batch)..."):
            response = self.llm.generate_batch(transcript)
        # In batch, first token and all tokens are effectively same time for our granularity, 
        # but strictly we mark them.
        self.metrics.mark("t_llm_first_token_received") 
        self.metrics.mark("t_llm_all_tokens_received")
        self.metrics.set_response(response)
        console.print(f"[bold]Response:[/bold] {response}")
        
        # 4. TTS
        self.metrics.mark("t_tts_request_sent")
        with console.status("Synthesizing Audio (Batch)..."):
            audio_bytes = self.tts.synthesize_batch(response)
        self.metrics.mark("t_tts_first_audio_chunk_received")
        self.metrics.mark("t_tts_all_audio_received")
        
        # 5. Playback
        self.metrics.mark("t_tts_playback_start")
        # Convert bytes to int16 numpy array for playback
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
        self.audio_player.play(audio_np)
        self.metrics.mark("t_tts_playback_end")
        
        # --- Metrics Enhancement ---
        console.print("\n[bold yellow]Metrics Collection[/bold yellow]")
        ground_truth = console.input("Enter ground truth text for WER (or press Enter to skip): ").strip()
        if ground_truth:
            self.metrics.set_wer(ground_truth)
            console.print(f"WER: {self.metrics.current_turn.wer:.2f}")
            
        console.print("Judging interaction...")
        judge_result = self.llm.judge_interaction(transcript, response)
        self.metrics.set_judge_score(judge_result.get("score", 0.0), judge_result.get("reason", "No reason"))
        console.print(f"Judge Score: {judge_result.get('score')}/5 ({judge_result.get('reason')})")
        # ---------------------------
        
        self.metrics.save_turn()
        console.print("[bold green]Turn Complete.[/bold green]")

    def run_streaming_turn(self):
        turn_id = self.metrics.start_turn("streaming")
        console.print(f"[bold blue]Starting Streaming Turn (ID: {turn_id})[/bold blue]")
        
        # 1. Streaming Capture -> STT
        console.print("[yellow]Listening... (Speak now)[/yellow]")
        
        audio_stream = self.audio_capture.stream_until_silence(self.vad, self.metrics)
        
        # We need to consume the audio stream and feed it to STT
        # STT returns a generator of transcript updates
        self.metrics.mark("t_stt_streaming_start")
        
        transcript_stream = self.stt.transcribe_stream(audio_stream)
        
        final_transcript = ""
        first_partial = True
        with console.status("Transcribing (Streaming)...") as status:
            for text in transcript_stream:
                if first_partial:
                    self.metrics.mark("t_stt_streaming_first_partial")
                    first_partial = False
                final_transcript = text
                status.update(f"Transcribing: {text}")
        
        self.metrics.mark("t_stt_streaming_final")
        self.metrics.set_transcript(final_transcript)
        console.print(f"[bold]Final Transcript:[/bold] {final_transcript}")
        
        # 2. Streaming LLM
        self.metrics.mark("t_llm_request_sent")
        console.print("[bold]Response:[/bold] ", end="")
        
        # Helper to intercept first token for metrics
        full_response = []
        def llm_wrapper(gen):
            first = True
            for token in gen:
                if first:
                    self.metrics.mark("t_llm_first_token_received")
                    print("DEBUG: LLM first token received")
                    first = False
                print(token, end="", flush=True)
                full_response.append(token)
                yield token
            self.metrics.mark("t_llm_all_tokens_received")
            print("\nDEBUG: LLM stream complete")
            self.metrics.set_response("".join(full_response))

        token_stream = self.llm.generate_stream(final_transcript)
        wrapped_token_stream = llm_wrapper(token_stream)
        
        # 3. Streaming TTS
        self.metrics.mark("t_tts_request_sent")
        print("DEBUG: Calling TTS synthesize_stream")
        
        # Helper to intercept first audio chunk for metrics
        def tts_wrapper(gen):
            first = True
            print("DEBUG: TTS wrapper started iteration")
            for chunk in gen:
                if first:
                    self.metrics.mark("t_tts_first_audio_chunk_received")
                    print("DEBUG: TTS first audio chunk received")
                    first = False
                yield chunk
            self.metrics.mark("t_tts_all_audio_received")
            print("DEBUG: TTS wrapper finished iteration")

        audio_stream = self.tts.synthesize_stream(wrapped_token_stream)
        wrapped_audio_stream = tts_wrapper(audio_stream)
        
        # 4. Streaming Playback
        # play_stream handles t_tts_playback_start and t_tts_playback_end
        self.audio_player.play_stream(wrapped_audio_stream, self.metrics)
        
        # --- Metrics Enhancement ---
        console.print("\n[bold yellow]Metrics Collection[/bold yellow]")
        ground_truth = console.input("Enter ground truth text for WER (or press Enter to skip): ").strip()
        if ground_truth:
            self.metrics.set_wer(ground_truth)
            console.print(f"WER: {self.metrics.current_turn.wer:.2f}")
            
        console.print("Judging interaction...")
        final_response_text = "".join(full_response)
        judge_result = self.llm.judge_interaction(final_transcript, final_response_text)
        self.metrics.set_judge_score(judge_result.get("score", 0.0), judge_result.get("reason", "No reason"))
        console.print(f"Judge Score: {judge_result.get('score')}/5 ({judge_result.get('reason')})")
        
        self.metrics.save_turn()
        console.print("[bold green]Turn Complete.[/bold green]")
