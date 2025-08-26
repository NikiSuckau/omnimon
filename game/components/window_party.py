import math
import pygame
import game.core.constants as constants
from core import game_globals, runtime_globals
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow, get_font

def get_grid_dimensions(max_pets):
    if max_pets == 1:
        return (1, 1)
    elif max_pets == 2:
        return (1, 2)
    else:
        cols = math.ceil(math.sqrt(max_pets))
        rows = math.ceil(max_pets / cols)
        if (rows - 1) * cols >= max_pets:
            rows -= 1
        return (rows, cols)

class WindowParty:
    def __init__(self):
        self.selected_index = 0
        self._cache_surface = None
        self._cache_key = None

    def draw(self, surface):
        # Compose cache key from selected index and pet names
        cache_key = (
            self.selected_index,
            tuple(pet.name for pet in game_globals.pet_list),
        )

        if cache_key != self._cache_key or self._cache_surface is None:
            win_w, win_h = surface.get_width(), surface.get_height()
            cache_surface = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
            margin = int(20 * (win_w / 240))
            top_margin = int(40 * (win_h / 240))
            grid_area_w = win_w - 2 * margin
            grid_area_h = win_h - top_margin - margin

            max_pets = max(constants.MAX_PETS, len(game_globals.pet_list))
            rows, cols = get_grid_dimensions(max_pets)

            slot_w = grid_area_w // cols
            slot_h = grid_area_h // rows

            # Scale sprite and font sizes
            sprite_size = int(min(slot_w, slot_h) * 0.6)
            font_size = max(10, int(slot_h * 0.18))
            font = get_font(font_size)

            for i in range(max_pets):
                row = i // cols
                col = i % cols
                x = margin + col * slot_w
                y = top_margin + row * slot_h

                # Draw background rectangle for slot
                rect = pygame.Rect(x, y, slot_w, slot_h)
                pygame.draw.rect(cache_surface, (60, 60, 60), rect, border_radius=8)

                # Draw pet if present
                if i < len(game_globals.pet_list):
                    pet = game_globals.pet_list[i]
                    # Draw attribute color overlay
                    attr_color = constants.ATTR_COLORS.get(getattr(pet, "attribute", None), (171, 71, 188))
                    pygame.draw.rect(cache_surface, attr_color, rect, 0, border_radius=8)

                    # Draw pet sprite (scaled)
                    sprite_obj = runtime_globals.pet_sprites.get(pet)[0]
                    sprite = pygame.transform.smoothscale(sprite_obj, (sprite_size, sprite_size))
                    sprite_x = x + (slot_w - sprite_size) // 2
                    sprite_y = y + int(slot_h * 0.12)
                    blit_with_shadow(cache_surface, sprite, (sprite_x, sprite_y))

                    # Draw module flag (scaled)
                    flag_sprite = runtime_globals.game_module_flag.get(pet.module)
                    flag = pygame.transform.smoothscale(flag_sprite, (sprite_size, sprite_size))
                    blit_with_shadow(cache_surface, flag, (sprite_x, sprite_y))

                    # Draw pet name (centered)
                    name_surface = font.render(pet.name, True, (255, 255, 255))
                    name_x = x + (slot_w - name_surface.get_width()) // 2
                    name_y = y + slot_h - font_size - 6
                    blit_with_shadow(cache_surface, name_surface, (name_x, name_y))
                else:
                    # Draw empty slot
                    plus_surface = font.render("+", True, constants.FONT_COLOR_GRAY)
                    plus_x = x + (slot_w - plus_surface.get_width()) // 2
                    plus_y = y + (slot_h - plus_surface.get_height()) // 2
                    blit_with_shadow(cache_surface, plus_surface, (plus_x, plus_y))

                if i == self.selected_index:
                    pygame.draw.rect(cache_surface, constants.FONT_COLOR_GREEN, rect, 3, border_radius=8)

            self._cache_surface = cache_surface
            self._cache_key = cache_key

        # Blit cached party scene
        #surface.blit(self._cache_surface, (0, 0))
        blit_with_cache(surface, self._cache_surface, (0, 0))

    def handle_event(self, input_action):
        max_pets = max(constants.MAX_PETS, len(game_globals.pet_list))
        rows, cols = get_grid_dimensions(max_pets)
        if input_action == "LEFT":
            runtime_globals.game_sound.play("menu")
            self.selected_index = (self.selected_index - 1) % max_pets
        elif input_action == "RIGHT":
            runtime_globals.game_sound.play("menu")
            self.selected_index = (self.selected_index + 1) % max_pets
        elif input_action == "UP":
            runtime_globals.game_sound.play("menu")
            self.selected_index = (self.selected_index - cols) % max_pets
        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            self.selected_index = (self.selected_index + cols) % max_pets
