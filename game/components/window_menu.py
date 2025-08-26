import pygame
from core import runtime_globals
import game.core.constants as constants
from core.utils.pygame_utils import blit_with_cache, get_font

class WindowMenu:
    def __init__(self):
        self.font = get_font(constants.FONT_SIZE_SMALL)
        self.options = []
        self.menu_index = 0
        self.active = False
        self.position = (0, 0)
        self._last_cache = None
        self._last_cache_key = None

    def open(self, position, options):
        self.active = True
        self.menu_index = 0
        self.position = position
        self.options = options
        self._last_cache = None  # Invalidate cache

    def close(self):
        self.active = False

    def handle_event(self, input_action):
        if input_action == "UP":
            runtime_globals.game_sound.play("menu")
            self.menu_index = (self.menu_index - 1) % len(self.options)
            self._last_cache = None  # Invalidate cache
        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            self.menu_index = (self.menu_index + 1) % len(self.options)
            self._last_cache = None  # Invalidate cache

    def update(self):
        """Update method called every frame to handle mouse hover."""
        if runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            self.check_mouse_hover(mouse_pos)

    def check_mouse_hover(self, mouse_pos):
        """Check if mouse is hovering over any menu option and update selection accordingly."""
        if not self.active:
            return
            
        mouse_x, mouse_y = mouse_pos
        menu_x, menu_y = self.position
        
        # Calculate menu option positions (same logic as in _precompute_menu_surface)
        option_height = int(25 * constants.UI_SCALE)
        
        for i, option in enumerate(self.options):
            option_y = menu_y + int(10 * constants.UI_SCALE) + i * option_height
            option_rect = pygame.Rect(
                menu_x, 
                option_y, 
                int(120 * constants.UI_SCALE), 
                option_height
            )
            
            if option_rect.collidepoint(mouse_x, mouse_y):
                if self.menu_index != i:
                    self.menu_index = i
                    self._last_cache = None  # Invalidate cache
                break

    def _precompute_menu_surface(self):
        # Cache key includes options, index, position, and UI_SCALE
        x, y = self.position
        cache_key = (tuple(self.options), self.menu_index, x, y, constants.UI_SCALE)
        if self._last_cache_key == cache_key and self._last_cache is not None:
            return self._last_cache

        menu_width = int(120 * constants.UI_SCALE)
        option_height = int(25 * constants.UI_SCALE)
        menu_height = int(10 * constants.UI_SCALE) + len(self.options) * option_height + int(10 * constants.UI_SCALE)
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        menu_surface.set_alpha(200)
        menu_surface.fill((0, 0, 0, 220))

        for i, option in enumerate(self.options):
            color = constants.FONT_COLOR_GREEN if i == self.menu_index else constants.FONT_COLOR_DEFAULT
            text_surface = self.font.render(option, True, color)
            text_x = int(10 * constants.UI_SCALE)
            text_y = int(10 * constants.UI_SCALE) + i * option_height
            menu_surface.blit(text_surface, (text_x, text_y))

        self._last_cache = menu_surface
        self._last_cache_key = cache_key
        return menu_surface

    def draw(self, surface):
        if not self.active:
            return
        x, y = self.position
        menu_surface = self._precompute_menu_surface()
        #surface.blit(menu_surface, (x, y))
        blit_with_cache(surface, menu_surface, (x, y))