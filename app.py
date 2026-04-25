import pygame
import pygame.midi
from theory import ChordLibrary
from sound import SoundEngine
from screen import InputSelector, Visualizer

class ChordApp:
    def __init__(self, handler, visualizer):
        self.handler = handler
        self.visualizer = visualizer
        self.clock = pygame.time.Clock()

    def run(self):
        try:
            while True:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        return
                chord = self.handler.update(events)
                self.visualizer.handle_events(events)
                self.visualizer.set_chord(chord)
                self.visualizer.update()
                self.clock.tick(60)
        except KeyboardInterrupt:
            pass
        finally:
            pygame.midi.quit()
            pygame.quit()

def create_app():
    pygame.init()
    pygame.display.set_caption("Real-Time Musical Chord Visualizer")
    library = ChordLibrary()
    sound_engine = SoundEngine()
    screen = pygame.display.set_mode((800, 600))
    selector = InputSelector(library, sound_engine, screen)
    handler = selector.get_handler()
    visualizer = Visualizer(screen)
    return ChordApp(handler, visualizer)


if __name__ == "__main__":
    create_app().run()