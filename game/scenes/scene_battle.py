"""
Scene Training
Handles both Dummy and Head-to-Head training modes for pets.
"""
import pygame
import os

from components.window_background import WindowBackground
from components.window_horizontalmenu import WindowHorizontalMenu
from components.window_menu import WindowMenu
from components.window_petview import WindowPetList
from core import game_globals, runtime_globals
from core.combat.battle_encounter import BattleEncounter
from core.combat.battle_encounter_versus import BattleEncounterVersus
from core.combat.sim.battle_simulator import BattleProtocol
import game.core.constants as constants
from core.game_module import sprite_load
from core.utils.module_utils import get_module
from core.utils.pet_utils import get_battle_targets
from core.utils.pygame_utils import blit_with_shadow, get_font, sprite_load_percent
from core.utils.scene_utils import change_scene
from core.utils.inventory_utils import get_inventory_value, remove_from_inventory

#=====================================================================
# SceneTraining (Training Menu)
#=====================================================================

class SceneBattle:
    """
    Menu scene where players choose between Dummy or Head-to-Head training.
    """

    def __init__(self) -> None:
        self.background = WindowBackground(False)
        self.font = get_font(constants.FONT_SIZE_LARGE)

        self.phase = "menu"
        self.mode = None
        self.area = 0
        self.round = 0

        # Use new method for backgrounds and icons, scale appropriately
        self.selectionBackground = sprite_load_percent(constants.PET_SELECTION_BACKGROUND_PATH, percent=100, keep_proportion=True, base_on="width")
        self.jogress_slot_on = sprite_load_percent(constants.PET_SELECTION_SMALL_ON_PATH, percent=40, keep_proportion=True, base_on="height")
        self.jogress_slot_off = sprite_load_percent(constants.PET_SELECTION_SMALL_OFF_PATH, percent=40, keep_proportion=True, base_on="height")
        self.backgroundIm = sprite_load_percent(constants.TRAINING_BACKGROUND_PATH, percent=100, keep_proportion=True, base_on="width")

        self.options1 = [
            ("Adventure", sprite_load_percent(constants.BATTLE_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")),
            ("Versus", sprite_load_percent(constants.VERSUS_BATTLE_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")),
            ("Jogress", sprite_load_percent(constants.JOGRESS_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")),
            ("Armor", sprite_load_percent(constants.ARMOR_EVOLUTION_ICON_PATH, percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height"))
        ]

        # Track selected area/round per module (do not overwrite game_globals.battle_area/battle_round)
        self.selected_area = {}
        self.selected_round = {}
        self.area_round_counts = {}  # <-- Store area/round limits per module

        for module in runtime_globals.game_modules.values():
            if module.name not in game_globals.battle_round:
                game_globals.battle_round[module.name] = 1
                game_globals.battle_area[module.name] = 1

            if not module.is_valid_area_round(game_globals.battle_area[module.name], game_globals.battle_round[module.name]):
                runtime_globals.game_console.log(f"[SceneBattle] Invalid saved area/round for {module.name}: {game_globals.battle_area[module.name]}/{game_globals.battle_round[module.name]} -> reset to 1/1")
                game_globals.battle_round[module.name] = 1
                game_globals.battle_area[module.name] = 1
                
            # Initialize selection to max unlocked
            self.selected_area[module.name] = game_globals.battle_area[module.name]
            self.selected_round[module.name] = game_globals.battle_round[module.name]
            # Store area/round counts for this module
            if hasattr(module, "get_area_round_counts"):
                self.area_round_counts[module.name] = module.get_area_round_counts()
            else:
                self.area_round_counts[module.name] = {}

        self.options2 = []
        self.module_lookup = []
        for module in runtime_globals.game_modules.values():
            if module.adventure_mode:
                area = self.selected_area[module.name]
                round_ = self.selected_round[module.name]
                if module.battle_sequential_rounds:
                    label = f"Area {area}"
                else:
                    label = f"Area {area}-{round_}"
                self.options2.append((label, sprite_load_percent(module.folder_path + "/BattleIcon.png", percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")))
                self.module_lookup.append(module.name)

        self.selected_module = None

        self.pet_list_window = WindowPetList(lambda: get_battle_targets())

        if runtime_globals.battle_index.get("menu") is None:
            runtime_globals.battle_index["menu"] = 0
        if runtime_globals.battle_index.get("module") is None:
            runtime_globals.battle_index["module"] = 0
        if runtime_globals.battle_index.get("battle_select") is None:
            runtime_globals.battle_index["battle_select"] = 0

        self.menu_window1 = WindowHorizontalMenu(
            options=self.options1,
            get_selected_index_callback=lambda: runtime_globals.battle_index["menu"],
        )

        self.menu_window2 = WindowHorizontalMenu(
            options=self.options2,
            get_selected_index_callback=lambda: runtime_globals.battle_index["module"],
        )

        self.menu = self.menu_window1
        runtime_globals.game_console.log("[SceneTraining] Training scene initialized.")

        self.versus_ready = False
        self.jogress_ready = False
        self.armor_ready = False

        self.armor_selected_item_index = 0
        self.armor_digimental_items = self.get_digimental_items()

        self._cache_surface = None
        self._cache_key = None

    def update(self):
        if self.mode:
            self.mode.update()
        
        # Update menu windows for mouse hover if in menu phases
        if not self.mode and runtime_globals.game_input.mouse_enabled:
            if self.phase in ["menu", "module", "battle_select"] and hasattr(self, 'menu'):
                self.menu.update()
            elif self.phase == "armor":
                if hasattr(self, 'menu_window1'):
                    self.menu_window1.update()
                if hasattr(self, 'menu_window2'):
                    self.menu_window2.update()

    def draw(self, surface: pygame.Surface):
        # Compose a cache key that reflects the dynamic state of the menu
        cache_key = (
            self.phase,
            getattr(self.menu, "get_selected_index_callback", lambda: None)(),
            tuple(pet.name for pet in self.pet_list_window.targets) if hasattr(self.pet_list_window, "targets") else tuple(),
            tuple(self.pet_list_window.selected_indices) if hasattr(self.pet_list_window, "selected_indices") else tuple(),
            self.armor_selected_item_index if self.phase == "armor" else None,
        )

        # Only cache menu phases, not self.mode
        if not self.mode:
            if cache_key != self._cache_key or self._cache_surface is None:
                cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
                self.background.draw(cache_surface)

                if self.phase in ["menu", "module", "battle_select"]:
                    # Draw horizontal menu
                    if len(self.menu.options) > 2:
                        self.menu.draw(cache_surface, x=int(72 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(30 * constants.UI_SCALE))
                    else:
                        self.menu.draw(cache_surface, x=int(16 * constants.UI_SCALE), y=int(16 * constants.UI_SCALE), spacing=int(16 * constants.UI_SCALE))
                    # Draw pets at the bottom
                    self.pet_list_window.draw(cache_surface)
                elif self.phase == "jogress":
                    self.draw_selection_phase(
                        cache_surface,
                        prompt_text="Press START to confirm Jogress",
                        require_compatibility=True
                    )
                elif self.phase == "versus":
                    self.draw_selection_phase(
                        cache_surface,
                        prompt_text="Press START to begin Battle",
                        require_compatibility=False
                    )
                elif self.phase == "protocol_selection":
                    self.protocol_menu.draw(cache_surface)
                elif self.phase == "armor":
                    self.draw_armor_selection_phase(
                        cache_surface,
                        prompt_text="Press START to evolve"
                    )

                self._cache_surface = cache_surface
                self._cache_key = cache_key

            # Blit cached menu scene
            surface.blit(self._cache_surface, (0, 0))
        elif self.mode:
            self.background.draw(surface)
            self.mode.draw(surface)

    def draw_selection_phase(self, surface, prompt_text, require_compatibility=False):
        self.pet_list_window.draw(surface)

        selected = self.pet_list_window.selected_indices  # 0–2 indices
        is_compatible = self.check_jogress_compatibility(selected) if require_compatibility else True

        spacing = (constants.SCREEN_WIDTH - (2*self.jogress_slot_off.get_width())) // 3
        for i in range(2):
            x = spacing + i * (self.jogress_slot_off.get_width() + spacing)
            y = int(16 * constants.UI_SCALE)

            # Slot sprite (ON if selected and valid, else OFF)
            if i < len(selected) and is_compatible:
                blit_with_shadow(surface, self.jogress_slot_on, (x, y))
            else:
                blit_with_shadow(surface, self.jogress_slot_off, (x, y))

            # Draw pet sprite inside slot
            if i < len(selected):
                pet = game_globals.pet_list[selected[i]]
                sprite = self.pet_list_window.get_scaled_sprite(pet)
                sprite_x = x + (self.jogress_slot_on.get_width() - sprite.get_width()) // 2
                sprite_y = y + (self.jogress_slot_on.get_height() - sprite.get_height()) // 2
                blit_with_shadow(surface, sprite, (sprite_x, sprite_y))

        # Show prompt if ready
        ready = (self.jogress_ready if require_compatibility else self.versus_ready)
        if ready:
            font = get_font(int(20 * constants.UI_SCALE))
            text = font.render(prompt_text, True, constants.FONT_COLOR_GREEN)
            text_x = (constants.SCREEN_WIDTH - text.get_width()) // 2
            text_y = constants.SCREEN_HEIGHT - int(120 * constants.UI_SCALE)
            blit_with_shadow(surface, text, (text_x, text_y))

    def draw_armor_selection_phase(self, surface, prompt_text):
        self.pet_list_window.draw(surface)
        selected = self.pet_list_window.selected_indices  # Should be 0 or 1 index

        spacing = (constants.SCREEN_WIDTH - (2*self.jogress_slot_off.get_width())) // 3
        for i in range(2):
            x = spacing + i * (self.jogress_slot_off.get_width() + spacing)
            y = int(16 * constants.UI_SCALE)

            # Slot sprite
            if i == 0 and len(selected) > 0:
                if self.armor_ready:
                    blit_with_shadow(surface, self.jogress_slot_on, (x, y))
                else:
                    blit_with_shadow(surface, self.jogress_slot_off, (x, y))
            elif i == 1 and self.armor_digimental_items:
                # Use ON if ready, OFF if not
                slot_sprite = self.jogress_slot_on if self.armor_ready else self.jogress_slot_off
                blit_with_shadow(surface, slot_sprite, (x, y))
            else:
                blit_with_shadow(surface, self.jogress_slot_off, (x, y))

            # Draw pet sprite in left slot
            if i == 0 and len(selected) > 0:
                pet = game_globals.pet_list[selected[0]]
                sprite = self.pet_list_window.get_scaled_sprite(pet)
                sprite_x = x + (self.jogress_slot_on.get_width() - sprite.get_width()) // 2
                sprite_y = y + (self.jogress_slot_on.get_height() - sprite.get_height()) // 2
                blit_with_shadow(surface, sprite, (sprite_x, sprite_y))

            # Draw digimental item in right slot
            if i == 1:
                if self.armor_digimental_items:
                    idx = self.armor_selected_item_index % len(self.armor_digimental_items)
                    digimental = self.armor_digimental_items[idx]
                    icon = digimental["icon"]
                    icon_x = x + (self.jogress_slot_on.get_width() - icon.get_width()) // 2
                    icon_y = y + (self.jogress_slot_on.get_height() - icon.get_height()) // 2

                    # Dim icon if not ready
                    if not self.armor_ready:
                        icon = icon.copy()
                        icon.fill((120, 120, 120, 180), special_flags=pygame.BLEND_RGBA_MULT)
                    blit_with_shadow(surface, icon, (icon_x, icon_y - (5 * constants.UI_SCALE)))

                    # Draw item name (centered under icon)
                    font = get_font(int(16 * constants.UI_SCALE))
                    name_text = font.render(digimental["item"].name, True, (255, 255, 255))
                    name_x = x + (self.jogress_slot_on.get_width() - name_text.get_width()) // 2
                    name_y = y + self.jogress_slot_on.get_height() - name_text.get_height() - 24 * constants.UI_SCALE
                    # Add shadow for visibility
                    surface.blit(font.render(digimental["item"].name, True, (0, 0, 0)), (name_x+2, name_y+2))
                    surface.blit(name_text, (name_x, name_y))

                    # Draw quantity (bottom right)
                    qty_text = font.render(f"x{digimental['amount']}", True, (255, 255, 255))
                    qty_x = x + self.jogress_slot_on.get_width() - qty_text.get_width() - 8
                    qty_y = y + self.jogress_slot_on.get_height() - qty_text.get_height() - 8
                    surface.blit(font.render(f"x{digimental['amount']}", True, (0, 0, 0)), (qty_x+2, qty_y+2))
                    surface.blit(qty_text, (qty_x, qty_y))

                    # Draw up/down triangles (white, with black border for visibility)
                    tri_color = (255, 255, 255)
                    border_color = (0, 0, 0)
                    tri_size = int(10 * constants.UI_SCALE)
                    # Up triangle
                    up_center = (x + self.jogress_slot_on.get_width() // 2, y + 8)
                    up_points = [
                        (up_center[0], up_center[1]),
                        (up_center[0] - tri_size, up_center[1] + tri_size),
                        (up_center[0] + tri_size, up_center[1] + tri_size)
                    ]
                    pygame.draw.polygon(surface, border_color, up_points, 0)
                    pygame.draw.polygon(surface, tri_color, [(p[0], p[1]-2) for p in up_points], 0)
                    # Down triangle
                    down_center = (x + self.jogress_slot_on.get_width() // 2, y + self.jogress_slot_on.get_height() - 8)
                    down_points = [
                        (down_center[0], down_center[1]),
                        (down_center[0] - tri_size, down_center[1] - tri_size),
                        (down_center[0] + tri_size, down_center[1] - tri_size)
                    ]
                    pygame.draw.polygon(surface, border_color, down_points, 0)
                    pygame.draw.polygon(surface, tri_color, [(p[0], p[1]+2) for p in down_points], 0)
                else:
                    # No digimental items: show "no item" message in the square
                    blit_with_shadow(surface, self.jogress_slot_off, (x, y))
                    font = get_font(int(16 * constants.UI_SCALE))
                    no_item_text = font.render("no item", True, (255, 255, 255))
                    text_x = x + (self.jogress_slot_off.get_width() - no_item_text.get_width()) // 2
                    text_y = y + (self.jogress_slot_off.get_height() - no_item_text.get_height()) // 2
                    # Add shadow for visibility
                    surface.blit(font.render("no item", True, (0, 0, 0)), (text_x+2, text_y+2))
                    surface.blit(no_item_text, (text_x, text_y))

        # Show prompt
        font = get_font(int(20 * constants.UI_SCALE))
        if self.armor_ready:
            text = font.render(prompt_text, True, constants.FONT_COLOR_GREEN)
            text_x = (constants.SCREEN_WIDTH - text.get_width()) // 2
            text_y = constants.SCREEN_HEIGHT - int(120 * constants.UI_SCALE)
            blit_with_shadow(surface, text, (text_x, text_y))

    def handle_event(self, input_action):
        self._cache_surface = None
        if self.phase == "menu":
            self.handle_menu_input(input_action)
        elif self.phase == "module":
            self.handle_module_input(input_action)
        elif self.phase == "battle_select":
            self.handle_battle_select_input(input_action)
        elif self.phase == "jogress":
            self.handle_jogress_input(input_action)
        elif self.phase == "versus":
            self.handle_versus_input(input_action)
        elif self.phase == "protocol_selection":
            self.handle_protocol_selection_input(input_action)
        elif self.phase == "armor":
            self.handle_armor_input(input_action)
        elif self.mode:
            self.mode.handle_event(input_action)

    def handle_menu_input(self, input_action):
        # Handle mouse clicks on navigation arrows for multi-option menus
        if input_action == "A" and runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if hasattr(self, 'menu') and self.menu.handle_mouse_click(mouse_pos):
                # Mouse click was handled by the menu (navigation arrow click)
                return
        
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
        elif input_action in ("LEFT", "RIGHT"):
            runtime_globals.game_sound.play("menu")
            delta = -1 if input_action == "LEFT" else 1
            runtime_globals.battle_index[self.phase] = (runtime_globals.battle_index[self.phase] + delta) % len(self.menu.options)
        elif input_action == "A":
            if runtime_globals.battle_index[self.phase] == 0: #Adventure
                runtime_globals.game_sound.play("menu")
                self.phase = "module"
                self.menu = self.menu_window2
            elif runtime_globals.battle_index[self.phase] == 1: #Versus
                self.phase = "versus"
                self.pet_list_window.selection_label = "Versus"
                self.pet_list_window.max_selection = 2
                self.pet_list_window.select_mode = True
            elif runtime_globals.battle_index[self.phase] == 2: #Jogress
                self.phase = "jogress"
                self.pet_list_window.selection_label = "Jogress"
                self.pet_list_window.select_mode = True
                self.pet_list_window.max_selection = 2
            elif runtime_globals.battle_index[self.phase] == 3: # Armor
                self.phase = "armor"
                self.pet_list_window.selection_label = "Armor"
                self.pet_list_window.select_mode = True
                self.armor_selected_item_index = 0
                self.pet_list_window.max_selection = 1
                self.armor_digimental_items = self.get_digimental_items()

    def handle_module_input(self, input_action):
        """
        Optimized: Caches unlocked area/round pairs per module and avoids rebuilding them every call.
        """
        selected_index = runtime_globals.battle_index["module"]
        module_name = self.module_lookup[selected_index]
        module = get_module(module_name)
        max_area = game_globals.battle_area[module_name]
        area_round_counts = self.area_round_counts.get(module_name, {})

        # Cache unlocked pairs per module to avoid rebuilding every call
        if not hasattr(self, "_unlocked_pairs_cache"):
            self._unlocked_pairs_cache = {}
        cache_key = (module_name, max_area, game_globals.battle_round[module_name])
        if cache_key not in self._unlocked_pairs_cache:
            unlocked = []
            for a in range(1, max_area + 1):
                if a == max_area:
                    max_round = game_globals.battle_round[module_name]
                else:
                    max_round = area_round_counts.get(a, 1)
                for r in range(1, max_round + 1):
                    unlocked.append((a, r))
            if not unlocked:
                unlocked = [(1, 1)]
            self._unlocked_pairs_cache[cache_key] = unlocked
        else:
            unlocked = self._unlocked_pairs_cache[cache_key]

        def get_next_area_round(area, round_, direction):
            """Cycles through unlocked area/round pairs in the correct order."""
            try:
                idx = unlocked.index((area, round_))
            except ValueError:
                idx = 0
            idx = (idx + direction) % len(unlocked)
            return unlocked[idx]

        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.phase = "menu"
            self.menu = self.menu_window1
        elif input_action == "A" and runtime_globals.game_input.mouse_enabled:
            # Handle mouse clicks on navigation arrows for multi-option menus
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if hasattr(self, 'menu') and self.menu.handle_mouse_click(mouse_pos):
                # Mouse click was handled by the menu (navigation arrow click)
                return
        elif input_action in ("LEFT", "RIGHT"):
            runtime_globals.game_sound.play("menu")
            delta = -1 if input_action == "LEFT" else 1
            runtime_globals.battle_index[self.phase] = (runtime_globals.battle_index[self.phase] + delta) % len(self.menu.options)
        elif input_action == "UP":
            runtime_globals.game_sound.play("menu")
            if module.battle_sequential_rounds:
                area = self.selected_area[module_name]
                area = area + 1 if area < max_area else 1
                self.selected_area[module_name] = area
            else:
                area = self.selected_area[module_name]
                round_ = self.selected_round[module_name]
                next_area, next_round = get_next_area_round(area, round_, 1)
                self.selected_area[module_name] = next_area
                self.selected_round[module_name] = next_round
            self.update_module_label(selected_index)
        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            if module.battle_sequential_rounds:
                area = self.selected_area[module_name]
                area = area - 1 if area > 1 else max_area
                self.selected_area[module_name] = area
            else:
                area = self.selected_area[module_name]
                round_ = self.selected_round[module_name]
                prev_area, prev_round = get_next_area_round(area, round_, -1)
                self.selected_area[module_name] = prev_area
                self.selected_round[module_name] = prev_round
            self.update_module_label(selected_index)
        elif input_action == "A":
            runtime_globals.game_sound.play("menu")
            self.selected_module = module_name
            self.area = self.selected_area[module_name]
            self.round = self.selected_round[module_name]
            for pet in get_battle_targets():
                pet.check_disturbed_sleep()
            self.mode = BattleEncounter(
                self.selected_module,
                self.area,
                1 if module.battle_sequential_rounds else self.round,
                1
            )
            self.phase = "next"
            runtime_globals.game_console.log("Starting Battle.")

    def handle_battle_select_input(self, input_action):
        # Handle mouse clicks on navigation arrows for multi-option menus
        if input_action == "A" and runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if hasattr(self, 'menu') and self.menu.handle_mouse_click(mouse_pos):
                # Mouse click was handled by the menu (navigation arrow click)
                return
        
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.phase = "module"
            self.menu = self.menu_window2
        elif input_action in ("LEFT", "RIGHT"):
            runtime_globals.game_sound.play("menu")
            delta = -1 if input_action == "LEFT" else 1
            runtime_globals.battle_index[self.phase] = (runtime_globals.battle_index[self.phase] + delta) % len(self.menu.options)
        elif input_action == "A":
            runtime_globals.game_sound.play("menu")
            if runtime_globals.battle_index[self.phase] == 1:
                game_globals.battle_round[self.selected_module] = 1
                game_globals.battle_area[self.selected_module] = 1
            self.phase = "next"
            for pet in get_battle_targets():
                pet.check_disturbed_sleep()
            self.mode = BattleEncounter(self.selected_module, self.area, 1 if get_module(self.selected_module).battle_sequential_rounds else self.round, 1)
            runtime_globals.game_console.log("Starting Battle.")

    def handle_jogress_input(self, input_action):
        if input_action == "LEFT" or input_action == "RIGHT":
            self.pet_list_window.handle_input(input_action)
        elif input_action == "A":
            self.pet_list_window.handle_input(input_action)
            if len(self.pet_list_window.selected_indices) == 2:
                self.jogress_ready = self.check_jogress_compatibility(self.pet_list_window.selected_indices)
            else:
                self.jogress_ready = False
        elif input_action == "B":
            # Cancel Jogress selection
            self.pet_list_window.selected_indices.clear()
            self.phase = "menu"
            self.pet_list_window.select_mode = False
            runtime_globals.game_sound.play("cancel")
        elif input_action == "START":
            if self.jogress_ready:
                self.perform_jogress()
            else:
                runtime_globals.game_sound.play("fail")

    def handle_versus_input(self, input_action):
        if input_action in ("LEFT", "RIGHT"):
            self.pet_list_window.handle_input(input_action)
        elif input_action == "A":
            self.pet_list_window.handle_input(input_action)
            self.versus_ready = len(self.pet_list_window.selected_indices) == 2
        elif input_action == "B":
            # Cancel Jogress selection
            self.pet_list_window.selected_indices.clear()
            self.phase = "menu"
            self.pet_list_window.select_mode = False
            runtime_globals.game_sound.play("cancel")
        elif input_action == "START":
            if self.versus_ready:
                # Show protocol selection menu
                self.protocol_menu = WindowMenu()
                self.protocol_menu.open(
                    position=((constants.SCREEN_WIDTH - int(120 * constants.UI_SCALE)) // 2, (constants.SCREEN_HEIGHT - int(100 * constants.UI_SCALE)) // 2),
                    options=["DM20", "Pen20", "DMX/PenZ", "DMC"]
                )
                self.phase = "protocol_selection"
            else:
                runtime_globals.game_sound.play("fail")

    def handle_protocol_selection_input(self, input_action):
        if input_action == "B":
            # Cancel protocol selection and return to Versus setup
            self.protocol_menu.close()
            self.phase = "versus"
            runtime_globals.game_sound.play("cancel")
        elif input_action in ("UP", "DOWN"):
            self.protocol_menu.handle_event(input_action)
        elif input_action == "A":
            # Confirm protocol selection and start the battle
            selected_protocol = self.protocol_menu.options[self.protocol_menu.menu_index]
            protocol_mapping = {
                "DM20": BattleProtocol.DM20_BS,
                "Pen20": BattleProtocol.PEN20_BS,
                "DMX/PenZ": BattleProtocol.DMX_BS,
                "DMC": BattleProtocol.DMC_BS
            }
            protocol = protocol_mapping[selected_protocol]

            # Transition to Versus battle mode
            selected = [game_globals.pet_list[i] for i in self.pet_list_window.selected_indices]
            self.mode = BattleEncounterVersus(selected[0], selected[1], protocol)
            selected[0].check_disturbed_sleep()
            selected[1].check_disturbed_sleep()
            self.phase = "next"
            runtime_globals.game_console.log(f"Starting Versus Battle with protocol: {selected_protocol}")

    def handle_armor_input(self, input_action):
        if input_action in ("LEFT", "RIGHT"):
            self.pet_list_window.handle_input(input_action)
        elif input_action == "UP":
            runtime_globals.game_sound.play("menu")
            if self.armor_digimental_items:
                self.armor_selected_item_index = (self.armor_selected_item_index - 1) % len(self.armor_digimental_items)
                self.update_armor_digimental_items()
        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            if self.armor_digimental_items:
                self.armor_selected_item_index = (self.armor_selected_item_index + 1) % len(self.armor_digimental_items)
                self.update_armor_digimental_items()
        elif input_action == "A":
            self.pet_list_window.handle_input(input_action)
            # Check for armor evolution compatibility
            self.update_armor_digimental_items()
        elif input_action == "B":
            self.pet_list_window.selected_indices.clear()
            self.phase = "menu"
            self.pet_list_window.select_mode = False
            runtime_globals.game_sound.play("cancel")
        elif input_action == "START":
            if self.armor_ready:
                pet = game_globals.pet_list[self.pet_list_window.selected_indices[0]]
                idx = self.armor_selected_item_index % len(self.armor_digimental_items)
                digimental_item = self.armor_digimental_items[idx]["item"]
                # Find the correct evolution
                for evo in getattr(pet, "evolve", []):
                    if "item" in evo and evo["item"] == digimental_item.name:
                        # Evolve the pet
                        pet.evolve_to(evo["to"], pet.version)
                        # Remove the digimental from inventory
                        remove_from_inventory(digimental_item.id, 1)
                        runtime_globals.game_sound.play("evolution")
                        runtime_globals.game_console.log(f"[Armor Evolution] {pet.name} evolved to {evo['to']} using {digimental_item.name}!")
                        runtime_globals.game_message.add_slide(f"{pet.name} evolved to {evo['to']}!", constants.FONT_COLOR_GREEN, 56 * constants.UI_SCALE, constants.FONT_SIZE_SMALL)
                        
                        # Update quest progress for armor evolution
                        from core.utils.quest_event_utils import update_evolution_quest_progress
                        update_evolution_quest_progress("armor", pet.module)
                        
                        break
                # Return to game scene
                change_scene("game")
            else:
                runtime_globals.game_sound.play("fail")

    def update_armor_digimental_items(self):
        self.armor_ready = False
        if len(self.pet_list_window.selected_indices) == 1 and self.armor_digimental_items:
            pet = game_globals.pet_list[self.pet_list_window.selected_indices[0]]
            idx = self.armor_selected_item_index % len(self.armor_digimental_items)
            digimental_item = self.armor_digimental_items[idx]["item"]
            for evo in getattr(pet, "evolve", []):
                if "item" in evo and evo["item"] == digimental_item.name:
                    self.armor_ready = True
                    break

    def check_jogress_compatibility(self, selected_indices):
        if len(selected_indices) != 2:
            return False

        pet1 = game_globals.pet_list[selected_indices[0]]
        pet2 = game_globals.pet_list[selected_indices[1]]

        # Must belong to the same module
        if pet1.module != pet2.module:
            return False

        # Pet1 must have jogress options
        for evo in pet1.evolve:
            if "jogress" not in evo:
                continue

            if evo.get("jogress_prefix", False):
                if pet2.name.startswith(evo["jogress"]):
                    return True

            # 🔸 Standard jogress
            if evo["jogress"] != "PenC":
                if pet2.name == evo["jogress"] and pet2.version == evo.get("version", pet1.version):
                    return True

            # 🔸 PenC jogress (based on attribute + stage)
            elif evo["jogress"] == "PenC":
                if (
                    (pet2.attribute == evo.get("attribute") or (pet2.attribute == "" and evo.get("attribute") == "Free"))  and
                    pet2.stage == evo.get("stage")
                ):
                    return True

        return False

    def perform_jogress(self):
        selected = self.pet_list_window.selected_indices
        if len(selected) != 2:
            return

        pet1 = game_globals.pet_list[selected[0]]
        pet2 = game_globals.pet_list[selected[1]]

        if pet1.module != pet2.module:
            return

        for evo in pet1.evolve:
            if "jogress" not in evo:
                continue

            if evo.get("jogress_prefix", False):
                if pet2.name.startswith(evo["jogress"]):
                    pet1.evolve_to(evo["to"], pet1.version)
                    pet2.evolve_to(evo["to"], pet2.version)
                    if pet2.traited:
                        pet1.trated = True
                    if pet2.shiny:
                        pet1.shiny = True
                    if pet2.shook:
                        pet1.shook = True
                    game_globals.pet_list.remove(pet2)
                    runtime_globals.game_sound.play("evolution")
                    runtime_globals.game_console.log(f"[Jogress] {pet1.name} jogressed to {evo['to']}!")
                    
                    # Update quest progress for jogress
                    from core.utils.quest_event_utils import update_evolution_quest_progress
                    update_evolution_quest_progress("jogress", pet1.module)
                    
                    change_scene("game")
                    return

            if evo["jogress"] != "PenC":
                if pet2.name == evo["jogress"] and pet2.version == evo.get("version", pet1.version):
                    pet1.evolve_to(evo["to"], pet1.version)
                    pet2.evolve_to(evo["to"], pet2.version)
                    if pet2.traited:
                        pet1.trated = True
                    if pet2.shiny:
                        pet1.shiny = True
                    if pet2.shook:
                        pet1.shook = True
                    game_globals.pet_list.remove(pet2)
                    runtime_globals.game_sound.play("evolution")
                    runtime_globals.game_console.log(f"[Jogress] {pet1.name} jogressed to {evo['to']}!")
                    change_scene("game")
                    return

            elif evo["jogress"] == "PenC":
                if (pet2.attribute == evo.get("attribute") or (pet2.attribute == "" and evo.get("attribute") == "Free")) and pet2.stage == evo.get("stage"):
                    evo2 = next((e for e in pet2.evolve if e.get("jogress") == "PenC" and e.get("attribute") == pet1.attribute), None)

                    if evo2:
                        pet1.evolve_to(evo["to"], pet1.version)  # pet1 evolves to pet2's attribute evolution
                        pet2.evolve_to(evo2["to"], pet2.version)  # pet2 evolves to pet1's attribute evolution

                    runtime_globals.game_sound.play("evolution")
                    runtime_globals.game_console.log(f"[Jogress] {pet1.name} jogressed to {evo['to']}!")
                    change_scene("game")
                    return

        runtime_globals.game_console.log("[Jogress] Invalid combination.")
        runtime_globals.game_sound.play("fail")

    def update_module_label(self, index):
        module_name = self.module_lookup[index]
        module = get_module(module_name)
        area = self.selected_area[module_name]
        round_ = self.selected_round[module_name]
        if module.battle_sequential_rounds:
            label = f"Area {area}"
        else:
            label = f"Area {area}-{round_}"
        self.menu_window2.set_option_label(index, label)

    def get_digimental_items(self):
        digimental_items = []
        for module in runtime_globals.game_modules.values():
            if hasattr(module, "items"):
                for item in module.items:
                    if getattr(item, "effect", "") == "digimental":
                        amount = get_inventory_value(item.id)
                        if amount > 0:
                            sprite_name = item.sprite_name
                            if not sprite_name.lower().endswith(".png"):
                                sprite_name += ".png"
                            sprite_path = os.path.join(module.folder_path, "items", sprite_name)
                            if os.path.exists(sprite_path):
                                icon = pygame.image.load(sprite_path).convert_alpha()
                            else:
                                icon = pygame.Surface((48 * constants.UI_SCALE, 48 * constants.UI_SCALE), pygame.SRCALPHA)
                            digimental_items.append({
                                "item": item,
                                "icon": icon,
                                "amount": amount
                            })
        return digimental_items