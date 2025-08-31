"""
Reward Popup Component
Shows quest rewards one by one in animated popups.
"""
import pygame
import os
from typing import List, Dict, Optional

from core import runtime_globals
import game.core.constants as constants
from game.core.utils.pygame_utils import blit_with_shadow, get_font
from core.game_quest import RewardType


class RewardPopup:
    """
    Component for displaying quest rewards in animated popups.
    """
    
    def __init__(self):
        """Initialize the reward popup system."""
        self.reward_queue = []  # List of rewards to show
        self.current_reward = None  # Currently displayed reward
        self.show_timer = 0  # Timer for how long to show current reward
        self.fade_timer = 0  # Timer for fade in/out animation
        self.state = "hidden"  # hidden, fade_in, showing, fade_out
        
        # Load icons
        self.icons = {}
        self._load_icons()
        
    def _load_icons(self):
        """Load reward type icons."""
        try:
            # Trophy icon
            trophy_path = constants.TROPHIES_ICON_PATH
            if os.path.exists(trophy_path):
                self.icons['trophy'] = pygame.image.load(trophy_path).convert_alpha()
                self.icons['trophy'] = pygame.transform.scale(
                    self.icons['trophy'], 
                    (int(32 * constants.UI_SCALE), int(32 * constants.UI_SCALE))
                )
            
            # Heart icon for vital values
            heart_path = constants.HEART_FULL_ICON_PATH
            if os.path.exists(heart_path):
                self.icons['vital_values'] = pygame.image.load(heart_path).convert_alpha()
                self.icons['vital_values'] = pygame.transform.scale(
                    self.icons['vital_values'], 
                    (int(32 * constants.UI_SCALE), int(32 * constants.UI_SCALE))
                )
                
        except Exception as e:
            print(f"[RewardPopup] Error loading icons: {e}")
    
    def add_rewards(self, rewards: List[Dict]):
        """Add a list of rewards to the display queue."""
        for reward in rewards:
            self.reward_queue.append(reward)
        
        # Start showing if not already active
        if self.state == "hidden" and self.reward_queue:
            self._start_next_reward()
    
    def _start_next_reward(self):
        """Start showing the next reward in the queue."""
        if not self.reward_queue:
            self.state = "hidden"
            self.current_reward = None
            return
            
        self.current_reward = self.reward_queue.pop(0)
        self.state = "fade_in"
        self.fade_timer = 0
        self.show_timer = 0
        
        # Play reward sound
        runtime_globals.game_sound.play("happy")
    
    def update(self):
        """Update the popup animation and timing."""
        if self.state == "hidden":
            return
            
        fade_duration = int(15 * constants.UI_SCALE)  # 15 frames for fade
        show_duration = int(120 * constants.UI_SCALE)  # 2 seconds at 60fps
        
        if self.state == "fade_in":
            self.fade_timer += 1
            if self.fade_timer >= fade_duration:
                self.state = "showing"
                self.show_timer = 0
                
        elif self.state == "showing":
            self.show_timer += 1
            if self.show_timer >= show_duration:
                self.state = "fade_out"
                self.fade_timer = fade_duration
                
        elif self.state == "fade_out":
            self.fade_timer -= 1
            if self.fade_timer <= 0:
                # Start next reward or hide
                self._start_next_reward()
    
    def draw(self, surface: pygame.Surface):
        """Draw the current reward popup."""
        if self.state == "hidden" or not self.current_reward:
            return
            
        # Calculate fade alpha
        fade_duration = int(15 * constants.UI_SCALE)
        if self.state == "fade_in":
            alpha = int(255 * (self.fade_timer / fade_duration))
        elif self.state == "fade_out":
            alpha = int(255 * (self.fade_timer / fade_duration))
        else:
            alpha = 255
            
        alpha = max(0, min(255, alpha))
        
        # Create popup surface
        popup_width = int(200 * constants.UI_SCALE)
        popup_height = int(80 * constants.UI_SCALE)
        popup_x = (constants.SCREEN_WIDTH - popup_width) // 2
        popup_y = int(60 * constants.UI_SCALE)  # Position near top
        
        # Create popup surface with alpha
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        
        # Draw popup background
        background_color = (40, 40, 40, alpha)
        border_color = (0, 231, 58, alpha)
        
        popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
        pygame.draw.rect(popup_surface, background_color, popup_rect)
        pygame.draw.rect(popup_surface, border_color, popup_rect, int(2 * constants.UI_SCALE))
        
        # Draw reward content
        self._draw_reward_content(popup_surface, alpha)
        
        # Blit popup to main surface
        surface.blit(popup_surface, (popup_x, popup_y))
    
    def _draw_reward_content(self, surface: pygame.Surface, alpha: int):
        """Draw the reward content on the popup surface."""
        reward = self.current_reward
        if not reward:
            return
            
        padding = int(8 * constants.UI_SCALE)
        
        # Draw "REWARD!" title
        title_font = get_font(constants.FONT_SIZE_MEDIUM)
        title_text = title_font.render("REWARD!", True, (*constants.FONT_COLOR_YELLOW, alpha))
        title_x = (surface.get_width() - title_text.get_width()) // 2
        surface.blit(title_text, (title_x, padding))
        
        # Draw reward based on type
        reward_type = reward["reward_type"]
        reward_quantity = reward["reward_quantity"]
        reward_value = reward["reward_value"]
        
        content_y = padding + title_text.get_height() + int(4 * constants.UI_SCALE)
        
        if reward_type == "ITEM":
            self._draw_item_reward(surface, reward_value, reward_quantity, content_y, alpha)
        elif reward_type == "TROPHY":
            self._draw_icon_reward(surface, "trophy", f"+{reward_quantity} Trophies", content_y, alpha)
        elif reward_type == "EXPERIENCE":
            self._draw_text_reward(surface, f"+{reward_quantity} EXP", content_y, alpha)
        elif reward_type == "VITAL_VALUES":
            self._draw_icon_reward(surface, "vital_values", f"+{reward_quantity} Vital Values", content_y, alpha)
    
    def _draw_item_reward(self, surface: pygame.Surface, item_name: str, quantity: int, y: int, alpha: int):
        """Draw item reward with icon if available."""
        # Try to load item icon (simplified for now)
        text = f"+{quantity}x {item_name}"
        self._draw_text_reward(surface, text, y, alpha)
    
    def _draw_icon_reward(self, surface: pygame.Surface, icon_type: str, text: str, y: int, alpha: int):
        """Draw reward with icon and text."""
        icon = self.icons.get(icon_type)
        if icon:
            # Apply alpha to icon
            icon_with_alpha = icon.copy()
            icon_with_alpha.set_alpha(alpha)
            
            # Center icon and text
            total_width = icon.get_width() + int(8 * constants.UI_SCALE)
            reward_font = get_font(constants.FONT_SIZE_SMALL)
            text_surface = reward_font.render(text, True, (*constants.FONT_COLOR_DEFAULT, alpha))
            total_width += text_surface.get_width()
            
            start_x = (surface.get_width() - total_width) // 2
            
            # Draw icon
            icon_y = y + (text_surface.get_height() - icon.get_height()) // 2
            surface.blit(icon_with_alpha, (start_x, icon_y))
            
            # Draw text
            text_x = start_x + icon.get_width() + int(8 * constants.UI_SCALE)
            surface.blit(text_surface, (text_x, y))
        else:
            # Fallback to text only
            self._draw_text_reward(surface, text, y, alpha)
    
    def _draw_text_reward(self, surface: pygame.Surface, text: str, y: int, alpha: int):
        """Draw text-only reward."""
        reward_font = get_font(constants.FONT_SIZE_SMALL)
        text_surface = reward_font.render(text, True, (*constants.FONT_COLOR_DEFAULT, alpha))
        text_x = (surface.get_width() - text_surface.get_width()) // 2
        surface.blit(text_surface, (text_x, y))
    
    def is_active(self) -> bool:
        """Check if the popup system is currently showing rewards."""
        return self.state != "hidden" or len(self.reward_queue) > 0
