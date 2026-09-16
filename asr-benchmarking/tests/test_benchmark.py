import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stt_benchmark.main import main

class TestBenchmark(unittest.TestCase):
    @patch('stt_benchmark.main.OpenAIProvider')
    @patch('stt_benchmark.main.DeepgramProvider')
    @patch('stt_benchmark.main.AssemblyAIProvider')
    @patch('stt_benchmark.main.GoogleV1Provider')
    @patch('stt_benchmark.main.GoogleV2Provider')
    @patch('stt_benchmark.main.AWSTranscribeProvider')
    @patch('stt_benchmark.main.LLMJudge')
    @patch('stt_benchmark.main.argparse.ArgumentParser.parse_args')
    @patch('stt_benchmark.main.os.path.exists')
    @patch('stt_benchmark.main.os.path.isdir')
    @patch('glob.glob')
    def test_main_flow(self, mock_glob, mock_isdir, mock_exists, mock_args, MockJudge, MockAWS, MockGoogleV2, MockGoogleV1, MockAssembly, MockDeepgram, MockOpenAI):
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_glob.return_value = ["test1.mp3", "test2.mp3"]
        
        # Mock providers
        for MockProvider in [MockOpenAI, MockDeepgram, MockAssembly, MockGoogleV1, MockGoogleV2, MockAWS]:
            instance = MockProvider.return_value
            instance.transcribe.return_value = ("Sample Transcript", 1.0)
        
        # Mock Judge
        mock_judge_instance = MockJudge.return_value
        mock_judge_instance.judge_transcripts.return_value = {
            "winner": "MockProvider",
            "reasoning": "It was the best.",
            "consensus_transcript": "Consensus",
            "wers": {
                "OpenAI Whisper (whisper-1)": 0.1,
                "Deepgram (nova-2)": 0.2,
                "AssemblyAI (None)": 0.3,
                "Google V1 (default)": 0.4,
                "Google V2 Chirp 2 (chirp2)": 0.5,
                "Google V2 Chirp 3 (chirp3)": 0.6,
                "AWS Transcribe (None)": 0.7
            }
        }

        with patch('sys.argv', ['main.py', 'dummy_dir']):
            main()
        
        # Verify providers called for all files
        # glob is called 5 times (for 5 extensions). Mock returns 2 files each time.
        # Total files = 5 * 2 = 10.
        # So each provider is called 10 times.
        self.assertEqual(MockOpenAI.return_value.transcribe.call_count, 10)
        self.assertEqual(MockDeepgram.return_value.transcribe.call_count, 10)
        self.assertEqual(MockAssembly.return_value.transcribe.call_count, 10)
        self.assertEqual(MockGoogleV1.return_value.transcribe.call_count, 10)
        # Google V2: 10 files * 2 models = 20 calls
        self.assertEqual(MockGoogleV2.return_value.transcribe.call_count, 20)
        self.assertEqual(MockAWS.return_value.transcribe.call_count, 10)
        
        # Verify judge called 10 times
        self.assertEqual(mock_judge_instance.judge_transcripts.call_count, 10)

if __name__ == '__main__':
    import argparse
    unittest.main()
