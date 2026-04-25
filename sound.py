import numpy as np
import pygame


class NotePlayer:
    def __init__(self, hertz, sample_rate, amplitude):
        self._channel = None
        self._sound = self._generate(hertz, sample_rate, amplitude)

    def _generate(self, hertz, sample_rate, amplitude):
        t = np.linspace(0, 2.0, int(sample_rate * 2.0), endpoint=False)
        wave = np.sin(2 * np.pi * hertz * t)
        fade = int(sample_rate * 0.01)
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
        samples = (amplitude * wave * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((samples, samples)))

    def play(self):
        self._channel = self._sound.play(-1)

    def stop(self):
        if self._channel:
            self._channel.fadeout(50)
            self._channel = None


class SoundEngine:
    SAMPLE_RATE = 44100
    AMPLITUDE = 0.05

    def __init__(self):
        pygame.mixer.pre_init(frequency=self.SAMPLE_RATE, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        self._playing = {}

    def play_note(self, note):
        if note.midi_value not in self._playing:
            pn = NotePlayer(note.hertz, self.SAMPLE_RATE, self.AMPLITUDE)
            pn.play()
            self._playing[note.midi_value] = pn

    def stop_note(self, note):
        pn = self._playing.pop(note.midi_value, None)
        if pn:
            pn.stop()