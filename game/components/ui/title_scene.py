"""
Title Scene Component - A scene title with background sprite and left-aligned text
"""
import pygame
from components.ui.component import UIComponent
from components.ui.ui_constants import TEXT_FONT, TITLE_FONT
from core import runtime_globals


class TitleScene(UIComponent):
    def __init__(self, x, y, title_text):
        """
        Initialize the title scene component.
        
        Args:
            x: X position (should be 0 to connect with border)
            y: Y position 
            title_text: Text to display with title font
        """
        # Base dimensions at 1x scale
        width = 120
        height = 116
        
        super().__init__(x, y, width, height)
        
        self.title_text = title_text
        self.text_margin = 5  # Left margin for text in base scale
        
        # Sprites will be loaded when manager is set
        self.yellow_background_sprite = None
        self.blue_background_sprite = None
        self.font = None
        
        # Animation properties for background fade
        self.current_mode = "sleep"  # "sleep" or "wake"
        self.is_animating = False
        self.animation_alpha = 255  # 0-255 for fade effect
        
    def on_manager_set(self):
        """Called when UI manager is set - load scaled assets"""
        if not self.manager:
            return
            
        # Get sprite scale and current theme
        sprite_scale = self.manager.get_sprite_scale()
        theme = self.manager.theme
        
        runtime_globals.game_console.log(f"[TitleScene] Loading assets: theme={theme}, sprite_scale={sprite_scale}, ui_scale={self.manager.ui_scale}")
        
        # Load theme-appropriate background sprites
        try:
            sprite_path = f"assets/ui/Sleep_Title_{theme}_{sprite_scale}.png"
            self.yellow_background_sprite = pygame.image.load(sprite_path).convert_alpha()
            runtime_globals.game_console.log(f"[TitleScene] Loaded background sprite: {sprite_path}, size={self.yellow_background_sprite.get_size()}")
        except pygame.error as e:
            runtime_globals.game_console.log(f"[TitleScene] Could not load {theme} background sprite: {e}")
            # Create a fallback colored rectangle with current theme
            theme_colors = self.manager.get_theme_colors()
            self.yellow_background_sprite = pygame.Surface((self.rect.width, self.rect.height))
            self.yellow_background_sprite.fill(theme_colors["bg"])
        
        # For now, use the same sprite for both modes (can be different in the future)
        self.blue_background_sprite = self.yellow_background_sprite.copy()
            
        # Get title font using centralized method with proper scaling
        # Manager already handles scaling through get_title_font_size()
        self.font = self.get_font(font_type="title")
        font_size = self.manager.get_title_font_size()
        runtime_globals.game_console.log(f"[TitleScene] Font loaded: size={font_size}")
        
        # Force redraw
        self.needs_redraw = True
        
    def set_mode(self, mode):
        """Set the background mode (sleep=yellow, wake=blue)"""
        if mode != self.current_mode:
            self.current_mode = mode
            self.needs_redraw = True
            
    def set_text(self, text):
        """Update the title text"""
        self.title_text = text
        self.needs_redraw = True
        
    def render(self):
        """Render the title scene component"""
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw appropriate background sprite based on current mode
        if self.current_mode == "wake" and self.yellow_background_sprite:
            surface.blit(self.yellow_background_sprite, (0, 0))
        elif self.current_mode == "sleep" and self.blue_background_sprite:
            surface.blit(self.blue_background_sprite, (0, 0))
        
        # Draw title text with left margin and proper theme color
        if self.font and self.title_text:
            colors = self.manager.get_theme_colors()
            text_color = colors["highlight"]  # Use highlight color as requested
            text_surface = self.font.render(self.title_text, True, text_color)
            
            # Position text with left margin and in the upper portion of the sprite
            # UIManager handles scaling, so use base coordinates
            text_x = self.text_margin  # Base margin value
            text_y = 2  # Base y position
            
            surface.blit(text_surface, (text_x, text_y))
            
        return surface