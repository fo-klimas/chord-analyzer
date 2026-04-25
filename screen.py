import math
import sys
import time
from enum import Enum, auto

import pygame
import pygame.midi

from input import KeyboardHandler, MIDIHandler

class UI:
    COLOR_BG = (0, 0, 0)
    COLOR_BTN = (0, 60, 60)
    COLOR_BTN_HOVER = (0, 100, 100)
    COLOR_TEXT = (0, 255, 200)

    def _draw_button(self, rect, label, font):
        color = self.COLOR_BTN_HOVER if rect.collidepoint(pygame.mouse.get_pos()) else self.COLOR_BTN
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        self._draw_text(label, font, rect.centerx, rect.centery)

    def _draw_text(self, text, font, x, y):
        surface = font.render(text, True, self.COLOR_TEXT)
        self.screen.blit(surface, surface.get_rect(center=(x, y)))

class MainMenu(UI):
    class State(Enum):
        EDIT = auto()
        EXIT = auto()

    def __init__(self, screen, library):
        self.screen = screen
        self.library = library
        self._font = pygame.font.SysFont("monospace", 28)
        self._small_font = pygame.font.SysFont("monospace", 20)
        self._tiny_font = pygame.font.SysFont("monospace", 16)
        self._intervals_text = ""
        self._name_text = ""
        self._active_field = None
        self._status_msg = ""
        self._status_timer = 0
        self._btn_device = pygame.Rect(290, 380, 200, 50)
        self._btn_save = pygame.Rect(570, 270, 120, 40)
        self._field_intervals = pygame.Rect(240, 240, 310, 38)
        self._field_name = pygame.Rect(240, 300, 310, 38)
        self._state = self.State.EDIT

    def run(self):
        clock = pygame.time.Clock()
        while self._state != self.State.EXIT:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)
            self._draw()
            clock.tick(60)

    def _handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._field_intervals.collidepoint(event.pos):
                self._active_field = "intervals"
            elif self._field_name.collidepoint(event.pos):
                self._active_field = "name"
            elif self._btn_save.collidepoint(event.pos):
                self._try_save()
            elif self._btn_device.collidepoint(event.pos):
                self._active_field = None
                self._state = self.State.EXIT
            else:
                self._active_field = None

        elif event.type == pygame.KEYDOWN and self._active_field:
            if event.key == pygame.K_BACKSPACE:
                if self._active_field == "intervals":
                    self._intervals_text = self._intervals_text[:-1]
                else:
                    self._name_text = self._name_text[:-1]
            elif event.key == pygame.K_TAB:
                self._active_field = "name" if self._active_field == "intervals" else "intervals"
            elif event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
                char = event.unicode
                if self._active_field == "intervals":
                    if char in "0123456789, ":
                        self._intervals_text += char
                else:
                    self._name_text += char

    def _try_save(self):
        try:
            intervals = tuple(int(x.strip()) for x in self._intervals_text.split(",") if x.strip())
            if not intervals:
                raise ValueError
            name = self._name_text.strip()
            if not name:
                raise ValueError
            self.library.add(intervals, name)
            self._status_msg = f"Saved: {name}"
            self._intervals_text = ""
            self._name_text = ""
        except ValueError:
            self._status_msg = "Invalid — use format: 0,4,7  and a name"
        self._status_timer = 180

    def _draw(self):
        self.screen.fill(self.COLOR_BG)

        self._draw_text("CHORD VISUALIZER", self._font, 400, 80)
        self._draw_text("Intervals:", self._small_font, 160, 258)
        self._draw_text("Name:", self._small_font, 160, 316)
        self._draw_text("Add chord definition  (optional)", self._small_font, 400, 210)

        for rect, field, text in [
            (self._field_intervals, "intervals", self._intervals_text),
            (self._field_name,      "name",      self._name_text),
        ]:
            border_color = self.COLOR_TEXT if self._active_field == field else self.COLOR_BTN
            pygame.draw.rect(self.screen, self.COLOR_BTN, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
            cursor = "|" if self._active_field == field else ""
            label = self._tiny_font.render(text + cursor, True, self.COLOR_TEXT)
            self.screen.blit(label, (rect.x + 8, rect.y + 10))

        self._draw_button(self._btn_save, "SAVE", self._small_font)
        self._draw_text("e.g.  0,4,7  ->  Major", self._tiny_font, 400, 358)

        if self._status_timer > 0:
            self._draw_text(self._status_msg, self._small_font, 400, 445)
            self._status_timer -= 1
        
        self._draw_button(self._btn_device, "SELECT DEVICE", self._small_font)

        pygame.display.flip()

class InputSelector(UI):
    class State(Enum):
        MAIN_MENU = auto()
        INPUT_TYPE = auto()
        MIDI_DEVICE = auto()
        MESSAGE = auto()
        COMPLETE = auto()

    def __init__(self, library, sound_engine, screen=None):
        self.library = library
        self.sound_engine = sound_engine
        self.screen = screen or pygame.display.set_mode((800, 600))
        self.font = pygame.font.SysFont("monospace", 28)
        self.small_font = pygame.font.SysFont("monospace", 20)
        self.tiny_font = pygame.font.SysFont("monospace", 16)
        self._clock = pygame.time.Clock()
        self._state = self.State.MAIN_MENU
        self._result_handler = None
        self._message_text = ""
        self._message_deadline = 0.0
        self._midi_devices = {}
        self._intervals_text = ""
        self._name_text = ""
        self._active_field = None
        self._status_msg = ""
        self._status_timer = 0
        self._btn_device = pygame.Rect(290, 380, 200, 50)
        self._btn_save = pygame.Rect(570, 270, 120, 40)
        self._field_intervals = pygame.Rect(240, 240, 310, 38)
        self._field_name = pygame.Rect(240, 300, 310, 38)
        self._choice_buttons = {
            "KEYBOARD": pygame.Rect(150, 250, 180, 60),
            "MIDI": pygame.Rect(470, 250, 180, 60),
        }
        self._device_buttons = {}

    def get_handler(self):
        self._reset_state_machine()

        while self._state != self.State.COMPLETE:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self._handle_event(event)
            self._update_state()
            self._draw_state()
            pygame.display.flip()
            self._clock.tick(60)

        return self._result_handler or KeyboardHandler(self.library, self.sound_engine)

    def _reset_state_machine(self):
        self._state = self.State.MAIN_MENU
        self._result_handler = None
        self._message_text = ""
        self._message_deadline = 0.0
        self._midi_devices = {}
        self._device_buttons = {}
        self._active_field = None
        self._status_msg = ""
        self._status_timer = 0

    def _handle_event(self, event):
        if self._state == self.State.MAIN_MENU:
            self._handle_main_menu_event(event)
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        if self._state == self.State.INPUT_TYPE:
            self._handle_input_type_click(event.pos)
        elif self._state == self.State.MIDI_DEVICE:
            self._handle_midi_device_click(event.pos)

    def _handle_main_menu_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._field_intervals.collidepoint(event.pos):
                self._active_field = "intervals"
            elif self._field_name.collidepoint(event.pos):
                self._active_field = "name"
            elif self._btn_save.collidepoint(event.pos):
                self._try_save()
            elif self._btn_device.collidepoint(event.pos):
                self._active_field = None
                self._state = self.State.INPUT_TYPE
            else:
                self._active_field = None

        elif event.type == pygame.KEYDOWN and self._active_field:
            if event.key == pygame.K_BACKSPACE:
                if self._active_field == "intervals":
                    self._intervals_text = self._intervals_text[:-1]
                else:
                    self._name_text = self._name_text[:-1]
            elif event.key == pygame.K_TAB:
                self._active_field = "name" if self._active_field == "intervals" else "intervals"
            elif event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
                char = event.unicode
                if self._active_field == "intervals":
                    if char in "0123456789, ":
                        self._intervals_text += char
                else:
                    self._name_text += char

    def _handle_input_type_click(self, pos):
        for label, rect in self._choice_buttons.items():
            if not rect.collidepoint(pos):
                continue
            if label == "KEYBOARD":
                self._result_handler = KeyboardHandler(self.library, self.sound_engine)
                self._state = self.State.COMPLETE
            else:
                self._enter_midi_selection()
            return

    def _handle_midi_device_click(self, pos):
        for name, rect in self._device_buttons.items():
            if rect.collidepoint(pos):
                device_id = self._midi_devices[name]
                self._result_handler = MIDIHandler(device_id, self.library, self.sound_engine)
                self._state = self.State.COMPLETE
                return

    def _enter_midi_selection(self):
        if not pygame.midi.get_init():
            pygame.midi.init()

        raw_devices = self._scan_devices()
        if not raw_devices:
            self._result_handler = KeyboardHandler(self.library, self.sound_engine)
            self._message_text = "No MIDI devices found. Defaulting to Keyboard."
            self._message_deadline = time.time() + 2
            self._state = self.State.MESSAGE
            return

        id_by_name = {name: did for did, name in raw_devices.items()}
        self._midi_devices = id_by_name
        self._device_buttons = {
            name: pygame.Rect(200, 160 + i * 80, 400, 50)
            for i, name in enumerate(id_by_name)
        }
        self._state = self.State.MIDI_DEVICE

    def _update_state(self):
        if self._state == self.State.MESSAGE and time.time() >= self._message_deadline:
            self._state = self.State.COMPLETE
        if self._status_timer > 0:
            self._status_timer -= 1

    def _draw_state(self):
        self.screen.fill(self.COLOR_BG)
        if self._state == self.State.MAIN_MENU:
            self._draw_main_menu_state()
        elif self._state == self.State.INPUT_TYPE:
            self._draw_input_type_state()
        elif self._state == self.State.MIDI_DEVICE:
            self._draw_midi_device_state()
        elif self._state == self.State.MESSAGE:
            self._draw_message_state()

    def _draw_main_menu_state(self):
        self._draw_text("CHORD VISUALIZER", self.font, 400, 80)
        self._draw_text("Intervals:", self.small_font, 160, 258)
        self._draw_text("Name:", self.small_font, 160, 316)
        self._draw_text("Add chord definition  (optional)", self.small_font, 400, 210)

        for rect, field, text in [
            (self._field_intervals, "intervals", self._intervals_text),
            (self._field_name, "name", self._name_text),
        ]:
            border_color = self.COLOR_TEXT if self._active_field == field else self.COLOR_BTN
            pygame.draw.rect(self.screen, self.COLOR_BTN, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
            cursor = "|" if self._active_field == field else ""
            label = self.tiny_font.render(text + cursor, True, self.COLOR_TEXT)
            self.screen.blit(label, (rect.x + 8, rect.y + 10))

        self._draw_button(self._btn_save, "SAVE", self.small_font)
        self._draw_text("e.g.  0,4,7  ->  Major", self.tiny_font, 400, 358)
        if self._status_timer > 0:
            self._draw_text(self._status_msg, self.small_font, 400, 445)
        self._draw_button(self._btn_device, "SELECT DEVICE", self.small_font)

    def _draw_input_type_state(self):
        self._draw_text("Select Input Source", self.font, 400, 150)
        for label, rect in self._choice_buttons.items():
            self._draw_button(rect, label, self.small_font)

    def _draw_midi_device_state(self):
        self._draw_text("Select MIDI Device", self.font, 400, 100)
        for name, rect in self._device_buttons.items():
            self._draw_button(rect, name, self.small_font)

    def _draw_message_state(self):
        self._draw_text(self._message_text, self.small_font, 400, 300)

    def _try_save(self):
        try:
            intervals = tuple(int(x.strip()) for x in self._intervals_text.split(",") if x.strip())
            if not intervals:
                raise ValueError
            name = self._name_text.strip()
            if not name:
                raise ValueError
            self.library.add(intervals, name)
            self._status_msg = f"Saved: {name}"
            self._intervals_text = ""
            self._name_text = ""
        except ValueError:
            self._status_msg = "Invalid - use format: 0,4,7 and a name"
        self._status_timer = 180

    def _scan_devices(self):
        devices = {}
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            if info[2] == 1:
                devices[i] = info[1].decode('utf-8')
        return devices

class Visualizer(UI):
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.font = pygame.font.SysFont("monospace", 24)
        self.c_val = 0
        self.time_offset = 0
        self.current_chord = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

    def update(self):
        self.c_val += 0.03
        self.time_offset += 0.05
        self.screen.fill(self.COLOR_BG)
        if self.current_chord:
            self._draw_lissajous(self.current_chord)
        self._draw_chord_text()
        pygame.display.flip()

    def set_chord(self, chord):
        self.current_chord = chord

    def _draw_chord_text(self):
        if self.current_chord:
            self._draw_text(self.current_chord.chord_string, self.font, self.width // 2, 20)

    def _draw_lissajous(self, chord):
        a = chord.A
        b = chord.B
        E = chord.dissonance
        hertz_vec = chord.hertz_vector
        f = math.pi / 2
        steps = 1000
        scale = min(self.width, self.height) * 0.4
        center = (self.width // 2, self.height // 2)

        points = []
        for i in range(steps):
            t = (i / steps) * math.pi * 2
            x_val = math.sin(a * t + f * (1 + self.c_val))
            harmonic_sum = 0
            if chord.notes:
                for hz in hertz_vec:
                    harmonic_sum += math.sin(f * hz * (t + self.time_offset))
                harmonic_sum /= len(hertz_vec)
            y_val = math.sin(b * t) + (E * harmonic_sum)
            points.append((int(center[0] + x_val * scale), int(center[1] + y_val * scale)))

        if len(points) > 1:
            pygame.draw.lines(self.screen, self.COLOR_TEXT, False, points, 2)