import pygame
from core import runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow, get_font, sprite_load_percent

GRID_DIM = 5

def get_cell_size():
    return int(40 * constants.UI_SCALE)  # Includes content and margins

def get_margin():
    return int(1 * constants.SCREEN_WIDTH / 240)

def get_content_size():
    return int(32 * constants.UI_SCALE)

def get_window_size():
    return GRID_DIM * get_cell_size()


class WindowFreezer:
    def __init__(self, freezer_page):
        self.font = get_font(constants.FONT_SIZE_SMALL)
        self.page_index = 0
        self.cursor_row = 0
        self.cursor_col = 0
        self.scaled_pet_sprites = {}
        self.scaled_module_flags = {}
        self._background_cache = None
        self._placeholder_cache = {}
        self._last_screen_size = (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self._scene_cache_surface = None
        self._scene_cache_key = None
        self.set_page(freezer_page)

    def set_page(self, freezer_page):
        self.pet_grid = freezer_page.pet_grid
        self.prepare_sprites()
        self._background_cache = None  # Invalidate cache

    def prepare_sprites(self):
        CONTENT_SIZE = get_content_size()
        # Cache scaled versions of pet sprites
        for pet_key, sprite_list in runtime_globals.pet_sprites.items():
            if sprite_list:
                original_sprite = sprite_list[0]
                percent = (CONTENT_SIZE / constants.SCREEN_HEIGHT) * 100
                scaled = sprite_load_percent(
                    pet_key.sprite_path if hasattr(pet_key, "sprite_path") else None,
                    percent=percent,
                    keep_proportion=True,
                    base_on="height"
                ) if hasattr(pet_key, "sprite_path") else pygame.transform.scale(original_sprite, (CONTENT_SIZE, CONTENT_SIZE))
                self.scaled_pet_sprites[pet_key.name] = scaled

        # Cache scaled versions of module flags
        for module_name, flag_surface in runtime_globals.game_module_flag.items():
            if flag_surface:
                self.scaled_module_flags[module_name] = pygame.transform.scale(flag_surface, (CONTENT_SIZE, CONTENT_SIZE))

        # Cache placeholder dash for empty slots
        dash = self.font.render("-", True, constants.FONT_COLOR_GRAY)
        self._placeholder_cache['dash'] = dash

    def _precompute_background(self):
        """Precompute the static background grid and placeholders."""
        CELL_SIZE = get_cell_size()
        MARGIN = get_margin()
        CONTENT_SIZE = get_content_size()
        WINDOW_SIZE = get_window_size()
        # Only recompute if screen size or grid changes
        if self._background_cache and self._last_screen_size == (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT):
            return

        self._background_cache = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        width_scale = constants.SCREEN_WIDTH / 240
        height_scale = constants.SCREEN_HEIGHT / 240
        mmargin = (constants.SCREEN_WIDTH - (WINDOW_SIZE + (GRID_DIM * MARGIN))) / 2

        for row in range(GRID_DIM):
            for col in range(GRID_DIM):
                x = mmargin + (col * CELL_SIZE)
                y = int(35 * height_scale) + row * CELL_SIZE
                pet = self._get_pet_at(row, col)
                attr_color = constants.ATTR_COLORS.get(pet.attribute, constants.ATTR_COLORS[""]) if pet else (50, 50, 50)
                pygame.draw.rect(self._background_cache, attr_color, (x, y, CELL_SIZE - MARGIN, CELL_SIZE - MARGIN))
                if not pet:
                    dash = self._placeholder_cache['dash']
                    dx = x + (CELL_SIZE - dash.get_width()) // 2
                    dy = y + (CELL_SIZE - dash.get_height()) // 2
                    blit_with_shadow(self._background_cache, dash, (dx, dy))

        self._last_screen_size = (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)

    def draw(self, surface):
        CELL_SIZE = get_cell_size()
        MARGIN = get_margin()
        CONTENT_SIZE = get_content_size()
        WINDOW_SIZE = get_window_size()
        cache_key = (
            self.page_index,
            self.cursor_row,
            self.cursor_col,
        )

        if cache_key != self._scene_cache_key or self._scene_cache_surface is None:
            # Redraw full grid scene once on state change
            cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            self._precompute_background()
            blit_with_cache(cache_surface, self._background_cache, (0, 0))

            height_scale = constants.SCREEN_HEIGHT / 240
            mmargin = (constants.SCREEN_WIDTH - (WINDOW_SIZE + (GRID_DIM * MARGIN))) / 2

            # Only draw pets and flags (dynamic content)
            for row in range(GRID_DIM):
                for col in range(GRID_DIM):
                    x = mmargin + (col * CELL_SIZE)
                    y = int(35 * height_scale) + row * CELL_SIZE
                    pet = self._get_pet_at(row, col)
                    if pet:
                        # Module flag (on top)
                        flag = self.scaled_module_flags.get(pet.module)
                        if flag:
                            fx = x + (CELL_SIZE - CONTENT_SIZE) // 2
                            fy = y + int(1 * height_scale)
                            blit_with_shadow(cache_surface, flag, (fx, fy))

                        # Pet sprite (below flag)
                        pet_sprite = self.scaled_pet_sprites.get(pet.name)
                        if pet_sprite:
                            sx = x + (CELL_SIZE - CONTENT_SIZE) // 2
                            sy = y + int(5 * height_scale)
                            blit_with_cache(cache_surface, pet_sprite, (sx, sy))

            # Draw cursor overlay (always on top)
            x = mmargin + (self.cursor_col * CELL_SIZE)
            y = int(35 * height_scale) + self.cursor_row * CELL_SIZE
            pygame.draw.rect(cache_surface, constants.FONT_COLOR_GREEN, (x, y, CELL_SIZE - MARGIN, CELL_SIZE - MARGIN), 2)

            self._scene_cache_surface = cache_surface
            self._scene_cache_key = cache_key

        # Blit cached grid scene
        blit_with_cache(surface, self._scene_cache_surface, (0, 0))

    def _get_pet_at(self, row, col):
        if row < len(self.pet_grid) and col < len(self.pet_grid[row]):
            return self.pet_grid[row][col]
        return None

    def handle_event(self, input_action):
        pass

    def update(self):
        pass