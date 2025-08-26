import pygame
from datetime import datetime

from components.window_background import WindowBackground
from components.window_horizontalmenu import WindowHorizontalMenu
from components.window_petview import WindowPetList
from core import runtime_globals
import game.core.constants as constants
from core.utils.pet_utils import distribute_pets_evenly, get_selected_pets
from core.utils.pygame_utils import sprite_load_percent
from core.utils.scene_utils import change_scene

OPTION_ICON_SIZE = int(48 * constants.UI_SCALE)
SLEEP_RECOVERY_HOURS = constants.SLEEP_RECOVERY_HOURS

#=====================================================================
# SceneSleepMenu
#=====================================================================
class SceneSleepMenu:
    def __init__(self) -> None:
        self.background = WindowBackground()
        self.options = [
            ("Sleep", sprite_load_percent(constants.SLEEP_ICON_PATH, percent=(OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")),
            ("Wake", sprite_load_percent(constants.WAKE_ICON_PATH, percent=(OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height"))
        ]

        self.selected_index = 0
        runtime_globals.strategy_index = 0
        
        self.pet_list_window = WindowPetList(lambda: self.pets_can())
        self.menu_window = WindowHorizontalMenu(
            options=self.options,
            get_selected_index_callback=lambda: self.selected_index,
        )

        self._cache_surface = None
        self._cache_key = None

        runtime_globals.game_console.log("[SceneSleepMenu] Sleep menu initialized.")

    def update(self) -> None:
        # Update menu window for mouse hover
        if runtime_globals.game_input.mouse_enabled:
            self.menu_window.update()

    def pets_can(self):
        if self.selected_index == 0:
            return self.pets_can_sleep()
        else:
            return self.pets_can_wake()

    def pets_can_sleep(self):
        return [pet for pet in get_selected_pets() if pet.stage > 1 and pet.state != "nap" and pet.state != "dead"]

    def pets_can_wake(self):
        return [pet for pet in get_selected_pets() if pet.state == "nap"]
    
    def draw(self, surface: pygame.Surface) -> None:
        # Use a cache key for the current state that affects rendering
        cache_key = (self.selected_index, tuple(pet.name for pet in self.pets_can()))

        if cache_key != self._cache_key or self._cache_surface is None:
            # Redraw full scene on new state
            cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)

            self.background.draw(cache_surface)
            self.menu_window.draw(cache_surface, x=int(16 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(16 * constants.UI_SCALE))
            self.pet_list_window.draw(cache_surface)

            self._cache_surface = cache_surface
            self._cache_key = cache_key

        # Blit cached surface every frame
        surface.blit(self._cache_surface, (0, 0))

    def handle_event(self, input_action) -> None:
        if input_action:
            # Handle mouse clicks on navigation arrows for multi-option menus
            if input_action == "A" and runtime_globals.game_input.mouse_enabled:
                mouse_pos = runtime_globals.game_input.get_mouse_position()
                if self.menu_window.handle_mouse_click(mouse_pos):
                    # Mouse click was handled by the menu (navigation arrow click)
                    self._cache_surface = None  # Invalidate cache to redraw
                    return
            
            if input_action == "B":  # ESC or START
                runtime_globals.game_sound.play("cancel")
                change_scene("game")

            elif input_action in ("LEFT", "RIGHT"):
                runtime_globals.game_sound.play("menu")
                direction = 1 if input_action == "RIGHT" else -1
                self.selected_index = (self.selected_index + direction) % len(self.options)
                self._cache_surface = None  # Invalidate cache to redraw

            elif input_action == "A":
                self.confirm_selection()

    def confirm_selection(self) -> None:
        if self.selected_index == 0:
            self.put_pets_to_sleep()
        else:
            self.wake_pets()

    def put_pets_to_sleep(self) -> None:
        now = datetime.now()
        pets = self.pets_can_sleep()
        if len(pets) > 0:
            runtime_globals.game_sound.play("menu")
        else:
            runtime_globals.game_sound.play("cancel")
            return
        
        for pet in pets:
            pet.set_state("nap")
            pet.sleep_start_time = now
        runtime_globals.game_console.log("[SceneSleepMenu] Pets put to sleep manually.")
        distribute_pets_evenly()
        change_scene("game")

    def wake_pets(self) -> None:
        now = datetime.now()
        pets = self.pets_can_wake()
        if len(pets) > 0:
            runtime_globals.game_sound.play("menu")
        else:
            runtime_globals.game_sound.play("cancel")
            return

        for pet in pets:
            if pet.state == "nap":
                slept_hours = 0
                if hasattr(pet, "sleep_start_time"):
                    slept_hours = (now - pet.sleep_start_time).total_seconds() // 3600

                pet.set_state("idle")

                if slept_hours >= SLEEP_RECOVERY_HOURS:
                    pet.dp = pet.energy
                    runtime_globals.game_console.log(f"[SceneSleepMenu] {pet.name} fully recharged DP after sleeping {slept_hours}h.")

        runtime_globals.game_console.log("[SceneSleepMenu] Pets woke up manually.")
        distribute_pets_evenly()
        change_scene("game")
