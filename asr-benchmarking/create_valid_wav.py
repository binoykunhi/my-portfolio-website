import wave
import math
import struct

def create_sine_wave(filename="test.wav", duration=1.0, frequency=440.0, sample_rate=44100):
    n_frames = int(duration * sample_rate)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_frames):
            value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
            
    print(f"Created valid WAV file: {filename}")

if __name__ == "__main__":
    create_sine_wave()
