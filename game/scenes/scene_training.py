"""
Scene Training
Handles both Dummy and Head-to-Head training modes for pets.
"""

import pygame

from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.pet_selector import PetSelector
from components.ui.background import Background
from components.window_background import WindowBackground

from core import game_globals, runtime_globals
from core.combat.count_training import CountMatchTraining
from core.combat.dummy_training import DummyTraining
from core.combat.excite_training import ExciteTraining
from core.combat.head_training import HeadToHeadTraining
from core.combat.mogera_training import MogeraTraining
from core.combat.shake_training import ShakeTraining
import core.constants as constants
from core.utils.pet_utils import get_training_targets
from core.utils.scene_utils import change_scene
from components.ui.ui_constants import BASE_RESOLUTION, GREEN

#=====================================================================
# SceneTraining (Training Menu)
#=====================================================================

class SceneTraining:
    def __init__(self) -> None:
        # Use GREEN theme for training
        self.ui_manager = UIManager("GREEN")
        
        # UI Components for menu phase
        self.background = None
        self.title_scene = None
        self.pet_selector = None
        self.dummy_button = None
        self.head_button = None
        self.count_button = None
        self.excite_button = None
        self.punch_button = None
        self.mogera_button = None
        self.exit_button = None
        
        # Training phase UI components
        self.training_exit_button = None
        
        # Legacy background for training phase
        self.window_background = WindowBackground(False)

        self.phase = "menu"
        self.mode = None
        
        # Create static background surface with border for menu phase
        self.static_border_surface = None
        self.create_static_background()
        
        # Set up modern UI for menu
        self.setup_ui()

        runtime_globals.game_console.log("[SceneTraining] Training scene initialized.")

    def create_static_background(self):
        """Create a static surface with GREEN border around the screen"""
        # Get screen dimensions and UI information
        screen_width, screen_height = constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT
        ui_scale = self.ui_manager.ui_scale
        
        # Calculate border size (2 pixels * ui_scale)
        border_size = 2 * ui_scale
        
        # Create surface for just the GREEN border
        self.static_border_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.static_border_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Draw GREEN border around the UI area
        for i in range(border_size):
            border_rect = pygame.Rect(0, 0, 
                                    screen_width, screen_height)
            pygame.draw.rect(self.static_border_surface, GREEN, border_rect, border_size)
        
        # Blit position is always (0, 0) since surface covers entire screen
        self.static_border_pos = (0, 0)

    def setup_ui(self):
        """Setup the UI components for the training menu."""
        try:
            # Use base 240x240 resolution for UI layout
            ui_width = ui_height = BASE_RESOLUTION
            
            # Create and add the UI background that covers the full UI area
            self.background = Background(ui_width, ui_height)
            # Set single black region covering entire UI
            self.background.set_regions([(0, ui_height, "black")])
            self.ui_manager.add_component(self.background)
            
            # Create and add the title scene at top left
            self.title_scene = TitleScene(0, 5, "TRAINING")
            self.ui_manager.add_component(self.title_scene)
            
            # Create and add the pet selector at bottom right (60% of UI width)
            selector_width = int(ui_width * 0.6)  # 60% of UI width
            selector_height = 46
            selector_x = ui_width - selector_width - 5  # Right aligned with margin
            selector_y = ui_height - selector_height - 5  # Bottom aligned with margin
            
            self.pet_selector = PetSelector(selector_x, selector_y, selector_width, selector_height)
            # Set pets and make it static for now
            self.pet_selector.set_pets(get_training_targets())
            self.pet_selector.set_interactive(False)  # Static display for now
            self.ui_manager.add_component(self.pet_selector)
            
            # Create training type buttons (56x56) arranged in 2 rows of 3
            button_size = 54
            button_spacing = 2
            start_x = 36  # Left margin
            start_y = 25  # Below title
            
            # Row 1: Dummy, Head-to-Head, Count Match
            self.dummy_button = Button(
                start_x, start_y, button_size, button_size,
                "", self.on_dummy_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': False},
                decorators=["Dummy"]
            )
            self.ui_manager.add_component(self.dummy_button)

            self.head_button = Button(
                start_x + (button_size + button_spacing), start_y, button_size, button_size,
                "", self.on_head_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': False},
                decorators=["HeadToHead"]
            )
            self.ui_manager.add_component(self.head_button)

            self.count_button = Button(
                start_x + (button_size + button_spacing) * 2, start_y, button_size, button_size,
                "", self.on_count_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': True},
                decorators=["CountMatch"]
            )
            self.ui_manager.add_component(self.count_button)

            # Row 2: Excite, Punch, Mogera
            row2_y = start_y + button_size + button_spacing

            # Excite button has two decorators: Excite and current XAI number
            excite_decorators = ["Excite", f"Xai_{game_globals.xai}"]
            self.excite_button = Button(
                start_x, row2_y, button_size, button_size,
                "", self.on_excite_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': True},
                decorators=excite_decorators
            )
            self.ui_manager.add_component(self.excite_button)
            
            self.punch_button = Button(
                start_x + (button_size + button_spacing), row2_y, button_size, button_size,
                "", self.on_punch_training,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False},
                decorators=["Punch"]
            )
            self.ui_manager.add_component(self.punch_button)

            self.mogera_button = Button(
                start_x + (button_size + button_spacing) * 2, row2_y, button_size, button_size,
                "", self.on_mogera_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': True},
                decorators=["Mogera"]
            )
            self.ui_manager.add_component(self.mogera_button)

            # Row 3: Exit (under Punch)
            row3_y = row2_y + button_size + button_spacing

            self.exit_button = Button(
                start_x + (button_size + button_spacing), row3_y, button_size, button_size,
                "EXIT", self.on_exit_training,
                cut_corners={'tl': True, 'tr': False, 'bl': False, 'br': True}
            )
            self.ui_manager.add_component(self.exit_button)
            
            runtime_globals.game_console.log("[SceneTraining] UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneTraining] ERROR in setup_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneTraining] Traceback: {traceback.format_exc()}")
            raise
        
        # Set mouse mode and focus on the first button initially
        self.ui_manager.set_mouse_mode()
        if self.dummy_button:
            self.ui_manager.set_focused_component(self.dummy_button)
            
    # Button callback methods that preserve existing training logic
    def on_dummy_training(self):
        """Handle Dummy training button press."""
        if len(get_training_targets()) > 0:
            runtime_globals.game_sound.play("menu")
            self.phase = "dummy"
            self.mode = DummyTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Dummy Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_head_training(self):
        """Handle Head-to-Head training button press."""
        if len(get_training_targets()) > 1:
            runtime_globals.game_sound.play("menu")
            self.phase = "headtohead"

            self.mode = HeadToHeadTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Head-to-Head Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_count_training(self):
        """Handle Count Match training button press."""
        if len(get_training_targets()) > 0:
            runtime_globals.game_sound.play("menu")
            self.phase = "count"
            self.mode = CountMatchTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Count Match Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_excite_training(self):
        """Handle Excite training button press."""
        if len(get_training_targets()) > 0:
            runtime_globals.game_sound.play("menu")
            self.phase = "excite"
            self.mode = ExciteTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Excite Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_punch_training(self):
        """Handle Punch training button press."""
        if len(get_training_targets()) > 0:
            runtime_globals.game_sound.play("menu")
            self.phase = "punch"
            self.mode = ShakeTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Shake Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_mogera_training(self):
        """Handle Mogera training button press."""
        if len(get_training_targets()) > 0:
            runtime_globals.game_sound.play("menu")
            self.phase = "mogera"
            self.mode = MogeraTraining(self.ui_manager)
            self.create_training_exit_button()  # Create exit button for training phase
            runtime_globals.game_console.log("Starting Mogera Training.")
            for pet in get_training_targets():
                pet.check_disturbed_sleep()
        else:
            runtime_globals.game_sound.play("cancel")
            
    def on_exit_training(self):
        """Handle EXIT button press."""
        runtime_globals.game_sound.play("cancel")
        change_scene("game")

    def on_training_exit(self):
        """Handle training exit button press - send B key to current training mode."""
        if self.mode:
            runtime_globals.game_sound.play("cancel")
            self.mode.handle_event("B")

    def create_training_exit_button(self):
        """Create the exit button for training phases using screen coordinates."""
        if not self.training_exit_button:
            # Calculate screen position (top right corner with margin)
            screen_width = constants.SCREEN_WIDTH
            button_size = 30  # 30x30 at 1x scale
            margin = 10
            
            # Position at top right corner of screen
            screen_x = screen_width - (button_size * self.ui_manager.ui_scale) - margin
            screen_y = margin
            
            self.training_exit_button = Button(
                0, 0, button_size, button_size,  # Base size, position will be set via screen coords
                "", self.on_training_exit,
                decorators=["ExitButton_Green"],
                shadow_mode="full"
            )
            
            # Enable screen coordinates and set position
            self.training_exit_button.use_screen_coordinates = True
            self.ui_manager.add_component(self.training_exit_button)
            
            # Set screen position after adding to manager (so scaling is applied)
            self.training_exit_button.set_screen_coordinates(True, screen_x, screen_y)
            self.training_exit_button.focusable = True

    def remove_training_exit_button(self):
        """Remove the training exit button."""
        if self.training_exit_button:
            # Remove from UI manager components list
            if self.training_exit_button in self.ui_manager.components:
                self.ui_manager.components.remove(self.training_exit_button)
            self.training_exit_button = None

    def update(self):
        if self.phase == "menu":
            # Update UI manager for menu phase
            self.ui_manager.update()
            # Update pet selector with current targets
            if self.pet_selector:
                self.pet_selector.set_pets(get_training_targets())
                
        elif self.mode:
            self.mode.update()
            
            # Update the training exit button if it exists
            if self.training_exit_button:
                self.training_exit_button.update()
                
            # Check if training mode completed and return to menu
            if hasattr(self.mode, 'phase') and self.mode.phase == "exit":
                self.phase = "menu"
                self.mode = None
                self.remove_training_exit_button()

    def draw(self, surface: pygame.Surface):
        # Always draw the window background first (all states)
        self.window_background.draw(surface)
        
        # Draw the GREEN border on top
        surface.blit(self.static_border_surface, self.static_border_pos)
        
        if self.phase == "menu":
            # Draw UI components on top
            self.ui_manager.draw(surface)
            
        elif self.mode:
            # Draw training exit button if it exists and mouse is enabled
            # The button is managed by UI manager now, so we draw it separately
            if (self.training_exit_button and 
                runtime_globals.game_input.is_mouse_enabled()):
                self.training_exit_button.draw(surface)


            # Use legacy system for training phases
            if self.mode.phase in ["alert", "impact"]:
                self.mode.draw(surface)
            else:
                self.mode.draw(surface)
                
    def handle_event(self, input_action):
        if input_action:
            if self.phase == "menu":
                self.handle_menu_input(input_action)
            elif self.mode:
                # Handle training exit button events through UI manager
                if (self.training_exit_button and 
                    runtime_globals.game_input.is_mouse_enabled() and
                    hasattr(input_action, 'type') and 
                    input_action.type == pygame.MOUSEBUTTONDOWN and 
                    input_action.button == 1):
                    
                    mouse_pos = input_action.pos
                    if self.training_exit_button.rect.collidepoint(mouse_pos):
                        self.on_training_exit()
                        return
                
                # Pass event to training mode
                self.mode.handle_event(input_action)

    def handle_menu_input(self, input_action):
        # Handle pygame events through UI manager first
        if self.ui_manager.handle_event(input_action):
            return
        
        # Handle string action events (from input manager)
        elif isinstance(input_action, str):
            if input_action == "B":
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
                return

