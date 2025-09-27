"""
Label Component - Text display with optional color override
"""
import pygame
from components.ui.component import UIComponent
from core.utils.pygame_utils import blit_with_cache


class Label(UIComponent):
    def __init__(self, x, y, text, is_title=False, color_override=None, align_right=False, fixed_width=None, tooltip_text=None, scroll_text=False):
        super().__init__(x, y, 1, 1)  # Width/height will be set after rendering
        self.text = text
        self.is_title = is_title
        self.color_override = color_override
        self.align_right = align_right
        self.fixed_width = fixed_width
        self.tooltip_text = tooltip_text
        self.scroll_text = scroll_text
        self.focusable = bool(tooltip_text)  # Only focusable if it has a tooltip
        self.needs_redraw = True
        
        # Scrolling animation variables
        self.scroll_offset = 0
        self.scroll_direction = 1  # 1 for right, -1 for left
        self.scroll_speed = 1  # pixels per frame
        self.scroll_pause_timer = 0
        self.scroll_pause_duration = 60  # frames to pause at each end
        self.last_update_time = 0
        
    def set_text(self, text):
        """Update the label text"""
        if self.text != text:
            self.text = text
            self.needs_redraw = True
            # Reset scrolling when text changes
            self.scroll_offset = 0
            self.scroll_direction = 1
            self.scroll_pause_timer = 0
    
    def set_tooltip(self, tooltip_text):
        """Set or update the tooltip text"""
        self.tooltip_text = tooltip_text
        self.focusable = bool(tooltip_text)
    
    def on_click(self):
        """Handle click events"""
        if self.tooltip_text and self.manager:
            self.manager.show_tooltip(self.tooltip_text)
            
    def on_activate(self):
        """Handle activation (A key or click)"""
        if self.tooltip_text and self.manager:
            self.manager.show_tooltip(self.tooltip_text)
            return True
        return False
    
    def update(self):
        """Update scrolling animation if enabled"""
        super().update()
        
        if self.scroll_text and self.fixed_width:
            current_time = pygame.time.get_ticks()
            
            # Only update scrolling if enough time has passed (smoother animation)
            if current_time - self.last_update_time >= 16:  # ~60 FPS
                self.last_update_time = current_time
                
                # Get text width to determine if scrolling is needed
                if self.is_title:
                    font = self.get_font("title")
                else:
                    font = self.get_font("text")
                
                text_surface = font.render(self.text, True, (255, 255, 255))  # Color doesn't matter for width
                text_width = text_surface.get_width()
                display_width = self.manager.scale_value(self.fixed_width)
                
                # Only scroll if text is wider than display area
                if text_width > display_width:
                    if self.scroll_pause_timer > 0:
                        # Pausing at one end
                        self.scroll_pause_timer -= 1
                    else:
                        # Update scroll position
                        self.scroll_offset += self.scroll_direction * self.scroll_speed
                        
                        # Check boundaries and reverse direction
                        max_offset = text_width - display_width
                        if self.scroll_offset >= max_offset:
                            self.scroll_offset = max_offset
                            self.scroll_direction = -1
                            self.scroll_pause_timer = self.scroll_pause_duration
                        elif self.scroll_offset <= 0:
                            self.scroll_offset = 0
                            self.scroll_direction = 1
                            self.scroll_pause_timer = self.scroll_pause_duration
                        
                        self.needs_redraw = True
                else:
                    # Reset scrolling if text fits
                    self.scroll_offset = 0
        
    def render(self):
        # Choose font based on type using centralized font method
        if self.is_title:
            font = self.get_font("title")
        else:
            font = self.get_font("text")
        
        # Get color
        if self.color_override:
            color = self.color_override
        else:
            colors = self.get_colors()
            color = colors["fg"]
            
        # Render text at proper scale
        text_surface = font.render(self.text, True, color)
        
        # Handle scrolling text
        if self.scroll_text and self.fixed_width:
            scaled_width = self.manager.scale_value(self.fixed_width)
            
            # Create a surface with fixed width for scrolling
            scroll_surface = pygame.Surface((scaled_width, text_surface.get_height()), pygame.SRCALPHA)
            
            # If text is wider than display area, apply scrolling offset
            if text_surface.get_width() > scaled_width:
                # Create a subsurface or blit with offset
                text_rect = pygame.Rect(-self.scroll_offset, 0, text_surface.get_width(), text_surface.get_height())
                blit_with_cache(scroll_surface, text_surface, text_rect)
            else:
                # Text fits, center it or align as normal
                if self.align_right:
                    text_rect = text_surface.get_rect()
                    text_rect.right = scaled_width
                    blit_with_cache(scroll_surface, text_surface, text_rect)
                else:
                    blit_with_cache(scroll_surface, text_surface, (0, 0))
            
            # Update component screen size
            self.rect.width = scaled_width
            self.rect.height = text_surface.get_height()
            return scroll_surface
            
        # Handle right alignment (non-scrolling)
        elif self.align_right and self.fixed_width:
            # Create a surface with fixed width for right alignment (scaled)
            scaled_width = self.manager.scale_value(self.fixed_width)
            aligned_surface = pygame.Surface((scaled_width, text_surface.get_height()), pygame.SRCALPHA)
            
            # Truncate text if it's too wide and not scrolling
            if text_surface.get_width() > scaled_width:
                # Create truncated version
                truncated_surface = pygame.Surface((scaled_width, text_surface.get_height()), pygame.SRCALPHA)
                blit_with_cache(truncated_surface, text_surface, (0, 0))
                text_surface = truncated_surface
            
            # Blit text surface to the right side
            text_rect = text_surface.get_rect()
            text_rect.right = scaled_width
            blit_with_cache(aligned_surface, text_surface, text_rect)
            
            # Update component screen size (don't modify base_rect)
            self.rect.width = scaled_width
            self.rect.height = text_surface.get_height()
            return aligned_surface
        else:
            # Handle truncation for fixed width without scrolling
            if self.fixed_width and not self.scroll_text:
                scaled_width = self.manager.scale_value(self.fixed_width)
                if text_surface.get_width() > scaled_width:
                    # Truncate the text
                    truncated_surface = pygame.Surface((scaled_width, text_surface.get_height()), pygame.SRCALPHA)
                    blit_with_cache(truncated_surface, text_surface, (0, 0))
                    text_surface = truncated_surface
                
                # Update component screen size
                self.rect.width = scaled_width
                self.rect.height = text_surface.get_height()
            else:
                # Update component screen size (don't modify base_rect)
                self.rect.width = text_surface.get_width()
                self.rect.height = text_surface.get_height()
            
            return text_surface
