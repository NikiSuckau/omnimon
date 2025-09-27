"""
Scene Inventory - Modern UI version with inventory management
Allows the player to browse inventory items and use/discard them.
"""

import pygame
import os

from components.ui.ui_manager import UIManager
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.pet_selector import PetSelector
from components.ui.background import Background
from components.ui.item_list import ItemList
from components.ui.text_panel import TextPanel
from components.window_background import WindowBackground
from core import runtime_globals, game_globals
import game.core.constants as constants
from core.utils.pet_utils import get_selected_pets
from core.utils.scene_utils import change_scene
from core.utils.inventory_utils import get_inventory_value, remove_from_inventory, add_to_inventory
from components.ui.ui_constants import BASE_RESOLUTION

#=====================================================================
# SceneInventory
#=====================================================================
class SceneInventory:
    """
    Modern UI scene for inventory management and item usage.
    """

    def __init__(self) -> None:
        """Initialize the inventory scene with new UI system."""
        
        # Use BLUE theme for inventory
        self.ui_manager = UIManager("BLUE")
        
        # UI Components
        self.background = None
        self.title_scene = None
        self.item_list = None
        self.pet_selector = None
        self.text_panel = None
        self.use_button = None
        self.discard_button = None
        self.selection_button = None
        self.exit_button = None
        
        # Black background for areas not covered by UI
        self.window_background = WindowBackground(False)
        
        self.setup_ui()
        
        runtime_globals.game_console.log("[SceneInventory] Modern inventory scene initialized.")

    def load_inventory_items(self):
        """Load items from inventory, similar to the old inventory menu."""
        items = []
        
        # Add default items (Protein and Vitamin) as the first options, without amount
        default_sprite_folder = os.path.join("assets", "items")
        for default_item in runtime_globals.default_items.values():
            sprite_path = os.path.join(default_sprite_folder, default_item.sprite_name)
            anim_path = os.path.join(default_sprite_folder, f"{default_item.sprite_name.split('.')[0]}_anim.png")
            if os.path.exists(sprite_path):
                icon = pygame.image.load(sprite_path).convert_alpha()
            else:
                icon = pygame.Surface((48, 48), pygame.SRCALPHA)
            
            # Create item object with icon
            class InventoryItem:
                def __init__(self, item_id, game_item, icon, quantity=-1, anim_path=None):
                    self.id = item_id
                    self.game_item = game_item
                    self.icon = icon
                    self.quantity = quantity
                    self.anim_path = anim_path
                    
            # Add description for default items
            items.append(InventoryItem(default_item.id, default_item, icon, -1, anim_path))

        # Add items from inventory (from all modules)
        for module in runtime_globals.game_modules.values():
            if hasattr(module, "items"):
                for item in module.items:
                    if getattr(item, "effect", "") == "digimental":
                        continue
                    amount = get_inventory_value(item.id)
                    if amount > 0:
                        sprite_name = item.sprite_name
                        if not sprite_name.lower().endswith(".png"):
                            sprite_name += ".png"
                        sprite_path = os.path.join(module.folder_path, "items", sprite_name)
                        anim_path = os.path.join(module.folder_path, "items", f"{sprite_name.split('.')[0]}_anim.png")
                        if os.path.exists(sprite_path):
                            icon = pygame.image.load(sprite_path).convert_alpha()
                        else:
                            icon = pygame.Surface((48, 48), pygame.SRCALPHA)
                        
                        items.append(InventoryItem(item.id, item, icon, amount, anim_path))
        
        return items

    def setup_ui(self):
        """Setup the UI components for the inventory scene."""
        try:
            # Use base 240x240 resolution for UI layout
            ui_width = ui_height = BASE_RESOLUTION
            
            # Create and add the UI background that covers the full UI area
            self.background = Background(ui_width, ui_height)
            # Set single black region covering entire UI
            self.background.set_regions([(0, ui_height, "black")])
            self.ui_manager.add_component(self.background)
            
            # Create and add the title scene at top
            self.title_scene = TitleScene(0, 5, "INVENTORY")
            self.ui_manager.add_component(self.title_scene)
            
            # Create and add the item list positioned at 0, 27 with size 156x176
            item_list_x = 0
            item_list_y = 27
            item_list_width = 156
            item_list_height = 176
            
            self.item_list = ItemList(item_list_x, item_list_y, item_list_width, item_list_height, 
                                     on_item_activated=self.on_item_activated)
            
            # Hide background and border for the inventory - we only want the items visible
            self.item_list.set_background_visible(False)
            self.item_list.set_border_visible(False)
            
            # Load actual inventory items
            inventory_items = self.load_inventory_items()
            self.item_list.set_items(inventory_items)
            self.ui_manager.add_component(self.item_list)
            
            # Create and add the pet selector at bottom (150x46 size)
            selector_width = 145
            selector_height = 46
            selector_x = 5  # Center horizontally
            selector_y = 194  # Near bottom with margin
            
            self.pet_selector = PetSelector(selector_x, selector_y, selector_width, selector_height)
            # Set pets and make it static for now
            self.pet_selector.set_pets(get_selected_pets())
            self.pet_selector.set_interactive(False)  # Static display for now
            self.ui_manager.add_component(self.pet_selector)
            
            # Create and add the text panel for item descriptions
            text_panel_x = 158
            text_panel_y = 24
            text_panel_width = 78
            text_panel_height = 106
            
            self.text_panel = TextPanel(text_panel_x, text_panel_y, text_panel_width, text_panel_height)
            self.text_panel.set_text("Select an item to view its description")
            self.ui_manager.add_component(self.text_panel)
            
            # Create buttons positioned at 135x160 and below
            button_width = 80
            button_height = 23
            button_x = 158
            button_y = 134
            button_spacing = 3  # Vertical spacing between buttons
            
            # USE button
            self.use_button = Button(
                button_x, button_y, button_width, button_height,
                "USE", self.on_use_button
            )
            self.ui_manager.add_component(self.use_button)
            
            # DISCARD button
            self.discard_button = Button(
                button_x, button_y + button_height + button_spacing, button_width, button_height,
                "DISCARD", self.on_discard_button
            )
            self.ui_manager.add_component(self.discard_button)
            
            # SELECTION button
            self.selection_button = Button(
                button_x, button_y + ((button_height + button_spacing) * 2), button_width, button_height,
                "SELECTION", self.on_selection_button
            )
            self.ui_manager.add_component(self.selection_button)
            
            # EXIT button
            self.exit_button = Button(
                button_x, button_y + ((button_height + button_spacing) * 3), button_width, button_height,
                "EXIT", self.on_exit_button
            )
            self.ui_manager.add_component(self.exit_button)
            
            runtime_globals.game_console.log("[SceneInventory] UI setup completed successfully")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneInventory] ERROR in setup_ui: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneInventory] Traceback: {traceback.format_exc()}")
            raise
        
        # Set mouse mode and focus on the item list initially
        self.ui_manager.set_mouse_mode()
        if self.item_list:
            self.ui_manager.set_focused_component(self.item_list)

                
    def update(self) -> None:
        """Update the inventory scene."""
        self.window_background.update()
        self.ui_manager.update()
        
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the inventory scene."""
        # Fill with black background first
        surface.fill((0, 0, 0))
        
        # Draw window background (for texture/pattern if needed)
        self.window_background.draw(surface)
        
        # Draw UI components on top
        self.ui_manager.draw(surface)
        
    def handle_event(self, event) -> None:
        """Handle events in the inventory scene."""
        
        # Handle pygame events through UI manager first
        if hasattr(event, 'type'):
            if self.ui_manager.handle_event(event):
                return
        
        # Handle string action events (from input manager)
        elif isinstance(event, str):
            if event == "B":
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
                return

            # Let UI manager handle navigation and other input actions
            if self.ui_manager.handle_input_action(event):
                return

    def on_item_activated(self, item, index, use_immediately=False):
        """Called when an item is activated - use immediately for keyboard, just select for mouse"""
        # Update text panel with item description
        self._update_item_description(item)
        
        if use_immediately:
            # For keyboard activation (A button), directly use the item
            runtime_globals.game_console.log(f"[SceneInventory] Using item immediately: {item.game_item.name}")
            self._use_item(item, index)
        else:
            # For mouse clicks, just select the item (no focus change)
            runtime_globals.game_console.log(f"[SceneInventory] Item '{item.game_item.name}' selected")
            
    def _update_item_description(self, item):
        """Update the text panel with the selected item's description"""
        if not self.text_panel:
            return
            
        # Get item description
        description = item.game_item.description
            
        self.text_panel.set_text(description)
            
    def _use_item(self, item, index):
        """Internal method to use an item - handles the actual usage logic"""
        runtime_globals.game_sound.play("menu")
        
        # Get targets (selected pets)
        targets = get_selected_pets()
        if not targets:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log("[SceneInventory] No pets selected for feeding")
            return
            
        # Handle different item effects
        if item.game_item.effect == "component":
            # Component crafting
            remove_from_inventory(item.id, item.game_item.amount)
            
            # Find the component item in the same module
            component_item = None
            for module in runtime_globals.game_modules.values():
                if hasattr(module, "items"):
                    for it in module.items:
                        if it.name == item.component_item:
                            component_item = it
                            break
                    if component_item:
                        break
                        
            if component_item:
                add_to_inventory(component_item.id, 1)
                runtime_globals.game_console.log(f"[SceneInventory] Crafted {component_item.name} from {item.name}")
            else:
                runtime_globals.game_console.log(f"[SceneInventory] Component item not found for {item.name}")
            
            change_scene("game")
            runtime_globals.game_sound.play("happy2")
            return
            
        # Handle status boost items
        if item.game_item.effect == "status_boost":
            eff = game_globals.battle_effects.get(item.status, {"amount": 0, "boost_time": 0})
            eff["amount"] += item.game_item.amount
            eff["boost_time"] += item.game_item.boost_time
            game_globals.battle_effects[item.status] = eff
            
        # Feed the item to pets
        runtime_globals.game_pet_eating = {}
        food_status = item.game_item.status
        food_amount = item.game_item.amount
        
        for pet in targets:
            pet.check_disturbed_sleep()
            try:
                pet_index = game_globals.pet_list.index(pet)
            except ValueError:
                continue
                
            accepted = pet.set_eating(food_status, food_amount)
            if accepted:
                pet.animation_counter = 0
                anim_path = item.anim_path
                anim_frames = None
                if anim_path and os.path.exists(anim_path):
                    anim_image = pygame.image.load(anim_path).convert_alpha()
                    w, h = anim_image.get_width() // 4, anim_image.get_height()
                    anim_frames = [
                        pygame.transform.scale(
                            anim_image.subsurface((i * w, 0, w, h)).copy(),
                            (int(constants.PET_WIDTH * 0.75), int(constants.PET_HEIGHT * 0.75))
                        )
                        for i in range(4)
                    ]
                # Create sprite for eating animation
                if item.icon:
                    scaled_sprite = pygame.transform.scale(
                        item.icon, (int(constants.PET_WIDTH * 0.75), int(constants.PET_HEIGHT * 0.75))
                    )
                    
                runtime_globals.game_pet_eating[pet_index] = {
                    "item": item,
                    "sprite": scaled_sprite,
                    "anim_frames": anim_frames
                }
                
                # Remove from inventory for non-default items
                if item.id not in [ditem.id for ditem in runtime_globals.default_items.values()]:
                    remove_from_inventory(item.id)
                    
        runtime_globals.game_console.log(f"[SceneInventory] Fed {len(runtime_globals.game_pet_eating)} pets with {item.game_item.name}")
        change_scene("game")
        
    # Button callback methods
    def on_use_button(self):
        """Handle USE button press - feed the selected item to pets."""
        if not self.item_list or not self.item_list.items:
            runtime_globals.game_sound.play("cancel")
            return
            
        # Get the currently selected item
        selected_index = self.item_list.selected_index
        if selected_index < 0 or selected_index >= len(self.item_list.items):
            runtime_globals.game_sound.play("cancel")
            return
            
        item = self.item_list.items[selected_index]
        self._use_item(item, selected_index)
        
    def on_discard_button(self):
        """Handle DISCARD button press - remove item from inventory."""
        if not self.item_list or not self.item_list.items:
            runtime_globals.game_sound.play("cancel")
            return
            
        # Get the currently selected item
        selected_index = self.item_list.selected_index
        if selected_index < 0 or selected_index >= len(self.item_list.items):
            runtime_globals.game_sound.play("cancel")
            return
            
        item = self.item_list.items[selected_index]
        
        # Don't allow discarding default items (Protein/Vitamin)
        if hasattr(item, 'id') and item.id in [ditem.id for ditem in runtime_globals.default_items.values()]:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log(f"[SceneInventory] Cannot discard default item: {item.name}")
            return
            
        runtime_globals.game_sound.play("menu")
        
        # Remove 1 from inventory
        if hasattr(item, 'id'):
            remove_from_inventory(item.id, 1)
            runtime_globals.game_console.log(f"[SceneInventory] Discarded 1x {item.name}")
            
            # Refresh the inventory items list
            inventory_items = self.load_inventory_items()
            self.item_list.set_items(inventory_items)
            
            # If no items left, focus back to item list
            if not inventory_items:
                self.ui_manager.set_focused_component(self.item_list)
        else:
            runtime_globals.game_console.log(f"[SceneInventory] Could not discard item - no ID found")
        
    def on_selection_button(self):
        """Handle SELECTION button press - toggle pet selection strategy."""
        runtime_globals.game_sound.play("menu")
        # Cycle through pet selection strategies
        runtime_globals.strategy_index = (runtime_globals.strategy_index + 1) % 2
        strategy_names = ["All Pets", "Active Pet"]
        current_strategy = strategy_names[runtime_globals.strategy_index]
        runtime_globals.game_console.log(f"[SceneInventory] Switched to strategy: {current_strategy}")
        
        # Update pet selector if needed
        if self.pet_selector:
            self.pet_selector.set_pets(get_selected_pets())
        
    def on_exit_button(self):
        """Handle EXIT button press."""
        runtime_globals.game_sound.play("cancel")
        change_scene("game")
