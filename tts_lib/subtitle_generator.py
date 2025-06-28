from typing import List
from .data_structures import SpeechSegment

class SubtitleGenerator:
    """Generate SRT subtitle files"""

    @staticmethod
    def format_time(seconds: float) -> str:
        """Convert seconds to SRT time format: 00:00:01,000"""
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        ms = (s % 1) * 1000
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(ms):03d}"

    @staticmethod
    def generate_srt(segments: List[SpeechSegment], output_file: str):
        """Generate SRT subtitle file from speech segments"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(filter(lambda s: s.text.strip() and s.duration > 0, segments), 1):
                f.write(f"{i}\n")
                f.write(f"{SubtitleGenerator.format_time(segment.start_time)} --> {SubtitleGenerator.format_time(segment.end_time)}\n")
                f.write(f"{segment.text.strip()}\n\n")
        print(f"Subtitle file generated: {output_file}")
