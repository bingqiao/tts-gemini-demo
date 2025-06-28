
"""
Advanced Text-to-Speech with Subtitle Generation
"""

import argparse
import sys
import os
import datetime
import shutil # Import shutil for directory removal

from TTS.api import TTS
from pydub import AudioSegment

from tts_lib.pipeline import TTSPipeline

def load_markup_file(file_path: str) -> str:
    """Load markup text from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        sys.exit(1)

def list_models():
    """Lists available TTS models"""
    print("Available TTS models:")
    for model in TTS.list_models():
        print(f"- {model}")

def list_speakers(model_name):
    """Lists available speakers for a given model"""
    try:
        tts = TTS(model_name=model_name)
        if tts.is_multi_speaker:
            print(f"Available speakers for {model_name}:")
            for speaker in tts.speakers:
                print(f"- {speaker}")
        else:
            print(f"Model {model_name} is not a multi-speaker model.")
    except Exception as e:
        print(f"Could not load model {model_name}: {e}")

def clean_up_files():
    """Removes all generated output, test output, and __pycache__ directories."""
    print("Cleaning up temporary and generated files...")
    
    dirs_to_remove = [
        'out',
        'test_output',
        '__pycache__',
        'tts_lib/__pycache__',
        'tests/__pycache__'
    ]

    for d in dirs_to_remove:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"Removed: {d}/")
            except OSError as e:
                print(f"Error removing {d}/: {e}")
        else:
            print(f"Skipped: {d}/ (not found)")
    print("Cleanup complete.")

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate audio and subtitles from bracket markup text.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python tts_generator.py script.txt
  python tts_generator.py script.txt -o my_audio -f mp3 --play
  python tts_generator.py --list-models
  python tts_generator.py --model "tts_models/en/vctk/vits" --list-speakers
  python tts_generator.py --clean

Bracket Markup Format:
  [happy,slower]Hello![/] Normal text [pause:1.0] More text.
  Presets are defined in config.json.
"""
    )
    parser.add_argument('input_file', nargs='?', default=None, help='Input markup text file.')
    parser.add_argument('--output', '-o', default='output', help='Output base name (default: output)')
    parser.add_argument('--format', '-f', default='wav', choices=['wav', 'mp3'], help='Output audio format (default: wav)')
    parser.add_argument('--play', '-p', action='store_true', help='Play audio after generation')
    parser.add_argument('--model', '-m', default=None, help='TTS model name (e.g., tts_models/en/jenny/jenny)')
    parser.add_argument('--speaker', '-s', default=None, help='Speaker name for multi-speaker models')
    parser.add_argument('--config', '-c', default='config.json', help='Path to config file (default: config.json)')
    parser.add_argument('--list-models', action='store_true', help='List available TTS models and exit')
    parser.add_argument('--list-speakers', action='store_true', help='List speakers for the specified model and exit')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (e.g., individual segment audio files)')
    parser.add_argument('--spell-pause-duration', type=float, default=0.0, help='Duration of pause between spelled-out letters (default: 0.0 seconds)')
    parser.add_argument('--clean', action='store_true', help='Remove all generated output and temporary files')

    args = parser.parse_args()

    if args.clean:
        clean_up_files()
        sys.exit(0)

    if args.list_models:
        list_models()
        sys.exit(0)

    if args.list_speakers:
        if not args.model:
            print("Error: --model must be specified to list speakers.")
            sys.exit(1)
        list_speakers(args.model)
        sys.exit(0)

    if not args.input_file:
        parser.print_help()
        print("\nError: input_file is required unless using discovery flags.")
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)

    print("=" * 70)
    print("Advanced Text-to-Speech with Subtitle Generation")
    print("=" * 70)

    try:
        markup_text = load_markup_file(args.input_file)
        pipeline = TTSPipeline(model_name=args.model, speaker=args.speaker, config_path=args.config, debug=args.debug)

        # Generate timestamped output filename
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        base_name = args.output
        if base_name == 'output':
            final_output_base = f"out/{timestamp}_output"
        else:
            final_output_base = f"out/{timestamp}_{base_name}"

        audio_file, subtitle_file = pipeline.generate_audio_and_subtitles(markup_text, final_output_base, args.format)

        if audio_file and subtitle_file:
            print("\n" + "="*50 + "\nGENERATION COMPLETE!\n" + "="*50)
            print(f"Audio file: {audio_file}")
            print(f"Subtitle file: {subtitle_file}")

            if args.play:
                try:
                    from pydub.playback import play
                    audio = AudioSegment.from_file(audio_file, format=args.format)
                    print("\nPlaying audio... (press Ctrl+C to stop)")
                    play(audio)
                except ImportError:
                    print("\nInstall pygame for audio playback: pip install pygame")
                except KeyboardInterrupt:
                    print("\nPlayback stopped.")
        else:
            print("Failed to generate audio and subtitles")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
