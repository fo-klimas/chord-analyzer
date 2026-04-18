import pygame
import pygame.midi
from abc import ABC, abstractmethod

class InputHandler(ABC):
    def __init__(self):
        self.active_notes = set()
    
    def update(self, events):
        return self.active_notes

class MIDIHandler(InputHandler):
    def __init__(self, device_id):
        super().__init__()
        try:
            pygame.midi.init()
            self.midi_input = pygame.midi.Input(device_id)
        except Exception as e:
            print(f"Error opening MIDI device: {e}")
            self.midi_input = None

    def update(self, events=None):
        if self.midi_input and self.midi_input.poll():
            midi_events = self.midi_input.read(10)
            for event in midi_events:
                status, note, velocity = event[0][0], event[0][1], event[0][2]

                if status == 144 and velocity > 0:
                    self.active_notes.add(note)
                elif status == 128 or (status == 144 and velocity == 0):
                    self.active_notes.discard(note)
        
        return self.active_notes
    
class KeyboardHandler(InputHandler):
    def __init__(self):
        super().__init__()
        self.key_map = {
            pygame.K_a: 60, pygame.K_w: 61, pygame.K_s: 62, 
            pygame.K_e: 63, pygame.K_d: 64, pygame.K_f: 65
        }

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in self.key_map:
                    self.active_notes.add(self.key_map[event.key])
            elif event.type == pygame.KEYUP:
                if event.key in self.key_map:
                    self.active_notes.discard(self.key_map[event.key])
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
        return self.active_notes
    
class InputFactory:
    @staticmethod
    def get_input_source():
        print("1: Keyboard | 2: MIDI")
        try:
            choice = input("Selection: ").strip()
            if choice == '2':
                device_id = DeviceManager._select_midi_id()
                if device_id is not None:
                    return MIDIHandler(device_id)
            print("Invalid selection. Defaulting to Keyboard.")
        except Exception as e:
            print(f"Error: {e}. Defaulting to Keyboard.")
        return KeyboardHandler()

class DeviceManager: 
    @staticmethod
    def _select_midi_id():
        pygame.midi.init()
        device_count = pygame.midi.get_count()
        valid_ids = []

        print("\n--- Active MIDI Devices ---")
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            if info[2] == 1: 
                name = info[1].decode('utf-8')
                valid_ids.append(i)
                print(f"[{i}] {name}")

        if not valid_ids:
            print("No MIDI devices found.")
            return None

        try:
            selection = int(input("\nEnter MIDI Device ID: "))
            return selection if selection in valid_ids else None
        except ValueError:
            return None

class Note:
    NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, midi_number):
        self.midi_value = midi_number

    @property
    def hertz(self):
        return 440.0 * (2.0 ** ((self.midi_value - 69) / 12.0))

    @property
    def pitch_class(self):
        return self.NAMES[self.midi_value % 12]

    @property
    def octave(self):
        return (self.midi_value // 12) - 1

    @property
    def name(self):
        return f"{self.pitch_class()}{self.octave()}"

class Chord:
    def __init__(self, raw_midi_notes):
        self.notes = [Note(n) for n in sorted(raw_midi_notes)]
    
    @property
    def hertz_vector(self):
        return [note.hertz for note in self.notes]
    
    def get_interval_vector(self):
        vector = [0] * 6
        n = len(self.notes)
        if n < 2:
            return vector
        for i in range(n):
            for j in range(i + 1, n):
                diff = abs(self.notes[i].midi_value - self.notes[j].midi_value) % 12    
                if diff > 6:
                    diff = 12 - diff
                if diff > 0:
                    vector[diff - 1] += 1
        return vector
    
    def get_chord_string(self):
        if self.notes:
            return ", ".join(f"{n.hertz:.2f}Hz" for n in self.notes)
        else:
            return ""
    
    def __eq__(self, other):
        if not isinstance(other, Chord):
            return False
        return [n.midi_value for n in self.notes] == [n.midi_value for n in other.notes]

class NotePrinter:
    def __init__(self):
        self.last_chord = None

    def update(self, current_chord):
        if current_chord != self.last_chord:
            display_text = current_chord.get_chord_string()
            
            if display_text:
                print(f"Notes Changed: [{display_text}]")
            else:
                print("All notes released.")
            
            self.last_chord = current_chord

class ChordApp:
    def __init__(self, handler):
        pygame.init()
        self.screen = pygame.display.set_mode((200, 100))
        pygame.display.set_caption("Input Focus")
        self.handler = handler
        self.printer = NotePrinter()
        self.clock = pygame.time.Clock()
        self.running = True

    def run(self):
        try:
            while self.running:
                self._process_logic()
                self.clock.tick(60)
        except KeyboardInterrupt:
            self.running = False
        finally:
            pygame.midi.quit()
            pygame.quit()
    
    def _process_logic(self):
        events = pygame.event.get()
        raw_notes = self.handler.update(events)
        current_chord = Chord(raw_notes)
        self.printer.update(current_chord)

if __name__ == "__main__":
    selection = InputFactory.get_input_source()
    app = ChordApp(selection)
    app.run()