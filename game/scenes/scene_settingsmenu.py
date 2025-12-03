
"""
Scene Settings Menu
Settings menu with options and navigation to Background and Secrets views.
Refactored to use the new UI system with gray theme.
"""

# Standard library imports
import datetime

# Third-party imports
import pygame

# Project imports
from core import game_globals, runtime_globals
from core.utils.scene_utils import change_scene
from core.utils.utils_unlocks import get_unlocked_backgrounds, is_unlocked

from components.ui.ui_manager import UIManager
from components.ui.background import Background
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.ui_constants import BASE_RESOLUTION, YELLOW_BRIGHT
from components.window_background import WindowBackground
from components.ui.label import Label


class SceneSettingsMenu:
    """
    Scene for navigating game settings, including background selection.
    Refactored to use the new UI system.
    """

    def __init__(self) -> None:
        """Initializes the settings menu with UI components."""
        # Global background
        self.window_background = WindowBackground(False)
        
        # UI Manager with gray theme
        self.ui_manager = UIManager(theme="GRAY")
        
        # Connect input manager to UI manager for mouse handling
        self.ui_manager.set_input_manager(runtime_globals.game_input)
        
        # Current view mode: "main", "background", "unlockables"
        self.mode = "main"
        
        # Screen timeout choices in seconds (0 = off). Cycle: 0,10,20,30,60,120
        self._SCREEN_TIMEOUT_CHOICES = [0, 10, 20, 30, 60, 120]
        
        # Unlockables data
        self.unlockables_data = []
        self.current_unlock_module_index = 0
        self.current_unlock_item_index = 0
        
        # Background selection data
        self.unlocked_backgrounds = []
        for module in runtime_globals.game_modules.values():
            for bg in get_unlocked_backgrounds(module.name, getattr(module, "backgrounds", [])):
                self.unlocked_backgrounds.append((module.name, bg["name"], bg.get("label", bg["name"])))
        self.current_bg_index = self.get_current_background_index()
        
        # UI Components
        self.background = None
        self.title_scene = None
        self.option_buttons = []  # 5 setting option buttons
        self.background_button = None
        self.secrets_button = None
        self.exit_button = None
        
        # Background mode components
        self.bg_name_label = None
        self.bg_highres_label = None
        self.bg_left_button = None  # Mouse navigation
        self.bg_right_button = None  # Mouse navigation
        self.bg_select_button = None  # Toggle high-res
        self.bg_back_button = None  # Return to main
        
        # Unlockables mode components
        self.unlockables_header_label = None
        self.unlockables_item_labels = []  # Up to 5 item labels
        self.unlockables_back_button = None  # Return to main
        self.unlockables_left_button = None  # Mouse navigation for modules
        self.unlockables_right_button = None  # Mouse navigation for modules
        
        # Instruction panels for keyboard mode (when mouse disabled)
        self.bg_instructions_labels = []
        self.unlockables_instructions_labels = []
        
        self._setup_ui()
        self.load_unlockables()
        
        runtime_globals.game_console.log("[SceneSettingsMenu] Settings menu initialized with UI system (GRAY theme).")
    
    def _setup_ui(self):
        """Setup UI components for the settings menu."""
        ui_width = ui_height = BASE_RESOLUTION
        
        # Background
        self.background = Background(ui_width, ui_height)
        self.background.set_regions([(0, ui_height, "black")])
        self.ui_manager.add_component(self.background)
        
        # Title
        self.title_scene = TitleScene(0, 5, "SETTINGS")
        self.ui_manager.add_component(self.title_scene)
        
        # Setting option buttons (5 options stacked vertically)
        option_names = ["Show Clock", "Sound", "Global Wake", "Global Sleep", "Screen Timeout"]
        button_width = 224
        button_height = 24
        button_spacing = 2
        start_x = 8
        start_y = 40
        
        for i, name in enumerate(option_names):
            button_y = start_y + (i * (button_height + button_spacing))
            button = Button(
                start_x, button_y, button_width, button_height,
                self._get_setting_display_text(name),
                lambda n=name: self._on_setting_change(n, increase=True),  # LEFT/RIGHT handled in handle_event
                draw_background=True,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': True}
            )
            self.option_buttons.append(button)
            self.ui_manager.add_component(button)
        
        # Bottom buttons (3 buttons side by side)
        button_y = 180
        button_width = 75
        button_height = 52
        button_spacing = 5
        total_width = (button_width * 3) + (button_spacing * 2)
        start_x = (ui_width - total_width) // 2
        
        # Background button
        self.background_button = Button(
            start_x, button_y, button_width, button_height,
            "", self._on_background,
            decorators=["Settings_Background"]
        )
        self.ui_manager.add_component(self.background_button)
        
        # Secrets button
        secrets_x = start_x + button_width + button_spacing
        self.secrets_button = Button(
            secrets_x, button_y, button_width, button_height,
            "", self._on_secrets,
            decorators=["Settings_Secrets"]
        )
        self.ui_manager.add_component(self.secrets_button)
        
        # EXIT button
        exit_x = secrets_x + button_width + button_spacing
        self.exit_button = Button(
            exit_x, button_y, button_width, button_height,
            "EXIT", self._on_exit
        )
        self.ui_manager.add_component(self.exit_button)
        
        # Background mode components (initially hidden)
        self.bg_name_label = Label(6, 80, "", shadow_mode="full", is_title=True, color_override=YELLOW_BRIGHT)
        self.bg_name_label.visible = False
        self.ui_manager.add_component(self.bg_name_label)
        
        self.bg_highres_label = Label(6, 110, "", shadow_mode="full")
        self.bg_highres_label.visible = False
        self.ui_manager.add_component(self.bg_highres_label)
        
        # Mouse navigation buttons for background mode (side by side at bottom)
        nav_button_y = 200
        nav_button_width = 52
        nav_button_height = 32
        nav_button_spacing = 6
        
        # Left arrow button
        left_x = 6
        self.bg_left_button = Button(
            left_x, nav_button_y, nav_button_width, nav_button_height,
            "", lambda: self.change_background(increase=False),
            icon_name="Left", icon_prefix="Settings"
        )
        self.bg_left_button.visible = False
        self.ui_manager.add_component(self.bg_left_button)
        
        # Right arrow button
        right_x = left_x + nav_button_width + nav_button_spacing
        self.bg_right_button = Button(
            right_x, nav_button_y, nav_button_width, nav_button_height,
            "", lambda: self.change_background(increase=True),
            icon_name="Right", icon_prefix="Settings"
        )
        self.bg_right_button.visible = False
        self.ui_manager.add_component(self.bg_right_button)
        
        # SELECT button (toggle high-res)
        select_x = right_x + nav_button_width + nav_button_spacing
        self.bg_select_button = Button(
            select_x, nav_button_y, nav_button_width, nav_button_height,
            "SEL", self._on_toggle_highres
        )
        self.bg_select_button.visible = False
        self.ui_manager.add_component(self.bg_select_button)
        
        # BACK button
        back_x = select_x + nav_button_width + nav_button_spacing
        self.bg_back_button = Button(
            back_x, nav_button_y, nav_button_width, nav_button_height,
            "BACK", self._on_exit
        )
        self.bg_back_button.visible = False
        self.ui_manager.add_component(self.bg_back_button)
        
        # Unlockables mode components (initially hidden)
        self.unlockables_header_label = Label(0, 40, "", shadow_mode="full", color_override=YELLOW_BRIGHT)
        self.unlockables_header_label.visible = False
        self.ui_manager.add_component(self.unlockables_header_label)
        
        # Create 5 item labels for unlockables list
        for i in range(5):
            item_label = Label(20, 70 + i*25, "", shadow_mode="full")
            item_label.visible = False
            self.unlockables_item_labels.append(item_label)
            self.ui_manager.add_component(item_label)
        
        # Navigation buttons for unlockables mode (left/right module navigation)
        unlockables_left_x = 6
        self.unlockables_left_button = Button(
            unlockables_left_x, nav_button_y, nav_button_width, nav_button_height,
            "", self._on_unlockables_prev_module,
            icon_name="Left", icon_prefix="Settings"
        )
        self.unlockables_left_button.visible = False
        self.ui_manager.add_component(self.unlockables_left_button)
        
        unlockables_right_x = unlockables_left_x + nav_button_width + nav_button_spacing
        self.unlockables_right_button = Button(
            unlockables_right_x, nav_button_y, nav_button_width, nav_button_height,
            "", self._on_unlockables_next_module,
            icon_name="Right", icon_prefix="Settings"
        )
        self.unlockables_right_button.visible = False
        self.ui_manager.add_component(self.unlockables_right_button)
        
        # BACK button for unlockables mode
        unlockables_back_x = ui_width - nav_button_width - 6
        self.unlockables_back_button = Button(
            unlockables_back_x, nav_button_y, nav_button_width, nav_button_height,
            "BACK", self._on_exit
        )
        self.unlockables_back_button.visible = False
        self.ui_manager.add_component(self.unlockables_back_button)
        
        # Instruction panels for keyboard mode (shown when mouse disabled)
        # Background mode instructions (3 lines)
        instructions_y = nav_button_y + 2
        line_spacing = 10
        self.bg_instructions_labels = []
        bg_instructions = ["L/R: Change", "SELECT: Hi-Res", "B: Back"]
        for i, text in enumerate(bg_instructions):
            label = Label(6, instructions_y + i * line_spacing, text, shadow_mode="full")
            label.visible = False
            self.bg_instructions_labels.append(label)
            self.ui_manager.add_component(label)
        
        # Unlockables mode instructions (4 lines)
        self.unlockables_instructions_labels = []
        unlockables_instructions = ["L/R: Module", "UP/DOWN: Scroll", "B: Back"]
        for i, text in enumerate(unlockables_instructions):
            label = Label(6, instructions_y + i * line_spacing, text, shadow_mode="full")
            label.visible = False
            self.unlockables_instructions_labels.append(label)
            self.ui_manager.add_component(label)
        
        # Set mouse mode and initial focus
        self.ui_manager.set_mouse_mode()
        if self.option_buttons:
            self.ui_manager.set_focused_component(self.option_buttons[0])
    
    def _get_setting_display_text(self, name):
        """Get the display text for a setting option."""
        if name == "Show Clock":
            return f"Show Clock: {'ON' if game_globals.showClock else 'OFF'}"
        elif name == "Sound":
            return f"Sound: {game_globals.sound * 10}%"
        elif name == "Global Wake":
            wake_str = self._format_time(game_globals.wake_time)
            return f"Wake: {wake_str}"
        elif name == "Global Sleep":
            sleep_str = self._format_time(game_globals.sleep_time)
            return f"Sleep: {sleep_str}"
        elif name == "Screen Timeout":
            timeout = getattr(game_globals, 'screen_timeout', 0)
            timeout_str = "OFF" if timeout == 0 else f"{timeout}s"
            return f"Timeout: {timeout_str}"
        return name
    
    def _update_button_texts(self):
        """Update all option button texts."""
        option_names = ["Show Clock", "Sound", "Global Wake", "Global Sleep", "Screen Timeout"]
        for i, button in enumerate(self.option_buttons):
            if i < len(option_names):
                button.text = self._get_setting_display_text(option_names[i])
                button.needs_redraw = True
    
    def _on_setting_change(self, name, increase=True):
        """Handle setting option change."""
        if name == "Show Clock":
            game_globals.showClock = not game_globals.showClock
            runtime_globals.game_sound.play("menu")
        elif name == "Sound":
            # Cycle sound from 0-10 (wraps around)
            new_sound = game_globals.sound + (1 if increase else -1)
            game_globals.sound = new_sound % 11  # 0-10 inclusive
            runtime_globals.game_sound.play("menu")
        elif name == "Global Wake":
            game_globals.wake_time = self._change_time(game_globals.wake_time, increase, 0, 12, is_sleep=False)
            runtime_globals.game_sound.play("menu")
        elif name == "Global Sleep":
            game_globals.sleep_time = self._change_time(game_globals.sleep_time, increase, 12, 0, is_sleep=True)
            runtime_globals.game_sound.play("menu")
        elif name == "Screen Timeout":
            current = getattr(game_globals, 'screen_timeout', 0)
            new_val = self._cycle_screen_timeout(current, increase)
            game_globals.screen_timeout = new_val
            runtime_globals.game_sound.play("menu")
        
        self._update_button_texts()
    
    def _on_background(self):
        """Handle Background button press."""
        runtime_globals.game_sound.play("menu")
        self.mode = "background"
        self.title_scene.set_text("BACKGROUND")
        # Update current background index to reflect currently selected background
        self.current_bg_index = self.get_current_background_index()
        self._update_view_visibility()
    
    def _on_secrets(self):
        """Handle Secrets button press."""
        runtime_globals.game_sound.play("menu")
        self.mode = "unlockables"
        self.title_scene.set_text("SECRETS")
        self._update_view_visibility()
    
    def _on_toggle_highres(self):
        """Toggle high-resolution backgrounds."""
        game_globals.background_high_res = not game_globals.background_high_res
        runtime_globals.game_console.log(f"[SceneSettingsMenu] High-Res Backgrounds: {game_globals.background_high_res}")
        self.window_background.load_sprite(False)
        runtime_globals.game_sound.play("menu")
        self._update_background_labels()
    
    def _on_exit(self):
        """Handle EXIT/BACK button press."""
        if self.mode != "main":
            # Return to main settings view
            runtime_globals.game_sound.play("cancel")
            self.mode = "main"
            self.title_scene.set_text("SETTINGS")
            self._update_view_visibility()
        else:
            # Exit to game (only when in main mode)
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
    
    def _on_unlockables_prev_module(self):
        """Handle previous module button in unlockables view."""
        module_count = len(self.unlockables_data)
        if module_count > 0:
            self.current_unlock_module_index = (self.current_unlock_module_index - 1) % module_count
            self.current_unlock_item_index = 0
            runtime_globals.game_sound.play("menu")
            self._update_unlockables_labels()
    
    def _on_unlockables_next_module(self):
        """Handle next module button in unlockables view."""
        module_count = len(self.unlockables_data)
        if module_count > 0:
            self.current_unlock_module_index = (self.current_unlock_module_index + 1) % module_count
            self.current_unlock_item_index = 0
            runtime_globals.game_sound.play("menu")
            self._update_unlockables_labels()
    
    def _update_view_visibility(self):
        """Update visibility of components based on current mode."""
        # Check if mouse is enabled
        mouse_enabled = getattr(runtime_globals.game_input, 'mouse_enabled', False)
        
        # Main settings components (visible in main mode only)
        for button in self.option_buttons:
            button.visible = (self.mode == "main")
        self.background_button.visible = (self.mode == "main")
        self.secrets_button.visible = (self.mode == "main")
        self.exit_button.visible = (self.mode == "main")
        
        # Hide UI background when not in main mode (show only global background)
        self.background.visible = (self.mode != "background")
        
        # Background mode components
        is_bg_mode = (self.mode == "background")
        self.bg_name_label.visible = is_bg_mode
        self.bg_highres_label.visible = is_bg_mode
        # Show buttons only if mouse is enabled, otherwise show instructions
        self.bg_left_button.visible = is_bg_mode and mouse_enabled
        self.bg_right_button.visible = is_bg_mode and mouse_enabled
        self.bg_select_button.visible = is_bg_mode and mouse_enabled
        self.bg_back_button.visible = is_bg_mode and mouse_enabled
        # Show instruction labels when mouse disabled
        for label in self.bg_instructions_labels:
            label.visible = is_bg_mode and not mouse_enabled
        if is_bg_mode:
            self._update_background_labels()
        
        # Unlockables mode components
        is_unlockables_mode = (self.mode == "unlockables")
        self.unlockables_header_label.visible = is_unlockables_mode
        for label in self.unlockables_item_labels:
            label.visible = is_unlockables_mode
        # Show buttons only if mouse is enabled, otherwise show instructions
        self.unlockables_left_button.visible = is_unlockables_mode and mouse_enabled
        self.unlockables_right_button.visible = is_unlockables_mode and mouse_enabled
        self.unlockables_back_button.visible = is_unlockables_mode and mouse_enabled
        # Show instruction labels when mouse disabled
        for label in self.unlockables_instructions_labels:
            label.visible = is_unlockables_mode and not mouse_enabled
        if is_unlockables_mode:
            self._update_unlockables_labels()

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

    def update(self) -> None:
        """Updates the settings menu."""
        # Check if mouse mode changed and update visibility accordingly
        mouse_enabled = getattr(runtime_globals.game_input, 'mouse_enabled', False)
        if not hasattr(self, '_last_mouse_enabled'):
            self._last_mouse_enabled = mouse_enabled
        
        if self._last_mouse_enabled != mouse_enabled:
            self._last_mouse_enabled = mouse_enabled
            self._update_view_visibility()
        
        self.ui_manager.update()

    def draw(self, surface: pygame.Surface) -> None:
        """Draws the settings menu."""
        # Draw global background layer
        self.window_background.draw(surface)
        
        # Draw UI components (visibility is controlled by mode)
        self.ui_manager.draw(surface)
    
    def handle_event(self, event) -> None:
        """Handle pygame events and input actions."""
        if not event:
            return
        
        # Handle string input actions from buttons/keyboard
        elif isinstance(event, str):
            input_action = event
            
            # Check if mouse is enabled
            mouse_enabled = getattr(runtime_globals.game_input, 'mouse_enabled', False)
            
            # Handle mode-specific inputs
            if self.mode == "background":
                # B always works to go back
                if input_action == "B":
                    self._on_exit()
                    return
                # Block keyboard shortcuts if mouse is enabled (force button usage)
                if not mouse_enabled:
                    if input_action in ("LEFT", "RIGHT"):
                        self.change_background(increase=(input_action == "RIGHT"))
                        return
                    elif input_action == "SELECT":
                        # Toggle high-resolution via method
                        self._on_toggle_highres()
                        return
            
            elif self.mode == "unlockables":
                module_count = len(self.unlockables_data)
                if module_count == 0:
                    if input_action == "B":
                        self._on_exit()
                    return
                
                # B always works to go back
                if input_action == "B":
                    self._on_exit()
                    return
                
                # Block keyboard shortcuts if mouse is enabled (force button usage)
                if not mouse_enabled:
                    module_idx = self.current_unlock_module_index
                    item_idx = self.current_unlock_item_index
                    unlocked = self.unlockables_data[module_idx]["unlocked"]
                    
                    if input_action == "LEFT":
                        self.current_unlock_module_index = (module_idx - 1) % module_count
                        self.current_unlock_item_index = 0
                        runtime_globals.game_sound.play("menu")
                        self._update_unlockables_labels()
                        return
                    elif input_action == "RIGHT":
                        self.current_unlock_module_index = (module_idx + 1) % module_count
                        self.current_unlock_item_index = 0
                        runtime_globals.game_sound.play("menu")
                        self._update_unlockables_labels()
                        return
                    elif input_action == "UP":
                        if unlocked:
                            self.current_unlock_item_index = (item_idx - 1) % len(unlocked)
                            runtime_globals.game_sound.play("menu")
                            self._update_unlockables_labels()
                        return
                    elif input_action == "DOWN":
                        if unlocked:
                            self.current_unlock_item_index = (item_idx + 1) % len(unlocked)
                            runtime_globals.game_sound.play("menu")
                            self._update_unlockables_labels()
                        return
            elif input_action == "B":
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
                return
            # Main settings mode - handle LEFT/RIGHT for focused option button
            elif self.mode == "main" and input_action in ("LEFT", "RIGHT"):
                if self.ui_manager.focused_index >= 0 and self.ui_manager.focused_index < len(self.ui_manager.focusable_components):
                    focused = self.ui_manager.focusable_components[self.ui_manager.focused_index]
                else:
                    focused = None
                if focused and focused in self.option_buttons:
                    option_idx = self.option_buttons.index(focused)
                    option_names = ["Show Clock", "Sound", "Global Wake", "Global Sleep", "Screen Timeout"]
                    if option_idx < len(option_names):
                        if input_action in ("LEFT", "RIGHT"):
                            self._on_setting_change(option_names[option_idx], increase=(input_action == "RIGHT"))
                return
        
        # Handle pygame events (mouse clicks, etc.)
        if self.ui_manager.handle_event(event):
            return
    
    def _update_background_labels(self):
        """Update background selection labels."""
        if self.unlocked_backgrounds:
            mod, name, label = self.unlocked_backgrounds[self.current_bg_index]
            self.bg_name_label.set_text(label)
            
            high_res_text = f"High-Res: {'ON' if game_globals.background_high_res else 'OFF'}"
            self.bg_highres_label.set_text(high_res_text)
    
    def _update_unlockables_labels(self):
        """Update unlockables/secrets labels."""
        if not self.unlockables_data:
            self.unlockables_header_label.set_text("No modules found")
            for label in self.unlockables_item_labels:
                label.set_text("")
            return
        
        module_data = self.unlockables_data[self.current_unlock_module_index]
        unlocked = module_data["unlocked"]
        
        if not unlocked:
            self.unlockables_header_label.set_text(f"No items unlocked for module {module_data['name']}")
            for label in self.unlockables_item_labels:
                label.set_text("")
            return
        
        # Update header
        header_text = f"{module_data['name']}: {len(unlocked)} of {len(module_data['all'])} unlocked"
        self.unlockables_header_label.set_text(header_text)
        
        # Update item list (5 visible)
        visible_start = max(0, self.current_unlock_item_index - 2)
        visible_items = unlocked[visible_start:visible_start + 5]
        
        for i in range(5):
            if i < len(visible_items):
                item = visible_items[i]
                label_text = item.get("label", item.get("name", "???"))
                self.unlockables_item_labels[i].set_text(label_text)
                
                # Highlight selected item (using color override)
                actual_index = visible_start + i
                self.unlockables_item_labels[i].color_override = None
            else:
                self.unlockables_item_labels[i].set_text("")

    def change_background(self, increase: bool) -> None:
        """Changes background index while keeping it cyclic."""
        if not self.unlocked_backgrounds:
            return  

        self.current_bg_index = (self.current_bg_index + 1) % len(self.unlocked_backgrounds) if increase else (self.current_bg_index - 1) % len(self.unlocked_backgrounds)

        mod, name, label = self.unlocked_backgrounds[self.current_bg_index]
        game_globals.game_background = name
        game_globals.background_module_name = mod

        self.window_background.load_sprite(False)  # Force reload
        runtime_globals.game_console.log(f"[SceneSettingsMenu] Background changed to {label} ({mod})")
        
        # Update labels
        self._update_background_labels()

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

    def _change_time(self, current, increase, start_hour, end_hour, is_sleep=False):
        """
        Cycle through time slots with 30-minute increments.
        Wake: Off -> 00:30 -> 01:00 -> ... -> 12:00 -> Off
        Sleep: Off -> 12:30 -> 13:00 -> ... -> 23:30 -> 00:00 -> Off
        
        The cycle includes None (Off) as the first/last position.
        """
        # Generate time slots in 30-minute increments
        time_slots = []
        
        if is_sleep:
            # Sleep: 12:30 -> 13:00 -> ... -> 23:30 -> 00:00
            # Start at 12:30, go through 23:30, end with 00:00
            time_slots.append(datetime.time(12, 30))
            for hour in range(13, 24):
                time_slots.append(datetime.time(hour, 0))
                time_slots.append(datetime.time(hour, 30))
            # Add 00:00 as the final slot for sleep
            time_slots.append(datetime.time(0, 0))
        else:
            # Wake: 00:30 -> 01:00 -> 01:30 -> ... -> 11:30 -> 12:00
            # Start at 00:30, end at 12:00
            time_slots.append(datetime.time(0, 30))
            for hour in range(1, end_hour + 1):
                time_slots.append(datetime.time(hour, 0))
                if hour < end_hour:  # Don't add 12:30 for wake
                    time_slots.append(datetime.time(hour, 30))
        
        if not time_slots:
            # Fallback if something went wrong
            return None
        
        # Find current position in cycle (or closest match)
        if current is None:
            # Off state - move to first or last time slot
            if increase:
                return time_slots[0]  # Off -> first time
            else:
                return None  # Already Off, stay Off (or could return last time)
        
        # Find closest matching slot
        try:
            current_idx = time_slots.index(current)
        except ValueError:
            # Current time not in slots, find closest
            cur_dt = datetime.datetime(2000, 1, 1, current.hour, current.minute)
            best_idx = 0
            best_diff = None
            for i, slot in enumerate(time_slots):
                slot_dt = datetime.datetime(2000, 1, 1, slot.hour, slot.minute)
                diff = abs((slot_dt - cur_dt).total_seconds())
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_idx = i
            current_idx = best_idx
        
        # Move to next/previous
        if increase:
            new_idx = current_idx + 1
            if new_idx >= len(time_slots):
                # Wrap to Off
                return None
            return time_slots[new_idx]
        else:
            new_idx = current_idx - 1
            if new_idx < 0:
                # Wrap to Off
                return None
            return time_slots[new_idx]