"""
Scene Library
Displays daily quests, with navigation to Digidex and Freezer.
"""

import os
import pygame

from components.window_background import WindowBackground
from components.reward_popup import RewardPopup
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.scene_utils import change_scene
from core.utils.inventory_utils import get_item_by_name
from core.utils.pygame_utils import blit_with_shadow, get_font
from core.utils.quest_event_utils import claim_all_completed_quests, generate_daily_quests
from core.game_quest import QuestStatus, RewardType

#=====================================================================
# SceneLibrary
#=====================================================================
class SceneLibrary:
    """
    Scene for displaying daily quests and providing access to Digidex and Freezer.
    """

    def __init__(self) -> None:
        """
        Initializes the library scene.
        """
        self.background = WindowBackground()
        self.menu_index = 0  # 0 = Digidex, 1 = Freezer
        
        # Initialize reward popup system
        self.reward_popup = RewardPopup()
        
        # Load menu icons
        self.menu_icons = {}
        self.menu_icons['digidex'] = pygame.image.load(constants.DIGIDEX_ICON_PATH).convert_alpha()
        self.menu_icons['digidex'] = pygame.transform.scale(
            self.menu_icons['digidex'], 
            (26 * constants.UI_SCALE, 26 * constants.UI_SCALE)
        )
        
        self.menu_icons['freezer'] = pygame.image.load(constants.FREEZER_ICON_PATH).convert_alpha()
        self.menu_icons['freezer'] = pygame.transform.scale(
            self.menu_icons['freezer'], 
            (26 * constants.UI_SCALE, 26 * constants.UI_SCALE)
        )
        
        self.trophy_icon = pygame.image.load(constants.TROPHIES_ICON_PATH).convert_alpha()
        self.trophy_icon = pygame.transform.scale(
            self.trophy_icon, 
            (int(24 * constants.UI_SCALE), int(24 * constants.UI_SCALE))
        )
        
        # Load heart icon for vital values rewards
        self.heart_icon = pygame.image.load(constants.HEART_FULL_ICON_PATH).convert_alpha()
        self.heart_icon = pygame.transform.scale(
            self.heart_icon, 
            (int(20 * constants.UI_SCALE), int(20 * constants.UI_SCALE))
        )
        
        # Cache variables
        self._cached_surface = None
        self._cache_key = None
        
        runtime_globals.game_console.log("[SceneLibrary] Library scene initialized.")

    def update(self) -> None:
        """
        Updates the library scene and reward popup system.
        """
        self.reward_popup.update()

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the library scene with caching.
        """
        # Create cache key based on quest states and menu selection
        quest_states = []
        for quest in game_globals.quests:
            quest_states.append((quest.id, quest.current_amount, quest.status))
        
        cache_key = (tuple(quest_states), self.menu_index)
        
        # Redraw only if cache is invalid
        if self._cache_key != cache_key or self._cached_surface is None:
            self._cached_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            self._draw_full_scene(self._cached_surface)
            self._cache_key = cache_key
        
        # Blit cached surface
        surface.blit(self._cached_surface, (0, 0))
        
        # Draw reward popup on top (not cached)
        self.reward_popup.draw(surface)

    def _draw_full_scene(self, surface: pygame.Surface) -> None:
        """
        Draws the complete library scene to the given surface.
        """
        # Draw background
        self.background.draw(surface)
        
        # Draw title
        self._draw_title(surface)
        
        # Draw quest areas
        self._draw_quests(surface)
        
        # Draw bottom menu
        self._draw_bottom_menu(surface)

    def _draw_title(self, surface: pygame.Surface) -> None:
        """
        Draws the "Daily Quests" title.
        """
        title_font = get_font(constants.FONT_SIZE_LARGE)
        title_text = title_font.render("Daily Quests", True, constants.FONT_COLOR_ORANGE)
        
        blit_with_shadow(surface, title_text, (constants.SCREEN_WIDTH // 2 - title_text.get_width() // 2, int(10 * constants.UI_SCALE)))

    def _draw_quests(self, surface: pygame.Surface) -> None:
        """
        Draws the three daily quest areas.
        """
        quest_start_y = int(50 * constants.UI_SCALE)
        quest_height = int(46 * constants.UI_SCALE)
        quest_spacing = int(2 * constants.UI_SCALE)
        quest_padding = int(4 * constants.UI_SCALE)
        
        # Always show 3 quest slots
        for i in range(3):
            quest_y = quest_start_y + (i * (quest_height + quest_spacing))
            quest_rect = pygame.Rect(
                int(8 * constants.UI_SCALE),
                quest_y,
                constants.SCREEN_WIDTH - int(16 * constants.UI_SCALE),
                quest_height
            )
            
            # Check if we have a quest for this slot
            if i < len(game_globals.quests):
                quest = game_globals.quests[i]
                
                # Determine quest status color
                if quest.status == QuestStatus.SUCCESS:
                    border_color = constants.FONT_COLOR_GREEN
                elif quest.status == QuestStatus.FINISHED:
                    border_color = constants.FONT_COLOR_GRAY
                elif quest.current_amount > 0:
                    border_color = constants.FONT_COLOR_BLUE
                else:
                    border_color = constants.FONT_COLOR_RED
                
                # Draw quest background with border
                pygame.draw.rect(surface, (40, 40, 40), quest_rect)  # Dark background
                pygame.draw.rect(surface, border_color, quest_rect, int(2 * constants.UI_SCALE))
                
                # Draw quest content
                self._draw_quest_content(surface, quest, quest_rect, quest_padding)
            else:
                # Empty quest slot
                pygame.draw.rect(surface, (30, 30, 30), quest_rect)  # Darker background for empty
                pygame.draw.rect(surface, constants.FONT_COLOR_GRAY, quest_rect, int(2 * constants.UI_SCALE))
                
                # Draw "No quest available" text
                self._draw_empty_quest_content(surface, quest_rect, quest_padding)

    def _draw_quest_content(self, surface: pygame.Surface, quest, rect: pygame.Rect, padding: int) -> None:
        """
        Draws the content within a single quest area.
        """
        # Quest title (top left) - bigger font
        title_font = get_font(constants.FONT_SIZE_MEDIUM_LARGE)
        title_text = title_font.render(quest.name[:20], True, constants.FONT_COLOR_DEFAULT)  # Limit length
        surface.blit(title_text, (rect.x + padding, rect.y))
        
        # Module name (bottom left) or quest status messages
        module_font = get_font(constants.FONT_SIZE_SMALL)
        if quest.status == QuestStatus.SUCCESS:
            # Show "READY TO CLAIM" in green
            status_text = module_font.render("READY TO CLAIM", True, constants.FONT_COLOR_GREEN)
            blit_with_shadow(surface, status_text, (rect.x + padding, rect.bottom - status_text.get_height()))
        elif quest.status == QuestStatus.FINISHED:
            # Show "DONE" in gray
            status_text = module_font.render("DONE", True, constants.FONT_COLOR_GRAY)
            blit_with_shadow(surface, status_text, (rect.x + padding, rect.bottom - status_text.get_height()))
        else:
            # Show module name normally
            module_text = module_font.render(quest.module.upper(), True, constants.FONT_COLOR_GRAY)
            blit_with_shadow(surface, module_text, (rect.x + padding, rect.bottom - module_text.get_height()))
        
        # Quest progress (top right) or "DONE" for finished quests
        progress_font = get_font(constants.FONT_SIZE_MEDIUM)
        if quest.status == QuestStatus.FINISHED:
            progress_text = progress_font.render("DONE", True, constants.FONT_COLOR_GRAY)
        else:
            progress_str = f"{quest.current_amount}/{quest.target_amount}"
            progress_text = progress_font.render(progress_str, True, constants.FONT_COLOR_DEFAULT)
        progress_x = rect.right - padding - progress_text.get_width()
        blit_with_shadow(surface, progress_text, (progress_x, rect.y))
        
        # Quest reward (bottom right)
        self._draw_quest_reward(surface, quest, rect, padding)

    def _draw_empty_quest_content(self, surface: pygame.Surface, rect: pygame.Rect, padding: int) -> None:
        """
        Draws content for empty quest slots.
        """
        # Center "No quest available" text
        empty_font = pygame.font.Font(None, constants.FONT_SIZE_MEDIUM)
        empty_text = empty_font.render("No quest available", True, constants.FONT_COLOR_GRAY)
        
        # Center the text in the quest area
        text_x = rect.centerx - empty_text.get_width() // 2
        text_y = rect.centery - empty_text.get_height() // 2
        
        blit_with_shadow(surface, empty_text, (text_x, text_y))

    def _draw_quest_reward(self, surface: pygame.Surface, quest, rect: pygame.Rect, padding: int) -> None:
        """
        Draws the quest reward (item icon + quantity or trophy + EXP).
        """
        reward_font = pygame.font.Font(None, constants.FONT_SIZE_SMALL)
        
        if quest.reward_type == RewardType.ITEM:
            self._draw_item_reward(surface, quest, rect, padding, reward_font)
        else:
            self._draw_non_item_reward(surface, quest, rect, padding, reward_font)

    def _draw_item_reward(self, surface: pygame.Surface, quest, rect: pygame.Rect, padding: int, reward_font) -> None:
        """
        Draws item rewards with icon and quantity.
        """
        item_icon = self._load_item_icon(quest)
        
        if item_icon:
            self._draw_reward_with_icon(surface, item_icon, f"x{quest.reward_quantity}", rect, padding, reward_font)
        else:
            # Fallback: show item name and quantity as text
            from core.utils.inventory_utils import get_item_by_id
            item_instance = get_item_by_id(quest.reward_value)
            item_name = item_instance.name if item_instance else quest.reward_value
            
            reward_text = reward_font.render(f"{quest.reward_quantity}x {item_name}", True, constants.FONT_COLOR_DEFAULT)
            self._draw_reward_text(surface, reward_text, rect, padding)

    def _draw_non_item_reward(self, surface: pygame.Surface, quest, rect: pygame.Rect, padding: int, reward_font) -> None:
        """
        Draws non-item rewards (experience, trophy, vital values).
        """
        if quest.reward_type == RewardType.EXPERIENCE:
            # For experience, show text only without icon
            reward_text = reward_font.render(f"{quest.reward_value} EXP", True, constants.FONT_COLOR_DEFAULT)
            self._draw_reward_text(surface, reward_text, rect, padding)
            
        elif quest.reward_type == RewardType.TROPHY:
            # For trophies, show trophy icon + value
            if self.trophy_icon:
                self._draw_reward_with_icon(surface, self.trophy_icon, str(quest.reward_value), rect, padding, reward_font)
            else:
                reward_text = reward_font.render(str(quest.reward_value), True, constants.FONT_COLOR_DEFAULT)
                self._draw_reward_text(surface, reward_text, rect, padding)
                
        elif quest.reward_type == RewardType.VITAL_VALUES:
            # For vital values, show heart icon + value
            if self.heart_icon:
                self._draw_reward_with_icon(surface, self.heart_icon, str(quest.reward_value), rect, padding, reward_font)
            else:
                reward_text = reward_font.render(f"{quest.reward_value} VV", True, constants.FONT_COLOR_DEFAULT)
                self._draw_reward_text(surface, reward_text, rect, padding)
            # For vital values, show heart icon + value
            if self.heart_icon:
                self._draw_reward_with_icon(surface, self.heart_icon, str(quest.reward_quantity), rect, padding, reward_font)
            else:
                reward_text = reward_font.render(f"{quest.reward_quantity} VV", True, constants.FONT_COLOR_DEFAULT)
                self._draw_reward_text(surface, reward_text, rect, padding)

    def _load_item_icon(self, quest) -> pygame.Surface:
        """
        Loads and scales the item icon for the quest reward.
        """
        try:
            from core.utils.inventory_utils import get_item_by_id
            item_instance = get_item_by_name(quest.module, quest.reward_value)
            
            if item_instance:
                item_sprite_path = f"modules/{quest.module}/items/{item_instance.sprite_name}.png"
                if os.path.exists(item_sprite_path):
                    item_icon = pygame.image.load(item_sprite_path).convert_alpha()
                    return pygame.transform.scale(item_icon, (int(20 * constants.UI_SCALE), int(20 * constants.UI_SCALE)))
        except:
            pass
        return None

    def _draw_reward_with_icon(self, surface: pygame.Surface, icon: pygame.Surface, text: str, rect: pygame.Rect, padding: int, reward_font) -> None:
        """
        Draws a reward with icon and accompanying text.
        """
        # Draw icon in bottom-right corner
        icon_x = rect.right - padding - icon.get_width()
        icon_y = rect.bottom - padding - icon.get_height()
        blit_with_shadow(surface, icon, (icon_x, icon_y))
        
        # Draw text to the left of icon
        value_text = reward_font.render(text, True, constants.FONT_COLOR_DEFAULT)
        value_x = icon_x - value_text.get_width() - int(2 * constants.UI_SCALE)
        value_y = rect.bottom - padding - value_text.get_height()
        blit_with_shadow(surface, value_text, (value_x, value_y))

    def _draw_reward_text(self, surface: pygame.Surface, text_surface: pygame.Surface, rect: pygame.Rect, padding: int) -> None:
        """
        Draws reward text in the bottom-right corner.
        """
        text_x = rect.right - padding - text_surface.get_width()
        text_y = rect.bottom - padding - text_surface.get_height()
        blit_with_shadow(surface, text_surface, (text_x, text_y))

    def _draw_bottom_menu(self, surface: pygame.Surface) -> None:
        """
        Draws the bottom menu with Digidex and Freezer options.
        """
        menu_y = constants.SCREEN_HEIGHT - int(42 * constants.UI_SCALE)
        menu_width = int(105 * constants.UI_SCALE)
        menu_height = int(32 * constants.UI_SCALE)
        menu_spacing = int(14 * constants.UI_SCALE)
        
        # Calculate positions to center both options
        total_width = (menu_width * 2) + menu_spacing
        start_x = (constants.SCREEN_WIDTH - total_width) // 2
        
        menu_options = [
            ("Digidex", self.menu_icons['digidex']),
            ("Freezer", self.menu_icons['freezer'])
        ]
        
        for i, (label, icon) in enumerate(menu_options):
            menu_x = start_x + (i * (menu_width + menu_spacing))
            menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
            
            # Draw selection background
            if i == self.menu_index:
                pygame.draw.rect(surface, (80, 80, 80), menu_rect)
                pygame.draw.rect(surface, constants.FONT_COLOR_YELLOW, menu_rect, int(2 * constants.UI_SCALE))
            else:
                pygame.draw.rect(surface, (50, 50, 50), menu_rect)
                pygame.draw.rect(surface, constants.FONT_COLOR_GRAY, menu_rect, int(1 * constants.UI_SCALE))
            
            # Draw icon to the left of the text, vertically centered
            icon_y = menu_rect.y + (menu_height - icon.get_height()) // 2
            icon_x = menu_rect.x + int(6 * constants.UI_SCALE)
            blit_with_shadow(surface, icon, (icon_x, icon_y))

            # Draw label to the right of the icon, vertically centered
            label_font = get_font(constants.FONT_SIZE_SMALL)
            label_text = label_font.render(label, True, constants.FONT_COLOR_DEFAULT)
            label_x = icon_x + icon.get_width() + int(8 * constants.UI_SCALE)
            label_y = menu_rect.y + (menu_height - label_text.get_height()) // 2
            blit_with_shadow(surface, label_text, (label_x, label_y))

    def handle_event(self, input_action) -> None:
        """
        Handles keyboard and GPIO button inputs for the library scene.
        """
        if input_action == "B":  # Back to main menu
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
            
        elif input_action == "LEFT":  # Move menu selection left
            runtime_globals.game_sound.play("menu")
            self.menu_index = (self.menu_index - 1) % 2
            
        elif input_action == "RIGHT":  # Move menu selection right
            runtime_globals.game_sound.play("menu")
            self.menu_index = (self.menu_index + 1) % 2
            
        elif input_action == "START":  # Claim completed quest rewards
            rewards = claim_all_completed_quests()
            if rewards:
                runtime_globals.game_sound.play("happy")
                runtime_globals.game_console.log(f"[SceneLibrary] Claimed rewards for {len(rewards)} completed quests")
                
                # Add quest completion counter to all pets
                for pet in game_globals.pet_list:
                    pet.quests_completed += len(rewards)
                
                # Show rewards using popup system
                self.reward_popup.add_rewards(rewards)
            else:
                runtime_globals.game_sound.play("cancel")
                runtime_globals.game_console.log("[SceneLibrary] No completed quests to claim")
            
        elif input_action == "A":  # Select menu option
            runtime_globals.game_sound.play("menu")
            if self.menu_index == 0:
                # Open Digidex
                change_scene("digidex")
                runtime_globals.game_console.log("[SceneLibrary] Opening Digidex")
            elif self.menu_index == 1:
                # Open Freezer
                change_scene("freezer")
                runtime_globals.game_console.log("[SceneLibrary] Opening Freezer")
