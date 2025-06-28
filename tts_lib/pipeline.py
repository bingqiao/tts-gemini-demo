"""
Main TTS pipeline orchestrating all components.
"""

from tqdm import tqdm
import os
import json

from .markup_parser import BracketMarkupProcessor
from .tts_engine import TTSEngine
from .audio_processor import AudioProcessor
from .subtitle_generator import SubtitleGenerator

class TTSPipeline:
    """Main TTS pipeline orchestrating all components"""

    def __init__(self, model_name: str = None, speaker: str = None, config_path: str = "config.json", debug: bool = False, spell_pause_duration: float = 0.0):
        self.markup_processor = BracketMarkupProcessor(config_path, spell_pause_duration)
        self.tts_engine = TTSEngine(model_name, speaker)
        self.audio_processor = AudioProcessor()
        self.subtitle_generator = SubtitleGenerator()
        self.debug = debug
        self.debug_output_dir = None

    def generate_audio_and_subtitles(self, markup_text: str, output_base: str, output_format: str):
        """Generate audio and subtitle files from markup text"""
        print("Parsing markup...")
        segments = self.markup_processor.parse_markup(markup_text)
        print(f"Found {len(segments)} speech segments")

        audio_file = f"{output_base}.{output_format}"
        subtitle_file = f"{output_base}.srt"

        # Setup debug output directory if debug mode is enabled
        if self.debug:
            self.debug_output_dir = f"{os.path.dirname(output_base)}/debug_{os.path.basename(output_base)}"
            os.makedirs(self.debug_output_dir, exist_ok=True)
            print(f"Debug output will be saved to: {self.debug_output_dir}")

        audio_segments = []
        current_time = 0.0

        for i, segment in enumerate(tqdm(segments, desc="Processing segments")):
            if segment.pause_before > 0:
                silence = self.audio_processor.create_silence(segment.pause_before)
                audio_segments.append(silence)
                current_time += segment.pause_before

            if segment.text.strip():
                segment.start_time = current_time
                synthesis_result = self.tts_engine.synthesize_to_memory(segment)

                if synthesis_result:
                    samples, sr = synthesis_result
                    processed_audio = self.audio_processor.apply_effects(samples, sr, segment)
                    
                    if len(processed_audio) < 50:
                        print(f"Warning: Skipping segment '{segment.text[:50]}...' due to short duration ({len(processed_audio)}ms)")
                        continue

                    segment.duration = len(processed_audio) / 1000.0
                    segment.end_time = segment.start_time + segment.duration
                    current_time = segment.end_time
                    audio_segments.append(processed_audio)

                    # Save individual segment audio and JSON data in debug mode
                    if self.debug:
                        segment_base_name = f"segment_{i:03d}"
                        debug_audio_filename = os.path.join(self.debug_output_dir, f"{segment_base_name}.wav")
                        debug_json_filename = os.path.join(self.debug_output_dir, f"{segment_base_name}.json")
                        
                        processed_audio.export(debug_audio_filename, format="wav")
                        with open(debug_json_filename, 'w', encoding='utf-8') as f:
                            json.dump(segment.__dict__, f, indent=2)

            if segment.pause_after > 0:
                silence = self.audio_processor.create_silence(segment.pause_after)
                audio_segments.append(silence)
                current_time += segment.pause_after

        if audio_segments:
            print("Combining audio segments...")
            final_audio = sum(audio_segments)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(audio_file)
            os.makedirs(output_dir, exist_ok=True)

            print(f"Exporting audio to {audio_file}...")
            final_audio.export(audio_file, format=output_format)
            print(f"Audio generated successfully: {audio_file}")
            self.subtitle_generator.generate_srt(segments, subtitle_file)
            return audio_file, subtitle_file
        else:
            print("No valid audio segments generated")
            return None, None
