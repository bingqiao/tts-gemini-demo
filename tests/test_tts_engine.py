import unittest
from unittest.mock import Mock, patch
import numpy as np

from tts_lib.tts_engine import TTSEngine
from tts_lib.data_structures import SpeechSegment

class TestTTSEngine(unittest.TestCase):
    def setUp(self):
        # Mock the TTS.api.TTS class
        self.mock_tts_class = Mock()
        self.mock_tts_instance = Mock()
        self.mock_tts_class.return_value = self.mock_tts_instance
        self.mock_tts_instance.synthesizer.output_sample_rate = 22050
        self.mock_tts_instance.tts.return_value = np.array([0.1, 0.2, 0.3]) # Dummy audio data

        # Patch the TTS.api.TTS class in the tts_engine module
        self.patcher = patch('tts_lib.tts_engine.TTS', self.mock_tts_class)
        self.patcher.start()

        self.engine = TTSEngine(model_name="test_model", speaker="test_speaker")

    def tearDown(self):
        self.patcher.stop()

    def test_synthesize_normal_text(self):
        segment = SpeechSegment(text="Hello world")
        self.engine.synthesize_to_memory(segment)
        self.mock_tts_instance.tts.assert_called_with(text="Hello world", speaker="test_speaker")

    def test_synthesize_spelled_text(self):
        segment = SpeechSegment(text="AI", spell=True)
        self.engine.synthesize_to_memory(segment)
        expected_ssml = '<speak><say-as interpret-as="spell-out">AI</say-as></speak>'
        self.mock_tts_instance.tts.assert_called_with(text=expected_ssml, speaker="test_speaker")

    def test_synthesize_empty_text(self):
        segment = SpeechSegment(text="")
        result = self.engine.synthesize_to_memory(segment)
        self.assertIsNone(result)
        self.mock_tts_instance.tts.assert_not_called()

if __name__ == '__main__':
    unittest.main()
