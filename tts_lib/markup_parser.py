"""
Parses bracket markup for TTS control, supporting nesting.
"""

import re
import json
import string
from typing import List, Dict, Tuple, Any
from copy import deepcopy

from .data_structures import SpeechSegment

class BracketMarkupProcessor:
    """Processes bracket markup format for TTS control using external config, supporting nesting."""

    def __init__(self, config_path: str = "config.json", spell_pause_duration: float = 0.0):
        self.emotion_presets, self.modifier_presets = self._load_presets(config_path)
        self.spell_pause_duration = spell_pause_duration
        # Regex to find all tags and plain text segments
        # Order matters: specific tags first, then general text
        self.token_pattern = re.compile(r'(\[pause:[0-9.]+\]|\[[^\]]+\]|\[/\]|[^[\]]+)')

    def _load_presets(self, config_path: str) -> Tuple[Dict, Dict]:
        """Loads presets from a JSON config file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"Loaded presets from {config_path}")
                return config.get("emotion_presets", {}), config.get("modifier_presets", {})
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}. Using empty presets.")
            return {}, {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {config_path}. Using empty presets.")
            return {}, {}

    def _get_default_attrs(self) -> Dict[str, float]:
        """Returns a fresh set of default attributes."""
        return {'rate': 1.0, 'pitch': 1.0, 'volume': 1.0, 'pause_before': 0.0, 'pause_after': 0.0, 'spell': False}

    _PHONETIC_SPELLING_MAP = {
        'A': 'AAY', 'B': 'Bee', 'C': 'See', 'D': 'Dee', 'E': 'Eee',
        'F': 'Eff', 'G': 'Gee', 'H': 'Aitch', 'I': 'Eye', 'J': 'Jay',
        'K': 'Kay', 'L': 'Ell', 'M': 'Em', 'N': 'En', 'O': 'Oh',
        'P': 'Pee', 'Q': 'Cue', 'R': 'Ar', 'S': 'Ess', 'T': 'Tee',
        'U': 'You', 'V': 'Vee', 'W': 'Double-you', 'X': 'Ex', 'Y': 'Why',
        'Z': 'Zee',
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }

    def _spell_text(self, text: str) -> str:
        """Handles spelling out text by replacing characters with their phonetic pronunciation and adding separators."""
        processed_words = []
        for char in text:
            upper_char = char.upper()
            if upper_char in self._PHONETIC_SPELLING_MAP:
                processed_words.append(self._PHONETIC_SPELLING_MAP[upper_char])
            else:
                # Fallback for characters not in map (e.g., punctuation, spaces)
                processed_words.append(char)
        return ' '.join(processed_words)

    def _apply_attributes(self, current_attrs: Dict[str, float], new_attrs_str: str) -> Dict[str, float]:
        """Applies new attributes from a string to the current attributes."""
        attrs = deepcopy(current_attrs)
        for attr in new_attrs_str.split(','):
            attr = attr.strip().lower()
            if ':' in attr:
                key, value = attr.split(':', 1)
                try:
                    if key.strip() == 'spell': # Handle spell attribute specifically
                        attrs['spell'] = (value.strip().lower() == 'true' or value.strip() == '1')
                    elif key.strip() in attrs:
                        attrs[key.strip()] = float(value.strip())
                except ValueError:
                    continue
            elif attr == 'spell': # Handle standalone spell flag
                attrs['spell'] = True
            elif attr in self.emotion_presets:
                for key, value in self.emotion_presets[attr].items():
                    attrs[key] *= value
            elif attr in self.modifier_presets:
                for key, value in self.modifier_presets[attr].items():
                    attrs[key] *= value
        return attrs

    

    def parse_markup(self, markup_text: str) -> List[SpeechSegment]:
        """Parse bracket format, supporting nesting: [happy,slower]Hello [emphasis]world![/] [/]"""
        segments: List[SpeechSegment] = []
        attribute_stack: List[Dict[str, float]] = [self._get_default_attrs()]
        
        tokens = self.token_pattern.findall(markup_text)

        current_text_buffer = []
        text_segment_created = False

        def _flush_text_buffer():
            nonlocal current_text_buffer, segments, text_segment_created
            if current_text_buffer:
                text_content = " ".join(current_text_buffer).strip()
                if text_content:
                    # Get base attributes from the current stack level
                    attrs_for_segment = deepcopy(attribute_stack[-1])
                    # Remove pause and spell attributes from base_attrs as they will be handled explicitly
                    attrs_for_segment.pop('pause_before', None)
                    attrs_for_segment.pop('pause_after', None)
                    attrs_for_segment.pop('spell', None) # 'spell' is an internal flag, not a SpeechSegment attribute

                    # Check if the content is just punctuation
                    if all(c in string.punctuation for c in text_content) and segments and segments[-1].text != "":
                        segments[-1].text += text_content
                    else:
                        text_segment_created = True
                        # Get base attributes from the current stack level
                        attrs_for_segment = deepcopy(attribute_stack[-1])
                        # Remove pause and spell attributes from base_attrs as they will be handled explicitly
                        attrs_for_segment.pop('pause_before', None)
                        attrs_for_segment.pop('pause_after', None)
                        attrs_for_segment.pop('spell', None) # 'spell' is an internal flag, not a SpeechSegment attribute

                        if attribute_stack[-1].get('spell'): # Check 'spell' from the original attribute_stack
                            spelled_out_chars = []
                            for char in text_content:
                                upper_char = char.upper()
                                if upper_char in self._PHONETIC_SPELLING_MAP:
                                    spelled_out_chars.append(self._PHONETIC_SPELLING_MAP[upper_char])
                                else:
                                    spelled_out_chars.append(char)

                            for i, char_text in enumerate(spelled_out_chars):
                                # Create segment for the character's sound
                                segment = SpeechSegment(text=char_text, pause_before=0.0, pause_after=0.0, **attrs_for_segment)
                                segments.append(segment)
                                if i < len(spelled_out_chars) - 1: # Add pause after each letter except the last
                                    # Create segment for the pause
                                    segments.append(SpeechSegment(text="", pause_before=self.spell_pause_duration, pause_after=0.0, **attrs_for_segment))
                        else: # Regular text or mixed content
                            # For regular text, use the pause_before from the current_attrs
                            # and set pause_after to 0.0 (it will be accumulated by subsequent pause tags)
                            segment = SpeechSegment(text=text_content,
                                                    pause_before=attribute_stack[-1]['pause_before'],
                                                    pause_after=0.0,
                                                    **attrs_for_segment)
                            segments.append(segment)
                current_text_buffer = []
                # Reset pause_before for the next segment, as it's been consumed by this one
                attribute_stack[-1]['pause_before'] = 0.0


        for token in tokens:
            if token.startswith('[') and token.endswith(']'):
                if token == '[/]': # Closing tag
                    _flush_text_buffer() # Flush text before changing attributes
                    if len(attribute_stack) > 1:
                        attribute_stack.pop()
                    else:
                        pass
                elif token.startswith('[pause:'): # Pause tag
                    _flush_text_buffer() # Flush text before a pause
                    try:
                        duration = float(token[7:-1])
                        if segments:
                            segments[-1].pause_after += duration
                        else:
                            attribute_stack[-1]['pause_before'] += duration
                    except ValueError:
                        pass
                else: # Opening tag with attributes (e.g., [happy,slower], [spell])
                    # Check if attributes are changing, if so, flush current text
                    attrs_str = token[1:-1] # Remove brackets
                    temp_attrs = self._apply_attributes(deepcopy(attribute_stack[-1]), attrs_str)
                    
                    # Only flush if the new attributes are different from the current ones
                    # and there's text in the buffer
                    if current_text_buffer and temp_attrs != attribute_stack[-1]:
                        _flush_text_buffer()

                    attribute_stack.append(temp_attrs)
            else: # Plain text
                if token.strip():
                    current_text_buffer.append(re.sub(r'\s+', ' ', token).strip())

        _flush_text_buffer() # Flush any remaining text at the end of the markup

        # Final handling for cases where only pauses or empty text were processed
        if not text_segment_created and attribute_stack[-1]['pause_before'] > 0:
            segments.append(SpeechSegment(text="", pause_before=attribute_stack[-1]['pause_before']))
        elif not segments and not text_segment_created:
            return [SpeechSegment(text="")]
        
        return segments