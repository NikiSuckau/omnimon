"""
Scene Training
Handles both Dummy and Head-to-Head training modes for pets.
"""

import pygame

from components.window_background import WindowBackground
from components.window_horizontalmenu import WindowHorizontalMenu
from components.window_petview import WindowPetList
from components.window_xai import WindowXai
from core import game_globals, runtime_globals
from core.combat.count_training import CountMatchTraining
from core.combat.dummy_training import DummyTraining
from core.combat.excite_training import ExciteTraining
from core.combat.head_training import HeadToHeadTraining
from game.core.combat.shake_training import ShakeTraining
import game.core.constants as constants
from core.utils.pet_utils import get_training_targets
from core.utils.pygame_utils import get_font, sprite_load_percent
from core.utils.scene_utils import change_scene

#=====================================================================
# SceneTraining (Training Menu)
#=====================================================================

class SceneTraining:
    def __init__(self) -> None:
        self.background = WindowBackground(False)
        self.font = get_font(constants.FONT_SIZE_LARGE)

        self.phase = "menu"
        self.mode = None

        self.options = []
        if runtime_globals.dmc_enabled:
            self.options.append(("Dummy", sprite_load_percent(constants.DUMMY_TRAINING_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))
            self.options.append(("HeadtoHead", sprite_load_percent(constants.HEAD_TRAINING_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))

        if runtime_globals.penc_enabled:
            self.options.append(("CountMatch", sprite_load_percent(constants.SHAKE_MATCH_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))

        if runtime_globals.dmx_enabled:
            self.options.append(("Excite", sprite_load_percent(constants.EXCITE_MATCH_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))

        if runtime_globals.dmc_enabled:
            self.options.append(("Punch", sprite_load_percent(constants.PUNCH_MATCH_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))

        self.selectionBackground = sprite_load_percent(constants.PET_SELECTION_BACKGROUND_PATH, percent=100, keep_proportion=True, base_on="width")
        self.backgroundIm = sprite_load_percent(constants.TRAINING_BACKGROUND_PATH, percent=100, keep_proportion=True, base_on="width")

        self.pet_list_window = WindowPetList(lambda: get_training_targets())

        xai_x = int(constants.SCREEN_WIDTH - (79 * constants.UI_SCALE))
        xai_y = int(123 * constants.UI_SCALE)
        xai_size = int(48 * constants.UI_SCALE)
        self.xai_window = WindowXai(xai_x, xai_y, xai_size, xai_size, game_globals.xai)

        self.menu_window = WindowHorizontalMenu(
            options=self.options,
            get_selected_index_callback=lambda: runtime_globals.training_index,
        )

        # Cache variables for menu phase only
        self._cache_surface = None
        self._cache_key = None

        runtime_globals.game_console.log("[SceneTraining] Training scene initialized.")

    def update(self):
        if self.mode:
            self.mode.update()
        
        # Update menu window for mouse hover if in menu phase
        if self.phase == "menu" and runtime_globals.game_input.mouse_enabled:
            self.menu_window.update()

    def draw(self, surface: pygame.Surface):
        if self.phase == "menu":
            # Compose a cache key that reflects the dynamic state of the menu
            cache_key = (
                runtime_globals.training_index,
                tuple(pet.name for pet in get_training_targets()),
                len(self.options),
            )

            if cache_key != self._cache_key or self._cache_surface is None:
                # Redraw full menu scene once on state change
                cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)

                self.background.draw(cache_surface)

                # Draw horizontal menu with spacing logic
                if len(self.options) > 2:
                    self.menu_window.draw(cache_surface, x=int(72 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(30 * constants.UI_SCALE))
                else:
                    self.menu_window.draw(cache_surface, x=int(16 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(16 * constants.UI_SCALE))

                # Draw pets at bottom
                self.pet_list_window.draw(cache_surface)

                # Draw Xai window if option "Excite" selected
                if self.options[runtime_globals.training_index][0] == "Excite":
                    self.xai_window.draw(cache_surface)

                self._cache_surface = cache_surface
                self._cache_key = cache_key

            # Blit cached menu scene
            surface.blit(self._cache_surface, (0, 0))

        elif self.mode:
            if self.mode.phase in ["alert", "impact"]:
                self.mode.draw(surface)
            else:
                self.background.draw(surface)
                surface.blit(self.backgroundIm, (0, 0))
                self.mode.draw(surface)

    def handle_event(self, input_action):
        if input_action:
            if self.phase == "menu":
                self.handle_menu_input(input_action)
            elif self.mode:
                self.mode.handle_event(input_action)

    def handle_menu_input(self, input_action):
        # Handle mouse clicks on navigation arrows for multi-option menus
        if input_action == "A" and runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if self.menu_window.handle_mouse_click(mouse_pos):
                # Mouse click was handled by the menu (navigation arrow click)
                self._cache_surface = None  # Invalidate cache on selection change
                return
        
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
        elif input_action in ("LEFT", "RIGHT"):
            runtime_globals.game_sound.play("menu")
            delta = -1 if input_action == "LEFT" else 1
            runtime_globals.training_index = (runtime_globals.training_index + delta) % len(self.options)
            self._cache_surface = None  # Invalidate cache on selection change
        elif input_action == "A":
            selected = self.options[runtime_globals.training_index][0]
            if selected == "Dummy":
                if len(get_training_targets()) > 0:
                    runtime_globals.game_sound.play("menu")
                    self.phase = "dummy"
                    self.mode = DummyTraining()
                    runtime_globals.game_console.log("Starting Dummy Training.")
                    for pet in get_training_targets():
                        pet.check_disturbed_sleep()
                else:
                    runtime_globals.game_sound.play("cancel")
            elif selected == "HeadtoHead":
                if len(get_training_targets()) > 1:
                    runtime_globals.game_sound.play("menu")
                    self.phase = "headtohead"
                    self.mode = HeadToHeadTraining()
                    runtime_globals.game_console.log("Starting Head-to-Head Training.")
                    for pet in get_training_targets():
                        pet.check_disturbed_sleep()
                else:
                    runtime_globals.game_sound.play("cancel")
            elif selected == "CountMatch":
                if len(get_training_targets()) > 0:
                    runtime_globals.game_sound.play("menu")
                    self.phase = "count"
                    self.mode = CountMatchTraining()
                    runtime_globals.game_console.log("Starting Dummy Training.")
                    for pet in get_training_targets():
                        pet.check_disturbed_sleep()
                else:
                    runtime_globals.game_sound.play("cancel")
            elif selected == "Excite":
                if len(get_training_targets()) > 0:
                    runtime_globals.game_sound.play("menu")
                    self.phase = "excite"
                    self.mode = ExciteTraining()
                    runtime_globals.game_console.log("Starting Dummy Training.")
                    for pet in get_training_targets():
                        pet.check_disturbed_sleep()
                else:
                    runtime_globals.game_sound.play("cancel")
            elif selected == "Punch":
                if len(get_training_targets()) > 0:
                    runtime_globals.game_sound.play("menu")
                    self.phase = "punch"
                    self.mode = ShakeTraining()
                    runtime_globals.game_console.log("Starting Shake Training.")
                    for pet in get_training_targets():
                        pet.check_disturbed_sleep()
                else:
                    runtime_globals.game_sound.play("cancel")
        elif input_action == "SELECT" and self.phase == "menu":
            runtime_globals.game_sound.play("menu")
            runtime_globals.strategy_index = (runtime_globals.strategy_index + 1) % 2
            self._cache_surface = None  # Invalidate cache if strategy affects menu visuals

