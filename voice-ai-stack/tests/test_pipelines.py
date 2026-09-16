import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from pipelines import VoicePipeline

@pytest.fixture
def mock_pipeline():
    with patch("pipelines.AudioCapture") as MockCapture, \
         patch("pipelines.AudioPlayer") as MockPlayer, \
         patch("pipelines.WhisperClient") as MockSTT, \
         patch("pipelines.LLMClient") as MockLLM, \
         patch("pipelines.TTSClient") as MockTTS:
        
        pipeline = VoicePipeline("fake_key", "fake_key")
        
        # Setup default mock returns
        pipeline.audio_capture.capture_until_silence.return_value = np.zeros(16000, dtype=np.float32)
        pipeline.stt.transcribe_batch.return_value = "Hello world"
        pipeline.llm.generate_batch.return_value = "Hi there"
        pipeline.tts.synthesize_batch.return_value = b"fake_audio_bytes"
        
        yield pipeline

def test_batch_pipeline_flow(mock_pipeline):
    mock_pipeline.run_batch_turn()
    
    # Verify calls
    mock_pipeline.audio_capture.capture_until_silence.assert_called_once()
    mock_pipeline.stt.transcribe_batch.assert_called_once()
    mock_pipeline.llm.generate_batch.assert_called_with("Hello world")
    mock_pipeline.tts.synthesize_batch.assert_called_with("Hi there")
    mock_pipeline.audio_player.play.assert_called_once()
    
    # Verify metrics logged
    assert mock_pipeline.metrics.current_turn.mode == "batch"
    assert "t_stt_start_batch" in mock_pipeline.metrics.current_turn.timestamps

def test_streaming_pipeline_flow(mock_pipeline):
    # Setup streaming mocks
    mock_pipeline.audio_capture.stream_until_silence.return_value = iter([np.zeros(1024)])
    mock_pipeline.stt.transcribe_stream.return_value = iter(["Hello", "Hello world"])
    mock_pipeline.llm.generate_stream.return_value = iter(["Hi", " there"])
    mock_pipeline.tts.synthesize_stream.return_value = iter([b"chunk1", b"chunk2"])
    
    mock_pipeline.run_streaming_turn()
    
    # Verify calls
    mock_pipeline.audio_capture.stream_until_silence.assert_called_once()
    mock_pipeline.stt.transcribe_stream.assert_called_once()
    mock_pipeline.llm.generate_stream.assert_called_with("Hello world") # Final transcript
    mock_pipeline.tts.synthesize_stream.assert_called_once()
    mock_pipeline.audio_player.play_stream.assert_called_once()
    
    # Verify metrics logged
    assert mock_pipeline.metrics.current_turn.mode == "streaming"
    assert "t_stt_stream_start" in mock_pipeline.metrics.current_turn.timestamps
