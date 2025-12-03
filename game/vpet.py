"""
Virtual Pet - Game Logic
Handles the Virtual Pet game logic, scene management, and game state.
Display and audio initialization is handled by main.py
"""

import pygame
import time

# Scenes
from core import game_globals, runtime_globals
from core.input.system_stats import get_system_stats
from core.utils.module_utils import load_modules
from core.utils.pygame_utils import blit_with_cache, load_misc_sprites
from core import constants
from scenes.scene_battle import SceneBattle
from scenes.scene_battle_pvp import SceneBattlePvP
from scenes.scene_boot import SceneBoot
from scenes.scene_connect import SceneConnect
from scenes.scene_digidex import SceneDigidex
from scenes.scene_eggselection import SceneEggSelection
from scenes.scene_evolution import SceneEvolution
from scenes.scene_freezerbox import SceneFreezerBox
from scenes.scene_library import SceneLibrary
from scenes.scene_settingsmenu import SceneSettingsMenu
from scenes.scene_sleep import SceneSleep
from scenes.scene_status import SceneStatus
from scenes.scene_maingame import SceneMainGame
from scenes.scene_inventory import SceneInventory
from scenes.scene_training import SceneTraining
from scenes.scene_debug import SceneDebug

# Game Version
runtime_globals.VERSION = "0.9.8"

# Global timing variable for system stats updates
last_stats_update = time.time()
cached_stats = get_system_stats()  # Initialize with actual values


class VirtualPetGame:
    """
    Main Virtual Pet Game class.
    Handles scene management, updating, drawing, and event handling.
    """

    def __init__(self) -> None:
        runtime_globals.misc_sprites = load_misc_sprites()
        load_modules()
        game_globals.load()
        self.scene = SceneBoot()
        print("[Init] Omnibot initialized with SceneBoot")
        self.rotated = False
        self.stat_font = pygame.font.Font(None, 16)
        
        # Load mouse pointer sprite
        self.mouse_pointer = None
        try:
            pointer_path = "assets/Pointer.png"
            self.mouse_pointer = pygame.image.load(pointer_path).convert_alpha()
            # Scale the pointer to an appropriate size
            pointer_size = int(16 * constants.UI_SCALE)
            self.mouse_pointer = pygame.transform.scale(self.mouse_pointer, (pointer_size, pointer_size))
            print(f"[Init] Mouse pointer sprite loaded: {pointer_path}")
        except (pygame.error, FileNotFoundError) as e:
            print(f"[Init] Could not load mouse pointer sprite: {e}")
            self.mouse_pointer = None
        # Clock is now managed by main.py

    def update(self) -> None:
        """
        Updates the current scene and handles scene transitions if needed.
        """
        self.scene.update()

        # Poll GPIO actions
        self.poll_gpio_inputs()

        # Poll joystick actions (including analog stick directions)
        #for action in runtime_globals.game_input.get_just_pressed_joystick():
        #    self.scene.handle_event(action)

        if runtime_globals.game_state_update:
            self.change_scene()

        if game_globals.rotated:
            game_globals.rotated = False
            self.rotated = not self.rotated

        if runtime_globals.shake_detector.check_for_shake():
            self.scene.handle_event("SHAKE")
            
        # Handle autosave
        game_globals.autosave()

    def draw(self, surface: pygame.Surface, clock: pygame.time.Clock = None) -> None:
        """
        Draws the current scene to the given surface.
        """
        self.scene.draw(surface)

        global last_stats_update, cached_stats

        # Draw debug stats if DEBUG_MODE is enabled and clock is provided
        if constants.SHOW_FPS and clock is not None:
            now = time.time()
            if now - last_stats_update >= 3:  # Update stats every 3 seconds
                cached_stats = get_system_stats()
                last_stats_update = now
            draw_system_stats(clock, surface, cached_stats, self.stat_font)

        # Draw mouse pointer if enabled and sprite is loaded
        if (runtime_globals.game_input.mouse_enabled and 
            self.mouse_pointer is not None):
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if mouse_pos != (0, 0):  # Only draw if mouse position is valid
                # Draw pointer slightly offset so the tip points to the actual position
                pointer_x = mouse_pos[0] - 2
                pointer_y = mouse_pos[1] - 2
                # Ensure pointer stays within screen bounds
                #pointer_x = max(0, min(pointer_x, constants.SCREEN_WIDTH - self.mouse_pointer.get_width()))
                #pointer_y = max(0, min(pointer_y, constants.SCREEN_HEIGHT - self.mouse_pointer.get_height()))
                blit_with_cache(surface, self.mouse_pointer, (pointer_x, pointer_y))

        if self.rotated:
            rotated_surface = pygame.transform.rotate(surface, 180)  # Rotate only the surface
            surface.blit(rotated_surface, (0, 0))

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Delegates event handling to the current scene.
        """
        input_action = runtime_globals.game_input.process_event(event)

        # First, let the scene handle the raw pygame event (for mouse motion, etc.)
        if self.scene.handle_event(input_action if input_action else event):
            return
        else: #Analog inputs only
            for action in runtime_globals.game_input.get_just_pressed_joystick():
                if action in ("ANALOG_UP", "ANALOG_DOWN", "ANALOG_LEFT", "ANALOG_RIGHT"):
                    self.scene.handle_event(action.replace("ANALOG_", ""))

    def poll_gpio_inputs(self):
        for action in runtime_globals.game_input.get_gpio_just_pressed():
            self.scene.handle_event(action)

    def change_scene(self) -> None:
        """
        Handles changing the current scene based on runtime_globals.game_state.
        """
        runtime_globals.game_state_update = False
        state = runtime_globals.game_state

        scene_mapping = {
            "egg": SceneEggSelection,
            "game": SceneMainGame,
            "settings": SceneSettingsMenu,
            "status": SceneStatus,
            "feeding": SceneInventory,
            "training": SceneTraining,
            "sleepmenu": SceneSleep,
            "battle": SceneBattle,
            "battle_pvp": SceneBattlePvP,
            "connect": SceneConnect,
            "digidex": SceneDigidex,
            "evolution": SceneEvolution,
            "freezer": SceneFreezerBox,
            "library": SceneLibrary,
            "debug": SceneDebug,
        }

        scene_class = scene_mapping.get(state)
        if scene_class and type(self.scene) is not scene_class:  # Prevent redundant scene switches
            print(f"[Scene] Switching to {scene_class.__name__}")
            self.scene = scene_class()

    def save(self) -> None:
        """
        Saves the current game state.
        """
        game_globals.save()
        runtime_globals.game_console.log("[VirtualPetGame] Game state saved.")


def main() -> None:
    """
    Main loop of the Virtual Pet game.
    This function is now handled by main.py
    """
    pass


cached_stats_surface = None
last_stats_values = None

def draw_system_stats(clock, surface, stats, font):
    """Efficiently draws FPS, CPU temp, memory, and CPU usage."""
    global cached_stats_surface, last_stats_values

    # Show system stats only when DEBUG_MODE is enabled, but FPS can be shown independently
    show_system_stats = constants.DEBUG_MODE
    show_fps_only = constants.SHOW_FPS and not constants.DEBUG_MODE

    if not show_system_stats and not show_fps_only:
        return

    temp, cpu_usage, memory_usage = stats
    fps = int(clock.get_fps())
    stats_tuple = (fps, temp, cpu_usage, memory_usage, show_system_stats, show_fps_only)

    # Only update cached surface if stats changed or display mode changed
    if cached_stats_surface is None or stats_tuple != last_stats_values:
        surface_height = 60 if show_system_stats else 20
        cached_stats_surface = pygame.Surface((140, surface_height), pygame.SRCALPHA)
        y = 0
        
        # Always show FPS if SHOW_FPS is enabled OR if DEBUG_MODE is enabled
        if constants.SHOW_FPS or constants.DEBUG_MODE:
            cached_stats_surface.blit(font.render(f"FPS: {fps}", True, (255, 255, 255)), (0, y))
            y += 16
            
        # Only show other system stats if DEBUG_MODE is enabled
        if show_system_stats:
            if temp is not None:
                cached_stats_surface.blit(font.render(f"Temp: {temp:.1f}°C", True, (255, 255, 255)), (0, y))
                y += 16
            if cpu_usage is not None:
                cached_stats_surface.blit(font.render(f"CPU: {cpu_usage:.1f}%", True, (255, 255, 255)), (0, y))
                y += 16
            if memory_usage is not None:
                cached_stats_surface.blit(font.render(f"RAM: {memory_usage:.1f}%", True, (255, 255, 255)), (0, y))
        last_stats_values = stats_tuple

    # Blit the cached stats surface
    blit_with_cache(surface, cached_stats_surface, (4, 64))