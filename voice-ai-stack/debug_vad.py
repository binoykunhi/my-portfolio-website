import sounddevice as sd
import numpy as np
import time
import sys

def print_bar(amplitude, threshold=0.01, width=50):
    # Logarithmic scale for better visualization
    if amplitude <= 0:
        val = 0
    else:
        val = int(np.clip(amplitude * 1000, 0, width))
    
    bar = "#" * val
    padding = " " * (width - val)
    
    status = "SPEECH" if amplitude > threshold else "SILENCE"
    color = "\033[92m" if status == "SPEECH" else "\033[90m" # Green for speech, Grey for silence
    reset = "\033[0m"
    
    sys.stdout.write(f"\r{color}[{bar}{padding}] {amplitude:.5f} | {status}{reset}")
    sys.stdout.flush()

def debug_vad():
    print("Debugging VAD... Press Ctrl+C to stop.")
    print("Speak into your microphone to see levels.")
    print(f"Threshold: 0.01")
    
    def callback(indata, frames, time, status):
        if status:
            print(status)
        amplitude = np.sqrt(np.mean(indata**2))
        print_bar(amplitude)

    try:
        with sd.InputStream(callback=callback, channels=1, samplerate=16000):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    debug_vad()
