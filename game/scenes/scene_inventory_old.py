"""
Scene Feeding Menu
Allows the player to choose food type and feeding strategy for pets.
"""

import os
import pygame

from components.window_background import WindowBackground
from components.window_horizontalmenu import WindowHorizontalMenu
from components.window_petview import WindowPetList
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.inventory_utils import add_to_inventory, get_inventory_value, remove_from_inventory
from core.utils.pet_utils import distribute_pets_evenly, get_selected_pets
from core.utils.pygame_utils import sprite_load_percent
from core.utils.scene_utils import change_scene
from core.game_quest import QuestType
from core.utils.quest_event_utils import update_quest_progress

#=====================================================================
# SceneFeedingMenu
#=====================================================================
class SceneFeedingMenu:
    """
    Scene for selecting food and feeding pets.
    """

    def __init__(self) -> None:
        """
        Initializes the feeding menu, loading food frames if necessary.
        """
        self.background = WindowBackground()

        # Add default items (Protein and Vitamin) as the first options, without amount
        self.options = []
        default_sprite_folder = os.path.join("assets", "items")
        for default_item in runtime_globals.default_items.values():
            sprite_path = os.path.join(default_sprite_folder, default_item.sprite_name)
            anim_path = os.path.join(default_sprite_folder, f"{default_item.sprite_name.split('.')[0]}_anim.png")
            if os.path.exists(sprite_path):
                icon = pygame.image.load(sprite_path).convert_alpha()
            else:
                icon = pygame.Surface((int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)), pygame.SRCALPHA)
            
            self.options.append((default_item.name, icon, -1, anim_path if os.path.exists(anim_path) else None))

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
                            icon = pygame.Surface((int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)), pygame.SRCALPHA)
                        # For inventory items, include amount
                        self.options.append((item.name, icon, amount, anim_path if os.path.exists(anim_path) else None, item.id))

        # Use new method for selection background, scale to screen width, keep proportions
        self.selectionBackground = sprite_load_percent(
            constants.PET_SELECTION_BACKGROUND_PATH,
            percent=100,
            keep_proportion=True,
            base_on="width"
        )

        self.pet_list_window = WindowPetList(lambda: self.get_targets())

        self.menu_window = WindowHorizontalMenu(
            options=self.options,
            get_selected_index_callback=lambda: runtime_globals.food_index,
        )    

        runtime_globals.game_console.log("[SceneFeedingMenu] Feeding frames loaded.")

        # Ensure food_index is valid
        if runtime_globals.food_index >= len(self.options):
            runtime_globals.food_index = 0

        self._last_food_index = None  # Cache for food index to avoid redundant updates
        self._last_strategy_index = None  # Cache for strategy index
        self._options_cache_key = None  # Cache key for options list
        self._cache_surface = None
        self._cache_key = None

    def _update_options_cache(self):
        """
        Updates the cached options list only if necessary.
        """
        current_key = (runtime_globals.food_index, runtime_globals.strategy_index)
        if self._options_cache_key != current_key:
            self._options_cache_key = current_key
            # Reload options dynamically
            self.options = []
            # Add default items (Protein and Vitamin) as the first options, without amount
            default_sprite_folder = os.path.join("assets", "items")
            for default_item in runtime_globals.default_items.values():
                sprite_path = os.path.join(default_sprite_folder, default_item.sprite_name)
                anim_path = os.path.join(default_sprite_folder, f"{default_item.sprite_name.split('.')[0]}_anim.png")
                if os.path.exists(sprite_path):
                    icon = pygame.image.load(sprite_path).convert_alpha()
                else:
                    icon = pygame.Surface((int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)), pygame.SRCALPHA)
                
                self.options.append((default_item.name, icon, -1, anim_path if os.path.exists(anim_path) else None))

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
                                icon = pygame.Surface((int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)), pygame.SRCALPHA)
                            # For inventory items, include amount
                            self.options.append((item.name, icon, amount, anim_path if os.path.exists(anim_path) else None, item.id))

    def get_selected_item(self):
        """
        Returns the currently selected food item based on the food index.
        """
        selected_option = self.options[runtime_globals.food_index]
        food_name = selected_option[0]
        food_id = selected_option[4] if len(selected_option) > 4 else None

        # Find the corresponding GameItem object (default or module)
        item_obj = None
        for item in runtime_globals.default_items.values():
            if item.name == food_name:
                item_obj = item
                break
        if not item_obj:
            for module in runtime_globals.game_modules.values():
                if hasattr(module, "items"):
                    for item in module.items:
                        if food_id and item.id == food_id:
                            item_obj = item
                            break
                        if not food_id and item.name == food_name:
                            item_obj = item
                            break
                    if item_obj:
                        break

        return item_obj if item_obj else None
    
    def get_targets(self) -> list:
        """
        Returns a list of pets to feed based on the selected strategy and food type.
        """
        item_obj = self.get_selected_item()

        # Fallback: if not found, treat as default hunger
        food_status = getattr(item_obj, "status", "hunger")
        effect = getattr(item_obj, "effect", "status_change")

        if effect == "component":
            if get_inventory_value(item_obj.id) >= item_obj.amount:
                return get_selected_pets()
            else:
                return []

        if runtime_globals.strategy_index == 0:
            # Manual selection
            if effect == "status_boost":
                # Only allow pets that can battle
                return [pet for pet in get_selected_pets() if pet.can_battle() and pet.stage > 0]
            else:
                # For now, allow all selected pets for hunger/strength/other
                return [pet for pet in get_selected_pets() if pet.stage > 0]
        else:
            # Auto selection
            if food_status == "hunger":
                return [pet for pet in game_globals.pet_list if pet.hunger < pet.stomach and pet.hunger < 4 and pet.state != "dead" and pet.stage > 0]
            elif food_status == "strength":
                return [pet for pet in game_globals.pet_list if (pet.strength < 4 and pet.state != "dead" and pet.stage > 0 and
                                                                 runtime_globals.game_modules.get(pet.module).protein_strengh_gain > 0
                                                                 )
                       ]
            elif effect == "status_boost":
                return [pet for pet in game_globals.pet_list if pet.can_battle() and pet.state != "dead" and pet.stage > 0]
            else:
                # For other types, allow all alive pets
                return [pet for pet in game_globals.pet_list if pet.state != "dead" and pet.stage > 0]

    def update(self) -> None:
        """
        Updates the feeding menu scene, ensuring options and targets are refreshed only when necessary.
        """
        self._update_options_cache()

        if runtime_globals.game_input.mouse_enabled:
            self.menu_window.update()

        # Update pet list targets only if strategy or food index changes
        if self._last_food_index != runtime_globals.food_index or self._last_strategy_index != runtime_globals.strategy_index:
            self.pet_list_window.targets = self.get_targets()
            self.pet_list_window._last_cache_key = None  # Invalidate cache to redraw
            self._last_food_index = runtime_globals.food_index
            self._last_strategy_index = runtime_globals.strategy_index

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the feeding menu and pet list.
        """
        # Update window components for mouse hover
        self.pet_list_window.update()
        
        # Compose a cache key that reflects the dynamic state of the menu
        cache_key = (
            runtime_globals.food_index,
            runtime_globals.strategy_index,
            tuple(pet.name for pet in self.pet_list_window.targets),
        )

        if cache_key != self._cache_key or self._cache_surface is None:
            # Redraw full menu scene once on state change
            cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            self.background.draw(cache_surface)

            # Draw menu window
            if len(self.options) > 2:
                self.menu_window.draw(cache_surface, x=int(72 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(30 * constants.UI_SCALE))
            else:
                self.menu_window.draw(cache_surface, x=int(16 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(16 * constants.UI_SCALE))

            # Draw pet list window
            self.pet_list_window.draw(cache_surface)

            self._cache_surface = cache_surface
            self._cache_key = cache_key

        # Blit cached menu scene
        surface.blit(self._cache_surface, (0, 0))

    def handle_event(self, input_action) -> None:
        """
        Handles keyboard and GPIO button inputs for food and strategy selection.
        """
        # Handle mouse clicks on navigation arrows for multi-option menus
        if input_action == "A" and runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if self.menu_window.handle_mouse_click(mouse_pos):
                # Mouse click was handled by the menu (navigation arrow click)
                self.pet_list_window.targets = self.get_targets()
                self.pet_list_window._last_cache_key = None  # Invalidate cache to redraw
                return
        
        if input_action == "B":  # Escape (Cancel/Menu)
            runtime_globals.game_sound.play("cancel")
            change_scene("game")

        elif input_action == "LEFT":  # Move food selection left
            runtime_globals.game_sound.play("menu")
            runtime_globals.food_index = (runtime_globals.food_index - 1) % len(self.options)
            self.pet_list_window.targets = self.get_targets()
            self.pet_list_window._last_cache_key = None  # Invalidate cache to redraw

        elif input_action == "RIGHT":  # Move food selection right
            runtime_globals.game_sound.play("menu")
            runtime_globals.food_index = (runtime_globals.food_index + 1) % len(self.options)
            self.pet_list_window.targets = self.get_targets()
            self.pet_list_window._last_cache_key = None

        elif input_action == "SELECT":  # Cycle strategy
            runtime_globals.game_sound.play("menu")
            runtime_globals.strategy_index = (runtime_globals.strategy_index + 1) % 2

        elif input_action == "A":  # Confirm feeding action (ENTER on PC, A button on Pi)
            targets = self.get_targets()

            if not targets:
                runtime_globals.game_sound.play("cancel")
                return

            runtime_globals.game_sound.play("menu")
            distribute_pets_evenly()

            selected_option = self.options[runtime_globals.food_index]
            food_name = selected_option[0]
            icon = selected_option[1]
            anim_path = selected_option[3] if len(selected_option) > 3 else None

            # Find the corresponding GameItem object (default or module)
            item_obj = self.get_selected_item()
            food_status = None
            food_amount = 1
            
            food_status = item_obj.status
            food_amount = item_obj.amount
                
             # Check for component effect
            if item_obj and item_obj.effect == "component":
                # Remove the required amount (already validated in get_targets)
                remove_from_inventory(item_obj.id, item_obj.amount)
                # Find the component item in the same module
                component_item = None
                for module in runtime_globals.game_modules.values():
                    if hasattr(module, "items"):
                        for it in module.items:
                            if it.name == item_obj.component_item:
                                component_item = it
                                break
                        if component_item:
                            break
                if component_item:
                    # Add the component item to inventory
                    add_to_inventory(component_item.id, 1)
                    runtime_globals.game_console.log(f"[SceneFeedingMenu] Crafted {component_item.name} from {item_obj.name}")
                    runtime_globals.game_message.add_slide(f"{component_item.name} obtained!", constants.FONT_COLOR_GREEN, 56 * constants.UI_SCALE, constants.FONT_SIZE_SMALL)
                else:
                    runtime_globals.game_console.log(f"[SceneFeedingMenu] Component item '{item_obj.component_item}' not found in module.")
                change_scene("game")
                runtime_globals.game_sound.play("happy2")
                return

            # If the item is a status_boost, update global battle_effects
            if item_obj and item_obj.effect == "status_boost":
                eff = game_globals.battle_effects.get(food_status, {"amount": 0, "boost_time": 0})
                eff["amount"] += food_amount
                eff["boost_time"] += item_obj.boost_time
                game_globals.battle_effects[food_status] = eff

            # Feed each pet and track accepted ones for animation
            runtime_globals.game_pet_eating = {}
            for pet in targets:
                pet.check_disturbed_sleep()
                try:
                    pet_index = game_globals.pet_list.index(pet)
                except ValueError:
                    continue

                accepted = pet.set_eating(food_status, food_amount)
                if accepted:
                    pet.animation_counter = 0  # <-- Reset animation for new food!
                    anim_frames = None
                    if anim_path and os.path.exists(anim_path):
                        anim_image = pygame.image.load(anim_path).convert_alpha()
                        w, h = anim_image.get_width() // 4, anim_image.get_height()
                        anim_frames = [
                            pygame.transform.smoothscale(
                                anim_image.subsurface((i * w, 0, w, h)).copy(),
                                (int(constants.PET_WIDTH * 0.75), int(constants.PET_HEIGHT * 0.75))
                            )
                            for i in range(4)
                        ]
                    runtime_globals.game_pet_eating[pet_index] = {
                        "item": item_obj,
                        "sprite": pygame.transform.smoothscale(
                            icon, (int(constants.PET_WIDTH * 0.75), int(constants.PET_HEIGHT * 0.75))
                        ),
                        "anim_frames": anim_frames  # None if not found
                    }

                    # Remove 1 from inventory for non-default items
                    if item_obj and item_obj.id not in [ditem.id for ditem in runtime_globals.default_items.values()]:
                        remove_from_inventory(item_obj.id)

            # Update FEEDING quest progress if items were consumed (excluding component and default items)
            if (item_obj and item_obj.effect != "component" and 
                item_obj.id not in [ditem.id for ditem in runtime_globals.default_items.values()] and
                len(runtime_globals.game_pet_eating) > 0):
                # Find the module for this item
                item_module = None
                for module in runtime_globals.game_modules.values():
                    if hasattr(module, "items"):
                        for it in module.items:
                            if it.id == item_obj.id:
                                item_module = module.name
                                break
                        if item_module:
                            break
                
                if item_module:
                    update_quest_progress(QuestType.FEEDING, len(runtime_globals.game_pet_eating), item_module)

            runtime_globals.game_console.log(f"[SceneFeedingMenu] Fed {len(runtime_globals.game_pet_eating)} pets with {food_name}")
            change_scene("game")