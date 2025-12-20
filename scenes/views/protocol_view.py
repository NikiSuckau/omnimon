"""
ProtocolView - Battle protocol selection
Shows protocol options for versus battles
"""
import pygame
from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.background import Background
from components.ui.ui_constants import BASE_RESOLUTION
from core import runtime_globals
from core.combat.sim.models import BattleProtocol


class ProtocolView:
    """Protocol selection view for versus battles."""
    
    def __init__(self, ui_manager: UIManager, change_view_callback, pet1, pet2):
        """Initialize the Protocol view.
        
        Args:
            ui_manager: The UI manager instance
            change_view_callback: Callback to change to another view
            pet1: First pet for battle
            pet2: Second pet for battle
        """
        self.ui_manager = ui_manager
        self.change_view = change_view_callback
        self.pet1 = pet1
        self.pet2 = pet2
        
        # UI Components
        self.background = None
        self.title_scene = None
        self.protocol_buttons = []
        self.cancel_button = None
        
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
        
        # Protocol selection buttons
        button_width = 120
        button_height = 30
        button_spacing = 8
        
        protocol_options = ["DM20", "Pen20", "DMX/PenZ", "DMC"]
        total_height = (len(protocol_options) * button_height) + ((len(protocol_options) - 1) * button_spacing)
        start_y = (ui_height - total_height) // 2 - 20
        start_x = (ui_width - button_width) // 2
        
        # Create protocol buttons
        for i, protocol in enumerate(protocol_options):
            button_y = start_y + (i * (button_height + button_spacing))
            button = Button(
                start_x, button_y, button_width, button_height,
                protocol, lambda p=protocol: self._on_protocol_selected(p),
                cut_corners={'tl': True, 'tr': True, 'bl': True, 'br': True}
            )
            self.ui_manager.add_component(button)
            self.protocol_buttons.append(button)
        
        # Cancel button
        cancel_y = start_y + total_height + button_spacing * 2
        self.cancel_button = Button(
            start_x, cancel_y, button_width, button_height,
            "CANCEL", self._on_cancel,
            cut_corners={'tl': True, 'tr': True, 'bl': True, 'br': True}
        )
        self.ui_manager.add_component(self.cancel_button)
        
        # Set initial focus
        if self.protocol_buttons:
            self.ui_manager.set_focused_component(self.protocol_buttons[0])
        
        runtime_globals.game_console.log("[ProtocolView] UI setup complete")
    
    def _on_protocol_selected(self, protocol_name):
        """Handle protocol selection."""
        runtime_globals.game_sound.play("menu")
        
        # Map protocol name to BattleProtocol enum
        protocol_mapping = {
            "DM20": BattleProtocol.DM20_BS,
            "Pen20": BattleProtocol.PEN20_BS,
            "DMX/PenZ": BattleProtocol.DMX_BS,
            "DMC": BattleProtocol.DMC_BS
        }
        
        protocol = protocol_mapping[protocol_name]
        runtime_globals.game_console.log(f"[ProtocolView] Protocol selected: {protocol_name}")
        
        # Change to versus battle view
        self.change_view("versus_battle", pet1=self.pet1, pet2=self.pet2, protocol=protocol)
    
    def _on_cancel(self):
        """Handle cancel button."""
        runtime_globals.game_sound.play("cancel")
        self.change_view("versus")
    
    def cleanup(self):
        """Remove all UI components."""
        if self.background:
            self.ui_manager.remove_component(self.background)
        if self.title_scene:
            self.ui_manager.remove_component(self.title_scene)
        for button in self.protocol_buttons:
            self.ui_manager.remove_component(button)
        if self.cancel_button:
            self.ui_manager.remove_component(self.cancel_button)
    
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
