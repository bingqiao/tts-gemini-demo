"""
Data structures for the TTS pipeline.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SpeechSegment:
    """Represents a segment of speech with its properties"""
    text: str
    pause_before: float = 0.0
    pause_after: float = 0.0
    rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    spell: bool = False
    voice: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0

@dataclass
class SubtitleEntry:
    """Represents a subtitle entry"""
    index: int
    start_time: str
    end_time: str
    text: str
