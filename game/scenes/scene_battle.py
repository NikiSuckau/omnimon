"""
Scene Battle
Handles Battle menu with new UI system.
"""
import pygame

from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.background import Background
from core import runtime_globals
from core.utils.scene_utils import change_scene
from components.ui.ui_constants import BASE_RESOLUTION

#=====================================================================
# SceneBattle (Battle Menu)
#=====================================================================

class SceneBattle:
    """
    Battle menu scene using the new UI system.
    """

    def __init__(self) -> None:
        # Use RED theme for battle
        self.ui_manager = UIManager("RED")
        
        # UI Components
        self.background = None
        self.title_scene = None
        self.jogress_button = None
        self.versus_button = None
        self.armor_button = None
        self.adventure_button = None
        self.exit_button = None
        
        # Set up UI
        self.setup_ui()
        
        runtime_globals.game_console.log("[SceneBattle] Battle scene initialized with new UI system.")

    def setup_ui(self):
        """Setup the UI components for the battle menu."""
        try:
            # Use base 240x240 resolution for UI layout
            ui_width = ui_height = BASE_RESOLUTION
            
            # Create and add the UI background that covers the full UI area
            self.background = Background(ui_width, ui_height)
            # Set single black region covering entire UI
            self.background.set_regions([(0, ui_height, "black")])
            self.ui_manager.add_component(self.background)
            
            # Create and add the title scene at top left
            self.title_scene = TitleScene(0, 5, "BATTLE")
            self.ui_manager.add_component(self.title_scene)
            
            # Create battle type buttons
            button_width = 56
            button_height = 56
            button_spacing = 8
            
            # Calculate positions for 3 buttons side by side
            total_width = (button_width * 3) + (button_spacing * 2)
            start_x = (ui_width - total_width) // 2
            start_y = 40  # Below title
            
            # Row 1: Jogress, Versus, Armor (3 buttons side by side with both top sides cut)
            self.jogress_button = Button(
                start_x, start_y, button_width, button_height,
                "JOGRESS", self.on_jogress,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.jogress_button)

            self.versus_button = Button(
                start_x + (button_width + button_spacing), start_y, button_width, button_height,
                "VERSUS", self.on_versus,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.versus_button)

            self.armor_button = Button(
                start_x + (button_width + button_spacing) * 2, start_y, button_width, button_height,
                "ARMOR", self.on_armor,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.armor_button)

            # Adventure button (occupying same width as 3 buttons above)
            adventure_y = start_y + button_height + button_spacing
            self.adventure_button = Button(
                start_x, adventure_y, total_width, button_height,
                "ADVENTURE", self.on_adventure,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.adventure_button)

            # Exit button (smaller, centered under adventure)
            exit_width = 80
            exit_height = 40
            exit_x = (ui_width - exit_width) // 2
            exit_y = adventure_y + button_height + button_spacing
            
            self.exit_button = Button(
                exit_x, exit_y, exit_width, exit_height,
                "EXIT", self.on_exit,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.exit_button)
            
            runtime_globals.game_console.log("[SceneBattle] UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
        
        # Set mouse mode and focus on the first button initially
        self.ui_manager.set_mouse_mode()
        if self.jogress_button:
            self.ui_manager.set_focused_component(self.jogress_button)
    
    # Button callback methods (placeholders for now, will implement step by step)
    def on_jogress(self):
        """Handle Jogress button press."""
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log("Jogress button pressed - not implemented yet")
        
    def on_versus(self):
        """Handle Versus button press."""
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log("Versus button pressed - not implemented yet")
        
    def on_armor(self):
        """Handle Armor button press."""
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log("Armor button pressed - not implemented yet")
        
    def on_adventure(self):
        """Handle Adventure button press."""
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log("Adventure button pressed - not implemented yet")
        
    def on_exit(self):
        """Handle Exit button press."""
        runtime_globals.game_sound.play("cancel")
        change_scene("game")

    def update(self):
        """Update the UI manager."""
        self.ui_manager.update()

    def draw(self, surface: pygame.Surface):
        """Draw the battle menu using the new UI system."""
        surface.fill((0, 0, 0))  # Black background
        self.ui_manager.draw(surface)

    def handle_event(self, input_action):
        """Handle input events for the battle menu."""
        self.ui_manager.handle_event(input_action)