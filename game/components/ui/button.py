"""
Button Component - Clickable button with text and optional icon
"""
import pygame
from components.ui.component import UIComponent
from core import runtime_globals


class Button(UIComponent):
    def __init__(self, x, y, width, height, text, callback=None, icon_name=None, icon_prefix="Sleep", cut_corners=None, decorators=None):
        super().__init__(x, y, width, height)
        self.text = text
        self.focusable = True
        self.on_click_callback = callback
        self.icon_name = icon_name
        self.icon_prefix = icon_prefix
        self.icon_sprite = None
        # cut_corners: dict with keys 'tl', 'tr', 'bl', 'br' (True/False)
        self.cut_corners = cut_corners or {'tl': False, 'tr': False, 'bl': False, 'br': False}
        # decorators: list of decorator names (e.g., ["Dummy", "Xai_4"])
        self.decorators = decorators or []
        self.decorator_sprites = {}  # Cache for loaded decorator sprites
        # Visual feedback timing
        self.click_hold_frames = 8  # Number of frames to hold clicked state
        self.click_frame_counter = 0
        self.was_activated = False
        
    def on_manager_set(self):
        """Called when UI manager is set - load icon and decorators if specified"""
        if self.icon_name and self.manager:
            sprite_scale = self.manager.get_sprite_scale()
            try:
                # Load icon sprite using <prefix>_<name>_<scale> format
                self.icon_sprite = pygame.image.load(f"assets/ui/{self.icon_prefix}_{self.icon_name}_{sprite_scale}.png").convert_alpha()
            except pygame.error as e:
                runtime_globals.game_console.log(f"[Button] Could not load icon {self.icon_name}: {e}")
        
        # Load decorator sprites
        if self.decorators and self.manager:
            sprite_scale = self.manager.get_sprite_scale()
            runtime_globals.game_console.log(f"[Button] Loading decorators for {self.decorators} at sprite_scale {sprite_scale}")
            for decorator in self.decorators:
                try:
                    # Load standard decorator sprite
                    standard_path = f"assets/ui/Training_{decorator}_{sprite_scale}.png"
                    standard_sprite = pygame.image.load(standard_path).convert_alpha()
                    
                    # Try to load highlight decorator sprite, fall back to standard if not found
                    highlight_sprite = standard_sprite  # Default fallback
                    try:
                        highlight_path = f"assets/ui/Training_{decorator}_Highlight_{sprite_scale}.png"
                        highlight_sprite = pygame.image.load(highlight_path).convert_alpha()
                        runtime_globals.game_console.log(f"[Button] Loaded highlight decorator: {highlight_path}")
                    except (pygame.error, FileNotFoundError):
                        # No highlight version available, use standard for both
                        runtime_globals.game_console.log(f"[Button] No highlight version for {decorator}, using standard")
                        pass
                    
                    self.decorator_sprites[decorator] = {
                        'standard': standard_sprite,
                        'highlight': highlight_sprite
                    }
                    
                    runtime_globals.game_console.log(f"[Button] Loaded decorator {decorator}: standard={standard_sprite.get_size()}, highlight={highlight_sprite.get_size()}")
                    
                except pygame.error as e:
                    runtime_globals.game_console.log(f"[Button] Could not load decorator {decorator} (sprites may not exist yet): {e}")
                    # Continue without this decorator instead of crashing
    
    def set_decorators(self, decorators):
        """Update the decorators for this button and reload sprites"""
        self.decorators = decorators
        self.decorator_sprites = {}
        if self.manager:
            self.on_manager_set()  # Reload decorator sprites
            self.needs_redraw = True
    
    def update(self):
        """Update button state, including visual click feedback"""
        # Handle mouse hover detection if input manager is available
        self.handle_mouse_hover()
        
        # Handle visual click feedback timing (custom behavior instead of base class)
        if self.was_activated and self.click_frame_counter > 0:
            self.click_frame_counter -= 1
            if self.click_frame_counter <= 0:
                self.was_activated = False
                self.clicked = False
                self.needs_redraw = True
        else:
            # Only reset click state from base class behavior if we're not in custom animation
            if self.clicked and not self.was_activated and pygame.time.get_ticks() - self.click_time > 200:
                self.clicked = False
                self.needs_redraw = True
        
    def render(self):
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Get colors using the centralized color system
        colors = self.get_colors()
        bg_color = colors["bg"]
        fg_color = colors["fg"]
        line_color = colors["line"]
        
        # Check if we need cut corners
        has_cuts = any(self.cut_corners.values())
        
        if has_cuts:
            # Use centralized cut corner polygon method
            # We need to convert to base coordinates for the method
            button_rect = (0, 0, self.rect.width // self.manager.ui_scale, self.rect.height // self.manager.ui_scale)
            cut_size = 12  # Base cut size
            
            # For the button surface, we need to draw at already-scaled coordinates
            # So we bypass the centralized method and draw directly
            cut = int(12 * self.manager.ui_scale)  # Diagonal cut size
            w, h = self.rect.width, self.rect.height
            border_size = self.manager.get_border_size()
            
            # Calculate border polygon points
            border_inset = border_size
            border_points = []
            
            # Top-left corner
            if self.cut_corners.get('tl'):
                border_points.extend([(cut, border_inset), (border_inset, cut)])
            else:
                border_points.append((border_inset, border_inset))
            
            # Bottom-left corner  
            if self.cut_corners.get('bl'):
                border_points.extend([(border_inset, h - cut - border_inset), (cut, h - border_inset)])
            else:
                border_points.append((border_inset, h - border_inset))
            
            # Bottom-right corner
            if self.cut_corners.get('br'):
                border_points.extend([(w - cut - border_inset, h - border_inset), (w - border_inset, h - cut - border_inset)])
            else:
                border_points.append((w - border_inset, h - border_inset))
            
            # Top-right corner
            if self.cut_corners.get('tr'):
                border_points.extend([(w - border_inset, cut), (w - cut - border_inset, border_inset)])
            else:
                border_points.append((w - border_inset, border_inset))
            
            # Calculate background polygon points (further inset)
            bg_inset = border_size * 2
            bg_points = []
            
            # Top-left corner
            if self.cut_corners.get('tl'):
                bg_points.extend([(cut, bg_inset), (bg_inset, cut)])
            else:
                bg_points.append((bg_inset, bg_inset))
            
            # Bottom-left corner
            if self.cut_corners.get('bl'):
                bg_points.extend([(bg_inset, h - cut - bg_inset), (cut, h - bg_inset)])
            else:
                bg_points.append((bg_inset, h - bg_inset))
            
            # Bottom-right corner
            if self.cut_corners.get('br'):
                bg_points.extend([(w - cut - bg_inset, h - bg_inset), (w - bg_inset, h - cut - bg_inset)])
            else:
                bg_points.append((w - bg_inset, h - bg_inset))
            
            # Top-right corner
            if self.cut_corners.get('tr'):
                bg_points.extend([(w - bg_inset, cut), (w - cut - bg_inset, bg_inset)])
            else:
                bg_points.append((w - bg_inset, bg_inset))
            
            # Draw border polygon (filled, not outline)
            if len(border_points) >= 3:
                pygame.draw.polygon(surface, line_color, border_points)
                
            # Draw background polygon on top
            if len(bg_points) >= 3:
                pygame.draw.polygon(surface, bg_color, bg_points)
                
        else:
            # Use centralized rounded rectangle method
            # Convert to base coordinates
            button_rect = (0, 0, self.rect.width // self.manager.ui_scale, self.rect.height // self.manager.ui_scale)
            
            # For button surface, we need to draw at screen coordinates, so draw directly
            border_size = self.manager.get_border_size()
            
            # Draw border first (full size)
            if border_size > 0:
                pygame.draw.rect(
                    surface, 
                    line_color, 
                    (0, 0, self.rect.width, self.rect.height), 
                    width=border_size,
                    border_radius=border_size
                )
            
            # Draw background (inset by border)
            border_offset = border_size // 2
            inner_rect = (border_offset, border_offset, 
                         self.rect.width - border_size, self.rect.height - border_size)
            pygame.draw.rect(
                surface, 
                bg_color, 
                inner_rect,
                border_radius=max(0, border_size - border_offset)
            )
        
        # Draw content (icon + text)
        font = self.get_font("text")
        
        # Prepare text surfaces (if any)
        lines = []
        line_surfaces = []
        line_spacing = int(8 * self.manager.ui_scale)
        total_height = 0
        max_line_width = 0

        if self.text:
            lines = self.text.split("\n")
            line_surfaces = [font.render(line, True, fg_color) for line in lines]
            total_height = sum(s.get_height() for s in line_surfaces) + line_spacing * (len(line_surfaces) - 1)
            max_line_width = max((s.get_width() for s in line_surfaces), default=0)

        icon_w = icon_h = 0
        if self.icon_sprite:
            icon_w, icon_h = self.icon_sprite.get_size()

        # Get border inset for available area
        border_size = self.manager.get_border_size() if self.manager else 0
        padding = int(8 * (self.manager.ui_scale if self.manager else 1))

        # Decide layout: if we have text and enough vertical room, put icon above text;
        # otherwise, try to put icon to the left if width allows. If no text, center icon.
        layout = 'none'
        inner_height = self.rect.height - (border_size * 2)
        inner_width = self.rect.width - (border_size * 2)

        if self.icon_sprite and self.text:
            combined_height = icon_h + padding + total_height
            if combined_height <= inner_height:
                layout = 'above'
            else:
                # try left layout if width allows
                combined_width = icon_w + padding + max_line_width
                if combined_width <= inner_width:
                    layout = 'left'
                else:
                    # fallback to above (may overlap slightly)
                    layout = 'above'
        elif self.icon_sprite and not self.text:
            layout = 'center'
        elif self.text:
            layout = 'text_only'

        # Render according to chosen layout
        if layout == 'above':
            # Icon centered above text
            start_y = (self.rect.height - (icon_h + padding + total_height)) // 2
            if self.icon_sprite:
                icon_x = (self.rect.width - icon_w) // 2
                surface.blit(self.icon_sprite, (icon_x, start_y))
            text_y = start_y + icon_h + padding
            for s in line_surfaces:
                text_x = (self.rect.width - s.get_width()) // 2
                surface.blit(s, (text_x, text_y))
                text_y += s.get_height() + line_spacing

        elif layout == 'left':
            # Icon to the left, text centered in remaining area vertically
            icon_x = border_size + padding
            icon_y = (self.rect.height - icon_h) // 2
            if self.icon_sprite:
                surface.blit(self.icon_sprite, (icon_x, icon_y))

            text_area_x = icon_x + icon_w + padding
            text_area_width = self.rect.width - text_area_x - border_size
            text_y = (self.rect.height - total_height) // 2
            for s in line_surfaces:
                text_x = text_area_x + (text_area_width - s.get_width()) // 2
                surface.blit(s, (text_x, text_y))
                text_y += s.get_height() + line_spacing

        elif layout == 'center':
            # Icon only, center it
            icon_x = (self.rect.width - icon_w) // 2
            icon_y = (self.rect.height - icon_h) // 2
            surface.blit(self.icon_sprite, (icon_x, icon_y))

        elif layout == 'text_only':
            # Only text, center vertically and horizontally
            y = (self.rect.height - total_height) // 2
            for s in line_surfaces:
                text_x = (self.rect.width - s.get_width()) // 2
                surface.blit(s, (text_x, y))
                y += s.get_height() + line_spacing
        
        # Draw decorators on top of everything
        for decorator in self.decorators:
            if decorator in self.decorator_sprites:
                # Use highlight version if button is focused or clicked, standard otherwise
                use_highlight = self.focused or self.clicked
                sprite_key = 'highlight' if use_highlight else 'standard'
                decorator_sprite = self.decorator_sprites[decorator][sprite_key]
                
                # Scale decorator sprite to match UI scale
                if self.manager:
                    ui_scale = self.manager.ui_scale
                    sprite_scale = self.manager.get_sprite_scale()
                    scale_factor = ui_scale / sprite_scale
                    
                    original_size = decorator_sprite.get_size()
                    runtime_globals.game_console.log(f"[Button] Decorator {decorator}: ui_scale={ui_scale}, sprite_scale={sprite_scale}, scale_factor={scale_factor:.2f}, original_size={original_size}")
                    
                    if scale_factor != 1.0:
                        # Scale the sprite to match UI scale
                        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                        scaled_sprite = pygame.transform.scale(decorator_sprite, new_size)
                        runtime_globals.game_console.log(f"[Button] Scaled decorator {decorator}: {original_size} -> {new_size}")
                        surface.blit(scaled_sprite, (0, 0))
                    else:
                        runtime_globals.game_console.log(f"[Button] No scaling needed for decorator {decorator}")
                        surface.blit(decorator_sprite, (0, 0))
                else:
                    # Fallback if no manager
                    surface.blit(decorator_sprite, (0, 0))
        
        return surface
    
    def handle_event(self, action):
        """Handle input events for the button"""
        if action == "A":
            return self.activate()
        return False
    
    def activate(self):
        """Activate the button (call callback)"""
        # Set visual feedback state
        self.clicked = True
        self.was_activated = True
        self.click_frame_counter = self.click_hold_frames
        self.needs_redraw = True
        
        if self.on_click_callback:
            self.on_click_callback()
            return True
        return False
