import pygame
import pygame.midi

from theory import Note, Chord


class InputHandler:
    def __init__(self, library, sound_engine):
        self.library = library
        self.sound_engine = sound_engine
        self.active_notes = set()

    def update(self, events: list) -> Chord:
        return


class MIDIHandler(InputHandler):
    def __init__(self, device_id, library, sound_engine):
        super().__init__(library, sound_engine)
        try:
            self.midi_input = pygame.midi.Input(device_id)
        except Exception as e:
            print(f"Error opening MIDI device: {e}")
            self.midi_input = None

    def update(self, events: list) -> Chord:
        if self.midi_input and self.midi_input.poll():
            midi_events = self.midi_input.read(10)
            for event in midi_events:
                status, note, velocity = event[0][0], event[0][1], event[0][2]
                if status == 144 and velocity > 0:
                    self.active_notes.add(note)
                    self.sound_engine.play_note(Note(note))
                elif status == 128 or (status == 144 and velocity == 0):
                    self.active_notes.discard(note)
                    self.sound_engine.stop_note(Note(note))
        return Chord(self.active_notes, self.library)


class KeyboardHandler(InputHandler):
    def __init__(self, library, sound_engine):
        super().__init__(library, sound_engine)
        self.key_map = {
            pygame.K_z: 60, pygame.K_s: 61, pygame.K_x: 62, pygame.K_d: 63,
            pygame.K_c: 64, pygame.K_v: 65, pygame.K_g: 66, pygame.K_b: 67,
            pygame.K_h: 68, pygame.K_n: 69, pygame.K_j: 70, pygame.K_m: 71,
            pygame.K_q: 72, pygame.K_2: 73, pygame.K_w: 74, pygame.K_3: 75,
            pygame.K_e: 76, pygame.K_r: 77, pygame.K_5: 78, pygame.K_t: 79,
            pygame.K_6: 80, pygame.K_y: 81, pygame.K_7: 82, pygame.K_u: 83
        }

    def update(self, events: list) -> Chord:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in self.key_map:
                midi_value = self.key_map[event.key]
                self.active_notes.add(midi_value)
                self.sound_engine.play_note(Note(midi_value))
            elif event.type == pygame.KEYUP and event.key in self.key_map:
                midi_value = self.key_map[event.key]
                self.active_notes.discard(midi_value)
                self.sound_engine.stop_note(Note(midi_value))
        return Chord(self.active_notes, self.library)
