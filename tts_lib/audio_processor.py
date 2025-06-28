"""
Audio processing for the TTS pipeline.
"""

import numpy as np
import librosa
from pydub import AudioSegment

from .data_structures import SpeechSegment

class AudioProcessor:
    """Audio processing using PyDub and Librosa on in-memory audio data"""

    @staticmethod
    def apply_effects(samples: np.ndarray, sr: int, segment: SpeechSegment) -> AudioSegment:
        """Apply audio effects based on segment properties to a numpy array"""
        # Ensure samples are float32 for librosa
        samples = samples.astype(np.float32)

        # Apply rate change (tempo)
        if segment.rate != 1.0:
            samples = librosa.effects.time_stretch(samples, rate=segment.rate)

        # Apply pitch change
        if segment.pitch != 1.0:
            n_steps = (segment.pitch - 1.0) * 12
            samples = librosa.effects.pitch_shift(samples, sr=sr, n_steps=n_steps)

        # Apply volume change
        if segment.volume != 1.0:
            samples *= segment.volume

        # Convert numpy array to AudioSegment
        samples_int16 = (samples * 32767).astype(np.int16)
        audio = AudioSegment(
            samples_int16.tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=1
        )
        return audio

    @staticmethod
    def create_silence(duration_seconds: float, sample_rate: int = 22050) -> AudioSegment:
        """Create silent audio segment"""
        return AudioSegment.silent(duration=int(duration_seconds * 1000), frame_rate=sample_rate)
