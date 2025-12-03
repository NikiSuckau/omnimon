import pygame
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow, get_font, sprite_load_percent_wh


class WindowPetList:
    def __init__(self, get_targets_callback, strategy_options=["Selected pets", "Pets in need"]):
        self.get_targets_callback = get_targets_callback
        self.strategy_options = strategy_options
        # Use new method for background, scale to screen width, keep proportions
        self.selectionBackground = sprite_load_percent_wh(
            constants.PET_SELECTION_BACKGROUND_PATH,
            percent_w=100,
            percent_h=40,
            keep_proportion=False
        )

        # Cache processed sprites to avoid recalculating every frame
        self.scaled_sprites = {}
        self.transparent_sprites = {}
        self.selected_indices = []
        self.cursor_index = 0
        self.max_selection = 2
        self.select_mode = False
        self.selection_label = "Jogress"
        self.targets = tuple(self.get_targets_callback())

    def get_scaled_sprite(self, pet):
        """Returns a cached version of the scaled sprite."""
        if pet not in self.scaled_sprites:
            sprite = pet.get_sprite(0).convert_alpha()
            sprite = pygame.transform.scale(sprite, (constants.PET_ICON_SIZE, constants.PET_ICON_SIZE))
            self.scaled_sprites[pet] = sprite
        return self.scaled_sprites[pet]

    def get_transparent_sprite(self, pet):
        """Returns a cached version of the transparent sprite."""
        if pet not in self.transparent_sprites:
            sprite = self.get_scaled_sprite(pet).copy()
            sprite.fill((255, 255, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)  # Fast alpha blending
            self.transparent_sprites[pet] = sprite
        return self.transparent_sprites[pet]

    def draw(self, surface: pygame.Surface):
        pets = game_globals.pet_list
        cache_key = (
            tuple(pet.name for pet in pets),
            tuple(self.selected_indices),
            self.cursor_index,
            self.select_mode,
            runtime_globals.strategy_index,
            self.targets,
            constants.UI_SCALE,
            constants.SCREEN_WIDTH,
            constants.SCREEN_HEIGHT,
        )
        if not hasattr(self, "_last_cache_key") or self._last_cache_key != cache_key:
            # Redraw and cache
            available_width = constants.SCREEN_WIDTH
            spacing = available_width // max(1, len(pets))
            start_x = 0
            bg_height = self.selectionBackground.get_height()
            y = constants.SCREEN_HEIGHT - bg_height + int(24 * constants.UI_SCALE)

            cached_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            cached_surface.blit(self.selectionBackground, (start_x, constants.SCREEN_HEIGHT - bg_height))
            font = get_font(constants.FONT_SIZE_SMALL)
            if self.select_mode:
                strategy_text = font.render(self.selection_label, True, constants.FONT_COLOR_DEFAULT)
            else:
                strategy_text = font.render(self.strategy_options[runtime_globals.strategy_index], True, constants.FONT_COLOR_DEFAULT)
            strategy_x = int(10 * constants.UI_SCALE)
            strategy_y = constants.SCREEN_HEIGHT - bg_height
            blit_with_shadow(cached_surface, strategy_text, (strategy_x, strategy_y))

            for i, pet in enumerate(pets):
                if pet in self.targets:
                    sprite = self.get_scaled_sprite(pet)
                else:
                    sprite = self.get_transparent_sprite(pet)
                x = start_x + i * spacing + (spacing - sprite.get_width()) // 2
                blit_with_shadow(cached_surface, sprite, (x, y))

                if self.select_mode:
                    if i in self.selected_indices:
                        pygame.draw.rect(cached_surface, constants.FONT_COLOR_GREEN, (x - int(2 * constants.UI_SCALE), y - int(2 * constants.UI_SCALE), sprite.get_width() + int(4 * constants.UI_SCALE), sprite.get_height() + int(4 * constants.UI_SCALE)), 2)
                    if i == self.cursor_index:
                        pygame.draw.rect(cached_surface, constants.FONT_COLOR_YELLOW, (x - int(4 * constants.UI_SCALE), y - int(4 * constants.UI_SCALE), sprite.get_width() + int(8 * constants.UI_SCALE), sprite.get_height() + int(8 * constants.UI_SCALE)), 2)

            self._last_cache = cached_surface
            self._last_cache_key = cache_key

        #surface.blit(self._last_cache, (0, 0))
        blit_with_cache(surface, self._last_cache, (0, 0))

    def get_selected_pets(self):
        return [game_globals.pet_list[i] for i in self.selected_indices]
    
    def handle_input(self, input_action):
        if input_action == "LEFT":
            runtime_globals.game_sound.play("menu")
            self.cursor_index = (self.cursor_index - 1) % len(game_globals.pet_list)
            self.targets = tuple(self.get_targets_callback())
            self._last_cache_key = None  # Invalidate cache to redraw
        elif input_action == "RIGHT":
            runtime_globals.game_sound.play("menu")
            self.cursor_index = (self.cursor_index + 1) % len(game_globals.pet_list)
            self.targets = tuple(self.get_targets_callback())
            self._last_cache_key = None
        elif input_action == "A":
            if game_globals.pet_list[self.cursor_index] in self.get_targets_callback():
                runtime_globals.game_sound.play("menu")
                if self.cursor_index in self.selected_indices:
                    self.selected_indices.remove(self.cursor_index)
                elif len(self.selected_indices) < self.max_selection:
                    self.selected_indices.append(self.cursor_index)
            else:
                runtime_globals.game_sound.play("cancel")

    def update(self):
        """Update method called every frame to handle mouse hover."""
        if runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            self.check_mouse_hover(mouse_pos)

    def check_mouse_hover(self, mouse_pos):
        """Check if mouse is hovering over any pet icon and update cursor accordingly."""
        mouse_x, mouse_y = mouse_pos
        pets = game_globals.pet_list
        
        # Calculate pet icon positions (same logic as in draw method)
        available_width = constants.SCREEN_WIDTH
        spacing = available_width // max(1, len(pets))
        start_x = 0
        bg_height = self.selectionBackground.get_height()
        y = constants.SCREEN_HEIGHT - bg_height + int(24 * constants.UI_SCALE)
        
        for i, pet in enumerate(pets):
            x = start_x + i * spacing + (spacing - constants.PET_ICON_SIZE) // 2
            
            # Check if mouse is within this pet's icon bounds
            icon_rect = pygame.Rect(x, y, constants.PET_ICON_SIZE, constants.PET_ICON_SIZE)
            
            if icon_rect.collidepoint(mouse_x, mouse_y):
                if self.cursor_index != i:
                    self.cursor_index = i
                    self.targets = tuple(self.get_targets_callback())
                    self._last_cache_key = None  # Invalidate cache to redraw
                break
