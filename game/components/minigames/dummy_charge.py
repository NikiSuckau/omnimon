import random
import pygame
from game.components.ui.ui_manager import UIManager
from game.core import runtime_globals
import game.core.constants as constants
from core.utils.pygame_utils import blit_with_shadow, sprite_load_percent


class DummyCharge:

    def __init__(self, ui_manager: UIManager):
        self.strength = 0
        self.bar_level = 14
        self._holding = False
        self._hold_ticks = 0
        self.ui_manager = ui_manager
        # cached sprites expected to be provided externally by the caller if needed
        self._sprite_cache = {}
        self._sprite_cache['bar_piece'] = self.ui_manager.load_sprite_non_integer_scaling(constants.BAR_PIECE_PATH, constants.UI_SCALE)
        self._sprite_cache['training_max'] = self.ui_manager.load_sprite_non_integer_scaling(constants.TRAINING_MAX_PATH, constants.UI_SCALE)
        self._sprite_cache['bar_back'] = self.ui_manager.load_sprite_non_integer_scaling(constants.BAR_BACK_PATH, constants.UI_SCALE)
        # internal state
        self.phase = "charge"  # charge, wait_attack, impact, result
        self.frame_counter = 0

    def update(self):
        pass

    def handle_event(self, input_action):
        """Process pygame events (mouse/button presses)."""
        if input_action in ["A", "LCLICK"]:
            runtime_globals.game_sound.play("menu")
            self.strength = min(getattr(self, "strength", 0) + 1, getattr(self, "bar_level", 14))

    def draw(self, surface):
        """Draws the charge UI and pets. draw_pets_callable should accept a PetFrame value."""
        bar_piece = self._sprite_cache['bar_piece']
        training_max = self._sprite_cache['training_max']
        bar_back = self._sprite_cache['bar_back']

        bar_x = (constants.SCREEN_WIDTH // 2 - bar_piece.get_width() // 2) - int(40 * constants.UI_SCALE)
        bar_bottom_y = constants.SCREEN_HEIGHT // 2 + int(110 * constants.UI_SCALE)

        if self.strength == 14:
            surface.blit(training_max, (bar_x - int(18 * constants.UI_SCALE), bar_bottom_y - int(209 * constants.UI_SCALE)))
        
        blit_with_shadow(surface, bar_back, (bar_x - int(3 * constants.UI_SCALE), bar_bottom_y - int(169 * constants.UI_SCALE)))

        for i in range(self.strength):
            y = bar_bottom_y - (i + 1) * bar_piece.get_height()
            blit_with_shadow(surface, bar_piece, (bar_x, y))