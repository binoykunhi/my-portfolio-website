import sounddevice as sd
import numpy as np
import queue
import threading
import time
from typing import Optional, Generator, List

class VAD:
    def __init__(self, threshold: float = 0.01, silence_duration: float = 2.0, sample_rate: int = 16000):
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.sample_rate = sample_rate
        self.silence_frames = 0
        self.is_speaking = False
        self.frames_per_buffer = 1024 # Adjust based on chunk size

    def process_chunk(self, chunk: np.ndarray) -> str:
        """
        Returns:
        - "silence": Silence detected
        - "speech": Speech detected
        - "speech_end": Speech ended (silence duration exceeded)
        """
        amplitude = np.sqrt(np.mean(chunk**2))
        
        if amplitude > self.threshold:
            self.is_speaking = True
            self.silence_frames = 0
            return "speech"
        else:
            if self.is_speaking:
                self.silence_frames += len(chunk)
                silence_sec = self.silence_frames / self.sample_rate
                if silence_sec >= self.silence_duration:
                    self.is_speaking = False
                    return "speech_end"
            return "silence"

class AudioCapture:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(status)
        # Store data and capture timestamp
        self.q.put((indata.copy(), time.perf_counter()))

    def start(self):
        self.stop_event.clear()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        self.stop_event.set()
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def read_chunk(self) -> Optional[tuple[np.ndarray, float]]:
        try:
            return self.q.get(timeout=0.1)
        except queue.Empty:
            return None

    def measure_noise_floor(self, duration: float = 1.0) -> float:
        """
        Measures the maximum amplitude over the given duration to determine noise floor.
        """
        self.start()
        amplitudes = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                result = self.read_chunk()
                if result is not None:
                    chunk, _ = result
                    amplitude = np.sqrt(np.mean(chunk**2))
                    amplitudes.append(amplitude)
        finally:
            self.stop()
            
        if not amplitudes:
            return 0.0
            
        return np.max(amplitudes)

    def capture_until_silence(self, vad: VAD, metrics_tracker=None) -> np.ndarray:
        """
        Captures audio until VAD detects silence after speech.
        Returns the full audio buffer.
        """
        audio_buffer = []
        self.start()
        
        speech_started = False
        # We'll mark start based on the first chunk's timestamp if available, 
        # or current time if not (fallback).
        # Actually, we should wait for the first chunk to mark start?
        # The original code marked it immediately. Let's stick to that for "start capture"
        # but use chunk timestamps for voice detection events.
        
        if metrics_tracker:
            metrics_tracker.mark("t_start_speech_capture")

        try:
            while not self.stop_event.is_set():
                result = self.read_chunk()
                if result is None:
                    continue
                
                chunk, ts = result
                status = vad.process_chunk(chunk)
                audio_buffer.append(chunk)

                if status == "speech":
                    if not speech_started:
                        speech_started = True
                        if metrics_tracker:
                            # Use the chunk's timestamp!
                            metrics_tracker.current_turn.timestamps["t_first_voice_detected"] = ts
                    if metrics_tracker:
                        metrics_tracker.current_turn.timestamps["t_end_voice_detected"] = ts
                
                elif status == "speech_end":
                    if metrics_tracker:
                        metrics_tracker.mark("t_vad_complete")
                    break
        finally:
            self.stop()

        return np.concatenate(audio_buffer)

    def stream_until_silence(self, vad: VAD, metrics_tracker=None) -> Generator[np.ndarray, None, None]:
        """
        Yields audio chunks until VAD detects silence after speech.
        """
        self.start()
        speech_started = False
        if metrics_tracker:
            metrics_tracker.mark("t_start_speech_capture")

        try:
            while not self.stop_event.is_set():
                result = self.read_chunk()
                if result is None:
                    continue

                chunk, ts = result
                status = vad.process_chunk(chunk)
                yield chunk

                if status == "speech":
                    if not speech_started:
                        speech_started = True
                        if metrics_tracker:
                            metrics_tracker.current_turn.timestamps["t_first_voice_detected"] = ts
                    if metrics_tracker:
                        metrics_tracker.current_turn.timestamps["t_end_voice_detected"] = ts
                
                elif status == "speech_end":
                    if metrics_tracker:
                        metrics_tracker.mark("t_vad_complete")
                    break
        finally:
            self.stop()

class AudioPlayer:
    def __init__(self, sample_rate: int = 24000): # ElevenLabs default is often 24k or 44.1k
        self.sample_rate = sample_rate

    def play(self, audio_data: np.ndarray):
        sd.play(audio_data, self.sample_rate)
        sd.wait()

    def play_stream(self, audio_generator: Generator[bytes, None, None], metrics_tracker=None):
        """
        Plays a stream of raw PCM audio bytes (16kHz, 16-bit mono).
        """
        # 16kHz, 1 channel, int16 is what we requested from ElevenLabs
        stream = sd.OutputStream(samplerate=16000, channels=1, dtype='int16')
        stream.start()
        
        first_chunk = True
        try:
            for chunk in audio_generator:
                if not chunk:
                    continue
                    
                if first_chunk:
                    if metrics_tracker:
                        metrics_tracker.mark("t_tts_playback_start")
                    first_chunk = False
                
                # Convert bytes to numpy array
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                stream.write(audio_data)
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            if metrics_tracker:
                metrics_tracker.mark("t_tts_playback_end")
            stream.stop()
            stream.close()
