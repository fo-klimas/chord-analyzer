# 1. Introduction 

## a. What is your application?
This application is a **Real-Time Musical Chord Visualizer**. It serves as an interactive tool that bridges music theory and geometry by identifying musical chords and representing them through dynamic **Lissajous-inspired** mathematical curves. The app captures input from either a MIDI device or a computer keyboard, calculates the dissonance and harmonic relationships of the notes, and renders a unique visual signature for every chord played.

---

## b. How to run the program?
To launch the application, follow these steps:

### Dependencies
Ensure you have **Python** installed along with the `pygame` and `numpy` libraries. To install the necessary libraries, run the following command in your terminal:
```bash
pip install pygame numpy
```

### Execution
Run the entry point script using the command:
```bash
python app.py
```

### Audio
Make sure your system speakers are on, as the app initializes a sound engine to play the notes back to you.

---

## c. How to use the program?
Once the application is running, you can interact with it as follows:

### Setup
Use the **Input Selector** menu to choose your source:
* **MIDI**: For external hardware.
* **KEYBOARD**: For using your computer keys.

### Performance
* **Keyboard**: Use the mapped keys (e.g., `Z` through `M` for the bottom octave, `Q` through `U` for the top) to play notes.
* **MIDI**: Simply play notes on your connected MIDI controller.

### Analysis
The screen will automatically display the **Chord Name** (if identified) and the **Intervals** (e.g., 0, 4, 7 for a Major Triad) at the top of the window.

### Customization
You can define and save new chords by typing the interval pattern and a custom name into the fields on the main menu, which updates the `chords.json` library permanently.

### Visualization
Observe how the curve's complexity and vibration change based on the number of notes held and the mathematical dissonance between them.

# 2. Body/Analysis

### a. Implementation of Functional Requirements
The application is built on an object-oriented foundation, ensuring that musical logic, audio processing, and visual rendering are modular and maintainable.

---

### The Four Pillars of OOP

#### 1. Inheritance
* **Meaning:** Inheritance allows a class (subclass) to acquire the properties and behaviors of another class (superclass), promoting code reuse.
* **Usage in Code:** In `screen.py`, the classes `MainMenu`, `InputSelector`, and `Visualizer` all inherit from the `UI` base class.
* **Why:** Instead of rewriting fundamental drawing functions for every screen, these subclasses inherit shared methods like `_draw_button` and `_draw_text`.

```python
class UI: 
    """Base class providing shared drawing tools.""" 
    COLOR_BG = (0, 0, 0) 
    COLOR_TEXT = (0, 255, 200) 
    
    def _draw_text(self, text, font, x, y): 
        surface = font.render(text, True, self.COLOR_TEXT) 
        self.screen.blit(surface, surface.get_rect(center=(x, y))) 

class Visualizer(UI): 
    """Subclass inheriting shared drawing logic.""" 
    def update(self): 
        # Accesses self.COLOR_BG and self._draw_text from UI 
        self.screen.fill(self.COLOR_BG) 
        self._draw_text("Chord Visualization", self.font, 400, 20)
```

#### 2. Abstraction
* **Meaning:** Abstraction hides complex implementation details, exposing only a simplified interface to the user.
* **Usage in Code:** The `SoundEngine` class serves as the primary abstraction for audio.
* **Why:** The main application simply calls `sound_engine.play_note(note)`. It does not need to manage `pygame.mixer` channels, buffer settings, or the mathematical generation of sine wave arrays.

```python
class SoundEngine: 
    def play_note(self, note): 
        """High-level interface used by the App.""" 
        if note.midi_value not in self._playing: 
            player = NotePlayer(note.hertz, self.SAMPLE_RATE, self.AMPLITUDE) 
            player.play() 
            self._playing[note.midi_value] = player 

# The App calls one simple method without knowing about 
# sample rates, buffers, or numpy arrays: 
sound_engine.play_note(middle_c)
```

#### 3. Encapsulation
* **Meaning:** Encapsulation protects the internal state of an object by restricting direct access to its data, typically through private or protected attributes.
* **Usage in Code:** The `ChordLibrary` class uses a protected attribute `self._library` to store chord definitions.
* **Why:** Direct access to the underlying dictionary is restricted. External classes must interact via the `lookup()` or `add()` methods, ensuring that data remains consistent and properly formatted.

```python
class ChordLibrary: 
    def __init__(self): 
        # Protected attribute (internal implementation) 
        self._library = self._load_from_json() 

    def lookup(self, intervals): 
        """Safe public access to data.""" 
        return self._library.get(intervals, "Unknown Chord")
```

#### 4. Polymorphism
* **Meaning:** Polymorphism allows different classes to be treated as instances of the same type through shared method signatures.
* **Usage in Code:** This is implemented through the `InputHandler` system. Both `MIDIHandler` and `KeyboardHandler` override the `update()` method.
* **Why:** The main application loop can hold a reference to a generic `InputHandler` object. It simply calls `input_handler.update(events)` to retrieve the current chord, without needing to know whether the notes are coming from a physical MIDI controller or a computer keyboard.

```python
class InputHandler:
    def update(self, events: list) -> Chord:
        return # Base definition

class MIDIHandler(InputHandler):
    def update(self, events: list) -> Chord:
        return Chord(self.active_notes, self.library)

class KeyboardHandler(InputHandler):
    def update(self, events: list) -> Chord:
        # Mapping PC keys to notes logic
        return Chord(self.active_notes, self.library)

current_chord = current_handler.update(events)
```
---

### Object Aggregation and Composition
The project utilizes specific structural relationships to build the system architecture:

* **Composition:** The `ChordApp` "owns" its essential components, such as the `SoundEngine` and `Visualizer`. Because these are created within the app's lifecycle, they are terminated if the app is destroyed.
* **Aggregation:** The `Chord` class aggregates `Note` objects. While a `Note` exists as an independent entity (containing its own MIDI value and frequency), the `Chord` groups them into a collection to perform interval analysis and name identification.


#### Implementation 

```python
class ChordApp:
    def __init__(self):
        # Composition: The App creates and owns these instances
        self.sound_engine = SoundEngine()
        self.visualizer = Visualizer()

class Chord:
    def __init__(self, notes, library):
        # Aggregation: The Chord contains a collection of Note objects
        # Notes can exist independently of this specific Chord
        self.notes = [Note(n) for n in notes]
        self.library = library
```
---
### Design Pattern: State Pattern
The program implements the **State Pattern** to manage the application flow, specifically when transitioning between Menu, Setup, and Visualization screens.

* **Reasoning:** Using a state-based approach prevents "spaghetti code" and deeply nested `if-else` blocks. The UI only responds to events and renders graphics that are relevant to the current state defined in the `AppState` Enum.


#### Implementation

```python
from enum import Enum, auto

class AppState(Enum):
    MENU = auto()
    SETUP = auto()
    VISUALIZING = auto()

class ChordApp:
    def run(self):
        # The logic branches based on the current state of the application
        if self.state == AppState.MENU:
            self.menu.render()
        elif self.state == AppState.VISUALIZING:
            self.visualizer.render()
```
---
### Reading and Writing to Files
The application manages data persistence through the `ChordLibrary` class, utilizing the **JSON** format for reliable storage.

* **Importing:** Upon startup, the app reads `chords.json` to load the database of known musical intervals into memory.
* **Exporting:** When a user defines a new chord in the interface, the library updates its internal state and writes the updated dictionary back to the file using `json.dump`, ensuring the data persists for future sessions.


#### Implementation

```python
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
        """Returns the name of the chord based on interval tuple."""
        return self._library.get(intervals, "Unknown Chord")
 
    def add(self, intervals: tuple, name: str):
        """Updates internal state and writes to the JSON file."""
        self._library[intervals] = name
        serialized = {",".join(str(i) for i in k): v for k, v in self._library.items()}
        with open(self._filepath, "w") as f:
            json.dump(serialized, f, indent=2)

```
---
### Unit Testing
To ensure the reliability of the application's musical logic, I implemented a suite of automated unit tests using the built-in Python `unittest` framework. These tests verify the underlying math and data processing before they reach the graphical interface.

#### Note Logic
Verifies that MIDI integers are correctly converted to frequencies (Hz) and scientific pitch notation (e.g., C4).

```python
def test_note_conversion(self):
    """Test MIDI to Pitch Class and Frequency conversion."""
    c4 = Note(60)
    self.assertEqual(c4.pitch_class, 'C')
    self.assertEqual(c4.name, 'C4')
    
    # Verify standard tuning (A4 = 440Hz)
    a4 = Note(69)
    self.assertEqual(a4.hertz, 440.0)
```

#### Chord Recognition
Validates that the `ChordLibrary` correctly matches intervals against the `chords.json` database.

```python
def test_chord_identification(self):
    """Test if a Major Triad (C, E, G) is correctly identified."""
    major_triad_midi = {60, 64, 67}
    chord = Chord(major_triad_midi, self.library)
    
    # Verify interval calculation and library lookup
    self.assertEqual(chord.intervals, (0, 4, 7))
    self.assertEqual(chord.name, "Major Triad")
```

#### Dissonance Calculations
Tests if the dissonance logic handles single notes and clusters correctly.

```python
def test_dissonance_calculation(self):
    # A single note should have zero dissonance
    single_note = Chord({60}, self.library)
    self.assertEqual(single_note.dissonance, 0.0)
    
    # A semi-tone cluster (C and C#) should produce positive dissonance
    cluster = Chord({60, 61}, self.library)
    self.assertGreater(cluster.dissonance, 0.0)
```

## 3. Results and Summary

### a. Results
* **Functional Musical Recognition:** The application successfully identifies complex chord structures and inversions in real-time by normalizing MIDI input into interval sets, which are then cross-referenced with the JSON database.
* **Dynamic Geometric Synthesis:** The primary achievement was the creation of a responsive visualizer that maps musical dissonance to the deformation and vibration of **Lissajous curves**, providing a tangible link between sound and geometry.
* **Persistent User Customization:** I successfully implemented a library system that allows users to expand the program's musical knowledge by adding custom chord definitions.



### b. Conclusions
This coursework resulted in a functional, object-oriented desktop application that serves as both a musical aid and a mathematical art tool. By applying the **State Pattern** and **OOP pillars**, I achieved a modular architecture that separates the "invisible" logic of music theory from the high-frequency rendering of the UI.

The key outcome is a program that allows users to **"see" harmony and dissonance**, making abstract music theory concepts more accessible through visual feedback. The project achieved its goal of creating a system for musical analysis that is extensible, tested, and user-friendly.



### c. Future Prospects 
The application provides a strong foundation for further development. Potential extensions include:

* **Musical Notation Integration:** Expanding the Visualizer to display the chord notes on a standard musical staff alongside the geometric curves.
* **Advanced Sound Synthesis:** Replacing the simple sine wave generator in `sound.py` with more complex oscillators and envelopes to simulate various instrument timbres (e.g., piano or organ).
* **AI-Driven Chord Suggestion:** Integrating a light machine learning model to suggest "next chords" in a progression based on the current musical context and the user's library.
