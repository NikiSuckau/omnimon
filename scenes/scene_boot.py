"""
Scene Boot
Initial boot scene responsible for setting up the game start.
Transitions automatically to either Egg Selection or Main Game based on pet list.
"""

import platform
import pygame
import os
import pickle

from components.window_background import WindowBackground
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.module_utils import get_module
from core.utils.pet_utils import distribute_pets_evenly
from core.utils.pygame_utils import blit_with_cache, sprite_load_percent
from core.utils.scene_utils import change_scene


def has_freezer_pets() -> bool:
    """
    Check if there are any pets stored in the freezer save file.
    Returns True if freezer.pkl exists and contains at least one pet.
    """
    freezer_path = "save/freezer.pkl"
    if not os.path.exists(freezer_path):
        return False
    
    try:
        with open(freezer_path, "rb") as f:
            freezer_data = pickle.load(f)
            # Check if any of the freezer pages have pets
            for page in freezer_data:
                if hasattr(page, 'pets') and page.pets and any(pet is not None for pet in page.pets):
                    return True
            return False
    except Exception:
        # If there's any error reading the file, assume no pets
        return False


#=====================================================================
# SceneBoot
#=====================================================================
class SceneBoot:
    """
    Boot scene for the Virtual Pet game.
    Shows background while initializing the next scene.
    """

    def __init__(self) -> None:
        """
        Initializes the boot scene with a temporary timer.
        """
        self.background = WindowBackground(True)
        # Use "Fit" method for logo image for both landscape and portrait devices
        if runtime_globals.SCREEN_WIDTH >= runtime_globals.SCREEN_HEIGHT:
            self.logo = sprite_load_percent(constants.OMNIMON_LOGO_PATH, percent=100, keep_proportion=True, base_on="height")
        else:
            self.logo = sprite_load_percent(constants.OMNIMON_LOGO_PATH, percent=100, keep_proportion=True, base_on="width")

        # --- Platform detection ---
        is_batocera = os.path.exists("/usr/share/batocera") or os.path.exists("/etc/batocera-release")
        is_rpi = False
        try:
            with open("/proc/device-tree/model") as f:
                is_rpi = "raspberry pi" in f.read().lower()
        except Exception:
            pass

        if platform.system() == "Windows":
            image_path = constants.CONTROLLERS_PC_PATH
        elif is_batocera:
            image_path = constants.CONTROLLERS_BATO_PATH  # Or a Batocera-specific image if you have one
        elif is_rpi:
            image_path = constants.CONTROLLERS_PI_PATH
        else:
            image_path = constants.CONTROLLERS_JOY_PATH  # Fallback for other Linux

        # Use "Fit" method for controller images for both landscape and portrait devices
        if runtime_globals.SCREEN_WIDTH >= runtime_globals.SCREEN_HEIGHT:
            self.controller_sprite = sprite_load_percent(image_path, percent=100, keep_proportion=True, base_on="height")
        else:
            self.controller_sprite = sprite_load_percent(image_path, percent=100, keep_proportion=True, base_on="width")
        self.boot_timer = int(150 * (constants.FRAME_RATE / 30)) 
        runtime_globals.game_console.log("[SceneBoot] Initialized")

    def update(self) -> None:
        """
        Updates the boot scene, transitioning to the appropriate next scene after the timer expires.
        """
        self.boot_timer -= 1

        if self.boot_timer <= 0:
            self.transition_to_next_scene()

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the boot background.
        """
        self.background.draw(surface)
        if self.boot_timer <= 80 * (constants.FRAME_RATE / 30):
            # Center the controller sprite on screen
            sprite_rect = self.controller_sprite.get_rect(center=(runtime_globals.SCREEN_WIDTH // 2, runtime_globals.SCREEN_HEIGHT // 2))
            blit_with_cache(surface, self.controller_sprite, sprite_rect)
        else:
            # Old way: blit_with_cache(surface, self.logo, ((runtime_globals.SCREEN_WIDTH - self.logo.get_width()) // 2, 0))
            # Center the logo image as well
            sprite_rect = self.logo.get_rect(center=(runtime_globals.SCREEN_WIDTH // 2, runtime_globals.SCREEN_HEIGHT // 2))
            blit_with_cache(surface, self.logo, sprite_rect)

    def handle_event(self, input_action) -> None:
        """
        Handles key press events, allowing early skip with ENTER.
        """

        if input_action in ["A", "START", "LCLICK"]:
            runtime_globals.game_console.log("[SceneBoot] Skipped boot timer with ENTER")
            self.boot_timer = 0

    def transition_to_next_scene(self) -> None:
        """
        Decides whether to transition to Main Game or Egg Selection based on saved pets.
        """
        if game_globals.pet_list:
            change_scene("game")
            runtime_globals.game_console.log("[SceneBoot] Transitioning to MainGame (pets found)")
            for pet in game_globals.pet_list:
                # Refresh evolution data from module
                module = get_module(pet.module)
                pet_data = module.get_monster(pet.name, pet.version)
                if pet_data:
                    pet.evolve = pet_data.get("evolve", [])
                pet.begin_position()
                if pet.state not in ["dead", "hatch", "nap"]:
                    pet.set_state("idle")
                pet.patch()
            distribute_pets_evenly()
        else:
            # No active pets, check if there are pets in the freezer
            if has_freezer_pets():
                change_scene("freezer")
                runtime_globals.game_console.log("[SceneBoot] Transitioning to Freezer (pets found in freezer)")
            else:
                change_scene("egg")
                runtime_globals.game_console.log("[SceneBoot] Transitioning to EggSelection (no pets)")
