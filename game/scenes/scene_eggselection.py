import pygame
import os
from core import game_globals, runtime_globals, constants
from core.game_digidex import register_digidex_entry
from core.game_pet import GamePet
from core.utils.module_utils import get_module
from core.utils.pygame_utils import blit_with_shadow, get_font, sprite_load_percent
from core.utils.scene_utils import change_scene
from core.utils.sprite_utils import load_pet_sprites
from core.utils.utils_unlocks import is_unlocked, unlock_item

class SceneEggSelection:
    GRID_COLUMNS = 4
    GRID_ROWS = 2  # Number of visible rows per page

    @property
    def EGG_SIZE(self):
        # Use similar sizing to digidex for consistency
        return (int(36 * constants.UI_SCALE), int(36 * constants.UI_SCALE))

    @property
    def LOGO_SIZE(self):
        # Make logo larger and more prominent
        logo_width = min(constants.SCREEN_WIDTH // 1.5, int(constants.SCREEN_HEIGHT * 0.6))
        logo_height = logo_width // 2
        return (logo_width, logo_height)

    def __init__(self) -> None:
        self.eggs_by_module = self.load_eggs_by_module()
        self.current_module_index = 0
        self.current_egg_row = 0
        self.current_egg_col = 0
        self.scroll_offset = 0  # For vertical scrolling
        self.egg_sprites = {}
        self.module_logo = None
        # Use same font sizing as digidex
        self.font = get_font(int(14 * constants.UI_SCALE))

        # Use new method for unknown sprite and scale
        try:
            self.unknown_sprite = sprite_load_percent(
                constants.UNKNOWN_SPRITE_PATH,
                percent=(self.EGG_SIZE[1] / constants.SCREEN_HEIGHT) * 100,
                keep_proportion=True,
                base_on="height"
            )
        except Exception:
            self.unknown_sprite = None

        # Traited overlay (same size as egg sprite) - optional
        try:
            self.traited_sprite = sprite_load_percent(
                constants.TRAITED_EGG_PATH,
                percent=(self.EGG_SIZE[1] / constants.SCREEN_HEIGHT) * 100,
                keep_proportion=True,
                base_on="height"
            )
        except Exception:
            self.traited_sprite = None

        runtime_globals.game_console.log(f"[SceneEggSelection] Modules loaded: {len(self.eggs_by_module)}")
        # Use same background handling as SceneDigidex
        if constants.SCREEN_WIDTH > constants.SCREEN_HEIGHT:
            self.bg_sprite = sprite_load_percent(
                constants.DIGIDEX_BACKGROUND_PATH,
                percent=600,
                keep_proportion=True,
                base_on="width"
            )
        else:
            self.bg_sprite = sprite_load_percent(
                constants.DIGIDEX_BACKGROUND_PATH,
                percent=100,
                keep_proportion=True,
                base_on="height"
            )
        
        self.bg_frame = 0
        self.bg_timer = 0
        self.bg_frame_width = self.bg_sprite.get_width() // 6  # 326

        self.load_egg_sprites()
        self.load_module_logo()
        self.locked_special_eggs = {}
        self.cache_locked_special_eggs()

        self._last_cache = None
        self._last_cache_key = None

    def load_eggs_by_module(self):
        eggs_by_module = {}
        for module_name, module in runtime_globals.game_modules.items():
            eggs = module.get_monsters_by_stage(0)
            if eggs:
                eggs_by_module[module_name] = eggs
                for egg in eggs:
                    if egg.get("special", False):
                        special_key = egg.get("special_key", "")
                        module_val = egg.get("module", module_name)
                        if not is_unlocked(module_val, None, special_key):
                            continue  # Skip locked special egg
        return eggs_by_module

    def load_egg_sprites(self):
        for module_name, eggs in self.eggs_by_module.items():
            for egg in eggs:
                egg_name = egg["name"]
                try:
                    module = get_module(egg["module"])
                    module_path = module.folder_path
                    
                    # Use the new sprite utilities to load pet sprites with fallback support
                    sprites_dict = load_pet_sprites(
                        egg_name, 
                        module_path, 
                        module.name_format, 
                        size=self.EGG_SIZE
                    )
                    
                    # Get the first frame (0.png)
                    if "0" in sprites_dict:
                        self.egg_sprites[egg_name] = sprites_dict["0"]
                        runtime_globals.game_console.log(f"[SceneEggSelection] Loaded sprite for {egg_name}")
                    else:
                        self.egg_sprites[egg_name] = None
                        runtime_globals.game_console.log(f"[SceneEggSelection] No sprite found for {egg_name}")
                        
                except Exception as e:
                    self.egg_sprites[egg_name] = None
                    runtime_globals.game_console.log(f"[SceneEggSelection] Failed to load sprite for {egg_name}: {e}")

    def cache_locked_special_eggs(self):
        """Cache locked status for all special eggs."""
        for module_name, eggs in self.eggs_by_module.items():
            for egg in eggs:
                if egg.get("special", False):
                    special_key = egg.get("special_key", "")
                    module = egg.get("module", module_name)
                    locked = not is_unlocked(module, None, special_key)
                    self.locked_special_eggs[(module, egg["name"])] = locked
                    
    def load_module_logo(self):
        module_name = list(self.eggs_by_module.keys())[self.current_module_index]
        module_path = get_module(module_name).folder_path
        logo_path = os.path.join(module_path, "logo.png")
        try:
            # Use new method for logo, scale to LOGO_SIZE height
            self.module_logo = sprite_load_percent(
                logo_path,
                percent=(self.LOGO_SIZE[1] / constants.SCREEN_HEIGHT) * 100,
                keep_proportion=True,
                base_on="height"
            )
            runtime_globals.game_console.log(f"[SceneEggSelection] Loaded module logo: {logo_path}")
        except Exception:
            self.module_logo = None
            runtime_globals.game_console.log(f"[SceneEggSelection] Failed to load logo: {logo_path}")

    def is_empty(self, x, y):
        module_name = list(self.eggs_by_module.keys())[self.current_module_index]
        eggs = self.eggs_by_module[module_name]
        index = y * self.GRID_COLUMNS + x
        return index >= len(eggs)
    
    def move_selection(self, direction):
        module_name = list(self.eggs_by_module.keys())[self.current_module_index]
        eggs = self.eggs_by_module[module_name]
        total_rows = (len(eggs) + self.GRID_COLUMNS - 1) // self.GRID_COLUMNS

        if direction == "LEFT":
            if self.current_egg_col == 0:
                self.current_module_index = (self.current_module_index - 1) % len(self.eggs_by_module)
                self.current_egg_col = self.GRID_COLUMNS - 1
                found = False
                while not found:
                    if self.is_empty(self.current_egg_col, self.current_egg_row):
                        self.current_egg_col -= 1
                        if self.current_egg_col < 0:
                            self.current_egg_col = self.GRID_COLUMNS - 1
                            self.current_egg_row -= 1
                            if self.current_egg_row < 0:
                                self.current_egg_row = total_rows - 1
                    else:
                        found = True
                    
                self.load_module_logo()
            else:
                self.current_egg_col -= 1

        elif direction == "RIGHT":
            if self.current_egg_col == self.GRID_COLUMNS - 1 or self.is_empty(self.current_egg_col + 1, self.current_egg_row):
                self.current_module_index = (self.current_module_index + 1) % len(self.eggs_by_module)
                self.current_egg_col = 0
                self.load_module_logo()
            else:
                self.current_egg_col += 1

        elif direction == "UP":
            prev_row = self.current_egg_row
            wrapped = False
            while True:
                if self.current_egg_row > 0:
                    self.current_egg_row -= 1
                else:
                    self.current_egg_row = total_rows - 1
                    wrapped = True
                # If not empty, break; if we've looped all rows, stop
                if not self.is_empty(self.current_egg_col, self.current_egg_row) or self.current_egg_row == prev_row:
                    break
            if self.current_egg_row < self.scroll_offset or wrapped:
                self.scroll_offset = max(0, self.current_egg_row - self.GRID_ROWS + 1)

        elif direction == "DOWN":
            prev_row = self.current_egg_row
            total_rows = (len(eggs) + self.GRID_COLUMNS - 1) // self.GRID_COLUMNS
            wrapped = False
            while True:
                if self.current_egg_row < total_rows - 1:
                    self.current_egg_row += 1
                else:
                    self.current_egg_row = 0
                    wrapped = True
                # If not empty, break; if we've looped all rows, stop
                if not self.is_empty(self.current_egg_col, self.current_egg_row) or self.current_egg_row == prev_row:
                    break
            if self.current_egg_row >= self.scroll_offset + self.GRID_ROWS or wrapped:
                self.scroll_offset = max(0, self.current_egg_row - self.GRID_ROWS + 1)

        runtime_globals.game_console.log(f"[SceneEggSelection] Module: {module_name}, Position: ({self.current_egg_row}, {self.current_egg_col}), Scroll Offset: {self.scroll_offset}")

    def invalidate_cache(self):
        self._last_cache = None
        self._last_cache_key = None

    def draw(self, surface):
        # Always update background animation
        frame_rect = pygame.Rect(self.bg_frame * self.bg_frame_width, 0, self.bg_frame_width, constants.SCREEN_HEIGHT)
        surface.blit(self.bg_sprite, (0, 0), frame_rect)

        # Cache key includes module, row, col, scroll, and UI/layout
        cache_key = (
            self.current_module_index,
            self.current_egg_row,
            self.current_egg_col,
            self.scroll_offset,
            constants.SCREEN_WIDTH,
            constants.SCREEN_HEIGHT,
            constants.UI_SCALE
        )
        if self._last_cache_key != cache_key or self._last_cache is None:
            cached_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)

            # Draw module logo with better positioning
            if self.module_logo:
                logo_x = (constants.SCREEN_WIDTH - self.module_logo.get_width()) // 2
                logo_y = int(20 * constants.UI_SCALE)  # Fixed top margin
                cached_surface.blit(self.module_logo, (logo_x, logo_y))

            module_name = list(self.eggs_by_module.keys())[self.current_module_index]
            eggs = self.eggs_by_module[module_name]

            # Calculate layout similar to digidex but for grid
            logo_height = self.module_logo.get_height() if self.module_logo else 0
            start_y = logo_height + int(30 * constants.UI_SCALE)  # More spacing after logo
            
            # Calculate proper spacing for eggs based on available space
            available_height = constants.SCREEN_HEIGHT - start_y - int(10 * constants.UI_SCALE)  # Bottom margin
            row_height = available_height // self.GRID_ROWS
            egg_spacing_y = max(row_height - self.EGG_SIZE[1], int(15 * constants.UI_SCALE))
            
            # Calculate adaptive horizontal spacing based on screen width
            available_width = constants.SCREEN_WIDTH - int(40 * constants.UI_SCALE)  # Side margins
            total_egg_width = self.GRID_COLUMNS * self.EGG_SIZE[0]
            remaining_width = available_width - total_egg_width
            col_spacing_x = max(remaining_width // (self.GRID_COLUMNS - 1), int(10 * constants.UI_SCALE)) if self.GRID_COLUMNS > 1 else 0
            
            # Calculate grid positioning - center the entire grid
            total_grid_width = total_egg_width + (self.GRID_COLUMNS - 1) * col_spacing_x
            grid_start_x = (constants.SCREEN_WIDTH - total_grid_width) // 2
            col_spacing = self.EGG_SIZE[0] + col_spacing_x

            for index, egg in enumerate(eggs):
                row = index // self.GRID_COLUMNS
                col = index % self.GRID_COLUMNS

                if not (self.scroll_offset <= row < self.scroll_offset + self.GRID_ROWS):
                    continue  # Skip rows outside of the visible range

                visible_row = row - self.scroll_offset
                x = grid_start_x + (col * col_spacing)
                y = start_y + (visible_row * (self.EGG_SIZE[1] + egg_spacing_y))

                egg_name = egg["name"]
                egg_sprite = self.egg_sprites.get(egg_name, None)

                # Check if special and locked
                module = egg.get("module", module_name)
                is_locked_special = self.locked_special_eggs.get((module, egg_name), False)

                # Background rectangle with proper padding - smaller boxes
                padding = int(4 * constants.UI_SCALE)  # Reduced from 15 to 8
                rect_surface = pygame.Surface((self.EGG_SIZE[0] + padding * 2, self.EGG_SIZE[1] + padding * 2), pygame.SRCALPHA)
                rect_surface.fill((206, 202, 239, 128))  # RGBA with alpha 128 (~50%)
                cached_surface.blit(rect_surface, (x - padding, y - padding))

                if is_locked_special:
                    if self.unknown_sprite:
                        blit_with_shadow(cached_surface, self.unknown_sprite, (x, y - (padding * 2)))
                elif egg_sprite:
                    blit_with_shadow(cached_surface, egg_sprite, (x, y - (padding * 2)))

                # Overlay trait mark if this egg/version is marked as traited
                egg_key = f"{module_name}@{egg.get('version')}"
                if egg_key in game_globals.traited and self.traited_sprite:
                    blit_with_shadow(cached_surface, self.traited_sprite, (x, y - (padding * 2)))

                display_name = "???" if is_locked_special else egg_name.replace("DmC", "").replace("PenC", "").replace("Version", "")
                text = self.font.render(display_name, True, constants.FONT_COLOR_DEFAULT)
                text_x = x + (self.EGG_SIZE[0] // 2) - (text.get_width() // 2)
                text_y = y + self.EGG_SIZE[1] + int(5 * constants.UI_SCALE)
                blit_with_shadow(cached_surface, text, (text_x, text_y - (padding * 3)))

            self._last_cache = cached_surface
            self._last_cache_key = cache_key

        # Blit cached content (eggs, logo, names)
        surface.blit(self._last_cache, (0, 0))

        # Draw cursor highlight (always on top, not cached) with proper positioning
        module_name = list(self.eggs_by_module.keys())[self.current_module_index]
        eggs = self.eggs_by_module[module_name]
        
        # Use the same calculation as in the cached section
        logo_height = self.module_logo.get_height() if self.module_logo else 0
        start_y = logo_height + int(30 * constants.UI_SCALE)
        
        available_height = constants.SCREEN_HEIGHT - start_y - int(10 * constants.UI_SCALE)
        row_height = available_height // self.GRID_ROWS
        egg_spacing_y = max(row_height - self.EGG_SIZE[1], int(15 * constants.UI_SCALE))
        
        # Calculate adaptive horizontal spacing (same as cached section)
        available_width = constants.SCREEN_WIDTH - int(40 * constants.UI_SCALE)  # Side margins
        total_egg_width = self.GRID_COLUMNS * self.EGG_SIZE[0]
        remaining_width = available_width - total_egg_width
        col_spacing_x = max(remaining_width // (self.GRID_COLUMNS - 1), int(10 * constants.UI_SCALE)) if self.GRID_COLUMNS > 1 else 0
        
        # Calculate grid positioning - center the entire grid
        total_grid_width = total_egg_width + (self.GRID_COLUMNS - 1) * col_spacing_x
        grid_start_x = (constants.SCREEN_WIDTH - total_grid_width) // 2
        col_spacing = self.EGG_SIZE[0] + col_spacing_x
        
        index = self.current_egg_row * self.GRID_COLUMNS + self.current_egg_col
        if 0 <= index < len(eggs):
            row = self.current_egg_row
            col = self.current_egg_col
            visible_row = row - self.scroll_offset
            if 0 <= visible_row < self.GRID_ROWS:
                x = grid_start_x + (col * col_spacing)
                y = start_y + (visible_row * (self.EGG_SIZE[1] + egg_spacing_y))
                padding = int(8 * constants.UI_SCALE)  # Match the reduced padding
                pygame.draw.rect(
                    surface,
                    constants.FONT_COLOR_GREEN,
                    (x - padding, y - padding, self.EGG_SIZE[0] + padding * 2, self.EGG_SIZE[1] + padding * 2),
                    int(3 * constants.UI_SCALE)  # Border thickness
                )

    def update(self):
        self.bg_timer += 1
        if self.bg_timer >= 3 * (constants.FRAME_RATE / 30):  # Change frame every 3 seconds like digidex
            self.bg_timer = 0
            self.bg_frame = (self.bg_frame + 1) % 6

    def handle_event(self, input_action):
        if input_action in ["LEFT", "RIGHT", "UP", "DOWN"]:
            runtime_globals.game_sound.play("menu")
            self.move_selection(input_action)
        elif input_action in ["A", "START"]:
            runtime_globals.game_sound.play("menu")
            module_name = list(self.eggs_by_module.keys())[self.current_module_index]
            eggs = self.eggs_by_module[module_name]
            index = self.current_egg_row * self.GRID_COLUMNS + self.current_egg_col
            if 0 <= index < len(eggs):
                selected_egg = eggs[index]
                module = selected_egg.get("module", module_name)
                if self.locked_special_eggs.get((module, selected_egg["name"]), False):
                    runtime_globals.game_console.log("[SceneEggSelection] This egg is locked!")
                    return
                self.select_egg(eggs[index])
        elif input_action == "B" and len(game_globals.pet_list) > 0:
            runtime_globals.game_sound.play("cancel")
            change_scene("game")

    def select_egg(self, selected_egg):
        runtime_globals.game_console.log(f"[SceneEggSelection] Selected egg: {selected_egg['name']}")
        pet = GamePet(selected_egg)
        egg_key = f"{selected_egg['module']}@{selected_egg['version']}"
        register_digidex_entry(pet.name, pet.module, pet.version)
        if egg_key in game_globals.traited:
            pet.traited = True
            game_globals.traited.remove(egg_key)
        game_globals.pet_list.append(pet)
        bg_name = f"ver{selected_egg['version']}"

        # Only unlock objects of type "egg" with no version or matching the egg's version
        module_unlockables = get_module(selected_egg["module"]).unlocks
        unlocks = module_unlockables if isinstance(module_unlockables, list) else []
        for unlock in unlocks:
            if unlock.get("type") == "egg":
                if "version" not in unlock or unlock.get("version") == selected_egg["version"]:
                    unlock_item(selected_egg["module"], "egg", unlock["name"])

        if not game_globals.game_background:
            game_globals.game_background = bg_name
            game_globals.background_module_name = selected_egg["module"]
        change_scene("game")
