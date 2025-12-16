"""
AdventureAreaSelectionView - Area selection for adventure battles
Shows area selection component and fight/back buttons
"""
import pygame
from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.background import Background
from components.ui.adventure_panel import AdventurePanel
from components.ui.area_selection import AreaSelection
from components.ui.pet_selector import PetSelector
from components.ui.ui_constants import BASE_RESOLUTION
from core import runtime_globals, game_globals
from core.utils.pet_utils import get_battle_targets


class AdventureAreaSelectionView:
    """Adventure area selection view."""
    
    def __init__(self, ui_manager: UIManager, change_view_callback, module, 
                 available_area=None, available_round=None, area_round_limits=None):
        """Initialize the Adventure Area Selection view.
        
        Args:
            ui_manager: The UI manager instance
            change_view_callback: Callback to change to another view
            module: The selected adventure module
            available_area: The current unlocked area for this module
            available_round: The current unlocked round for this module
            area_round_limits: Dict mapping area number to round count for that area
        """
        self.ui_manager = ui_manager
        self.change_view = change_view_callback
        self.module = module
        self.available_area = available_area
        self.available_round = available_round
        self.area_round_limits = area_round_limits if area_round_limits is not None else {}
        
        # UI Components
        self.background = None
        self.title_scene = None
        self.adventure_panel = None
        self.area_selection = None
        self.pet_selector = None
        self.fight_button = None
        self.back_button = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        ui_width = ui_height = BASE_RESOLUTION
        
        # Background
        self.background = Background(ui_width, ui_height)
        self.background.set_regions([(0, ui_height, "black")])
        self.ui_manager.add_component(self.background)
        
        # Title
        self.title_scene = TitleScene(0, 5, "BATTLE")
        self.ui_manager.add_component(self.title_scene)
        
        # Adventure panel (shows module info)
        self.adventure_panel = AdventurePanel(8, 43, 224, 55)
        self.adventure_panel.set_module(
            self.module,
            self.available_area,
            self.available_round,
            self.area_round_limits
        )
        self.ui_manager.add_component(self.adventure_panel)
        
        # Area selection (moved up slightly)
        self.area_selection = AreaSelection(
            8, 90, 224, 60,
            self.module,
            on_select=self._on_area_selected,
            available_area=self.available_area,
            available_round=self.available_round,
            area_round_limits=self.area_round_limits
        )
        self.ui_manager.add_component(self.area_selection)
        
        # Pet selector at bottom (shows battle-ready pets)
        pet_selector_width = 224
        pet_selector_height = 40
        pet_selector_x = 8
        pet_selector_y = 152  # Below area selection with small gap
        
        self.pet_selector = PetSelector(pet_selector_x, pet_selector_y, pet_selector_width, pet_selector_height)
        battle_ready_pets = get_battle_targets()
        self.pet_selector.set_pets(battle_ready_pets)
        self.pet_selector.set_interactive(False)  # Static display
        self.ui_manager.add_component(self.pet_selector)
        
        # Fight button (moved closer to pet selector)
        fight_button_width = 145
        button_height = 25
        button_y = 198  # Closer to pet selector
        
        self.fight_button = Button(
            9, button_y, fight_button_width, button_height,
            "FIGHT", self._on_fight,
            cut_corners={'tl': False, 'tr': False, 'bl': True, 'br': False}
        )
        self.ui_manager.add_component(self.fight_button)
        
        # Back button
        back_button_x = 9 + fight_button_width + 10
        back_button_width = 66
        
        self.back_button = Button(
            back_button_x, button_y, back_button_width, button_height,
            "BACK", self._on_back,
            cut_corners={'tl': False, 'tr': False, 'bl': False, 'br': True}
        )
        self.ui_manager.add_component(self.back_button)
        
        # Set initial focus
        self.ui_manager.set_focused_component(self.area_selection)
        
        runtime_globals.game_console.log(f"[AdventureAreaSelectionView] UI setup complete for {self.module.name}")
    
    def _on_area_selected(self, area, round_num):
        """Handle area selection."""
        runtime_globals.game_console.log(f"[AdventureAreaSelectionView] Area selected: Area {area}, Round {round_num}")
    
    def _on_fight(self):
        """Handle FIGHT button press."""
        if not self.area_selection or not self.module:
            runtime_globals.game_sound.play("cancel")
            return
        
        # Get selected area and round
        area, round_num = self.area_selection.get_selected_area_round()
        
        # Save last adventure module
        from core import game_globals
        game_globals.last_adventure_module = self.module.name
        game_globals.save()
        
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log(f"[AdventureAreaSelectionView] Starting battle: Area {area}, Round {round_num}")
        
        # Change to adventure battle view
        self.change_view("adventure_battle", module=self.module, area=area, round_num=round_num)
    
    def _on_back(self):
        """Handle BACK button press."""
        runtime_globals.game_sound.play("cancel")
        self.change_view("adventure_module_selection")
    
    def cleanup(self):
        """Remove all UI components."""
        if self.background:
            self.ui_manager.remove_component(self.background)
        if self.title_scene:
            self.ui_manager.remove_component(self.title_scene)
        if self.adventure_panel:
            self.ui_manager.remove_component(self.adventure_panel)
        if self.area_selection:
            self.ui_manager.remove_component(self.area_selection)
        if self.pet_selector:
            self.ui_manager.remove_component(self.pet_selector)
        if self.fight_button:
            self.ui_manager.remove_component(self.fight_button)
        if self.back_button:
            self.ui_manager.remove_component(self.back_button)
    
    def update(self):
        """Update the view."""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Draw the view."""
        pass
    
    def handle_event(self, event):
        """Handle input events."""
        if not isinstance(event, tuple) or len(event) != 2:
            return
        pass
