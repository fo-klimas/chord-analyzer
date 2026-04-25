import math
import json
import os

class Note:
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, midi_number):
        self.midi_value = midi_number

    @property
    def hertz(self):
        return 440.0 * (2.0 ** ((self.midi_value - 69) / 12.0))

    @property
    def pitch_class(self):
        return self.NOTES[self.midi_value % 12]

    @property
    def octave(self):
        return (self.midi_value // 12) - 1

    @property
    def name(self):
        return f"{self.pitch_class}{self.octave}"

    def _pair_dissonance(self, other_note):
        amp = 0.24
        f1, f2 = self.hertz, other_note.hertz
        if f1 > f2:
            f1, f2 = f2, f1
        S = amp / (0.021 * f1 + 19)
        x = S * (f2 - f1)
        total = math.exp(-3.5 * x) - math.exp(-5.75 * x)
        return total ** 2


class ChordLibrary:
    def __init__(self, filepath=None):
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "chords.json")
        self._filepath = filepath
        with open(filepath, "r") as f:
            raw = json.load(f)
        self._library = {
            tuple(int(i) for i in k.split(",")): v
            for k, v in raw.items()
        }
 
    def lookup(self, intervals):
        return self._library.get(intervals, "Unknown Chord")
 
    def add(self, intervals: tuple, name: str):
        self._library[intervals] = name
        serialized = {",".join(str(i) for i in k): v for k, v in self._library.items()}
        with open(self._filepath, "w") as f:
            json.dump(serialized, f, indent=2)


class Chord:
    def __init__(self, raw_midi_notes, library):
        self.notes = [Note(n) for n in sorted(raw_midi_notes)]
        self._library = library

    @property
    def hertz_vector(self):
        return [note.hertz for note in self.notes]

    @property
    def intervals(self):
        if not self.notes:
            return ()
        root = self.notes[0].midi_value
        return tuple(sorted(set((n.midi_value - root) % 12 for n in self.notes)))

    @property
    def name(self):
        return self._library.lookup(self.intervals)

    @property
    def chord_string(self):
        if not self.notes:
            return ""
        return f"Chord: {self.notes[0].pitch_class} {self.name} {self.intervals}"

    @property
    def A(self):
        n = len(self.notes)
        if n == 1:
            return 1
        return (n // 2) * 2

    @property
    def B(self):
        n = len(self.notes)
        return ((n - 1) // 2) * 2 + 1

    @property
    def dissonance(self):
        n = len(self.notes)
        if n < 2:
            return 0.0
        diss = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                diss += self.notes[i]._pair_dissonance(self.notes[j])
        return diss