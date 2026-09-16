"""
Audio utility functions for benchmarking
"""
import wave
import contextlib

def get_audio_duration(audio_path: str) -> float:
    """
    Get audio duration in seconds
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds, or 0.0 if unable to determine
    """
    try:
        # Try WAV format first
        with contextlib.closing(wave.open(audio_path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return round(duration, 2)
    except:
        # For non-WAV formats, try to use pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return round(len(audio) / 1000.0, 2)  # milliseconds to seconds
        except:
            # If all else fails, return 0
            return 0.0
