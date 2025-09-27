"""
Base UI Component - Foundation for all UI elements
"""
import pygame

from core import runtime_globals


class UIComponent:
    def __init__(self, x, y, width, height):
        # Store base coordinates (will be scaled by UIManager when added)
        self.rect = pygame.Rect(x, y, width, height)
        self.base_rect = None  # Will be set by UIManager
        self.focused = False
        self.clicked = False
        self.click_time = 0
        self.cached_surface = None
        self.needs_redraw = True
        self.manager = None
        self.focusable = False
        self.visible = True
        self.on_click_callback = None
        self.tooltip_text = None
        self.tooltip_active = False
        
        runtime_globals.game_console.log(f"[{self.__class__.__name__}] Created with base rect: {self.rect}")
        
    def set_position(self, x, y):
        """Set position in base coordinates"""
        if self.base_rect:
            self.base_rect.x = x
            self.base_rect.y = y
            # Update screen coordinates if manager is available
            if self.manager:
                self.rect = self.manager.scale_rect(self.base_rect)
        else:
            self.rect.x = x
            self.rect.y = y
        self.needs_redraw = True
        
    def set_size(self, width, height):
        """Set size in base coordinates"""
        if self.base_rect:
            self.base_rect.width = width
            self.base_rect.height = height
            # Update screen coordinates if manager is available
            if self.manager:
                self.rect = self.manager.scale_rect(self.base_rect)
        else:
            self.rect.width = width
            self.rect.height = height
        self.needs_redraw = True
        
    def update(self):
        # Handle mouse hover detection if input manager is available
        self.handle_mouse_hover()
        
        # Reset click state after a brief period
        if self.clicked and pygame.time.get_ticks() - self.click_time > 200:
            self.clicked = False
            self.needs_redraw = True
    
    def handle_mouse_hover(self):
        """Handle mouse hover detection using InputManager with screen coordinates"""
        if not runtime_globals or not hasattr(runtime_globals, 'game_input') or not runtime_globals.game_input:
            return
            
        if not runtime_globals.game_input.mouse_enabled:
            return
            
        # Don't override focus during keyboard navigation mode
        if self.manager and hasattr(self.manager, 'keyboard_navigation_mode') and self.manager.keyboard_navigation_mode:
            return
            
        mouse_pos = runtime_globals.game_input.get_mouse_position()
        was_focused = self.focused
        # Use screen coordinates for collision detection
        self.focused = self.rect.collidepoint(mouse_pos)
        if was_focused != self.focused:
            self.needs_redraw = True
            
    def draw(self, surface):
        if not self.visible:
            return
            
        if self.needs_redraw or self.cached_surface is None:
            self.cached_surface = self.render()
            self.needs_redraw = False
            
        # Blit at screen coordinates
        surface.blit(self.cached_surface, self.rect)
        
    def render(self):
        """Create and return the component surface at proper scale - to be implemented by subclasses"""
        # Use screen dimensions for surface creation
        return pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
    def handle_event(self, event):
        """Handle input events"""
        if not self.visible or not self.focusable:
            return False
            
        # Only handle string events from the input manager
        if isinstance(event, str):
            if event == "A":
                self.on_click()
                return True
                    
        return False
        
    def set_tooltip(self, text):
        """Set tooltip text for this component"""
        self.tooltip_text = text
        if text:
            self.focusable = True  # Make focusable if it has tooltip
        
    def show_tooltip(self):
        """Show tooltip if available"""
        if self.tooltip_text and self.manager:
            self.manager.show_tooltip(self.tooltip_text)
            self.tooltip_active = True
            
    def hide_tooltip(self):
        """Hide tooltip"""
        if self.tooltip_active and self.manager:
            self.manager.hide_tooltip()
            self.tooltip_active = False
        
    def on_focus_gained(self):
        """Called when component gains focus"""
        # Tooltips are now only shown on explicit activation (A key or click)
        pass
        
    def on_focus_lost(self):
        """Called when component loses focus"""
        self.hide_tooltip()
        
    def activate(self):
        """Called when component is activated (A button or click)"""
        if self.tooltip_text:
            self.show_tooltip()
            return True
        return False
        
    def on_click(self):
        self.clicked = True
        self.click_time = pygame.time.get_ticks()
        self.needs_redraw = True
        
        # Show tooltip on click if available
        if self.tooltip_text:
            self.show_tooltip()
        
        if self.on_click_callback:
            self.on_click_callback()
    
    def get_colors(self):
        """
        Get colors for component based on current state (clicked, focused, normal).
        Returns a dictionary with 'bg', 'fg', and 'line' color keys.
        Components can override this method for custom styling behavior.
        """
        if not self.manager:
            # Fallback colors if no manager is available
            return {"bg": (0, 0, 0), "fg": (255, 255, 255), "line": (255, 255, 255)}
        
        # Get base theme colors from manager
        theme_colors = self.manager.get_theme_colors()
        
        # Ensure all required color keys exist (fallback for missing keys during animation)
        if "highlight" not in theme_colors:
            theme_colors["highlight"] = theme_colors.get("fg", (255, 255, 255))
        
        # Default state: normal colors
        bg_color = theme_colors["bg"]
        fg_color = theme_colors["fg"]
        line_color = theme_colors["fg"]
        
        # Apply state-based modifications
        if self.clicked:
            # Clicked state: inverted colors for strong visual feedback
            bg_color = theme_colors["highlight"]
            fg_color = theme_colors["bg"]
            line_color = theme_colors["bg"]
        elif self.focused:
            # Focused state: highlighted text/foreground while keeping background
            bg_color = theme_colors["bg"]
            fg_color = theme_colors["highlight"]
            line_color = theme_colors["highlight"]
        
        return {
            "bg": bg_color,
            "fg": fg_color,
            "line": line_color
        }
    
    def get_font(self, font_type="text", custom_size=None):
        """
        Get font for component with consistent handling across the UI system.
        
        Args:
            font_type (str): Type of font - "text", "title", or custom path
            custom_size (int): Optional custom font size, overrides theme sizing
            
        Returns:
            pygame.font.Font: Configured font object
        """
        import pygame
        from components.ui.ui_constants import TEXT_FONT, TITLE_FONT
        
        # Determine font path
        if font_type == "title":
            font_path = TITLE_FONT
            # Get size from manager or fallback
            if self.manager and custom_size is None:
                font_size = self.manager.get_title_font_size()
            else:
                font_size = custom_size or 24
        elif font_type == "text":
            font_path = TEXT_FONT  
            # Get size from manager or fallback
            if self.manager and custom_size is None:
                font_size = self.manager.get_text_font_size()
            else:
                font_size = custom_size or 16
        else:
            # Custom font path provided
            font_path = font_type
            font_size = custom_size or 16
        
        # Try to load the font with error handling
        try:
            return pygame.font.Font(font_path, font_size)
        except (pygame.error, FileNotFoundError):
            # Fallback to default pygame font if loading fails
            fallback_size = custom_size or 16
            return pygame.font.Font(None, fallback_size)
