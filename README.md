# Text-to-Speech with Subtitle Generation

This project provides a command-line tool for generating audio and subtitles from text files with bracket-based markup. It uses the TTS (Text-to-Speech) library to convert text into speech and supports customizable speech attributes like emotion, speed, and pauses, as defined in a configuration file. The tool also generates subtitle files synchronized with the audio output.

N.B. recommend to use python virtual environment

on macOS:
```
python -m venv venv
source venv/bin/activate
```

### Bracket Markup Format
The input text file uses a bracket-based markup to control speech attributes. Example:
```
[happy,slower]Hello![/] Normal text [pause:1.0] More text.
```
- `[happy,slower]`: Applies the `happy` and `slower` presets (defined in `config.json`).
- `[/]`: Ends the current markup block.
- `[pause:1.0]`: Inserts a 1-second pause.
- Presets are defined in the `config.json` file.

## Installation
```
pip install TTS pydub librosa soundfile numpy tqdm
```

## Run test
```
python -m unittest tests/test_markup_parser.py
```

## Generate audio
```
python tts_generator.py input.txt 
```
or with --debug option that generates segments json and audio files for troubleshooting.

## Output
- **Audio**: Generated audio files are saved in the `out/` directory with a timestamped filename (e.g., `out/20250628_215500_output.wav`).
- **Subtitles**: SRT subtitle files are saved alongside the audio with the same base name (e.g., `out/20250628_215500_output.srt`).
- **Debug Mode**: If `--debug` is enabled, individual audio segments are saved for inspection.

## Clean up
```
python tts_generator.py input.txt 
```

## License
This project is licensed under the MIT License.