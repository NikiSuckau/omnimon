"""
Scene Battle
Handles Battle menu with new UI system.
"""
import pygame
import random

from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.background import Background
from components.ui.image import Image
from components.ui.pet_selector import PetSelector
from components.ui.jogress_display import JogressDisplay
from components.ui.versus_display import VersusDisplay
from components.ui.armor_display import ArmorDisplay
from components.ui.armor_item_list import ArmorItemList
from components.ui.adventure_panel import AdventurePanel
from components.ui.toggle_button import ToggleButton
from components.ui.button_group import ButtonGroup
from components.ui.area_selection import AreaSelection
from components.window_background import WindowBackground
from core import runtime_globals
from core.utils.scene_utils import change_scene
from core.utils.pet_utils import get_selected_pets
from components.ui.ui_constants import BASE_RESOLUTION
from core.combat.sim.models import BattleProtocol
from core.combat.battle_encounter import BattleEncounter
from core.combat.battle_encounter_versus import BattleEncounterVersus

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
        
        # Connect input manager to UI manager for mouse handling
        self.ui_manager.set_input_manager(runtime_globals.game_input)
        
        # Scene state management
        self.current_state = "main_menu"  # "main_menu", "jogress", "versus", "versus_protocol", "armor", "adventure", or "adventure_area"
        self.mode = None  # When set to a battle encounter, delegates update/draw/input to it
        
        # Protocol selection for versus battles
        self.selected_protocol = None
        self.versus_pets_selected = None  # Store pets when moving to protocol selection
        
        # Protocol selection buttons (created but initially hidden)
        self.protocol_buttons = []
        self.protocol_cancel_button = None
        
        # Adventure selection state
        self.selected_module = None
        self.module_buttons = []
        self.module_button_group = ButtonGroup()
        
        # UI Components - Main menu
        self.background = None
        self.title_scene = None
        self.battle_frame = None
        self.jogress_button = None
        self.versus_button = None
        self.armor_button = None
        self.adventure_button = None
        self.exit_button = None
        
        # Battle background for when in battle mode
        self.battle_background = WindowBackground()
        
        # UI Components - Jogress scene
        self.pet_selector = None
        self.jogress_display = None
        self.confirm_button = None
        self.back_button = None
        
        # UI Components - Versus scene
        self.versus_display = None
        # Note: versus scene reuses pet_selector, confirm_button, back_button
        
        # UI Components - Armor scene
        self.armor_display = None
        self.armor_item_list = None
        # Note: armor scene reuses pet_selector, confirm_button, back_button
        
        # UI Components - Adventure scene
        self.adventure_panel = None
        self.adventure_go_button = None
        self.adventure_module_selection_image = None
        self.adventure_random_button = None
        self.adventure_more_button = None
        self.adventure_back_button = None
        
        # UI Components - Adventure area selection
        self.area_selection = None
        self.area_selection_fight_button = None
        self.area_selection_back_button = None
        
        # Jogress selection state
        self.selected_pets = []  # List of selected pet indices (max 2)
        self.selection_themes = ["GREEN", "BLUE"]  # Themes for 1st and 2nd selected pets (Jogress: 1st→left/GREEN, 2nd→right/BLUE)
        self.versus_themes = ["BLUE", "GREEN"]  # Themes for versus mode (Versus: 1st→right/BLUE, 2nd→left/GREEN)
        self.pet_theme_assignments = {}  # Dict: pet_index -> theme_name (persistent assignments)
        
        # Versus selection state (reuses selected_pets and pet_theme_assignments)
        # Uses the same 2-pet selection system as Jogress
        
        # Armor selection state
        self.selected_armor_pet = None  # Single pet index for armor evolution
        self.selected_armor_item = None  # Selected armor item
        
        # Jogress evolution animation state
        self.evolution_animation_active = False
        self.evolution_animation_timer = 0.0
        self.evolution_animation_duration = 3.0  # 3 seconds total animation
        self.pet_circles = []  # List of circle data for animation
        self.particles = []  # List of particles for animation
        
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
            
            # Add Battle_Frame background image at 0,0
            self.battle_frame = Image(0, 0, ui_width, ui_height)
            # Load the Battle_Frame sprite using the UI manager's loading system
            if self.ui_manager:
                frame_sprite = self.ui_manager.load_sprite_integer_scaling("Battle", "Frame", "")
                if frame_sprite:
                    self.battle_frame.set_image(image_surface=frame_sprite)
            self.ui_manager.add_component(self.battle_frame)
            
            # Create battle type buttons with decorators instead of text
            button_width = 61
            button_height = 56
            button_spacing = 9
            
            # Calculate positions for 3 buttons side by side
            total_width = (button_width * 3) + (button_spacing * 2)
            start_x = (ui_width - total_width) // 2
            start_y = 60  # Below title
            
            # Row 1: Jogress, Versus, Armor (3 buttons side by side with decorators)
            self.jogress_button = Button(
                start_x, start_y, button_width, button_height,
                "", self.on_jogress,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False},
                decorators=["Battle_Jogress"]
            )
            self.ui_manager.add_component(self.jogress_button)

            self.versus_button = Button(
                start_x + (button_width + button_spacing), start_y, button_width, button_height,
                "", self.on_versus,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False},
                decorators=["Battle_Versus"]
            )
            self.ui_manager.add_component(self.versus_button)

            self.armor_button = Button(
                start_x + (button_width + button_spacing) * 2, start_y, button_width, button_height,
                "", self.on_armor,
                cut_corners={'tl': True, 'tr': True, 'bl': False, 'br': False},
                decorators=["Battle_Armor"]
            )
            self.ui_manager.add_component(self.armor_button)

            # Adventure button (occupying same width as 3 buttons above, with decorator)
            adventure_y = start_y + button_height + button_spacing//2
            self.adventure_button = Button(
                start_x+2, adventure_y, total_width-2, 34,
                "", self.on_adventure,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False},
                decorators=["Battle_Adventure"],
                draw_background=False  # Only show the decorator, no rectangle background
            )
            self.ui_manager.add_component(self.adventure_button)

            # Exit button (smaller, centered under adventure)
            exit_width = 75
            exit_height = 25
            exit_x = (ui_width - exit_width) // 2
            exit_y = adventure_y + button_height//2 + button_spacing
            
            self.exit_button = Button(
                exit_x, exit_y, exit_width, exit_height,
                "EXIT", self.on_exit,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False}
            )
            self.ui_manager.add_component(self.exit_button)
            
            # Create Jogress scene components (initially hidden)
            self.setup_jogress_ui(ui_width, ui_height)
            
            # Create Versus scene components (initially hidden)
            self.setup_versus_ui(ui_width, ui_height)
            
            # Create Armor scene components (initially hidden)
            self.setup_armor_ui(ui_width, ui_height)
            
            # Create Protocol selection buttons (initially hidden)
            self.setup_protocol_ui(ui_width, ui_height)
            
            # Create Adventure scene components (initially hidden)
            self.setup_adventure_ui(ui_width, ui_height)
            
            runtime_globals.game_console.log("[SceneBattle] UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
        
        # Set mouse mode and focus on the adventure button initially
        self.ui_manager.set_mouse_mode()
        if self.adventure_button:
            self.ui_manager.set_focused_component(self.adventure_button)
            
        # Show main menu initially
        self.show_main_menu()

    def setup_jogress_ui(self, ui_width, ui_height):
        """Setup the UI components for the Jogress sub-scene."""
        try:
            # Jogress display (centered, positioned higher up)
            display_width = 160  # Slightly smaller
            display_height = 125  # Slightly smaller
            display_x = (ui_width - display_width) // 2
            display_y = 25  # Higher up, below title
            
            self.jogress_display = JogressDisplay(display_x, display_y, display_width, display_height)
            self.jogress_display.set_compatibility_callback(self.check_pet_compatibility)
            self.ui_manager.add_component(self.jogress_display)
            
            # Confirm and Back buttons (positioned below jogress display)
            back_button_width = 60
            confirm_button_width = 80  # Confirm is bigger than back
            button_height = 25
            button_spacing = 5
            
            # Position buttons side by side, centered horizontally below jogress display
            total_button_width = back_button_width + confirm_button_width + button_spacing
            buttons_start_x = (ui_width - total_button_width) // 2
            buttons_y = display_y + display_height + 10  # Below jogress display
            
            # Back button (left)
            self.back_button = Button(
                buttons_start_x, buttons_y, back_button_width, button_height,
                "BACK", self.on_back
            )
            self.ui_manager.add_component(self.back_button)
            
            # Confirm button (right)
            confirm_button_x = buttons_start_x + back_button_width + button_spacing
            self.confirm_button = Button(
                confirm_button_x, buttons_y, confirm_button_width, button_height,
                "CONFIRM", self.on_confirm,
                enabled=False  # Disabled initially
            )
            self.ui_manager.add_component(self.confirm_button)
            
            # Pet selector positioned below buttons
            selector_y = buttons_y + button_height + 5  # Below buttons
            selector_height = 50
            self.pet_selector = PetSelector(10, selector_y, ui_width - 20, selector_height)
            self.pet_selector.set_pets(get_selected_pets())
            self.pet_selector.set_interactive(False)  # Start non-interactive, will be enabled in Jogress mode
            
            # Ensure we have pets and set initial focus
            pets = get_selected_pets()
            if pets:
                self.pet_selector.focused_cell = 0
                runtime_globals.game_console.log(f"[SceneBattle] Pet selector initialized with {len(pets)} pets")
            else:
                runtime_globals.game_console.log("[SceneBattle] Warning: No pets available for pet selector")
            
            # Configure pet selector for Jogress with custom activation
            self.pet_selector.activation_callback = self.handle_pet_activation
            
            self.ui_manager.add_component(self.pet_selector)
            
            runtime_globals.game_console.log("[SceneBattle] Jogress UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_jogress_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
    
    def setup_versus_ui(self, ui_width, ui_height):
        """Setup the UI components for the Versus sub-scene."""
        try:
            # Versus display (centered, similar position to jogress)
            display_width = 160  # Same as jogress
            display_height = 80   # Shorter since no top hexagon
            display_x = (ui_width - display_width) // 2
            display_y = 40  # Higher up, below title
            
            self.versus_display = VersusDisplay(display_x, display_y, display_width, display_height)
            self.ui_manager.add_component(self.versus_display)
            
            runtime_globals.game_console.log("[SceneBattle] Versus UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_versus_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
    
    def setup_armor_ui(self, ui_width, ui_height):
        """Setup the UI components for the Armor sub-scene."""
        try:
            # Armor display (left side, similar position to jogress but smaller)
            display_width = 80  # Smaller since it's just one hexagon
            display_height = 80
            display_x = 15  # Left side
            display_y = 40  # Below title
            
            self.armor_display = ArmorDisplay(display_x, display_y, display_width, display_height)
            self.ui_manager.add_component(self.armor_display)
            
            # Armor item list (right side)
            item_list_width = 120
            item_list_height = 130
            item_list_x = ui_width - item_list_width - 10  # Right side with margin
            item_list_y = 25  # Below title
            
            self.armor_item_list = ArmorItemList(
                item_list_x, item_list_y, item_list_width, item_list_height,
                on_item_activated=self.on_armor_item_activated
            )
            # Hide background and border for clean look
            self.armor_item_list.set_background_visible(False)
            self.armor_item_list.set_border_visible(False)
            self.ui_manager.add_component(self.armor_item_list)
            
            runtime_globals.game_console.log("[SceneBattle] Armor UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_armor_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
    
    def setup_protocol_ui(self, ui_width, ui_height):
        """Setup the UI components for the Protocol selection sub-scene."""
        try:
            # Protocol selection buttons (centered vertically)
            button_width = 120
            button_height = 30
            button_spacing = 8
            
            # Calculate starting position to center the buttons
            protocol_options = ["DM20", "Pen20", "DMX/PenZ", "DMC"]
            total_height = (len(protocol_options) * button_height) + ((len(protocol_options) - 1) * button_spacing)
            start_y = (ui_height - total_height) // 2 - 20  # Center vertically, slightly higher
            start_x = (ui_width - button_width) // 2  # Center horizontally
            
            # Create protocol buttons
            for i, protocol in enumerate(protocol_options):
                button_y = start_y + i * (button_height + button_spacing)
                
                # Create button with protocol selection callback
                protocol_button = Button(
                    start_x, button_y, button_width, button_height,
                    protocol, lambda p=protocol: self.on_protocol_selected(p),
                    cut_corners={'tl': True, 'tr': True, 'bl': True, 'br': True}
                )
                protocol_button.visible = False  # Initially hidden
                self.protocol_buttons.append(protocol_button)
                self.ui_manager.add_component(protocol_button)
            
            # Cancel button (below protocol buttons)
            cancel_y = start_y + total_height + button_spacing * 2
            self.protocol_cancel_button = Button(
                start_x, cancel_y, button_width, button_height,
                "CANCEL", self.on_protocol_cancel,
                cut_corners={'tl': True, 'tr': True, 'bl': True, 'br': True}
            )
            self.protocol_cancel_button.visible = False  # Initially hidden
            self.ui_manager.add_component(self.protocol_cancel_button)
            
            runtime_globals.game_console.log("[SceneBattle] Protocol UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_protocol_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
    
    def setup_adventure_ui(self, ui_width, ui_height):
        """Setup the UI components for the Adventure sub-scene."""
        try:
            # Adventure panel (displays selected module info)
            self.adventure_panel = AdventurePanel(8, 43, 165, 55)
            self.adventure_panel.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_panel)
            
            # GO button (to the right of adventure panel)
            self.adventure_go_button = Button(
                179, 43, 52, 55,
                "", self.on_adventure_go,
                cut_corners={},
                decorators=["Battle_BattleGo"]
            )
            self.adventure_go_button.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_go_button)
            
            # Module selection background image
            # Height should be auto-calculated from sprite, set to reasonable value
            self.adventure_module_selection_image = Image(0, 99, 240, 89)
            adventure_selection_sprite = self.ui_manager.load_sprite_integer_scaling("Battle", "ModuleSelection", "")
            if adventure_selection_sprite:
                self.adventure_module_selection_image.set_image(image_surface=adventure_selection_sprite)
                runtime_globals.game_console.log(f"[SceneBattle] ModuleSelection sprite loaded: {adventure_selection_sprite.get_size()}")
            else:
                runtime_globals.game_console.log("[SceneBattle] WARNING: ModuleSelection sprite not found")
            self.adventure_module_selection_image.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_module_selection_image)
            
            # Module toggle buttons (4 buttons in a row)
            button_size = 56
            button_spacing = 1
            start_x = 6
            start_y = 120
            
            # Get available modules with smart ordering
            available_modules = self._get_ordered_adventure_modules()[:4]  # Up to 4 modules
            
            for i, module in enumerate(available_modules):
                button_x = start_x + i * (button_size + button_spacing)
                
                # Create toggle button with module's BattleIcon
                # Note: on_toggle receives (button, toggled) so we capture module in closure
                module_button = ToggleButton(
                    button_x, start_y, button_size, button_size,
                    "",
                    on_toggle=lambda btn, tog, mod=module: self.on_module_toggled(mod, tog)
                )
                
                # Store module reference on button for direct access
                module_button.module = module
                
                # Load the module's BattleIcon sprite (48x48 base size, no scaled versions)
                # Use pygame to load and scale it manually with integer scaling
                try:
                    import pygame
                    battle_icon_path = module.folder_path + "/BattleIcon.png"
                    battle_icon = pygame.image.load(battle_icon_path).convert_alpha()
                    
                    # Scale to match UI scale (1x, 2x, 3x, etc.)
                    sprite_scale = self.ui_manager.get_sprite_scale()
                    scaled_size = (48 * sprite_scale, 48 * sprite_scale)
                    scaled_icon = pygame.transform.scale(battle_icon, scaled_size)
                    
                    # Set as icon for the button (will be centered automatically by Button class)
                    module_button.icon_sprite = scaled_icon
                    
                    runtime_globals.game_console.log(f"[SceneBattle] Loaded BattleIcon for {module.name}: {scaled_size}")
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneBattle] Failed to load BattleIcon for {module.name}: {e}")
                
                module_button.visible = False  # Initially hidden
                self.module_buttons.append(module_button)
                self.module_button_group.add_button(module_button)
                self.ui_manager.add_component(module_button)
            
            # Bottom buttons: Random, More, Back
            random_button_width = 66  # Wider for Random
            more_button_width = 56
            back_button_width = 66  # Wider for Back
            bottom_button_height = 25
            bottom_button_spacing = 10
            bottom_start_x = 9
            bottom_start_y = 198  # Adjusted for better vertical centering
            
            # Random button (cut bottom left)
            self.adventure_random_button = Button(
                bottom_start_x, bottom_start_y, random_button_width, bottom_button_height,
                "RANDOM", self.on_adventure_random,
                cut_corners={'tl': False, 'tr': False, 'bl': True, 'br': False}
            )
            self.adventure_random_button.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_random_button)
            
            # More button (no cuts)
            more_x = bottom_start_x + random_button_width + bottom_button_spacing
            self.adventure_more_button = Button(
                more_x, bottom_start_y,
                more_button_width, bottom_button_height,
                "MORE", self.on_adventure_more,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': False}
            )
            self.adventure_more_button.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_more_button)
            
            # Back button (cut bottom right)
            back_x = more_x + more_button_width + bottom_button_spacing
            self.adventure_back_button = Button(
                back_x, bottom_start_y,
                back_button_width, bottom_button_height,
                "BACK", self.on_adventure_back,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': True}
            )
            self.adventure_back_button.visible = False  # Initially hidden
            self.ui_manager.add_component(self.adventure_back_button)
            
            # Area selection components (initially None, created when module is selected)
            self.area_selection = None
            
            # Area selection Fight button (wider for better visibility)
            fight_button_width = 145
            fight_button_height = 25
            area_button_y = 198  # Match bottom button vertical position
            self.area_selection_fight_button = Button(
                9, area_button_y, fight_button_width, fight_button_height,
                "FIGHT", self.on_area_selection_fight,
                cut_corners={'tl': False, 'tr': False, 'bl': True, 'br': False}
            )
            self.area_selection_fight_button.visible = False
            self.ui_manager.add_component(self.area_selection_fight_button)
            
            # Area selection Back button
            back_button_x = 9 + fight_button_width + 10  # 10px spacing
            back_button_width = 66  # Match back button width
            self.area_selection_back_button = Button(
                back_button_x, area_button_y, back_button_width, fight_button_height,
                "BACK", self.on_area_selection_back,
                cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': True}
            )
            self.area_selection_back_button.visible = False
            self.ui_manager.add_component(self.area_selection_back_button)
            
            runtime_globals.game_console.log("[SceneBattle] Adventure UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattle] ERROR in setup_adventure_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattle] Traceback: {traceback.format_exc()}")
            raise
    
    def show_main_menu(self):
        """Show main menu components and hide Jogress and Armor components."""
        self.current_state = "main_menu"
        
        # Clear Jogress selection state and persistent theme assignments
        self.selected_pets = []
        self.pet_theme_assignments = {}
        if self.pet_selector:
            self.pet_selector.selected_pets = []
            self.pet_selector.clear_custom_themes()
            self.pet_selector.set_armor_mode(False)  # Disable armor mode when leaving armor menu
        if self.jogress_display:
            self.jogress_display.clear_all_slots()
            
        # Clear Armor selection state
        self.selected_armor_pet = None
        self.selected_armor_item = None
        if self.armor_display:
            self.armor_display.clear_pet()
        
        # Show main menu components
        if self.battle_frame:
            self.battle_frame.visible = True
        if self.jogress_button:
            self.jogress_button.visible = True
        if self.versus_button:
            self.versus_button.visible = True
        if self.armor_button:
            self.armor_button.visible = True
        if self.adventure_button:
            self.adventure_button.visible = True
        if self.exit_button:
            self.exit_button.visible = True
        
        # Hide Jogress components
        if self.pet_selector:
            self.pet_selector.visible = False
        if self.jogress_display:
            self.jogress_display.visible = False
        if self.confirm_button:
            self.confirm_button.visible = False
        if self.back_button:
            self.back_button.visible = False
            
        # Hide Versus components
        if self.versus_display:
            self.versus_display.visible = False
            
        # Hide Armor components
        if self.armor_display:
            self.armor_display.visible = False
        if self.armor_item_list:
            self.armor_item_list.visible = False
            
        # Hide Protocol selection components
        for button in self.protocol_buttons:
            button.visible = False
        if self.protocol_cancel_button:
            self.protocol_cancel_button.visible = False
            
        # Hide Adventure components
        if self.adventure_panel:
            self.adventure_panel.visible = False
        if self.adventure_go_button:
            self.adventure_go_button.visible = False
        if self.adventure_module_selection_image:
            self.adventure_module_selection_image.visible = False
        for button in self.module_buttons:
            button.visible = False
        if self.adventure_random_button:
            self.adventure_random_button.visible = False
        if self.adventure_more_button:
            self.adventure_more_button.visible = False
        if self.adventure_back_button:
            self.adventure_back_button.visible = False
            
        # Focus on first main menu button
        if self.jogress_button:
            self.ui_manager.set_focused_component(self.jogress_button)
    
    def show_jogress_menu(self):
        """Show Jogress components and hide main menu components (except title)."""
        self.current_state = "jogress"
        
        # Reset selection state and clear persistent theme assignments
        self.selected_pets = []
        self.pet_theme_assignments = {}
        if self.pet_selector:
            self.pet_selector.selected_pets = []
            self.pet_selector.clear_custom_themes()
            self.pet_selector.set_armor_mode(False)  # Disable armor mode when entering jogress menu
            self.pet_selector.needs_redraw = True
        if self.jogress_display:
            self.jogress_display.clear_all_slots()
        if self.confirm_button:
            self.confirm_button.set_enabled(False)
        
        # Hide main menu components (except title_scene)
        if self.battle_frame:
            self.battle_frame.visible = False
        if self.jogress_button:
            self.jogress_button.visible = False
        if self.versus_button:
            self.versus_button.visible = False
        if self.armor_button:
            self.armor_button.visible = False
        if self.adventure_button:
            self.adventure_button.visible = False
        if self.exit_button:
            self.exit_button.visible = False
        
        # Show Jogress components
        if self.pet_selector:
            self.pet_selector.visible = True
        if self.jogress_display:
            self.jogress_display.visible = True
        if self.confirm_button:
            self.confirm_button.visible = True
        if self.back_button:
            self.back_button.visible = True
            
        # Focus on pet selector and ensure it's interactive
        if self.pet_selector:
            self.pet_selector.set_interactive(True)
            self.ui_manager.set_focused_component(self.pet_selector)
            # Reset focus to first pet
            self.pet_selector.focused_cell = 0
    
    def show_versus_menu(self):
        """Show Versus components and hide main menu components (except title)."""
        self.current_state = "versus"
        
        # Reset selection state and clear persistent theme assignments
        self.selected_pets = []
        self.pet_theme_assignments = {}
        if self.pet_selector:
            self.pet_selector.selected_pets = []
            self.pet_selector.clear_custom_themes()
            self.pet_selector.set_armor_mode(False)  # Disable armor mode when entering versus menu
            self.pet_selector.needs_redraw = True
        if self.versus_display:
            self.versus_display.clear_all_slots()
        if self.confirm_button:
            self.confirm_button.set_enabled(False)
        
        # Hide main menu components (except title_scene)
        if self.battle_frame:
            self.battle_frame.visible = False
        if self.jogress_button:
            self.jogress_button.visible = False
        if self.versus_button:
            self.versus_button.visible = False
        if self.armor_button:
            self.armor_button.visible = False
        if self.adventure_button:
            self.adventure_button.visible = False
        if self.exit_button:
            self.exit_button.visible = False
        
        # Hide Jogress components
        if self.jogress_display:
            self.jogress_display.visible = False
        
        # Show Versus components
        if self.pet_selector:
            self.pet_selector.visible = True
        if self.versus_display:
            self.versus_display.visible = True
        if self.confirm_button:
            self.confirm_button.visible = True
        if self.back_button:
            self.back_button.visible = True
            
        # Focus on pet selector and ensure it's interactive
        if self.pet_selector:
            self.pet_selector.set_interactive(True)
            self.ui_manager.set_focused_component(self.pet_selector)
            # Reset focus to first pet
            self.pet_selector.focused_cell = 0
    
    def show_armor_menu(self):
        """Show Armor components and hide main menu components (except title)."""
        self.current_state = "armor"
        
        # Reset armor selection state
        self.selected_armor_pet = None
        self.selected_armor_item = None
        if self.pet_selector:
            self.pet_selector.selected_pets = []
            self.pet_selector.clear_custom_themes()
            self.pet_selector.set_armor_mode(True)  # Enable armor mode for special visual feedback
            self.pet_selector.needs_redraw = True
        if self.armor_display:
            self.armor_display.clear_pet()
        if self.confirm_button:
            self.confirm_button.set_enabled(False)
        
        # Hide main menu components (except title_scene)
        if self.battle_frame:
            self.battle_frame.visible = False
        if self.jogress_button:
            self.jogress_button.visible = False
        if self.versus_button:
            self.versus_button.visible = False
        if self.armor_button:
            self.armor_button.visible = False
        if self.adventure_button:
            self.adventure_button.visible = False
        if self.exit_button:
            self.exit_button.visible = False
        
        # Hide Jogress components
        if self.jogress_display:
            self.jogress_display.visible = False
        
        # Show Armor components
        if self.pet_selector:
            self.pet_selector.visible = True
        if self.armor_display:
            self.armor_display.visible = True
        if self.armor_item_list:
            self.armor_item_list.visible = True
        if self.confirm_button:
            self.confirm_button.visible = True
        if self.back_button:
            self.back_button.visible = True
            
        # Focus on pet selector and ensure it's interactive
        if self.pet_selector:
            self.pet_selector.set_interactive(True)
            self.ui_manager.set_focused_component(self.pet_selector)
            # Reset focus to first pet
            self.pet_selector.focused_cell = 0
    
    def _get_ordered_adventure_modules(self):
        """Get adventure modules ordered by: last played -> pet modules -> rest."""
        from core import game_globals
        
        all_modules = list(runtime_globals.game_modules.values())
        
        # Get last played module
        last_module_name = game_globals.last_adventure_module
        last_module = None
        if last_module_name:
            last_module = runtime_globals.game_modules.get(last_module_name)
        
        # Get pet modules (deduplicated)
        pet_module_names = set()
        for pet in game_globals.pet_list:
            if pet and hasattr(pet, 'module') and pet.module:
                pet_module_names.add(pet.module)
        
        pet_modules = []
        for module_name in pet_module_names:
            module = runtime_globals.game_modules.get(module_name)
            if module:
                pet_modules.append(module)
        
        # Build ordered list
        ordered_modules = []
        
        # 1. Add last played module first (if exists)
        if last_module and last_module not in ordered_modules:
            ordered_modules.append(last_module)
        
        # 2. Add pet modules (excluding last module if already added)
        for pet_module in pet_modules:
            if pet_module not in ordered_modules:
                ordered_modules.append(pet_module)
        
        # 3. Add remaining modules
        for module in all_modules:
            if module not in ordered_modules:
                ordered_modules.append(module)
        
        runtime_globals.game_console.log(f"[SceneBattle] Ordered modules: {[m.name for m in ordered_modules]}")
        return ordered_modules
    
    def show_adventure_menu(self):
        """Show Adventure components and hide main menu components (except title)."""
        self.current_state = "adventure"
        
        # Reset adventure selection state and clear button group
        self.selected_module = None
        self.module_button_group.clear_active()
        
        # Hide main menu components (except title_scene)
        if self.battle_frame:
            self.battle_frame.visible = False
        if self.jogress_button:
            self.jogress_button.visible = False
        if self.versus_button:
            self.versus_button.visible = False
        if self.armor_button:
            self.armor_button.visible = False
        if self.adventure_button:
            self.adventure_button.visible = False
        if self.exit_button:
            self.exit_button.visible = False
        
        # Show Adventure components
        if self.adventure_go_button:
            self.adventure_go_button.visible = True
        if self.adventure_module_selection_image:
            self.adventure_module_selection_image.visible = True
        for button in self.module_buttons:
            button.visible = True
        if self.adventure_random_button:
            self.adventure_random_button.visible = True
        if self.adventure_more_button:
            self.adventure_more_button.visible = True
        if self.adventure_back_button:
            self.adventure_back_button.visible = True
            
        # Activate first module button and show panel
        if self.module_buttons:
            first_button = self.module_buttons[0]
            first_button.set_toggled(True, silent=True)  # Set toggle without callback
            # Manually update selected module and panel
            self.selected_module = first_button.module if hasattr(first_button, 'module') else None
            if self.selected_module and self.adventure_panel:
                self.adventure_panel.set_module(self.selected_module)
                self.adventure_panel.visible = True
            
        # Focus on GO button
        if self.adventure_go_button:
            self.ui_manager.set_focused_component(self.adventure_go_button)
    
    def show_area_selection(self):
        """Show area selection view for the selected adventure module."""
        if not self.selected_module:
            return
        
        self.current_state = "adventure_area"
        
        # Hide module selection components
        if self.adventure_module_selection_image:
            self.adventure_module_selection_image.visible = False
        for button in self.module_buttons:
            button.visible = False
        if self.adventure_random_button:
            self.adventure_random_button.visible = False
        if self.adventure_more_button:
            self.adventure_more_button.visible = False
        if self.adventure_back_button:
            self.adventure_back_button.visible = False
        if self.adventure_go_button:
            self.adventure_go_button.visible = False
        
        # Create or update area selection component
        if self.area_selection:
            self.ui_manager.remove_component(self.area_selection)
        
        self.area_selection = AreaSelection(
            8, 99, 224, 89,
            self.selected_module,
            on_select=self.on_area_selected
        )
        self.area_selection.visible = True
        self.ui_manager.add_component(self.area_selection)
        
        # Show area selection buttons
        if self.area_selection_fight_button:
            self.area_selection_fight_button.visible = True
        if self.area_selection_back_button:
            self.area_selection_back_button.visible = True
        
        # Focus on area selection
        self.ui_manager.set_focused_component(self.area_selection)
        
        runtime_globals.game_console.log(f"[SceneBattle] Area selection shown for {self.selected_module.name}")
    
    def show_protocol_selection(self):
        """Show protocol selection menu for versus battles."""
        self.current_state = "versus_protocol"
        
        # Store the selected pets for battle creation
        self.versus_pets_selected = self.selected_pets.copy()
        
        # Hide UI components that are not needed during protocol selection
        if self.pet_selector:
            self.pet_selector.visible = False
        if self.versus_display:
            self.versus_display.visible = False
        if self.confirm_button:
            self.confirm_button.visible = False
        if self.back_button:
            self.back_button.visible = False
        
        # Show protocol selection buttons
        for button in self.protocol_buttons:
            button.visible = True
        if self.protocol_cancel_button:
            self.protocol_cancel_button.visible = True
        
        # Focus on first protocol button
        if self.protocol_buttons:
            self.ui_manager.set_focused_component(self.protocol_buttons[0])
        
        self.selected_protocol = None
        
        runtime_globals.game_console.log("[SceneBattle] Protocol selection menu opened")
    
    def handle_pet_activation(self):
        """Custom pet activation handler for Jogress/Versus/Armor scenes."""
        pet_index = self.pet_selector.get_activation_cell()
        if pet_index >= 0 and pet_index < len(self.pet_selector.pets):
            if pet_index in self.pet_selector.enabled_pets:
                if self.current_state == "jogress":
                    return self.toggle_pet_selection(pet_index)
                elif self.current_state == "versus":
                    return self.toggle_versus_pet_selection(pet_index)
                elif self.current_state == "armor":
                    return self.toggle_armor_pet_selection(pet_index)
        return False
        
    def toggle_pet_selection(self, pet_index):
        """Toggle selection of a pet with max 2 pets limit and persistent theme assignment.
        
        Jogress mode: 1st selected pet → left hexagon (GREEN), 2nd selected pet → right hexagon (BLUE)
        """
        if pet_index in self.selected_pets:
            # Deselect pet - remove from selection and clear persistent theme
            self.selected_pets.remove(pet_index)
            
            # Clear from jogress display
            if self.jogress_display:
                # Find which slot this pet was in and clear it
                slot_to_clear = None
                if pet_index in self.pet_theme_assignments:
                    theme = self.pet_theme_assignments[pet_index]
                    # Jogress: GREEN→left (slot 0), BLUE→right (slot 1)
                    if theme == "GREEN":
                        slot_to_clear = 0
                    elif theme == "BLUE":
                        slot_to_clear = 1
                        
                if slot_to_clear is not None:
                    self.jogress_display.clear_slot(slot_to_clear)
            
            # Clear persistent theme
            if pet_index in self.pet_theme_assignments:
                del self.pet_theme_assignments[pet_index]
                
            runtime_globals.game_sound.play("cancel")
        else:
            # Select pet (if we haven't reached the limit)
            if len(self.selected_pets) < 2:
                self.selected_pets.append(pet_index)
                
                # Assign a persistent theme based on available themes
                # Find the first unused theme from our selection themes
                used_themes = set(self.pet_theme_assignments.values())
                available_themes = [theme for theme in self.selection_themes if theme not in used_themes]
                
                if available_themes:
                    # Assign the first available theme
                    self.pet_theme_assignments[pet_index] = available_themes[0]
                    assigned_theme = available_themes[0]
                    
                    # Update jogress display: GREEN→slot 0 (left), BLUE→slot 1 (right)
                    if self.jogress_display:
                        pet = self.pet_selector.pets[pet_index] if pet_index < len(self.pet_selector.pets) else None
                        if pet:
                            slot_index = 0 if assigned_theme == "GREEN" else 1
                            self.jogress_display.set_pet_slot(slot_index, pet)
                else:
                    # Fallback: assign GREEN if no themes available (shouldn't happen with 2 pets max)
                    self.pet_theme_assignments[pet_index] = "GREEN"
                    assigned_theme = "GREEN"
                    
                    # Update jogress display
                    if self.jogress_display:
                        pet = self.pet_selector.pets[pet_index] if pet_index < len(self.pet_selector.pets) else None
                        if pet:
                            self.jogress_display.set_pet_slot(0, pet)
                
                runtime_globals.game_sound.play("menu")
            else:
                # Max pets reached, play error sound
                runtime_globals.game_sound.play("cancel")
                return False
        
        # Update pet selector's internal selection state
        self.pet_selector.selected_pets = self.selected_pets[:]
        
        # Update confirm button state (enable if 2 pets selected)
        if self.confirm_button:
            should_enable = len(self.selected_pets) == 2
            self.confirm_button.set_enabled(should_enable)
        
        # Update pet selector display with custom themes
        self.update_pet_themes()
        
        self.pet_selector.needs_redraw = True
        return True
        
    def update_pet_themes(self):
        """Update pet selector themes with persistent assignments."""
        if not self.pet_selector:
            return
            
        # Clear all custom themes first
        self.pet_selector.clear_custom_themes()
        
        # Apply persistent theme assignments for currently selected pets
        for pet_index in self.selected_pets:
            if pet_index in self.pet_theme_assignments:
                theme = self.pet_theme_assignments[pet_index]
                self.pet_selector.set_pet_custom_theme(pet_index, theme)
                runtime_globals.game_console.log(f"[SceneBattle] Pet {pet_index} assigned persistent theme {theme}")
    
    def toggle_versus_pet_selection(self, pet_index):
        """Toggle selection of a pet for versus battle (max 2 pets).
        
        Versus mode: 1st selected pet → right hexagon (BLUE), 2nd selected pet → left hexagon (GREEN)
        """
        if pet_index in self.selected_pets:
            # Deselect pet - remove from selection and clear persistent theme
            self.selected_pets.remove(pet_index)
            
            # Clear from versus display
            if self.versus_display:
                # Find which slot this pet was in and clear it
                slot_to_clear = None
                if pet_index in self.pet_theme_assignments:
                    theme = self.pet_theme_assignments[pet_index]
                    # Versus: GREEN→left (slot 0), BLUE→right (slot 1)
                    if theme == "GREEN":
                        slot_to_clear = 1
                    elif theme == "BLUE":
                        slot_to_clear = 0
                        
                if slot_to_clear is not None:
                    self.versus_display.clear_slot(slot_to_clear)
            
            # Clear persistent theme
            if pet_index in self.pet_theme_assignments:
                del self.pet_theme_assignments[pet_index]
                
            runtime_globals.game_sound.play("cancel")
        else:
            # Select pet (if we haven't reached the limit)
            if len(self.selected_pets) < 2:
                self.selected_pets.append(pet_index)
                
                # Assign a persistent theme based on available versus themes
                # Versus: 1st pet gets BLUE (right), 2nd pet gets GREEN (left)
                used_themes = set(self.pet_theme_assignments.values())
                available_themes = [theme for theme in self.versus_themes if theme not in used_themes]
                
                if available_themes:
                    # Assign the first available theme
                    self.pet_theme_assignments[pet_index] = available_themes[0]
                    assigned_theme = available_themes[0]
                    
                    # Update versus display: GREEN→left (slot 0), BLUE→right (slot 1)
                    if self.versus_display:
                        pet = self.pet_selector.pets[pet_index] if pet_index < len(self.pet_selector.pets) else None
                        if pet:
                            slot_index = 1 if assigned_theme == "GREEN" else 0
                            self.versus_display.set_pet_slot(slot_index, pet)
                else:
                    # Fallback: assign BLUE if no themes available (shouldn't happen with 2 pets max)
                    self.pet_theme_assignments[pet_index] = "BLUE"
                    assigned_theme = "BLUE"
                    
                    # Update versus display
                    if self.versus_display:
                        pet = self.pet_selector.pets[pet_index] if pet_index < len(self.pet_selector.pets) else None
                        if pet:
                            self.versus_display.set_pet_slot(1, pet)
                
                runtime_globals.game_sound.play("menu")
            else:
                # Max pets reached, play error sound
                runtime_globals.game_sound.play("cancel")
                return False
        
        # Update pet selector's internal selection state
        self.pet_selector.selected_pets = self.selected_pets[:]
        
        # Update confirm button state (enable if 2 pets selected)
        if self.confirm_button:
            should_enable = len(self.selected_pets) == 2
            self.confirm_button.set_enabled(should_enable)
        
        # Update pet selector display with custom themes
        self.update_pet_themes()
        
        self.pet_selector.needs_redraw = True
        return True
    
    def toggle_armor_pet_selection(self, pet_index):
        """Toggle selection of a pet for armor evolution (max 1 pet)."""
        if self.selected_armor_pet == pet_index:
            # Deselect pet
            self.selected_armor_pet = None
            if self.armor_display:
                self.armor_display.clear_pet()
            runtime_globals.game_sound.play("cancel")
        else:
            # Select pet
            self.selected_armor_pet = pet_index
            pet = self.pet_selector.pets[pet_index] if pet_index < len(self.pet_selector.pets) else None
            if pet and self.armor_display:
                self.armor_display.set_pet(pet, "BLUE")  # Use blue theme for armor
            runtime_globals.game_sound.play("menu")
        
        # Update pet selector display
        self.pet_selector.selected_pets = [self.selected_armor_pet] if self.selected_armor_pet is not None else []
        
        # Update confirm button state (enable if both pet and armor item selected)
        if self.confirm_button:
            should_enable = (self.selected_armor_pet is not None and 
                           self.selected_armor_item is not None)
            self.confirm_button.set_enabled(should_enable)
        
        self.pet_selector.needs_redraw = True
        return True
        
    def on_armor_item_activated(self):
        """Handle armor item selection."""
        if self.armor_item_list:
            self.selected_armor_item = self.armor_item_list.get_selected_armor_item_data()
            if self.selected_armor_item:
                runtime_globals.game_sound.play("menu")
                runtime_globals.game_console.log(f"[SceneBattle] Selected armor item: {self.selected_armor_item.name}")
                
                # Update confirm button state
                if self.confirm_button:
                    should_enable = (self.selected_armor_pet is not None and 
                                   self.selected_armor_item is not None)
                    self.confirm_button.set_enabled(should_enable)
            else:
                runtime_globals.game_sound.play("cancel")
    
    def check_pet_compatibility(self, pet1, pet2):
        """Check if two pets are compatible for Jogress fusion."""
        if not pet1 or not pet2:
            return False
            
        # Must belong to the same module
        if pet1.module != pet2.module:
            runtime_globals.game_console.log(f"[SceneBattle] Jogress incompatible: Different modules ({pet1.module} vs {pet2.module})")
            return False

        # Pet1 must have jogress options
        for evo in pet1.evolve:
            if "jogress" not in evo:
                continue

            # Prefix-based Jogress (e.g., Ancient)
            if evo.get("jogress_prefix", False):
                if pet2.name.startswith(evo["jogress"]):
                    runtime_globals.game_console.log(f"[SceneBattle] Jogress compatible: Prefix match ({pet1.name} + {pet2.name})")
                    return True

            # Standard Jogress (specific pet name match)
            if evo["jogress"] != "PenC":
                if pet2.name == evo["jogress"] and pet2.version == evo.get("version", pet1.version):
                    runtime_globals.game_console.log(f"[SceneBattle] Jogress compatible: Standard match ({pet1.name} + {pet2.name})")
                    return True

            # PenC Jogress (attribute + stage based, results in dual evolution)
            elif evo["jogress"] == "PenC":
                if (
                    (pet2.attribute == evo.get("attribute") or (pet2.attribute == "" and evo.get("attribute") == "Free"))  and
                    pet2.stage == evo.get("stage")
                ):
                    runtime_globals.game_console.log(f"[SceneBattle] Jogress compatible: PenC attribute match ({pet1.name} + {pet2.name})")
                    return True

        runtime_globals.game_console.log(f"[SceneBattle] Jogress incompatible: No valid evolution found for {pet1.name} + {pet2.name}")
        return False
        
    def get_jogress_evolution_info(self, pet1, pet2):
        """Get the evolution info for compatible pets, including whether it's dual evolution."""
        if not pet1 or not pet2:
            return None
            
        # Pet1 must have jogress options
        for evo in pet1.evolve:
            if "jogress" not in evo:
                continue

            # Prefix-based Jogress
            if evo.get("jogress_prefix", False):
                if pet2.name.startswith(evo["jogress"]):
                    return {"evolution": evo, "is_dual": False}

            # Standard Jogress
            if evo["jogress"] != "PenC":
                if pet2.name == evo["jogress"] and pet2.version == evo.get("version", pet1.version):
                    return {"evolution": evo, "is_dual": False}

            # PenC Jogress (dual evolution)
            elif evo["jogress"] == "PenC":
                if (
                    (pet2.attribute == evo.get("attribute") or (pet2.attribute == "" and evo.get("attribute") == "Free"))  and
                    pet2.stage == evo.get("stage")
                ):
                    return {"evolution": evo, "is_dual": True}

        return None
        
    def perform_jogress(self):
        """Execute Jogress evolution with animation delay."""
        if len(self.selected_pets) != 2:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Jogress: Need exactly 2 pets selected")
            return
            
        # Get the pets from the global pet list using the selected indices
        from core import game_globals
        pet1 = game_globals.pet_list[self.selected_pets[0]]
        pet2 = game_globals.pet_list[self.selected_pets[1]]
        
        if pet1.module != pet2.module:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Jogress: Pets from different modules")
            return
            
        # Find the valid evolution
        evolution_info = self.get_jogress_evolution_info(pet1, pet2)
        if not evolution_info:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Jogress: No valid evolution found")
            runtime_globals.game_sound.play("fail")
            return
            
        evolution = evolution_info["evolution"]
        is_dual = evolution_info["is_dual"]
        
        runtime_globals.game_sound.play("evolution")
        runtime_globals.game_console.log(f"[SceneBattle] Performing Jogress: {pet1.name} + {pet2.name}")
        
        if is_dual:
            # Dual evolution (PenC type) - both pets evolve based on attributes
            runtime_globals.game_console.log(f"[SceneBattle] Dual Jogress: Both pets will evolve")
            
            # For PenC jogress, both pets evolve to the same species but may have different attributes
            pet1.evolve_to(evolution['to'], evolution.get('version', pet1.version))
            pet2.evolve_to(evolution['to'], evolution.get('version', pet2.version))
            
            runtime_globals.game_console.log(f"[SceneBattle] Dual evolution completed: {pet1.name} + {pet2.name}")
        else:
            # Standard Jogress - merge into one pet
            runtime_globals.game_console.log(f"[SceneBattle] Standard Jogress: {pet1.name} + {pet2.name} = {evolution['to']}")
            
            # Remove pet2 and evolve pet1
            game_globals.pet_list.remove(pet2)
            pet1.evolve_to(evolution['to'], evolution.get('version', pet1.version))
            
        # Start 1-second delay before returning to game scene
        self.start_jogress_complete_animation()
        
    def perform_armor_evolution(self):
        """Execute Armor evolution using selected pet and armor item."""
        if self.selected_armor_pet is None or self.selected_armor_item is None:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Armor evolution: Missing pet or armor item")
            return
            
        # Get the pet from the global pet list
        from core import game_globals
        from core.utils.inventory_utils import remove_from_inventory
        
        pet = game_globals.pet_list[self.selected_armor_pet]
        armor_item = self.selected_armor_item
        
        runtime_globals.game_sound.play("evolution")
        runtime_globals.game_console.log(f"[SceneBattle] Performing Armor evolution: {pet.name} + {armor_item.name}")
        
        # Check if this armor item has a component_item for evolution
        if hasattr(armor_item, 'component_item') and armor_item.component_item:
            evolution_target = armor_item.component_item
            
            # Perform the armor evolution
            runtime_globals.game_console.log(f"[SceneBattle] Armor evolution: {pet.name} -> {evolution_target}")
            pet.evolve_to(evolution_target, pet.version)
            
            # Remove one armor item from inventory
            remove_from_inventory(armor_item.id, 1)
            runtime_globals.game_console.log(f"[SceneBattle] Consumed armor item: {armor_item.name}")
            
            # Refresh the armor item list
            if self.armor_item_list:
                self.armor_item_list.refresh_armor_items()
                
        else:
            runtime_globals.game_console.log(f"[SceneBattle] Error: Armor item {armor_item.name} has no component_item for evolution")
            runtime_globals.game_sound.play("fail")
            return
        
        # Return to game scene after evolution
        runtime_globals.game_console.log("[SceneBattle] Armor evolution completed, returning to game")
        change_scene("game")
        
    def perform_versus_battle(self):
        """Execute Versus battle using selected pets and protocol."""
        # Use stored pets from protocol selection phase
        if not self.versus_pets_selected or len(self.versus_pets_selected) != 2:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Versus battle: Need exactly 2 pets selected")
            return
            
        if not self.selected_protocol:
            runtime_globals.game_console.log("[SceneBattle] Cannot perform Versus battle: Need protocol selected")
            return
            
        # Get the pets from the global pet list
        from core import game_globals
        pet1 = game_globals.pet_list[self.versus_pets_selected[0]]
        pet2 = game_globals.pet_list[self.versus_pets_selected[1]]
        
        runtime_globals.game_sound.play("battle_online")
        runtime_globals.game_console.log(f"[SceneBattle] Starting Versus battle: {pet1.name} vs {pet2.name} using {self.selected_protocol}")
        
        # Create and start the versus battle (same pattern as old scene)
        runtime_globals.game_console.log(f"[SceneBattle] Creating BattleEncounterVersus with pets: {pet1.name} ({type(pet1)}) vs {pet2.name} ({type(pet2)}), protocol: {self.selected_protocol}")
        runtime_globals.game_console.log(f"[SceneBattle] Pet1 module: {getattr(pet1, 'module', 'NO MODULE')}, Pet2 module: {getattr(pet2, 'module', 'NO MODULE')}")
        
        self.mode = BattleEncounterVersus(pet1, pet2, self.selected_protocol)
        pet1.check_disturbed_sleep()
        pet2.check_disturbed_sleep()
        runtime_globals.game_console.log("[SceneBattle] Versus battle encounter created successfully")
            
        
    def start_jogress_complete_animation(self):
        """Start the 1-second delay animation after Jogress completion."""
        self.jogress_complete_timer = 0.0
        self.jogress_complete_duration = 1.0  # 1 second delay
        self.jogress_completing = True
        runtime_globals.game_console.log("[SceneBattle] Starting Jogress completion animation")
        
    def update_jogress_animation(self):
        """Update the Jogress completion animation timer."""
        if hasattr(self, 'jogress_completing') and self.jogress_completing:
            # Increment timer (assume ~30 FPS)
            self.jogress_complete_timer += 1.0 / 30.0
            
            if self.jogress_complete_timer >= self.jogress_complete_duration:
                # Animation complete, return to game scene
                self.jogress_completing = False
                runtime_globals.game_console.log("[SceneBattle] Jogress completion animation finished, returning to game")
                change_scene("game")
                
    def start_evolution_animation(self):
        """Start the Jogress evolution animation with circles and particles."""
        self.evolution_animation_active = True
        self.evolution_animation_timer = 0.0
        self.pet_circles = []
        self.particles = []
        
        # Hide confirm and back buttons during animation
        if self.confirm_button:
            self.confirm_button.visible = False
        if self.back_button:
            self.back_button.visible = False
            
        # Hide the pet sprites in the JogressDisplay
        if self.jogress_display:
            self.jogress_display.set_hide_pet_sprites(True)
            
        # Get pet positions from jogress display
        if self.jogress_display:
            # Convert base coordinates to screen coordinates
            if self.ui_manager:
                # Get the jogress display's screen position
                display_rect = self.jogress_display.rect
                display_offset_x = display_rect.x
                display_offset_y = display_rect.y
                
                # Pet circle positions (bottom hexagons)
                if self.jogress_display.bottom_left_center and self.jogress_display.bottom_right_center:
                    left_center = self.jogress_display.bottom_left_center
                    right_center = self.jogress_display.bottom_right_center
                    
                    # Convert to screen coordinates
                    left_screen_x = display_offset_x + self.ui_manager.scale_value(left_center[0])
                    left_screen_y = display_offset_y + self.ui_manager.scale_value(left_center[1])
                    right_screen_x = display_offset_x + self.ui_manager.scale_value(right_center[0])
                    right_screen_y = display_offset_y + self.ui_manager.scale_value(right_center[1])
                    
                    # Initial circle radius
                    initial_radius = self.ui_manager.scale_value(self.jogress_display.base_hexagon_size) * 0.6
                    
                    # Create pet circles
                    self.pet_circles = [
                        {
                            "x": left_screen_x,
                            "y": left_screen_y, 
                            "initial_radius": initial_radius,
                            "current_radius": initial_radius,
                            "color": (255, 255, 255)  # White
                        },
                        {
                            "x": right_screen_x,
                            "y": right_screen_y,
                            "initial_radius": initial_radius, 
                            "current_radius": initial_radius,
                            "color": (255, 255, 255)  # White
                        }
                    ]
        
        runtime_globals.game_console.log("[SceneBattle] Evolution animation started")
        
    def update_evolution_animation(self):
        """Update the evolution animation state."""
        if not self.evolution_animation_active:
            return
            
        import random
        import math
        
        # Update timer
        dt = 1.0 / 30.0  # Assume 30 FPS
        self.evolution_animation_timer += dt
        
        # Animation progress (0.0 to 1.0)
        progress = min(self.evolution_animation_timer / self.evolution_animation_duration, 1.0)
        
        # Phase 1: Spawn particles and shrink circles (first 80% of animation)
        if progress < 0.8:
            phase_progress = progress / 0.8
            
            # Shrink pet circles
            for circle in self.pet_circles:
                circle["current_radius"] = circle["initial_radius"] * (1.0 - phase_progress)
                
            # Spawn particles from circles
            if random.random() < 0.3:  # 30% chance per frame
                for circle in self.pet_circles:
                    if circle["current_radius"] > 2:  # Only spawn from visible circles
                        # Get target position (top hexagon center)
                        target_x, target_y = self.get_top_hexagon_screen_center()
                        
                        # Spawn particle at circle edge
                        angle = random.uniform(0, 2 * math.pi)
                        spawn_x = circle["x"] + math.cos(angle) * circle["current_radius"]
                        spawn_y = circle["y"] + math.sin(angle) * circle["current_radius"]
                        
                        # Calculate movement vector
                        dx = target_x - spawn_x
                        dy = target_y - spawn_y
                        distance = math.sqrt(dx * dx + dy * dy)
                        
                        if distance > 0:
                            # Normalize and set speed
                            speed = 3.0  # pixels per frame
                            vx = (dx / distance) * speed
                            vy = (dy / distance) * speed
                            
                            # Add particle
                            self.particles.append({
                                "x": spawn_x,
                                "y": spawn_y,
                                "vx": vx,
                                "vy": vy,
                                "target_x": target_x,
                                "target_y": target_y,
                                "life": 1.0,
                                "size": random.uniform(2, 4)
                            })
        
        # Update particles
        for particle in self.particles[:]:  # Copy list to allow removal
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 0.02  # Fade out
            
            # Check if particle reached target or faded out
            dx = particle["target_x"] - particle["x"]
            dy = particle["target_y"] - particle["y"]
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < 5 or particle["life"] <= 0:
                self.particles.remove(particle)
        
        # Phase 2: Complete animation (last 20%)
        if progress >= 0.8:
            # Clear remaining particles and circles
            if progress >= 0.9:
                self.particles.clear()
                for circle in self.pet_circles:
                    circle["current_radius"] = 0
        
        # End animation and perform evolution
        if progress >= 1.0:
            self.evolution_animation_active = False
            runtime_globals.game_console.log("[SceneBattle] Evolution animation completed, performing Jogress...")
            self.perform_jogress()
            
    def get_top_hexagon_screen_center(self):
        """Get the screen coordinates of the top hexagon center."""
        if self.jogress_display and self.jogress_display.top_hexagon_center:
            # Get the jogress display's screen position
            display_rect = self.jogress_display.rect
            display_offset_x = display_rect.x
            display_offset_y = display_rect.y
            
            top_center = self.jogress_display.top_hexagon_center
            screen_x = display_offset_x + self.ui_manager.scale_value(top_center[0])
            screen_y = display_offset_y + self.ui_manager.scale_value(top_center[1])
            
            return screen_x, screen_y
        return 120, 60  # Fallback center
        
    def draw_evolution_animation(self, surface):
        """Draw the evolution animation over the UI."""
        if not self.evolution_animation_active:
            return
            
        # Draw pet circles
        for circle in self.pet_circles:
            if circle["current_radius"] > 0:
                pygame.draw.circle(
                    surface, 
                    circle["color"], 
                    (int(circle["x"]), int(circle["y"])), 
                    int(circle["current_radius"])
                )
        
        # Draw particles
        for particle in self.particles:
            if particle["life"] > 0:
                # Fade particle alpha based on life
                alpha = int(255 * particle["life"])
                color = (255, 255, 255, alpha)
                
                # Create a small surface for the particle with alpha
                particle_surface = pygame.Surface((int(particle["size"] * 2), int(particle["size"] * 2)), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surface, 
                    color[:3],  # RGB only for circle
                    (int(particle["size"]), int(particle["size"])), 
                    int(particle["size"])
                )
                
                # Set surface alpha
                particle_surface.set_alpha(alpha)
                
                # Blit to main surface
                surface.blit(
                    particle_surface, 
                    (int(particle["x"] - particle["size"]), int(particle["y"] - particle["size"]))
                )
    
    # Button callback methods
    def on_jogress(self):
        """Handle Jogress button press - show Jogress menu."""
        runtime_globals.game_sound.play("menu")
        self.show_jogress_menu()
        
    def on_versus(self):
        """Handle Versus button press - show Versus menu."""
        runtime_globals.game_sound.play("menu")
        self.show_versus_menu()
        
    def on_armor(self):
        """Handle Armor button press - show Armor menu."""
        runtime_globals.game_sound.play("menu")
        self.show_armor_menu()
        
    def on_adventure(self):
        """Handle Adventure button press - show Adventure menu."""
        runtime_globals.game_sound.play("menu")
        self.show_adventure_menu()
        
    def on_exit(self):
        """Handle Exit button press."""
        runtime_globals.game_sound.play("cancel")
        change_scene("game")
    
    # Protocol selection button callbacks
    def on_protocol_selected(self, protocol_name):
        """Handle protocol selection button press."""
        runtime_globals.game_sound.play("menu")
        
        # Map protocol name to BattleProtocol enum
        protocol_mapping = {
            "DM20": BattleProtocol.DM20_BS,
            "Pen20": BattleProtocol.PEN20_BS,
            "DMX/PenZ": BattleProtocol.DMX_BS,
            "DMC": BattleProtocol.DMC_BS
        }
        
        self.selected_protocol = protocol_mapping[protocol_name]
        runtime_globals.game_console.log(f"[SceneBattle] Protocol selected: {protocol_name}")
        
        # Immediately start the battle
        self.perform_versus_battle()
    
    def on_protocol_cancel(self):
        """Handle protocol selection cancel button press."""
        runtime_globals.game_sound.play("cancel")
        self.show_versus_menu()
    
    # Adventure scene button callbacks
    def on_module_toggled(self, module, toggled):
        """Handle module button toggle."""
        if toggled:
            self.selected_module = module
            runtime_globals.game_console.log(f"[SceneBattle] Module selected: {module.name}")
            
            # Update adventure panel with module info
            if self.adventure_panel:
                # TODO: Get actual progress from game state
                progress_current = 0
                progress_total = 10  # Placeholder
                self.adventure_panel.set_module(module, progress_current, progress_total)
        else:
            self.selected_module = None
    
    def on_adventure_go(self):
        """Handle GO button press - show area selection."""
        if self.selected_module:
            runtime_globals.game_sound.play("menu")
            runtime_globals.game_console.log(f"[SceneBattle] Moving to area selection for module: {self.selected_module.name}")
            self.show_area_selection()
        else:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log("[SceneBattle] Cannot start adventure: No module selected")
    
    def on_adventure_random(self):
        """Handle RANDOM button press - select a random module."""
        if self.module_buttons:
            random_button = random.choice(self.module_buttons)
            self.module_button_group.set_active_button(random_button)
            runtime_globals.game_sound.play("menu")
    
    def on_adventure_more(self):
        """Handle MORE button press - show more modules."""
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log("[SceneBattle] More modules - not implemented yet")
        # TODO: Implement pagination for more than 4 modules
    
    def on_adventure_back(self):
        """Handle BACK button press in adventure scene."""
        runtime_globals.game_sound.play("cancel")
        self.show_main_menu()
    
    def on_area_selected(self, area, round_num):
        """Handle area selection from AreaSelection component."""
        runtime_globals.game_console.log(f"[SceneBattle] Area selected: Area {area}, Round {round_num}")
        # Just log for now, user needs to press FIGHT button to start
    
    def on_area_selection_fight(self):
        """Handle FIGHT button press in area selection."""
        if not self.area_selection or not self.selected_module:
            runtime_globals.game_sound.play("cancel")
            return
        
        # Get selected area and round
        area, round_num = self.area_selection.get_selected_area_round()
        
        # Save last adventure module
        from core import game_globals
        game_globals.last_adventure_module = self.selected_module.name
        game_globals.save()
        
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log(f"[SceneBattle] Starting battle: Area {area}, Round {round_num}")
        
        # Start the battle (reference scene_battle_backup.py logic)
        self._start_adventure_battle(area, round_num)
    
    def on_area_selection_back(self):
        """Handle BACK button press in area selection."""
        runtime_globals.game_sound.play("cancel")
        
        # Hide area selection
        if self.area_selection:
            self.area_selection.visible = False
        if self.area_selection_fight_button:
            self.area_selection_fight_button.visible = False
        if self.area_selection_back_button:
            self.area_selection_back_button.visible = False
        
        # Show module selection again
        self.current_state = "adventure"
        if self.adventure_module_selection_image:
            self.adventure_module_selection_image.visible = True
        for button in self.module_buttons:
            button.visible = True
        if self.adventure_random_button:
            self.adventure_random_button.visible = True
        if self.adventure_more_button:
            self.adventure_more_button.visible = True
        if self.adventure_back_button:
            self.adventure_back_button.visible = True
        if self.adventure_go_button:
            self.adventure_go_button.visible = True
        
        # Focus on first module button
        if self.module_buttons:
            self.ui_manager.set_focused_component(self.module_buttons[0])
    
    def _start_adventure_battle(self, area, round_num):
        """Start an adventure battle with the selected module, area, and round."""
        if not self.selected_module:
            return
        
        # Create battle encounter
        # BattleEncounter(module, area, round, pet_index)
        # For adventure mode, we'll use pet_index = 1 (first pet) by default
        # The player will choose which pet to use in the battle encounter
        self.mode = BattleEncounter(
            self.selected_module.name,
            area,
            round_num,
            1
        )
        
        runtime_globals.game_console.log(f"[SceneBattle] Battle started: {self.selected_module.name} Area {area}, Round {round_num}")
    
    # Jogress scene button callbacks
    def on_confirm(self):
        """Handle Confirm button press in Jogress, Versus, or Armor scene."""
        if self.current_state == "jogress":
            if len(self.selected_pets) == 2:
                # Check if pets are compatible before performing Jogress
                from core import game_globals
                pet1 = game_globals.pet_list[self.selected_pets[0]]
                pet2 = game_globals.pet_list[self.selected_pets[1]]
                
                if self.check_pet_compatibility(pet1, pet2):
                    runtime_globals.game_sound.play("menu")
                    runtime_globals.game_console.log("[SceneBattle] Starting Jogress evolution animation...")
                    self.start_evolution_animation()
                else:
                    runtime_globals.game_sound.play("cancel")
                    runtime_globals.game_console.log("[SceneBattle] Cannot execute Jogress: Pets not compatible")
            else:
                runtime_globals.game_sound.play("cancel")
                runtime_globals.game_console.log("[SceneBattle] Cannot execute Jogress: Need exactly 2 pets selected")
        elif self.current_state == "versus":
            if len(self.selected_pets) == 2:
                runtime_globals.game_sound.play("menu")
                runtime_globals.game_console.log("[SceneBattle] Moving to protocol selection...")
                self.show_protocol_selection()
            else:
                runtime_globals.game_sound.play("cancel")
                runtime_globals.game_console.log("[SceneBattle] Cannot start Versus battle: Need exactly 2 pets selected")
        elif self.current_state == "armor":
            if self.selected_armor_pet is not None and self.selected_armor_item is not None:
                runtime_globals.game_sound.play("menu")
                runtime_globals.game_console.log("[SceneBattle] Starting Armor evolution...")
                self.perform_armor_evolution()
            else:
                runtime_globals.game_sound.play("cancel")
                runtime_globals.game_console.log("[SceneBattle] Cannot execute Armor evolution: Need pet and armor item selected")
        
    def on_back(self):
        """Handle Back button press in Jogress, Versus, or Armor scene."""
        runtime_globals.game_sound.play("cancel")
        
        if self.current_state == "versus_protocol":
            # In protocol selection, go back to versus menu
            self.show_versus_menu()
        else:
            # In other scenes, clean up and go to main menu
            self.cleanup_evolution_animation()
            self.show_main_menu()
    
    def cleanup_evolution_animation(self):
        """Clean up evolution animation state"""
        self.evolution_animation_active = False
        if self.jogress_display:
            self.jogress_display.set_hide_pet_sprites(False)
        if self.confirm_button:
            self.confirm_button.visible = True
        if self.back_button:
            self.back_button.visible = True

    def update(self):
        """Update the UI manager."""
        if self.mode:
            self.mode.update()
            return
            
        self.ui_manager.update()
        
        # Update Jogress completion animation if active
        self.update_jogress_animation()
        
        # Update evolution animation if active
        self.update_evolution_animation()

    def draw(self, surface: pygame.Surface):
        """Draw the battle menu using the new UI system."""
        if self.mode:
            # During battle mode, only show background and battle
            self.battle_background.draw(surface)
            self.mode.draw(surface)
            return
            
        surface.fill((0, 0, 0))  # Black background
        self.ui_manager.draw(surface)
        
        # Draw evolution animation on top of UI
        self.draw_evolution_animation(surface)

    def handle_event(self, event):
        """Handle input events for the battle menu."""
        
        # Delegate to battle mode if active
        if self.mode:
            self.mode.handle_event(event)
            return
        
        # Handle pygame events through UI manager first
        if hasattr(event, 'type'):
            if self.ui_manager.handle_event(event):
                return
        
        # Handle string action events (from input manager)
        elif isinstance(event, str):
            if event == "B":
                if self.current_state == "versus_protocol":
                    # In protocol selection, B goes back to versus menu
                    runtime_globals.game_sound.play("cancel")
                    self.show_versus_menu()
                    return
                elif self.current_state == "adventure":
                    # In adventure menu, B goes back to main menu
                    runtime_globals.game_sound.play("cancel")
                    self.show_main_menu()
                    return
                elif self.current_state == "jogress" or self.current_state == "versus" or self.current_state == "armor":
                    # In Jogress, Versus, or Armor menu, B goes back to main menu
                    runtime_globals.game_sound.play("cancel")
                    self.show_main_menu()
                    return
                else:
                    # In main menu, B exits to game scene
                    runtime_globals.game_sound.play("cancel")
                    change_scene("game")
                    return
            
            # Let UI manager handle navigation and other input actions
            if self.ui_manager.handle_input_action(event):
                return