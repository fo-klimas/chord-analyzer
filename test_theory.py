import unittest
from theory import Note, Chord, ChordLibrary

class TestTheory(unittest.TestCase):
    def setUp(self):
        # Initialize library for testing lookup logic
        self.library = ChordLibrary()

    def test_note_conversion(self):
        # Test MIDI to Pitch Class and Name conversion
        c4 = Note(60)
        self.assertEqual(c4.pitch_class, 'C')
        self.assertEqual(c4.name, 'C4')
        
        a4 = Note(69)
        self.assertEqual(a4.hertz, 440.0)

    def test_chord_identification(self):
        # Test if a Major Triad (C, E, G) is correctly identified
        major_triad_midi = {60, 64, 67}
        chord = Chord(major_triad_midi, self.library)
        
        self.assertEqual(chord.intervals, (0, 4, 7))
        self.assertEqual(chord.name, "Major Triad")

    def test_dissonance_calculation(self):
        # Ensure dissonance is 0 for a single note and positive for a cluster
        single_note = Chord({60}, self.library)
        self.assertEqual(single_note.dissonance, 0.0)
        
        cluster = Chord({60, 61}, self.library)
        self.assertGreater(cluster.dissonance, 0.0)

if __name__ == '__main__':
    unittest.main()