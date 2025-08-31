"""
Scene Debug
A debug scene with various testing and debugging options for pets.
"""
import pygame
import random

from components.window_background import WindowBackground
from components.window_petview import WindowPetList
from core import game_globals, runtime_globals
import game.core.constants as constants
from core.utils.scene_utils import change_scene
from core.utils.pet_utils import get_selected_pets
from core.utils.module_utils import get_module
from game.core.game_quest import QuestStatus
from game.core.utils.pygame_utils import blit_with_shadow, get_font
from game.core.utils.quest_event_utils import force_complete_quest, generate_daily_quests, get_hourly_random_event
from core.game_pet import GamePet

#=====================================================================
# SceneDebug
#=====================================================================
class SceneDebug:
    """
    Debug scene with various testing options for pets and game systems.
    """

    def __init__(self) -> None:
        """
        Initializes the debug scene.
        """
        self.background = WindowBackground()
        self.pet_view = WindowPetList(lambda: game_globals.pet_list)
        
        # Menu navigation with scrolling
        self.current_row = 0
        self.current_col = 0
        self.scroll_offset = 0  # For vertical scrolling
        
        # Counter for each debug action
        self.action_counters = {}
        
        # Define debug options - order matters for display
        self.debug_options = [
            ("+60min", self._add_60min, "Add 60 minutes to pet timers"),
            ("Sick", self._add_sickness, "Add sickness and injuries"), 
            ("Mistake", self._add_mistake, "Add care mistake or remove condition heart"),
            ("Effort", self._add_effort, "Add to effort counter"),
            ("Overfeed", self._add_overfeed, "Add to overfeed counter"),
            ("Sp Enc ON", self._special_encounter_on, "Turn special encounter ON"),
            ("Sp Enc OFF", self._special_encounter_off, "Turn special encounter OFF"),
            ("+100 EXP", self._add_experience, "Add 100 experience points"),
            ("+1 Lv", self._add_level, "Add 1 level (max 10)"),
            ("+Quest Count", self._add_quest_count, "Add to quest completed counter"),
            ("Weight Res", self._reset_weight, "Reset weight to minimum"),
            ("+Trophy", self._add_trophy, "Add a trophy"),
            ("+1000VV", self._add_vital_values, "Add 1000 vital values (max 9999)"),
            ("+Stage5", self._add_stage5_kill, "Add to stage 5 enemy kills"),
            ("Sleep Dist", self._add_sleep_disturbance, "Add sleep disturbance"),
            ("+Battle Win", self._add_battle_win, "Add battle and win"),
            ("+Battle Lose", self._add_battle_lose, "Add battle loss"),
            ("DP", self._reset_dp, "Reset DP to energy value"),
            ("NAP", self._force_nap, "Force all pets to nap"),
            ("POOP", self._force_poop, "Force all pets to poop"),
            ("KILL", self._kill_pets, "Kill selected pets"),
            ("Traited", self._add_traited_egg, "Add random traited egg"),
            ("Quest Reset", self._reset_quests, "Reset daily quests"),
            ("Complete Quests", self._complete_quests, "Complete all available quests"),
            ("Try Event", self._try_event, "Attempt to trigger an event")
        ]
        
        # Initialize counters
        for option_name, _, _ in self.debug_options:
            self.action_counters[option_name] = 0
        
        # Grid layout configuration - horizontal scrolling grid
        self.grid_cols = 2  # Visible columns at once
        self.grid_rows = 3  # Fixed 3 rows
        self.total_cols = (len(self.debug_options) + self.grid_rows - 1) // self.grid_rows  # Total columns needed

        # Cache system
        self._last_cache = None
        self._last_cache_key = None
        
        runtime_globals.game_console.log("[SceneDebug] Debug scene initialized.")

    def update(self) -> None:
        """
        Updates the debug scene.
        """
        pass  # No constant updates needed, cache invalidated on input

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the debug scene with caching similar to egg selection.
        """
        # Draw background
        self.background.draw(surface)
        
        # Create cache key
        cache_key = (
            self.current_row,
            self.current_col,
            self.scroll_offset,
            tuple(self.action_counters.values()),
            len(runtime_globals.selected_pets) if runtime_globals.selected_pets else 0,
            constants.SCREEN_WIDTH,
            constants.SCREEN_HEIGHT,
            constants.UI_SCALE
        )
        
        # Use cached surface if unchanged
        if self._last_cache_key != cache_key or self._last_cache is None:
            cached_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            
            # Draw title
            self._draw_title(cached_surface)
            
            # Draw pet view
            self.pet_view.draw(cached_surface)
            
            # Draw debug menu grid
            self._draw_debug_menu(cached_surface)
            
            self._last_cache = cached_surface
            self._last_cache_key = cache_key
        
        # Blit cached content
        surface.blit(self._last_cache, (0, 0))

    def _draw_title(self, surface: pygame.Surface) -> None:
        """
        Draws the "Debug Menu" title.
        """
        title_font = get_font(constants.FONT_SIZE_LARGE)
        title_text = title_font.render("Debug Menu", True, constants.FONT_COLOR_ORANGE)
        title_x = constants.SCREEN_WIDTH // 2 - title_text.get_width() // 2
        title_y = int(8 * constants.UI_SCALE)
        blit_with_shadow(surface, title_text, (title_x, title_y))

    def _draw_debug_menu(self, surface: pygame.Surface) -> None:
        """
        Draws the debug options grid with scrolling, similar to egg selection.
        Also draws the cursor highlight for the currently selected option.
        """
        start_y = int(30 * constants.UI_SCALE) + int(15 * constants.UI_SCALE)
        col_width = constants.SCREEN_WIDTH // self.grid_cols
        option_width = col_width - int(8 * constants.UI_SCALE)  # Padding
        option_height = int(28 * constants.UI_SCALE)
        font = get_font(constants.FONT_SIZE_SMALL)

        # Draw only visible options (within scroll range)
        for index, (option_name, _, description) in enumerate(self.debug_options):
            col = index // self.grid_rows  # Column based on rows per column
            row = index % self.grid_rows   # Row within the column

            # Skip options outside visible range
            if not (self.scroll_offset <= col < self.scroll_offset + self.grid_cols):
                continue

            # Calculate position
            visible_col = col - self.scroll_offset
            x = (col_width * visible_col) + (col_width - option_width) // 2
            y = start_y + (row * (option_height + int(4 * constants.UI_SCALE)))

            # Create option rectangle
            option_rect = pygame.Rect(x, y, option_width, option_height)

            # Draw grey background with border
            pygame.draw.rect(surface, (64, 64, 64), option_rect)
            pygame.draw.rect(surface, (128, 128, 128), option_rect, 2)

            # Draw option text with counter
            counter = self.action_counters[option_name]
            option_text = f"{option_name} x{counter}"
            text_color = constants.FONT_COLOR_GREEN if counter > 0 else constants.FONT_COLOR_DEFAULT
            text_surface = font.render(option_text, True, text_color)

            # Center text in rectangle
            text_x = x + (option_width - text_surface.get_width()) // 2
            text_y = y + (option_height - text_surface.get_height()) // 2

            blit_with_shadow(surface, text_surface, (text_x, text_y))

            # Draw cursor highlight if this is the selected option
            if (
                row == self.current_row and col == self.current_col
                and self.scroll_offset <= col < self.scroll_offset + self.grid_cols
            ):
                highlight_rect = pygame.Rect(x - 2, y - 2, option_width + 4, option_height + 4)
                pygame.draw.rect(surface, constants.FONT_COLOR_YELLOW, highlight_rect, 3)

    def handle_event(self, input_action) -> None:
        """
        Handles keyboard and GPIO button inputs in the debug scene.
        """
        if not input_action:
            return
            
        # Invalidate cache on any input
        self._last_cache = None
        self._last_cache_key = None
        
        if input_action == "B":  # Back to main menu
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
            return

        self._handle_menu_input(input_action)

    def _handle_menu_input(self, input_action) -> None:
        """
        Handles menu navigation with proper grid movement and scrolling.
        """
        if input_action == "LEFT":
            runtime_globals.game_sound.play("menu")
            if self.current_col == 0:
                # Wrap to rightmost column
                self.current_col = self.total_cols - 1
            else:
                self.current_col -= 1
            self.adjust_scroll()

        elif input_action == "RIGHT":
            runtime_globals.game_sound.play("menu")
            if self.current_col == self.total_cols - 1:
                # Wrap to leftmost column
                self.current_col = 0
            else:
                self.current_col += 1
            self.adjust_scroll()

        elif input_action == "UP":
            runtime_globals.game_sound.play("menu")
            if self.current_row == 0:
                self.current_row = self.grid_rows - 1
            else:
                self.current_row -= 1
            # Check if position is valid, if not find a valid position
            if self.is_empty(self.current_col, self.current_row):
                # Try to find a valid row in this column, prefer staying in same row
                found = False
                # First try rows from current position upward
                for row in range(self.current_row, -1, -1):
                    if not self.is_empty(self.current_col, row):
                        self.current_row = row
                        found = True
                        break
                # If not found, try downward
                if not found:
                    for row in range(self.current_row + 1, self.grid_rows):
                        if not self.is_empty(self.current_col, row):
                            self.current_row = row
                            found = True
                            break

        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            if self.current_row == self.grid_rows - 1:
                self.current_row = 0
            else:
                self.current_row += 1
            # Check if position is valid, if not find a valid position
            if self.is_empty(self.current_col, self.current_row):
                # Try to find a valid row in this column, prefer staying in same row
                found = False
                # First try rows from current position downward
                for row in range(self.current_row, self.grid_rows):
                    if not self.is_empty(self.current_col, row):
                        self.current_row = row
                        found = True
                        break
                # If not found, try upward
                if not found:
                    for row in range(self.current_row - 1, -1, -1):
                        if not self.is_empty(self.current_col, row):
                            self.current_row = row
                            found = True
                            break

        elif input_action == "A":
            # Execute selected debug option
            current_index = self.current_row + (self.current_col * self.grid_rows)
            if 0 <= current_index < len(self.debug_options):
                option_name, action_func, description = self.debug_options[current_index]
                success = action_func()
                if success:
                    self.action_counters[option_name] += 1
                    runtime_globals.game_sound.play("menu")
                    runtime_globals.game_console.log(f"[SceneDebug] Executed: {option_name} - {description}")
                else:
                    runtime_globals.game_sound.play("cancel")

    def is_empty(self, col, row):
        """Check if a grid position is empty (no option available)."""
        index = row + (col * self.grid_rows)
        return index >= len(self.debug_options)

    def adjust_scroll(self):
        """Adjust scroll offset to keep current selection visible."""
        if self.current_col < self.scroll_offset:
            self.scroll_offset = self.current_col
        elif self.current_col >= self.scroll_offset + self.grid_cols:
            self.scroll_offset = self.current_col - self.grid_cols + 1
        
        # Ensure scroll offset is within bounds
        max_scroll = max(0, self.total_cols - self.grid_cols)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    # Debug action methods
    def _add_60min(self) -> bool:
        """Add 60 minutes to pet timers."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.timer += constants.FRAME_RATE * 60 * 60  # 60 minutes
            pet.age_timer += constants.FRAME_RATE * 60 * 60
        return True

    def _add_sickness(self) -> bool:
        """Add sickness and injuries."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.sick += 1
            pet.injuries += 1
        return True

    def _add_mistake(self) -> bool:
        """Add care mistake or remove condition heart."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            if get_module(pet.module).use_condition_hearts:
                if pet.condition_hearts > 0:
                    pet.condition_hearts -= 1
            else:
                pet.mistakes += 1
        return True

    def _add_effort(self) -> bool:
        """Add to effort counter."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.effort += 1
        return True

    def _add_overfeed(self) -> bool:
        """Add to overfeed counter."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.overfeed += 1
        return True

    def _special_encounter_on(self) -> bool:
        """Turn special encounter ON."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.special_encounter = True
        return True

    def _special_encounter_off(self) -> bool:
        """Turn special encounter OFF."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.special_encounter = False
        return True

    def _add_experience(self) -> bool:
        """Add 100 experience points."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.add_experience(100)
        return True

    def _add_level(self) -> bool:
        """Add 1 level (max 10)."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            if pet.level < 10:
                pet.level += 1
        return True

    def _add_quest_count(self) -> bool:
        """Add to quest completed counter."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.quests_completed += 1
        return True

    def _reset_weight(self) -> bool:
        """Reset weight to minimum."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.weight = pet.min_weight
        return True

    def _add_trophy(self) -> bool:
        """Add a trophy."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.trophies += 1
        return True

    def _add_vital_values(self) -> bool:
        """Add 1000 vital values (max 9999)."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.vital_values = min(9999, pet.vital_values + 1000)
        return True

    def _add_stage5_kill(self) -> bool:
        """Add to stage 5 enemy kills."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.enemy_kills[5] += 1
        return True

    def _add_sleep_disturbance(self) -> bool:
        """Add sleep disturbance."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.sleep_disturbances += 1
        return True

    def _add_battle_win(self) -> bool:
        """Add battle and win."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.battles += 1
            pet.totalBattles += 1
            pet.win += 1
            pet.totalWin += 1
        return True

    def _add_battle_lose(self) -> bool:
        """Add battle loss."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.battles += 1
            pet.totalBattles += 1
        return True

    def _reset_dp(self) -> bool:
        """Reset DP to energy value."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.dp = pet.energy
        return True

    def _force_nap(self) -> bool:
        """Force all pets to nap."""
        if not game_globals.pet_list:
            return False
            
        for pet in game_globals.pet_list:
            pet.set_state("nap")
        return True

    def _force_poop(self) -> bool:
        """Force all pets to poop."""
        if not game_globals.pet_list:
            return False
            
        for pet in game_globals.pet_list:
            pet.force_poop()
        return True

    def _kill_pets(self) -> bool:
        """Kill selected pets."""
        selected_pets = get_selected_pets()
        if not selected_pets:
            return False
            
        for pet in selected_pets:
            pet.set_state("dead")
        return True

    def _add_traited_egg(self) -> bool:
        """Add random traited egg."""
        if not runtime_globals.game_modules:
            return False
            
        # Get a random module
        module_names = list(runtime_globals.game_modules.keys())
        random_module_name = random.choice(module_names)
        random_module = runtime_globals.game_modules[random_module_name]
        
        # Get random egg from that module
        eggs = random_module.get_monsters_by_stage(0)
        if not eggs:
            return False
            
        random_egg = random.choice(eggs)
        key = f"{random_module_name}@{random_egg['version']}"
        if key not in game_globals.traited:
            game_globals.traited.append(key)

        runtime_globals.game_console.log(f"[SceneDebug] Added traited egg: {random_egg['name']} from {random_module_name}")
        return True

    def _reset_quests(self) -> bool:
        """Reset daily quests."""
        game_globals.quests = generate_daily_quests()
        runtime_globals.game_console.log("[SceneDebug] Daily quests reset")
        return True

    def _complete_quests(self) -> bool:
        """
        Complete all currently available quests.
        """
        if not game_globals.quests:
            runtime_globals.game_console.log("[SceneDebug] No quests available to complete.")
            return False
        
        for quest in game_globals.quests:
            force_complete_quest(quest.id)
        
        runtime_globals.game_console.log("[SceneDebug] All quests forcibly completed.")
        return True

    def _try_event(self) -> bool:
        """Attempt to trigger an event."""
        event = get_hourly_random_event()
        if event:
            game_globals.event = event
            runtime_globals.game_console.log(f"[SceneDebug] Triggered event: {event.name}")
            return True
        else:
            runtime_globals.game_console.log("[SceneDebug] No event triggered")
            return False
