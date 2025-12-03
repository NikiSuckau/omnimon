import pygame
import os
import datetime

from components.window_background import WindowBackground
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_shadow, get_font, sprite_load_percent
from core.utils.scene_utils import change_scene
from core.utils.utils_unlocks import get_unlocked_backgrounds, is_unlocked


class SceneSettingsMenu:
    """
    Scene for navigating game settings, including background selection.
    """

    def __init__(self) -> None:
        """Initializes the settings menu."""
        self.background = WindowBackground(False)
        self.font = get_font(constants.FONT_SIZE_MEDIUM)

        # Main options menu
        self.options = [
            "Digidex",      
            "Freezer Box",  
            "Unlockables",  
            "Settings"      
        ]
        
        # Settings submenu
        # Screen timeout choices in seconds (0 = off). Cycle: 0,10,20,30,60,120
        self._SCREEN_TIMEOUT_CHOICES = [0, 10, 20, 30, 60, 120]

        self.settings_options = [
            "Background",
            "Show Clock",
            "Sound",
            "Global Wake",
            "Global Sleep",
            "Screen Timeout"
        ]

        # Load sprites for visual indicators using the new method and scale
        self.settings_sprites = {
            "Show Clock": {
                "On": sprite_load_percent(constants.ICON_ON_PATH, percent=(constants.MENU_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height"),
                "Off": sprite_load_percent(constants.ICON_OFF_PATH, percent=(constants.MENU_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
            },
            "Debug": {
                "On": sprite_load_percent(constants.ICON_ON_PATH, percent=(constants.MENU_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height"),
                "Off": sprite_load_percent(constants.ICON_OFF_PATH, percent=(constants.MENU_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
            }
        }

        self.mode = "menu"  # Default mode starts with the main options menu
        self.unlockables_data = []  # Holds unlockables progress for modules
        self.load_unlockables()

        self.selected_index = 0

        self.unlocked_backgrounds = []
        for module in runtime_globals.game_modules.values():
            # Get unlocked backgrounds as dicts with name and label
            for bg in get_unlocked_backgrounds(module.name, getattr(module, "backgrounds", [])):
                self.unlocked_backgrounds.append((module.name, bg["name"], bg.get("label", bg["name"])))
        self.current_bg_index = self.get_current_background_index()
        runtime_globals.game_console.log("[SceneSettingsMenu] Settings menu loaded.")

        self._last_cache = None
        self._last_cache_key = None

    def load_unlockables(self):
        """Loads unlockable progress for all game modules."""
        self.unlockables_data = []
        for module in runtime_globals.game_modules.values():
            unlocks = getattr(module, "unlocks", [])
            # Get all unlocked items (any type) for this module
            unlocked_items = [u for u in unlocks if is_unlocked(module.name, u.get("type", ""), u.get("name", ""))]
            self.unlockables_data.append({
                "name": module.name,
                "icon": runtime_globals.game_module_flag.get(module.name, None),
                "unlocked": unlocked_items,
                "all": unlocks
            })
        self.current_unlock_module_index = 0
        self.current_unlock_item_index = 0

    def get_current_background_index(self) -> int:
        """Gets index of current background in the unlocked list."""
        if not game_globals.game_background:
            return 0
        for i, (mod, name, label) in enumerate(self.unlocked_backgrounds):
            if name == game_globals.game_background and mod == game_globals.background_module_name:
                return i
        return 0

    def invalidate_cache(self):
        self._last_cache = None
        self._last_cache_key = None

    def draw(self, surface: pygame.Surface) -> None:
        """Draws the appropriate menu based on the current mode, using cache for static content."""
        cache_key = (
            self.mode,
            self.selected_index,
            self.current_bg_index if self.mode == "background" else None,
            tuple(self.options) if self.mode == "menu" else None,
            tuple(self.settings_options) if self.mode == "settings" else None,
            constants.SCREEN_WIDTH,
            constants.SCREEN_HEIGHT,
            constants.UI_SCALE
        )
        if self._last_cache_key != cache_key or self._last_cache is None:
            # Redraw and cache
            cached_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            self.background.draw(cached_surface)
            overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 50, 50, 200))  

            title_font = get_font(constants.FONT_SIZE_LARGE)
            option_font = get_font(constants.FONT_SIZE_MEDIUM)

            if self.mode == "unlockables":
                blit_with_shadow(cached_surface, overlay, (0, 0))
                title_surface = title_font.render("Unlockables", True, constants.FONT_COLOR_ORANGE)
                blit_with_shadow(cached_surface, title_surface, (constants.SCREEN_WIDTH // 2 - title_surface.get_width() // 2, int(10 * constants.UI_SCALE)))

                module_count = len(self.unlockables_data)
                module_idx = getattr(self, "current_unlock_module_index", 0)
                item_idx = getattr(self, "current_unlock_item_index", 0)

                if module_count == 0:
                    msg_surface = option_font.render("No modules found.", True, (255, 100, 100))
                    blit_with_shadow(cached_surface, msg_surface, (constants.SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, constants.SCREEN_HEIGHT // 2))
                else:
                    module_data = self.unlockables_data[module_idx]
                    unlocked = module_data["unlocked"]
                    all_items = module_data["all"]

                    # Header: Unlocked X of Y
                    header = f"{module_data['name']}: {len(unlocked)} of {len(all_items)} unlocked"
                    header_surface = option_font.render(header, True, (255, 255, 0))
                    blit_with_shadow(cached_surface, header_surface, (constants.SCREEN_WIDTH // 2 - header_surface.get_width() // 2, int(54 * constants.UI_SCALE)))

                    # Show a scrollable list of unlocked item labels
                    visible_start = max(0, item_idx - 2)
                    visible_items = unlocked[visible_start:visible_start + 5]
                    start_y = int(90 * constants.UI_SCALE)
                    for i, item in enumerate(visible_items):
                        actual_index = visible_start + i
                        label = item.get("label", item.get("name", "???"))
                        color = (255, 255, 0) if actual_index == item_idx else constants.FONT_COLOR_DEFAULT
                        text_surface = option_font.render(label, True, color)
                        blit_with_shadow(cached_surface, text_surface, (int(40 * constants.UI_SCALE), start_y + i * int(40 * constants.UI_SCALE)))
                        if actual_index == item_idx:
                            pygame.draw.rect(
                                cached_surface, constants.FONT_COLOR_ORANGE,
                                (int(30 * constants.UI_SCALE), start_y + i * int(40 * constants.UI_SCALE), constants.SCREEN_WIDTH - int(60 * constants.UI_SCALE), int(36 * constants.UI_SCALE)), 2
                            )

                # Show navigation hints
                #nav_hint = "←/→: Change Module   ↑/↓: Scroll   B/START: Back"
                #nav_surface = option_font.render(nav_hint, True, (180, 180, 180))
                #blit_with_shadow(cached_surface, nav_surface, (constants.SCREEN_WIDTH // 2 - nav_surface.get_width() // 2, constants.SCREEN_HEIGHT - int(30 * constants.UI_SCALE)))

            elif self.mode == "menu":
                blit_with_shadow(cached_surface, overlay, (0, 0))
                title_surface = title_font.render("Settings Menu", True, constants.FONT_COLOR_ORANGE)
                options_list = self.options
            elif self.mode == "settings":
                blit_with_shadow(cached_surface, overlay, (0, 0))
                title_surface = title_font.render("Settings", True, constants.FONT_COLOR_ORANGE)
                options_list = self.settings_options
            elif self.mode == "background":
                title_surface = title_font.render("Select Background", True, constants.FONT_COLOR_ORANGE)
                options_list = []  # No list needed for background selection

                # Draw the current background label
                if self.unlocked_backgrounds:
                    mod, name, label = self.unlocked_backgrounds[self.current_bg_index]
                    bg_surface = option_font.render(label, True, (255, 255, 0))
                    blit_with_shadow(cached_surface, bg_surface, (constants.SCREEN_WIDTH // 2 - bg_surface.get_width() // 2, constants.SCREEN_HEIGHT // 2))

                # Display the high-resolution toggle status
                high_res_status = "High-Res: ON" if game_globals.background_high_res else "High-Res: OFF"
                high_res_surface = option_font.render(high_res_status, True, (200, 200, 200))
                blit_with_shadow(cached_surface, high_res_surface, (constants.SCREEN_WIDTH // 2 - high_res_surface.get_width() // 2, constants.SCREEN_HEIGHT // 2 + int(40 * constants.UI_SCALE)))

            blit_with_shadow(cached_surface, title_surface, (constants.SCREEN_WIDTH // 2 - title_surface.get_width() // 2, int(10 * constants.UI_SCALE)))

            VISIBLE_OPTIONS = 4

            if self.mode in ["menu", "settings"]:
                options_list = self.options if self.mode == "menu" else self.settings_options
                total_options = len(options_list)
                # Calculate which options to show
                if total_options > VISIBLE_OPTIONS:
                    if self.selected_index < VISIBLE_OPTIONS // 2:
                        visible_start = 0
                    elif self.selected_index > total_options - VISIBLE_OPTIONS // 2:
                        visible_start = total_options - VISIBLE_OPTIONS
                    else:
                        visible_start = self.selected_index - VISIBLE_OPTIONS // 2
                else:
                    visible_start = 0
                visible_options = options_list[visible_start:visible_start + VISIBLE_OPTIONS]

                for i, label in enumerate(visible_options):
                    option_idx = visible_start + i
                    color = (255, 255, 0) if option_idx == self.selected_index else constants.FONT_COLOR_DEFAULT
                    text_surface = option_font.render(label, True, color)
                    blit_with_shadow(
                        cached_surface, text_surface,
                        (int(25 * constants.UI_SCALE), int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE))
                    )

                    # --- Change here ---
                    if label == "Sound":
                        sound_value = str(game_globals.sound * 10)
                        value_surface = option_font.render(sound_value, True, color)
                        blit_with_shadow(
                            cached_surface,
                            value_surface,
                            (
                                constants.SCREEN_WIDTH - value_surface.get_width() - int(30 * constants.UI_SCALE),
                                int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE)
                            )
                        )
                    elif label == "Global Wake":
                        wake_str = self._format_time(game_globals.wake_time)
                        value_surface = option_font.render(wake_str, True, color)
                        blit_with_shadow(
                            cached_surface,
                            value_surface,
                            (
                                constants.SCREEN_WIDTH - value_surface.get_width() - int(30 * constants.UI_SCALE),
                                int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE)
                            )
                        )
                    elif label == "Global Sleep":
                        sleep_str = self._format_time(game_globals.sleep_time)
                        value_surface = option_font.render(sleep_str, True, color)
                        blit_with_shadow(
                            cached_surface,
                            value_surface,
                            (
                                constants.SCREEN_WIDTH - value_surface.get_width() - int(30 * constants.UI_SCALE),
                                int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE)
                            )
                        )
                    elif label == "Screen Timeout":
                        timeout = game_globals.screen_timeout if hasattr(game_globals, 'screen_timeout') else 0
                        # display seconds as 0 or minutes when >=60
                        if timeout == 0:
                            screen_timeout_str = "Off"
                        elif timeout < 60:
                            screen_timeout_str = f"{timeout}s"
                        else:
                            screen_timeout_str = f"{timeout // 60}m"
                        value_surface = option_font.render(screen_timeout_str, True, color)
                        blit_with_shadow(
                            cached_surface,
                            value_surface,
                            (
                                constants.SCREEN_WIDTH - value_surface.get_width() - int(30 * constants.UI_SCALE),
                                int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE)
                            )
                        )
                    else:
                        sprite = self.get_setting_sprite(label)
                        if sprite:
                            cached_surface.blit(sprite, (constants.SCREEN_WIDTH - sprite.get_width() - int(20 * constants.UI_SCALE), int(60 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE)))

                    if option_idx == self.selected_index:
                        pygame.draw.rect(
                            cached_surface,
                            constants.FONT_COLOR_ORANGE,
                            (int(15 * constants.UI_SCALE), int(54 * constants.UI_SCALE) + i * int(40 * constants.UI_SCALE), constants.SCREEN_WIDTH - int(30 * constants.UI_SCALE), int(36 * constants.UI_SCALE)),
                            2
                        )

            elif self.mode == "background":
                if self.unlocked_backgrounds:
                    mod, name, label = self.unlocked_backgrounds[self.current_bg_index]
                    # Draw the label instead of the name
                    bg_surface = option_font.render(label, True, (255, 255, 0))
                    blit_with_shadow(cached_surface, bg_surface, (constants.SCREEN_WIDTH // 2 - bg_surface.get_width() // 2, constants.SCREEN_HEIGHT // 2))

            self._last_cache = cached_surface
            self._last_cache_key = cache_key

        # Blit cached content
        surface.blit(self._last_cache, (0, 0))

    def get_setting_sprite(self, label: str):
        """Returns the correct sprite for a setting."""
        if label == "Show Clock":
            return self.settings_sprites["Show Clock"]["On"] if game_globals.showClock else self.settings_sprites["Show Clock"]["Off"]
        elif label == "Debug":
            return self.settings_sprites["Debug"]["On"] if constants.DEBUG_MODE else self.settings_sprites["Debug"]["Off"]
        return None
    
    def handle_event(self, input_action) -> None:
        """Handles navigation and updates mode accordingly, invalidating cache as needed."""
        if input_action:
            if self.mode == "background":
                if input_action == "B":
                    self.mode = "settings"
                    runtime_globals.game_sound.play("cancel")
                    self.invalidate_cache()
                elif input_action in ("LEFT", "RIGHT"):
                    runtime_globals.game_sound.play("menu")
                    self.change_background(increase=(input_action == "RIGHT"))
                    self.invalidate_cache()
                elif input_action == "SELECT":
                    # Toggle high-resolution backgrounds
                    game_globals.background_high_res = not game_globals.background_high_res
                    runtime_globals.game_console.log(f"[SceneSettingsMenu] High-Resolution Backgrounds set to {game_globals.background_high_res}")
                    self.background.load_sprite(False)  # Reload background with updated resolution
                    runtime_globals.game_sound.play("menu")
                    self.invalidate_cache()
                return
            elif self.mode == "unlockables":
                module_count = len(self.unlockables_data)
                module_idx = getattr(self, "current_unlock_module_index", 0)
                item_idx = getattr(self, "current_unlock_item_index", 0)
                unlocked = self.unlockables_data[module_idx]["unlocked"]

                if input_action == "B":
                    runtime_globals.game_sound.play("cancel")
                    self.mode = "menu"
                    self.invalidate_cache()
                elif input_action == "LEFT":
                    runtime_globals.game_sound.play("menu")
                    self.current_unlock_module_index = (module_idx - 1) % module_count
                    self.current_unlock_item_index = 0
                    self.invalidate_cache()
                elif input_action == "RIGHT":
                    runtime_globals.game_sound.play("menu")
                    self.current_unlock_module_index = (module_idx + 1) % module_count
                    self.current_unlock_item_index = 0
                    self.invalidate_cache()
                elif input_action == "UP":
                    runtime_globals.game_sound.play("menu")
                    if unlocked:
                        self.current_unlock_item_index = (item_idx - 1) % len(unlocked)
                    self.invalidate_cache()
                elif input_action == "DOWN":
                    runtime_globals.game_sound.play("menu")
                    if unlocked:
                        self.current_unlock_item_index = (item_idx + 1) % len(unlocked)
                    self.invalidate_cache()
            elif input_action == "START" or input_action == "B":
                runtime_globals.game_sound.play("cancel")
                self.exit_to_game()
                self.invalidate_cache()
            elif input_action == "UP":
                runtime_globals.game_sound.play("menu")
                self.selected_index = (self.selected_index - 1) % len(self.settings_options if self.mode == "settings" else self.options)
                self.invalidate_cache()
            elif input_action == "DOWN":
                runtime_globals.game_sound.play("menu")
                self.selected_index = (self.selected_index + 1) % len(self.settings_options if self.mode == "settings" else self.options)
                self.invalidate_cache()
            elif input_action in ("LEFT", "RIGHT"):
                if self.mode == "settings":
                    self.change_option(increase=(input_action == "RIGHT"))
                    self.invalidate_cache()
                runtime_globals.game_sound.play("menu")
            elif input_action == "A":
                self.handle_enter()
                self.invalidate_cache()

    def handle_enter(self) -> None:
        """Handles selection and transitions between modes."""
        runtime_globals.game_sound.play("menu")

        if self.mode == "settings" and self.settings_options[self.selected_index] == "Background":
            self.mode = "background"
            runtime_globals.game_console.log("[SceneSettingsMenu] Entered Background Selection.")
            return
        
        if self.mode == "menu":
            selected_option = self.options[self.selected_index]
            if selected_option == "Digidex":
                runtime_globals.game_console.log("[SceneSettingsMenu] Opening the Digidex.")
                change_scene("digidex")
            elif selected_option == "Freezer Box":
                runtime_globals.game_console.log("[SceneSettingsMenu] Opening the Freezer Box.")
                change_scene("freezer")
            elif selected_option == "Unlockables":
                runtime_globals.game_console.log("[SceneSettingsMenu] Opening Unlockables view.")
                self.mode = "unlockables"
                self.load_unlockables()
                self.current_unlock_module_index = 0  # Always start with the first module
                self.current_unlock_item_index = 0
                self.selected_index = 0
            elif selected_option == "Settings":
                runtime_globals.game_console.log("[SceneSettingsMenu] Opening Settings menu.")
                self.mode = "settings"
                self.current_submenu = "Settings"
                self.selected_index = 0

    def exit_to_game(self) -> None:
        """Returns to the main settings menu."""
        if self.mode == "settings":
            self.selected_index = 0
            self.mode = "menu" 
            runtime_globals.game_console.log("[SceneSettingsMenu] Returning to main settings menu.")
        else:
            runtime_globals.game_console.log("[SceneSettingsMenu] Returning to main game.")
            change_scene("game")

    def change_option(self, increase: bool) -> None:
        """Changes the value of the selected setting."""
        option = self.settings_options[self.selected_index]

        if option == "Show Clock":
            game_globals.showClock = not game_globals.showClock
            runtime_globals.game_console.log(f"[SceneSettingsMenu] Show Clock set to {game_globals.showClock}")
        elif option == "Sound":
            game_globals.sound = min(10, max(0, game_globals.sound + (1 if increase else -1)))
            runtime_globals.game_console.log(f"[SceneSettingsMenu] Sound set to {game_globals.sound * 10}")
        elif option == "Global Wake":
            game_globals.wake_time = self._change_time(
                game_globals.wake_time, increase, 0, 12
            )
            runtime_globals.game_console.log(f"[SceneSettingsMenu] Global Wake set to {self._format_time(game_globals.wake_time)}")
        elif option == "Global Sleep":
            game_globals.sleep_time = self._change_time(
                game_globals.sleep_time, increase, 12, 24
            )
            runtime_globals.game_console.log(f"[SceneSettingsMenu] Global Sleep set to {self._format_time(game_globals.sleep_time)}")
        elif option == "Screen Timeout":
            current = getattr(game_globals, 'screen_timeout', 0)
            new_val = self._cycle_screen_timeout(current, increase)
            game_globals.screen_timeout = new_val
            runtime_globals.game_console.log(f"[SceneSettingsMenu] Screen Timeout set to {new_val} seconds")

    def change_background(self, increase: bool) -> None:
        """Changes background index while keeping it cyclic."""
        if not self.unlocked_backgrounds:
            return  

        self.current_bg_index = (self.current_bg_index + 1) % len(self.unlocked_backgrounds) if increase else (self.current_bg_index - 1) % len(self.unlocked_backgrounds)

        mod, name, label = self.unlocked_backgrounds[self.current_bg_index]
        game_globals.game_background = name
        game_globals.background_module_name = mod

        self.background.load_sprite(False)  # Force reload
        runtime_globals.game_console.log(f"[SceneSettingsMenu] Background changed to {label} ({mod})")
        self.invalidate_cache()  # Invalidate cache so draw() will redraw with new background

    def _format_time(self, t):
        if t is None:
            return "Off"
        return t.strftime("%H:%M")

    def _cycle_screen_timeout(self, current, increase: bool):
        # Find index in choices and move forward/back with wrap
        try:
            idx = self._SCREEN_TIMEOUT_CHOICES.index(current)
        except ValueError:
            idx = 0
        idx = (idx + (1 if increase else -1)) % len(self._SCREEN_TIMEOUT_CHOICES)
        # Ensure minimum of 10 for non-zero values is already enforced by choices
        return self._SCREEN_TIMEOUT_CHOICES[idx]

    def _change_time(self, current, increase, start_hour, end_hour):
        # If None, set to start
        if current is None:
            if increase:
                return datetime.time(hour=start_hour, minute=30)
            else:
                return datetime.time(hour=end_hour if end_hour != 24 else 23, minute=0 if end_hour != 24 else 30)
        # Convert to minutes
        minutes = current.hour * 60 + current.minute
        step = 30 if increase else -30
        # Range in minutes
        min_minutes = start_hour * 60 + 30
        max_minutes = end_hour * 60 if end_hour != 24 else 0  # 0 for midnight wrap
        # Wrap around
        minutes += step
        if end_hour == 24:
            if minutes >= 24 * 60:
                return None  # Off
            if minutes < 12 * 60 + 30:
                return None  # Off
        else:
            if minutes > max_minutes:
                return None  # Off
            if minutes < min_minutes:
                return None  # Off
        # Clamp to valid time
        hour = (minutes // 60) % 24
        minute = minutes % 60
        return datetime.time(hour=hour, minute=minute)

    def update(self):
        pass