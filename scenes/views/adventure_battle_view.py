"""
AdventureBattleView - Adventure battle encounter
Handles the adventure battle including all phases, minigames, and result screen
"""
import pygame
from components.ui.ui_manager import UIManager
from components.window_background import WindowBackground
from core import runtime_globals
from core.combat.battle_encounter import BattleEncounter


class AdventureBattleView:
    """Adventure battle encounter view."""
    
    def __init__(self, ui_manager: UIManager, change_view_callback, module, area, round_num):
        """Initialize the Adventure Battle view.
        
        Args:
            ui_manager: The UI manager instance
            change_view_callback: Callback to change to another view
            module: The adventure module
            area: The area number
            round_num: The round number
        """
        self.ui_manager = ui_manager
        self.change_view = change_view_callback
        self.module = module
        self.area = area
        self.round_num = round_num
        
        # Battle encounter
        self.battle_encounter = None
        
        self._start_battle()
        
    def _start_battle(self):
        """Start the adventure battle."""
        runtime_globals.game_console.log(f"[AdventureBattleView] Starting battle: {self.module.name} Area {self.area}, Round {self.round_num}")
        
        # Create battle encounter
        # BattleEncounter(module, area, round, pet_index)
        # For adventure mode, pet_index = 1 (first pet) by default
        self.battle_encounter = BattleEncounter(
            self.module.name,
            self.area,
            self.round_num,
            1
        )
        
        runtime_globals.game_console.log("[AdventureBattleView] Battle encounter created")
    
    def cleanup(self):
        """Cleanup the view."""
        # Battle encounter handles its own cleanup
        pass
    
    def update(self):
        """Update the view."""
        if self.battle_encounter:
            self.battle_encounter.update()
    
    def draw(self, surface: pygame.Surface):
        """Draw the view."""
        
        # Draw battle encounter
        if self.battle_encounter:
            self.battle_encounter.draw(surface)
    
    def handle_event(self, event):
        """Handle input events."""
        if self.battle_encounter:
            self.battle_encounter.handle_event(event)
