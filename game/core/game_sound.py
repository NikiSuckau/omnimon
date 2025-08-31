import pygame
import os
from core import game_globals
import game.core.constants as constants

#=====================================================================
# GameSound - Sound management (loading and playing sounds)
#=====================================================================

class GameSound:
    """
    Handles loading and playing of game sounds.
    """

    def __init__(self, base_path: str = constants.DMC_SOUNDS_PATH) -> None:
        """
        Initializes the sound system and loads all sounds.

        Args:
            base_path (str): Path where sound files are located.
        """
        self.base_path = base_path
        self.sounds = {}
        self.sound_labels = {
            1: "noise_beep",
            2: "cancel",
            3: "menu",
            4: "evolution",
            5: "battle",
            6: "attack",
            7: "attack_hit",
            8: "attack_fail",
            9: "fail_long",
            10: "need_attention",
            11: "success",
            12: "happy",
            13: "alarm",
            14: "battle_online",
            15: "fail",
            16: "death",
            17: "happy2",
            18: "evolution_plus",
            19: "evolution_2020",
        }

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load all sounds
        self.load_sounds()

    def load_sounds(self) -> None:
        """
        Loads all sounds defined in sound_labels into memory.
        """
        for index, label in self.sound_labels.items():
            filename = f"{index}.wav"
            filepath = os.path.join(self.base_path, filename)
            try:
                if index < 18:
                    sound = pygame.mixer.Sound(filepath)
                    self.sounds[label] = sound
                else:
                    self.sounds[label] = filepath
            except pygame.error as e:
                print(f"[!] Failed to load sound '{filename}': {e}")

    def play(self, name: str) -> None:
        """
        Plays a sound by its label.

        Args:
            name (str): The sound label to play (e.g., 'menu', 'fail', 'evolution').
        """
        if not game_globals.sound:
            return

        if name in self.sounds:
            if isinstance(self.sounds[name], pygame.mixer.Sound):
                self.stop_all()
                self.sounds[name].set_volume(game_globals.sound / 10)
                self.sounds[name].play()
            else:
                pygame.mixer.music.load(self.sounds[name])
                pygame.mixer.music.set_volume(game_globals.sound / 10)
                pygame.mixer.music.play()
        else:
            print(f"[!] Sound '{name}' not found.")

    def stop_all(self) -> None:
        """
        Stops all currently playing sounds.
        """
        pygame.mixer.stop()

    def get_music_position(self) -> float:
        """Returns the current playback position in milliseconds."""
        return pygame.mixer.music.get_pos() / 1000

    def fade_in_music(target_volume=1.0, duration=3):
        """Gradually increases the volume over the given duration in seconds."""
        steps = 30  # 🔹 Adjust volume in 30 steps for smooth fading
        increment = target_volume / steps
        for i in range(steps):
            pygame.mixer.music.set_volume(i * increment)
            pygame.time.delay(duration * 1000 // steps)  # 🔥 Small delay for smooth transition

    def fade_out_music(duration=3):
        """Gradually decreases the volume to 0 over the given duration."""
        steps = 30  
        current_volume = pygame.mixer.music.get_volume()  # 🔹 Get current volume
        decrement = current_volume / steps
        for i in range(steps):
            pygame.mixer.music.set_volume(current_volume - (i * decrement))
            pygame.time.delay(duration * 1000 // steps)  
        pygame.mixer.music.stop()  # 🔥 Stops music after fade-out