"""
TTS engine using Coqui TTS.
"""

import numpy as np
from typing import Optional, Tuple

from TTS.api import TTS
from .data_structures import SpeechSegment

class TTSEngine:
    """Text-to-Speech engine using Coqui TTS"""

    def __init__(self, model_name: str = None, speaker: str = None):
        self.model_name = model_name or "tts_models/en/jenny/jenny"
        self.speaker = speaker
        print(f"Loading TTS model: {self.model_name} with speaker: {self.speaker or 'default'}")
        try:
            self.tts = TTS(model_name=self.model_name)
            print("TTS model loaded successfully!")
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            print("Trying fallback model...")
            try:
                self.tts = TTS(model_name="tts_models/en/ljspeech/fast_pitch")
                self.model_name = "tts_models/en/ljspeech/fast_pitch"
                self.speaker = None
                print("Fallback model loaded successfully!")
            except Exception as e2:
                print(f"Error loading fallback model: {e2}")
                raise

    def synthesize_to_memory(self, segment: SpeechSegment) -> Optional[Tuple[np.ndarray, int]]:
        """Synthesize a single speech segment to an in-memory numpy array"""
        if not segment.text.strip():
            return None
        text_to_synthesize = segment.text.strip()
        
        
        try:
            wav = self.tts.tts(text=text_to_synthesize, speaker=self.speaker)
            return np.array(wav), self.tts.synthesizer.output_sample_rate
        except Exception as e:
            print(f"Error synthesizing segment '{text[:50]}...': {e}")
            return None
