"""
Unit tests for the markup parser.
"""

import unittest
import json
import os

# This allows running tests from the root directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tts_lib.markup_parser import BracketMarkupProcessor
from tts_lib.data_structures import SpeechSegment

class TestMarkupParser(unittest.TestCase):
    """Test suite for the BracketMarkupProcessor"""

    def setUp(self):
        """Set up the test case by loading the config and input file."""
        self.config_path = 'config.json'
        self.input_path = 'tests/fixtures/input_test.txt'
        self.output_dir = 'test_output'
        # self.output_path = os.path.join(self.output_dir, 'test_markup_parser_output.json') # Moved to test method for uniqueness

        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        self.processor = BracketMarkupProcessor(config_path=self.config_path)

        with open(self.input_path, 'r', encoding='utf-8') as f:
            self.markup_text = f.read()

    def _write_segments_to_file(self, segments, test_name):
        """Helper to write generated segments to a JSON file for inspection."""
        output_file_name = f"test_markup_parser_output_{test_name}.json"
        output_path = os.path.join(self.output_dir, output_file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([s.__dict__ for s in segments], f, indent=2)
        return output_path

    def test_parser_output_and_correctness(self):
        """Test the parser's output and correctness, writing the result to a file."""
        segments = self.processor.parse_markup(self.markup_text)

        self.output_path = self._write_segments_to_file(segments, self._testMethodName)

        # This is the correct, expected output based on the parser's logic.
        expected_segments = [
            SpeechSegment(text='Welcome to our video presentation!', rate=0.9975, pitch=1.134, volume=1.26, pause_after=1.5),
            SpeechSegment(text='Artificial intelligence, or AI, refers to computer systems that can perform tasks typically requiring human intelligence.'),
            SpeechSegment(text='These include learning, reasoning, and perception.', rate=0.95, pitch=1.05, volume=1.2, pause_after=0.8),
            SpeechSegment(text='There are three main types of AI:', rate=1.05, pitch=1.08, volume=1.05, pause_after=0.5),
            SpeechSegment(text='First,'),
            SpeechSegment(text='Narrow AI', rate=0.95, pitch=1.05, volume=1.2),
            SpeechSegment(text='- which excels at specific tasks like chess or image recognition.')
        ]

        self.assertEqual(len(segments), len(expected_segments),
                         f"FAIL: Expected {len(expected_segments)} segments, but got {len(segments)}. See {self.output_path} for details.")

        for i, (actual, expected) in enumerate(zip(segments, expected_segments)):
            with self.subTest(i=i, msg=f"Comparing segment {i}: '{expected.text[:20]}...'"):
                self.assertEqual(actual.text, expected.text)
                self.assertAlmostEqual(actual.rate, expected.rate, places=4)
                self.assertAlmostEqual(actual.pitch, expected.pitch, places=4)
                self.assertAlmostEqual(actual.volume, expected.volume, places=4)
                self.assertAlmostEqual(actual.pause_before, expected.pause_before, places=4)
                self.assertAlmostEqual(actual.pause_after, expected.pause_after, places=4)

    def test_initial_pause_handling(self):
        """Test that a pause tag at the beginning of the input correctly sets pause_before."""
        markup_with_initial_pause = "[pause:0.75]Hello world!"
        segments = self.processor.parse_markup(markup_with_initial_pause)

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Hello world!")
        self.assertAlmostEqual(segments[0].pause_before, 0.75)
        self.assertAlmostEqual(segments[0].pause_after, 0.0)

        markup_only_initial_pause = "[pause:1.2]"
        segments_only_pause = self.processor.parse_markup(markup_only_initial_pause)
        self.assertEqual(len(segments_only_pause), 1)
        self.assertEqual(segments_only_pause[0].text, "")
        self.assertAlmostEqual(segments_only_pause[0].pause_before, 1.2)
        self.assertAlmostEqual(segments_only_pause[0].pause_after, 0.0)

    def test_spell_tag_processing(self):
        """Test that the [spell] tag correctly processes text by replacing characters with phonetic spellings and creating separate pause segments."""
        # Temporarily set spell_pause_duration to 0.0 for this test
        original_spell_pause_duration = self.processor.spell_pause_duration
        self.processor.spell_pause_duration = 0.0

        spell_markup_text = "The [spell]AI[/] system uses [spell]NASA[/] technology. This is a test of [spell]ABC[/] and [spell]123XYZ[/]."
        segments = self.processor.parse_markup(spell_markup_text)

        self.output_path = self._write_segments_to_file(segments, self._testMethodName)

        # Expected segments for "The [spell]AI[/] system uses [spell]NASA[/] technology. This is a test of [spell]ABC[/] and [spell]123XYZ[/]."
        # Note: Each spelled letter and each pause will be a separate SpeechSegment
        expected_segments = [
            SpeechSegment(text="The"),
            SpeechSegment(text="AAY"),
            SpeechSegment(text="", pause_before=0.0), # Pause after A
            SpeechSegment(text="Eye"),
            SpeechSegment(text="system uses"),
            SpeechSegment(text="En"),
            SpeechSegment(text="", pause_before=0.0), # Pause after N
            SpeechSegment(text="AAY"),
            SpeechSegment(text="", pause_before=0.0), # Pause after A
            SpeechSegment(text="Ess"),
            SpeechSegment(text="", pause_before=0.0), # Pause after S
            SpeechSegment(text="AAY"),
            SpeechSegment(text="technology. This is a test of"),
            SpeechSegment(text="AAY"),
            SpeechSegment(text="", pause_before=0.0), # Pause after A
            SpeechSegment(text="Bee"),
            SpeechSegment(text="", pause_before=0.0), # Pause after B
            SpeechSegment(text="See"),
            SpeechSegment(text="and"),
            SpeechSegment(text="one"),
            SpeechSegment(text="", pause_before=0.0), # Pause after 1
            SpeechSegment(text="two"),
            SpeechSegment(text="", pause_before=0.0), # Pause after 2
            SpeechSegment(text="three"),
            SpeechSegment(text="", pause_before=0.0), # Pause after 3
            SpeechSegment(text="Ex"),
            SpeechSegment(text="", pause_before=0.0), # Pause after X
            SpeechSegment(text="Why"),
            SpeechSegment(text="", pause_before=0.0), # Pause after Y
            SpeechSegment(text="Zee."),
        ]

        self.assertEqual(len(segments), len(expected_segments),
                         f"FAIL: Expected {len(expected_segments)} segments, but got {len(segments)}. See {self.output_path} for details.")

        for i, (actual, expected) in enumerate(zip(segments, expected_segments)):
            with self.subTest(i=i, msg=f"Comparing segment {i}: '{expected.text[:20]}...'"):
                self.assertEqual(actual.text, expected.text)
                self.assertAlmostEqual(actual.pause_before, expected.pause_before, places=4)
                self.assertAlmostEqual(actual.pause_after, expected.pause_after, places=4)
                # Add assertions for other attributes if they are expected to be different from defaults
                self.assertAlmostEqual(actual.rate, expected.rate, places=4)
                self.assertAlmostEqual(actual.pitch, expected.pitch, places=4)
                self.assertAlmostEqual(actual.volume, expected.volume, places=4)
        
        # Restore original spell_pause_duration
        self.processor.spell_pause_duration = original_spell_pause_duration

    def test_punctuation_after_spell_tag(self):
        """Test that punctuation immediately following a [spell] tag is correctly handled."""
        markup_text = "[happy]There are three main types of [spell]AI[/]:[/]"
        segments = self.processor.parse_markup(markup_text)

        self.output_path = self._write_segments_to_file(segments, self._testMethodName)

        expected_segments = [
            SpeechSegment(text="There are three main types of", rate=1.05, pitch=1.08, volume=1.05),
            SpeechSegment(text="AAY", rate=1.05, pitch=1.08, volume=1.05),
            SpeechSegment(text="", pause_before=0.0, rate=1.05, pitch=1.08, volume=1.05), # Pause after A
            SpeechSegment(text="Eye:", rate=1.05, pitch=1.08, volume=1.05), # Colon should be appended to Eye
        ]

        self.assertEqual(len(segments), len(expected_segments),
                         f"FAIL: Expected {len(expected_segments)} segments, but got {len(segments)}. See {self.output_path} for details.")

        for i, (actual, expected) in enumerate(zip(segments, expected_segments)):
            with self.subTest(i=i, msg=f"Comparing segment {i}: '{expected.text[:20]}...'"):
                self.assertEqual(actual.text, expected.text)
                self.assertAlmostEqual(actual.pause_before, expected.pause_before, places=4)
                self.assertAlmostEqual(actual.pause_after, expected.pause_after, places=4)
                self.assertAlmostEqual(actual.rate, expected.rate, places=4)
                self.assertAlmostEqual(actual.pitch, expected.pitch, places=4)
                self.assertAlmostEqual(actual.volume, expected.volume, places=4)

if __name__ == '__main__':
    unittest.main(verbosity=2)
