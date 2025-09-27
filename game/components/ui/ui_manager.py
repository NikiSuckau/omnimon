"""
UI Manager - Core component for handling UI scaling, themes, focus, and event management
"""
import math
import pygame
from components.ui.ui_constants import *
from core import runtime_globals
from core.utils.pygame_utils import blit_with_cache
import game.core.constants as constants

DEBUG_SCALE = False  # Set to True to enable detailed scaling debug logs

class UIManager:
    def __init__(self, theme="PURPLE"):
        self.screen_size = pygame.display.get_surface().get_size()
        self.ui_scale = self.determine_scale()
        self.components = []
        self.focusable_components = []
        self.focused_index = -1
        self.theme = theme
        self.animation_components = []
        self.cached_background = None
        
        # Calculate actual UI dimensions and offset
        self.ui_width, self.ui_height = self.get_scaled_resolution()
        self.ui_offset_x, self.ui_offset_y = self.get_ui_offset()
        
        # Global highlight system
        self.highlight_anim_start = 0
        self.highlight_anim_duration = 150  # ms - fast animation
        self.highlight_animating = False
        self.highlight_start_rect = None
        self.highlight_target_rect = None
        self.highlight_current_rect = None
        self.highlight_visible = True  # Can be hidden during drag
        
        # Mouse tracking
        self.last_mouse_pos = (0, 0)
        self.mouse_over_component = None
        self.mouse_over_sub_rect = None
        
        # Navigation mode tracking
        self.keyboard_navigation_mode = False  # True when using keyboard, False when using mouse
        self.last_keyboard_action_time = 0
        self.keyboard_timeout = 2000  # ms - after this time, switch back to mouse mode
        
        # Tooltip system
        self.active_tooltip = None
        
        # Color animation system - smooth interpolation
        self.is_animating_colors = False
        self.color_animation_frame_counter = 0
        self.color_animation_total_frames = constants.FRAME_RATE  # Exactly 1 second worth of frames
        self.color_animation_redraw_interval = max(1, constants.FRAME_RATE // 20)  # Redraw every ~20th of a second for smoothness, considering frame rate
        self.color_animation_source_theme = None
        self.color_animation_target_theme = None
        self.color_animation_callback = None
        self.current_animated_colors = None
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Initialized with {self.ui_scale}x scale, theme {theme}")
            runtime_globals.game_console.log(f"[UIManager] UI Resolution: {self.get_scaled_resolution()}, Screen: {self.screen_size}")
            runtime_globals.game_console.log(f"[UIManager] UI Offset: {self.get_ui_offset()}")
        
    def determine_scale(self):
        """Determine integer UI scale based on screen resolution"""
        width, height = self.screen_size
        min_dimension = min(width, height)
        
        # Integer scaling: 1x=240, 2x=480, 3x=720, 4x=960, etc.
        ui_scale = max(1, min_dimension // BASE_RESOLUTION)
        
        return ui_scale
    
    def get_scaled_resolution(self):
        """Get the UI resolution (always 240x240 * scale)"""
        scaled_size = BASE_RESOLUTION * self.ui_scale
        return (scaled_size, scaled_size)
    
    def get_ui_offset(self):
        """Get the offset to center the UI on screen"""
        scaled_width, scaled_height = self.get_scaled_resolution()
        offset_x = (self.screen_size[0] - scaled_width) // 2
        offset_y = (self.screen_size[1] - scaled_height) // 2
        return (offset_x, offset_y)
    
    def scale_value(self, base_value):
        """Scale a base value according to current UI scale"""
        scaled_value = base_value * self.ui_scale
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] scale_value: {base_value} -> {scaled_value} (scale: {self.ui_scale})")
        return scaled_value
        
    def scale_position(self, base_x, base_y):
        """Scale base position coordinates to actual screen positions"""
        scaled_pos = (
            self.ui_offset_x + (base_x * self.ui_scale),
            self.ui_offset_y + (base_y * self.ui_scale)
        )
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] scale_position: ({base_x}, {base_y}) -> {scaled_pos} (offset: {self.ui_offset_x}, {self.ui_offset_y})")
        return scaled_pos
    
    def scale_size(self, base_width, base_height):
        """Scale base size to actual screen size"""
        scaled_size = (base_width * self.ui_scale, base_height * self.ui_scale)
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] scale_size: ({base_width}, {base_height}) -> {scaled_size}")
        return scaled_size
    
    def scale_rect(self, base_rect):
        """Scale a base rect to actual screen rect"""
        scaled_x, scaled_y = self.scale_position(base_rect.x, base_rect.y)
        scaled_w, scaled_h = self.scale_size(base_rect.width, base_rect.height)
        scaled_rect = pygame.Rect(scaled_x, scaled_y, scaled_w, scaled_h)
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] scale_rect: {base_rect} -> {scaled_rect}")
        return scaled_rect
    
    def unscale_position(self, screen_x, screen_y):
        """Convert screen position back to base UI coordinates"""
        base_x = (screen_x - self.ui_offset_x) // self.ui_scale
        base_y = (screen_y - self.ui_offset_y) // self.ui_scale
        return (base_x, base_y)
            
    def get_border_size(self):
        """Get border size for current UI scale"""
        return BORDER_SIZES.get(self.ui_scale, 2)
        
    def get_title_font_size(self):
        """Get title font size for current UI scale"""
        font_size = TITLE_FONT_SIZES.get(self.ui_scale, 24)
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] get_title_font_size: {font_size} (scale: {self.ui_scale})")
        return font_size
        
    def get_text_font_size(self):
        """Get text font size for current UI scale"""
        font_size = TEXT_FONT_SIZES.get(self.ui_scale, 16)
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] get_text_font_size: {font_size} (scale: {self.ui_scale})")
        return font_size
        
    def get_spacing_value(self):
        """Get spacing value for current UI scale"""
        return SPACING_VALUES.get(self.ui_scale, 1)
    
    def get_sprite_scale(self):
        """Get the sprite scale index for current UI scale"""
        sprite_scale = SPRITE_SCALE_MAP.get(self.ui_scale, 1)
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] get_sprite_scale: {sprite_scale} (ui_scale: {self.ui_scale})")
        return sprite_scale
    
    def set_theme(self, theme):
        self.theme = theme
        # Mark all components for redraw
        for component in self.components:
            component.needs_redraw = True
        
    def get_theme_colors(self):
        """Return background, foreground, and highlight colors for current theme"""
        # If color animation is active, return interpolated colors
        if self.is_animating_colors and self.current_animated_colors:
            return self.current_animated_colors
            
        if self.theme == "PURPLE":
            return {"bg": PURPLE_DARK, "fg": PURPLE, "highlight": PURPLE_LIGHT, "black": BLACK, "grey": GREY}
        elif self.theme == "GREEN":
            return {"bg": GREEN_DARK, "fg": GREEN, "highlight": GREEN_LIGHT, "black": BLACK, "grey": GREY}
        elif self.theme == "BLUE":
            return {"bg": BLUE_DARK, "fg": BLUE, "highlight": BLUE_LIGHT, "black": BLACK, "grey": GREY}
        elif self.theme == "YELLOW":
            return {"bg": YELLOW_DARK, "fg": YELLOW, "highlight": YELLOW_LIGHT, "black": BLACK, "grey": GREY}
        elif self.theme == "RED":
            return {"bg": RED_DARK, "fg": RED, "highlight": RED_LIGHT, "black": BLACK, "grey": GREY}
        return {"bg": BLACK, "fg": GREY, "highlight": GREY, "black": BLACK, "grey": GREY}
    
    def start_color_animation(self, target_theme, callback=None):
        """Start color animation from current theme to target theme"""
        if self.is_animating_colors:
            # Already animating, finish current animation first
            self.finish_color_animation()
        
        self.is_animating_colors = True
        self.color_animation_frame_counter = 0
        self.color_animation_source_theme = self.theme
        self.color_animation_target_theme = target_theme
        self.color_animation_callback = callback
        
        # Initialize current animated colors to source theme
        self.current_animated_colors = self._get_theme_colors_by_name(self.color_animation_source_theme)
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Started color animation from {self.theme} to {target_theme}")
    
    def update_color_animation(self):
        """Update color animation progress with smooth color interpolation"""
        if not self.is_animating_colors:
            return False
            
        self.color_animation_frame_counter += 1
        
        # Only update colors every N frames to save performance (but still smooth)
        if self.color_animation_frame_counter % self.color_animation_redraw_interval == 0:
            # Calculate interpolation progress (0.0 to 1.0)
            progress = min(1.0, self.color_animation_frame_counter / self.color_animation_total_frames)
            
            # Get source and target color dictionaries
            source_colors = self._get_theme_colors_by_name(self.color_animation_source_theme)
            target_colors = self._get_theme_colors_by_name(self.color_animation_target_theme)
            
            # Interpolate each color channel
            self.current_animated_colors = {}
            for color_key in source_colors:
                self.current_animated_colors[color_key] = self._interpolate_color(
                    source_colors[color_key], 
                    target_colors[color_key], 
                    progress
                )
            
            # Mark all components for redraw
            for component in self.components:
                component.needs_redraw = True
        
        # Check if animation should end (after exactly 1 second based on frame rate)
        if self.color_animation_frame_counter >= self.color_animation_total_frames:
            self.finish_color_animation()
            return True
            
        return False
    
    def _interpolate_color(self, color1, color2, progress):
        """Interpolate between two RGB colors based on progress (0.0 to 1.0)"""
        if len(color1) >= 3 and len(color2) >= 3:
            r = int(color1[0] + (color2[0] - color1[0]) * progress)
            g = int(color1[1] + (color2[1] - color1[1]) * progress)
            b = int(color1[2] + (color2[2] - color1[2]) * progress)
            
            # Handle alpha channel if present
            if len(color1) >= 4 and len(color2) >= 4:
                a = int(color1[3] + (color2[3] - color1[3]) * progress)
                return (r, g, b, a)
            else:
                return (r, g, b)
        else:
            # Fallback for malformed colors
            return color2 if progress > 0.5 else color1
    
    def finish_color_animation(self):
        """Complete the color animation and switch to target theme"""
        if not self.is_animating_colors:
            return
            
        # Set final theme
        final_theme = self.color_animation_target_theme
        self.set_theme(final_theme)
        
        # Reset animation state
        self.is_animating_colors = False
        self.color_animation_frame_counter = 0
        self.current_animated_colors = None
        
        # Call callback if provided
        if self.color_animation_callback:
            self.color_animation_callback()
            self.color_animation_callback = None
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Finished color animation, now using theme {final_theme}")
    
    def _get_theme_colors_by_name(self, theme_name):
        """Get theme colors by theme name (internal helper)"""
        if theme_name == "PURPLE":
            return {"bg": PURPLE_DARK, "fg": PURPLE, "highlight": PURPLE_LIGHT, "black": BLACK, "grey": GREY}
        elif theme_name == "GREEN":
            return {"bg": GREEN_DARK, "fg": GREEN, "highlight": GREEN_LIGHT, "black": BLACK, "grey": GREY}
        elif theme_name == "BLUE":
            return {"bg": BLUE_DARK, "fg": BLUE, "highlight": BLUE_LIGHT, "black": BLACK, "grey": GREY}
        elif theme_name == "YELLOW":
            return {"bg": YELLOW_DARK, "fg": YELLOW, "highlight": YELLOW_LIGHT, "black": BLACK, "grey": GREY}
        elif theme_name == "RED":
            return {"bg": RED_DARK, "fg": RED, "highlight": RED_LIGHT, "black": BLACK, "grey": GREY}
        return {"bg": BLACK, "fg": GREY, "highlight": GREY, "black": BLACK, "grey": GREY}

    def add_component(self, component):
        """Add a component to the UI manager and scale its position/size"""
        self.components.append(component)
        component.manager = self
        
        # Scale the component's position and size from base coordinates to screen coordinates
        base_rect = component.rect.copy()
        component.base_rect = base_rect  # Store original base coordinates
        component.rect = self.scale_rect(base_rect)  # Scale to screen coordinates
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Added {component.__class__.__name__}: base={base_rect} -> screen={component.rect}")
        
        # Call component's manager set callback if it exists (after base_rect is set)
        if hasattr(component, 'on_manager_set'):
            component.on_manager_set()
        
        # Add to focusable list if the component is focusable
        if hasattr(component, "focusable") and component.focusable:
            self.focusable_components.append(component)
            
            # If this is the first focusable component, focus it
            if len(self.focusable_components) == 1 and self.focused_index == -1:
                self.focused_index = 0
                component.focused = True
                component.needs_redraw = True
                if hasattr(component, 'on_focus_gained'):
                    component.on_focus_gained()
        
        return component
        
    def get_next_visible_focusable(self, start_index):
        """Get the next visible focusable component index"""
        if not self.focusable_components:
            return -1
            
        total_components = len(self.focusable_components)
        for i in range(1, total_components + 1):
            next_index = (start_index + i) % total_components
            component = self.focusable_components[next_index]
            if not hasattr(component, 'visible') or component.visible:
                return next_index
        return -1
    
    def get_prev_visible_focusable(self, start_index):
        """Get the previous visible focusable component index"""
        if not self.focusable_components:
            return -1
            
        total_components = len(self.focusable_components)
        for i in range(1, total_components + 1):
            prev_index = (start_index - i) % total_components
            component = self.focusable_components[prev_index]
            if not hasattr(component, 'visible') or component.visible:
                return prev_index
        return -1
        
    def focus_next(self):
        if not self.focusable_components:
            return
            
        # Enter keyboard navigation mode
        self.keyboard_navigation_mode = True
        self.last_keyboard_action_time = pygame.time.get_ticks()
        self.highlight_visible = True
        
        # Find next visible focusable component
        current_index = self.focused_index if self.focused_index >= 0 else -1
        next_index = self.get_next_visible_focusable(current_index)
        
        if next_index == -1:
            return  # No visible components found
            
        # Get old and new component rects for highlight animation
        old_rect = None
        if self.focused_index >= 0:
            old_component = self.focusable_components[self.focused_index]
            old_component.focused = False
            old_component.needs_redraw = True
            if hasattr(old_component, 'on_focus_lost'):
                old_component.on_focus_lost()
            old_rect = old_component.rect
            
        self.focused_index = next_index
        new_component = self.focusable_components[self.focused_index]
        new_component.focused = True
        new_component.needs_redraw = True
        if hasattr(new_component, 'on_focus_gained'):
            new_component.on_focus_gained()
            
        # Get target rect - use sub-component if available
        target_rect = new_component.rect
        if hasattr(new_component, 'get_focused_sub_rect'):
            sub_rect = new_component.get_focused_sub_rect()
            target_rect = sub_rect
            
        # Start global highlight animation
        self.start_global_highlight_animation(old_rect, target_rect)
        
    def focus_prev(self):
        if not self.focusable_components:
            return
            
        # Enter keyboard navigation mode
        self.keyboard_navigation_mode = True
        self.last_keyboard_action_time = pygame.time.get_ticks()
        self.highlight_visible = True
        
        # Find previous visible focusable component
        current_index = self.focused_index if self.focused_index >= 0 else 0
        prev_index = self.get_prev_visible_focusable(current_index)
        
        if prev_index == -1:
            return  # No visible components found
            
        # Get old and new component rects for highlight animation
        old_rect = None
        if self.focused_index >= 0:
            old_component = self.focusable_components[self.focused_index]
            old_component.focused = False
            old_component.needs_redraw = True
            if hasattr(old_component, 'on_focus_lost'):
                old_component.on_focus_lost()
            old_rect = old_component.rect
            
        self.focused_index = prev_index
        new_component = self.focusable_components[self.focused_index]
        new_component.focused = True
        new_component.needs_redraw = True
        if hasattr(new_component, 'on_focus_gained'):
            new_component.on_focus_gained()
            
        # Get target rect - use sub-component if available
        target_rect = new_component.rect
        if hasattr(new_component, 'get_focused_sub_rect'):
            sub_rect = new_component.get_focused_sub_rect()
            target_rect = sub_rect
            
        # Start global highlight animation
        self.start_global_highlight_animation(old_rect, target_rect)
        
    def handle_event(self, event):
        """Handle input events (keyboard, joystick, mouse)"""

        if self.active_tooltip:
            return True
        
        # Handle mouse events with proper coordinate conversion
        if hasattr(event, 'type') and event.type == pygame.MOUSEMOTION:
            # Convert screen position to base UI coordinates for mouse handling
            self.update_mouse_focus(event.pos)
        
        # Let components handle the event first (priority order)
        for component in self.components:
            if hasattr(component, 'handle_event') and component.handle_event(event):
                return True
        
        return False
    
    def update_mouse_focus(self, mouse_pos):
        """Update focus based on mouse position with sub-component support"""
        if not runtime_globals.game_input.is_mouse_enabled():
            return
        
        # Check if mouse has moved significantly (exit keyboard mode if it has)
        if self.keyboard_navigation_mode:
            mouse_moved = (abs(mouse_pos[0] - self.last_mouse_pos[0]) > 5 or 
                          abs(mouse_pos[1] - self.last_mouse_pos[1]) > 5)
            if mouse_moved:
                self.keyboard_navigation_mode = False
            else:
                # Don't update focus while in keyboard navigation mode
                return
        
        # Hide highlight during drag operations
        if hasattr(runtime_globals.game_input, 'is_dragging') and runtime_globals.game_input.is_dragging():
            self.highlight_visible = False
            return
        else:
            self.highlight_visible = True
        
        self.last_mouse_pos = mouse_pos
        
        # Find which focusable component the mouse is over
        best_component = None
        best_component_index = -1
        best_sub_rect = None
        
        for i, component in enumerate(self.focusable_components):
            # Skip invisible components
            if hasattr(component, 'visible') and not component.visible:
                continue
                
            if hasattr(component, 'rect') and component.rect.collidepoint(mouse_pos):
                # Mouse is over this component
                best_component = component
                best_component_index = i
                
                # Check if component has sub-component support
                if hasattr(component, 'get_mouse_sub_rect'):
                    sub_rect = component.get_mouse_sub_rect(mouse_pos)
                    if sub_rect:
                        best_sub_rect = sub_rect
                        # Mouse is over a valid sub-component
                    else:
                        # Mouse is over component but not over any sub-component - skip this component
                        best_component = None
                        best_component_index = -1
                        continue
                else:
                    # Use the main component rect
                    best_sub_rect = component.rect
                break
        
        # If mouse is not over any valid component, hide highlight
        if not best_component:
            if self.highlight_visible:
                self.highlight_current_rect = None
                self.highlight_visible = False
                # Also clear focus
                if self.focused_index >= 0:
                    old_component = self.focusable_components[self.focused_index]
                    old_component.focused = False
                    old_component.needs_redraw = True
                    if hasattr(old_component, 'on_focus_lost'):
                        old_component.on_focus_lost()
                    self.focused_index = -1
            return
        
        # Update focus if needed
        if best_component and self.focused_index != best_component_index:
            # Store old highlight rect for animation
            old_rect = self.highlight_current_rect
            
            # Update focus
            if self.focused_index >= 0:
                old_component = self.focusable_components[self.focused_index]
                old_component.focused = False
                old_component.needs_redraw = True
                if hasattr(old_component, 'on_focus_lost'):
                    old_component.on_focus_lost()
            
            self.focused_index = best_component_index
            best_component.focused = True
            best_component.needs_redraw = True
            if hasattr(best_component, 'on_focus_gained'):
                best_component.on_focus_gained()
            
            # Start highlight animation to sub-rect
            self.start_global_highlight_animation(old_rect, best_sub_rect)
            
        elif best_component and best_sub_rect:
            # Same component, but potentially different sub-rect
            if not self.highlight_current_rect or not self.rects_equal(self.highlight_current_rect, best_sub_rect):
                # Move highlight to new sub-rect
                old_rect = self.highlight_current_rect
                self.start_global_highlight_animation(old_rect, best_sub_rect)
        
        # Store current state
        self.mouse_over_component = best_component
        self.mouse_over_sub_rect = best_sub_rect
    
    def rects_equal(self, rect1, rect2):
        """Check if two rects are equal (within a small tolerance)"""
        if not rect1 or not rect2:
            return False
        return (abs(rect1.x - rect2.x) < 2 and abs(rect1.y - rect2.y) < 2 and
                abs(rect1.width - rect2.width) < 2 and abs(rect1.height - rect2.height) < 2)
    
    def find_nearest_component_in_direction(self, direction):
        """Find the nearest focusable component in the given direction"""
        if self.focused_index < 0 or not self.focusable_components:
            return -1
            
        current_component = self.focusable_components[self.focused_index]
        current_rect = current_component.rect
        
        # Get current focus sub-rect if available
        if hasattr(current_component, 'get_focused_sub_rect'):
            current_rect = current_component.get_focused_sub_rect() or current_rect
        
        current_center = (current_rect.centerx, current_rect.centery)
        
        best_component_index = -1
        best_distance = float('inf')
        
        for i, component in enumerate(self.focusable_components):
            if i == self.focused_index:
                continue
            
            # Skip invisible components
            if hasattr(component, 'visible') and not component.visible:
                continue
                
            target_rect = component.rect
            target_center = (target_rect.centerx, target_rect.centery)
            
            # Check if component is in the right direction
            if direction == "UP" and target_center[1] >= current_center[1]:
                continue
            elif direction == "DOWN" and target_center[1] <= current_center[1]:
                continue
            elif direction == "LEFT" and target_center[0] >= current_center[0]:
                continue
            elif direction == "RIGHT" and target_center[0] <= current_center[0]:
                continue
            
            # Calculate distance with direction preference
            dx = target_center[0] - current_center[0]
            dy = target_center[1] - current_center[1]
            
            if direction in ["UP", "DOWN"]:
                # Prefer vertical movement, penalize horizontal deviation
                primary_distance = abs(dy)
                secondary_distance = abs(dx) * 2  # Penalty for horizontal deviation
            else:  # LEFT or RIGHT
                # Prefer horizontal movement, penalize vertical deviation
                primary_distance = abs(dx)
                secondary_distance = abs(dy) * 2  # Penalty for vertical deviation
            
            total_distance = primary_distance + secondary_distance
            
            if total_distance < best_distance:
                best_distance = total_distance
                best_component_index = i
        
        return best_component_index
    
    def focus_direction(self, direction):
        """Move focus in the specified direction (UP, DOWN, LEFT, RIGHT)"""
        if not self.focusable_components:
            return False
        
        # Check if currently focused component is still visible
        if self.focused_index >= 0:
            current_component = self.focusable_components[self.focused_index]
            if hasattr(current_component, 'visible') and not current_component.visible:
                # Current component is invisible, clear focus and find next visible one
                current_component.focused = False
                current_component.needs_redraw = True
                if hasattr(current_component, 'on_focus_lost'):
                    current_component.on_focus_lost()
                self.focused_index = -1
            
        # Enter keyboard navigation mode and preserve current focus
        self.keyboard_navigation_mode = True
        self.last_keyboard_action_time = pygame.time.get_ticks()
        self.highlight_visible = True
        
        # If no component is currently focused, focus the first visible one
        if self.focused_index < 0:
            first_visible = self.get_next_visible_focusable(-1)
            if first_visible == -1:
                return False  # No visible components
                
            self.focused_index = first_visible
            component = self.focusable_components[first_visible]
            component.focused = True
            component.needs_redraw = True
            if hasattr(component, 'on_focus_gained'):
                component.on_focus_gained()
            
            # Get target rect - use sub-component if available
            target_rect = component.rect
            if hasattr(component, 'get_focused_sub_rect'):
                sub_rect = component.get_focused_sub_rect()
                target_rect = sub_rect
                self.highlight_current_rect = None if not sub_rect else target_rect.copy()
            
            self.highlight_current_rect = target_rect.copy() if target_rect else None
            return True
            
        new_index = self.find_nearest_component_in_direction(direction)
        if new_index >= 0 and new_index != self.focused_index:
            # Store old highlight rect
            old_rect = self.highlight_current_rect
            
            # Update focus
            if self.focused_index >= 0:
                old_component = self.focusable_components[self.focused_index]
                old_component.focused = False
                old_component.needs_redraw = True
                if hasattr(old_component, 'on_focus_lost'):
                    old_component.on_focus_lost()
            
            self.focused_index = new_index
            new_component = self.focusable_components[self.focused_index]
            new_component.focused = True
            new_component.needs_redraw = True
            
            # Get target rect - use sub-component if available
            target_rect = new_component.rect
            if hasattr(new_component, 'get_focused_sub_rect'):
                sub_rect = new_component.get_focused_sub_rect()
                target_rect = sub_rect
            
            if hasattr(new_component, 'on_focus_gained'):
                new_component.on_focus_gained()
            
            # Start highlight animation
            self.start_global_highlight_animation(old_rect, target_rect)
            return True
        
        return False
    
    def rects_equal(self, rect1, rect2):
        """Check if two rects are equal (within a small tolerance)"""
        if not rect1 or not rect2:
            return False
        return (abs(rect1.x - rect2.x) < 2 and abs(rect1.y - rect2.y) < 2 and
                abs(rect1.width - rect2.width) < 2 and abs(rect1.height - rect2.height) < 2)
    
    def handle_input_action(self, action):
        """Handle input actions and route to appropriate components"""

        # Close tooltip on any other input (except mouse movement)
        if self.active_tooltip:
            self.hide_tooltip()
            return True

        # Handle mouse clicks differently from keyboard actions
        if action == "LCLICK":
            # For mouse clicks, find the component under the mouse and handle it there
            if hasattr(self, '_input_manager'):
                mouse_pos = self._input_manager.get_mouse_position()
                
                # Check components in reverse order (top to bottom) for mouse clicks
                for component in reversed(self.components):
                    # Skip invisible components
                    if hasattr(component, 'visible') and not component.visible:
                        continue
                        
                    if hasattr(component, 'rect') and component.rect.collidepoint(mouse_pos):
                        # First try explicit mouse click handler
                        if hasattr(component, 'handle_mouse_click'):
                            result = component.handle_mouse_click(mouse_pos, action)
                            if result:
                                # Update focus to this component if it's focusable and handled the click
                                if hasattr(component, 'focusable') and component.focusable:
                                    try:
                                        new_focus_index = self.focusable_components.index(component)
                                        if new_focus_index != self.focused_index:
                                            # Update focus
                                            if self.focused_index >= 0:
                                                old_component = self.focusable_components[self.focused_index]
                                                old_component.focused = False
                                                old_component.needs_redraw = True
                                                if hasattr(old_component, 'on_focus_lost'):
                                                    old_component.on_focus_lost()
                                        
                                        self.focused_index = new_focus_index
                                        component.focused = True
                                        component.needs_redraw = True
                                        if hasattr(component, 'on_focus_gained'):
                                            component.on_focus_gained()
                                    except ValueError:
                                        # Component not in focusable list, that's fine
                                        pass
                            return True
                        
                        # If no explicit handler, try standard focus and activation for focusable components
                        elif hasattr(component, 'focusable') and component.focusable:
                            try:
                                new_focus_index = self.focusable_components.index(component)
                                
                                # Update focus if needed
                                if new_focus_index != self.focused_index:
                                    if self.focused_index >= 0:
                                        old_component = self.focusable_components[self.focused_index]
                                        old_component.focused = False
                                        old_component.needs_redraw = True
                                        if hasattr(old_component, 'on_focus_lost'):
                                            old_component.on_focus_lost()
                                    
                                    self.focused_index = new_focus_index
                                    component.focused = True
                                    component.needs_redraw = True
                                    if hasattr(component, 'on_focus_gained'):
                                        component.on_focus_gained()
                                
                                # Activate the component (same as pressing A)
                                if hasattr(component, 'handle_event'):
                                    result = component.handle_event("A")
                                    if result:
                                        return True
                                elif hasattr(component, 'activate'):
                                    result = component.activate()
                                    if result:
                                        return True
                                elif hasattr(component, 'on_activate'):
                                    result = component.on_activate()
                                    if result:
                                        return True
                                
                                return True  # We handled the focus change even if activation didn't work
                                
                            except ValueError:
                                # Component not in focusable list, continue to next component
                                continue
                
                # If no component handled the mouse click, let it fall through
                return False
            else:
                # No input manager available, fall back to focused component behavior
                action = "A"  # Treat as keyboard action
        elif action == "RCLICK":
            # Similar handling for right clicks
            if hasattr(self, '_input_manager'):
                mouse_pos = self._input_manager.get_mouse_position()
                
                # Check components in reverse order (top to bottom) for mouse clicks
                for component in reversed(self.components):
                    # Skip invisible components
                    if hasattr(component, 'visible') and not component.visible:
                        continue
                        
                    if hasattr(component, 'handle_mouse_click') and hasattr(component, 'rect'):
                        if component.rect.collidepoint(mouse_pos):
                            return component.handle_mouse_click(mouse_pos, action)
                    elif hasattr(component, 'rect') and component.rect.collidepoint(mouse_pos):
                        # For right click, just focus without activating
                        if hasattr(component, 'focusable') and component.focusable:
                            try:
                                new_focus_index = self.focusable_components.index(component)
                                if new_focus_index != self.focused_index:
                                    if self.focused_index >= 0:
                                        old_component = self.focusable_components[self.focused_index]
                                        old_component.focused = False
                                        old_component.needs_redraw = True
                                        if hasattr(old_component, 'on_focus_lost'):
                                            old_component.on_focus_lost()
                                    
                                    self.focused_index = new_focus_index
                                    component.focused = True
                                    component.needs_redraw = True
                                    if hasattr(component, 'on_focus_gained'):
                                        component.on_focus_gained()
                            except ValueError:
                                continue
                
                # If no component handled the mouse click, let it fall through
                return False
            else:
                # No input manager available, treat as keyboard action
                action = "B"

        # Handle tooltip activation for keyboard A button
        if action == "A":
            if self.focused_index >= 0:
                focused_component = self.focusable_components[self.focused_index]
                if hasattr(focused_component, 'tooltip_text') and focused_component.tooltip_text:
                    # Toggle tooltip - hide if showing, show if hidden
                    if self.active_tooltip:
                        self.hide_tooltip()
                    else:
                        self.show_tooltip(focused_component.tooltip_text)
                    return True
            
        # First, let the focused component handle the action
        if self.focused_index >= 0:
            focused_component = self.focusable_components[self.focused_index]
            if hasattr(focused_component, 'handle_event'):
                if focused_component.handle_event(action):
                    return True
    
        # If focused component didn't handle it, try global UI actions
        # Scroll actions
        if action in ["SCROLL_UP", "SCROLL_DOWN"]:
            return self.handle_scroll(action)
        
        # Drag actions
        elif action in ["DRAG_START", "DRAG_MOTION", "DRAG_END"]:
            return self.handle_drag(action)
        
        # Global navigation actions (only if no component handled them)
        elif action == "LEFT":
            return self.focus_direction("LEFT")
        elif action == "RIGHT":
            return self.focus_direction("RIGHT")
        elif action == "UP":
            return self.focus_direction("UP")
        elif action == "DOWN":
            return self.focus_direction("DOWN")
        elif action in ["TAB"]:  # TAB for next component
            self.focus_next()
            return True
        elif action in ["SHIFT_TAB"]:  # SHIFT+TAB for previous component
            self.focus_prev()
            return True
        
        # These are only fallbacks if no focused component handled them
        elif action == "A":
            return self.activate_focused_component()
            
        return False
    
    def handle_mouse_click(self, action):
        """Handle mouse click on components"""
        if not hasattr(self, '_input_manager'):
            return False
            
        mouse_pos = self._input_manager.get_mouse_position()
        
        # Check components in reverse order (top to bottom) using screen coordinates
        for component in reversed(self.components):
            # Skip invisible components
            if hasattr(component, 'visible') and not component.visible:
                continue
                
            if hasattr(component, 'handle_mouse_click') and hasattr(component, 'rect'):
                if component.rect.collidepoint(mouse_pos):
                    return component.handle_mouse_click(mouse_pos, action)
        
        return False
    
    def handle_scroll(self, action):
        """Handle scroll events on focused or hovered components"""
        # First try the focused component
        if self.focused_index >= 0:
            focused_component = self.focusable_components[self.focused_index]
            if hasattr(focused_component, 'handle_scroll'):
                if focused_component.handle_scroll(action):
                    return True
        
        # If no focused component handled it, try mouse hover
        if hasattr(self, '_input_manager'):
            mouse_pos = self._input_manager.get_mouse_position()
            for component in self.components:
                if hasattr(component, 'handle_scroll') and hasattr(component, 'rect'):
                    if component.rect.collidepoint(mouse_pos):
                        return component.handle_scroll(action)
        
        return False
    
    def handle_drag(self, action):
        """Handle drag events"""
        if not hasattr(self, '_input_manager'):
            return False
            
        # Route to components that support dragging
        for component in self.components:
            if hasattr(component, 'handle_drag'):
                if component.handle_drag(action, self._input_manager):
                    return True
        
        return False
    
    def activate_focused_component(self):
        """Activate the currently focused component"""
        if self.focused_index >= 0:
            focused_component = self.focusable_components[self.focused_index]
            
            # Hide any existing tooltip first
            self.hide_tooltip()
            
            # Check if component has a tooltip and show it
            if hasattr(focused_component, 'tooltip_text') and focused_component.tooltip_text:
                self.show_tooltip(focused_component.tooltip_text)
                return True
            
            # Try the activate method first, then fall back to handle_event
            if hasattr(focused_component, 'activate'):
                return focused_component.activate()
            elif hasattr(focused_component, 'on_activate'):
                return focused_component.on_activate()
            elif hasattr(focused_component, 'handle_event'):
                return focused_component.handle_event("A")
        return False
    
    def set_input_manager(self, input_manager):
        """Set the input manager reference for mouse handling"""
        self._input_manager = input_manager
        
    def start_global_highlight_animation(self, from_rect, to_rect):
        """Start global highlight animation from one rect to another"""
        if from_rect and to_rect:
            self.highlight_start_rect = from_rect.copy()
            self.highlight_target_rect = to_rect.copy()
            self.highlight_current_rect = from_rect.copy()
            self.highlight_animating = True
            self.highlight_anim_start = pygame.time.get_ticks()
        else:
            self.highlight_current_rect = to_rect.copy() if to_rect else None
            self.highlight_animating = False
            
    def update_highlight_animation(self):
        """Update the global highlight animation"""
        if not self.highlight_animating:
            return
            
        elapsed = pygame.time.get_ticks() - self.highlight_anim_start
        progress = min(1.0, elapsed / self.highlight_anim_duration)
        
        # Ease-out animation
        progress = 1 - (1 - progress) ** 3
        
        # Interpolate rectangle
        start = self.highlight_start_rect
        target = self.highlight_target_rect
        
        self.highlight_current_rect = pygame.Rect(
            int(start.x + (target.x - start.x) * progress),
            int(start.y + (target.y - start.y) * progress),
            int(start.width + (target.width - start.width) * progress),
            int(start.height + (target.height - start.height) * progress)
        )
        
        if progress >= 1.0:
            self.highlight_animating = False
            
    def show_tooltip(self, text):
        """Show a tooltip with the given text (only if activated)"""
        if not text:
            return
            
        try:
            from components.ui.simple_tooltip import Tooltip
            # Create tooltip component
            screen_size = pygame.display.get_surface().get_size()
            self.active_tooltip = Tooltip(text, screen_size[0], screen_size[1])
            self.active_tooltip.set_manager(self)  # Use set_manager to trigger scaling
            
            # Play activation sound if available
            if hasattr(runtime_globals, 'game_audio') and runtime_globals.game_audio:
                runtime_globals.game_audio.play_sound("click")
        except ImportError as e:
            if DEBUG_SCALE:
                runtime_globals.game_console.log(f"[UIManager] Error importing Tooltip: {e}")
            self.active_tooltip = None
        
    def hide_tooltip(self):
        """Hide the current tooltip"""
        self.active_tooltip = None
        
    def draw_global_highlight(self, surface):
        """Draw the global highlight if active"""
        if not self.highlight_visible or not self.highlight_current_rect:
            return
            
        colors = self.get_theme_colors()
        highlight_color = colors["highlight"]
        
        # Calculate border width and radius based on scale
        border_width = max(1, self.get_border_size())  # 2px base * scale
        border_radius = max(2, self.get_border_size())  # 2px base * scale
        
        # Draw rounded rectangle highlight
        highlight_rect = pygame.Rect(
            int(self.highlight_current_rect.x),
            int(self.highlight_current_rect.y),
            int(self.highlight_current_rect.width),
            int(self.highlight_current_rect.height)
        )
        
        # Draw the rounded border highlight
        pygame.draw.rect(
            surface,
            highlight_color,
            highlight_rect,
            width=border_width,
            border_radius=border_radius
        )
        
    def update(self):
        """Update all components (animations, etc)"""
        self.update_highlight_animation()
        
        # Update color animation
        self.update_color_animation()
        
        # Update tooltip animation
        if self.active_tooltip:
            self.active_tooltip.update()
        
        for component in self.components:
            component.update()
            
    def draw(self, surface):
        """Draw all components directly at their scaled positions"""
        # Draw all components directly to the main surface at their scaled positions
        for component in self.components:
            component.draw(surface)
            
        # Draw external border if UI is smaller than screen
        if self.ui_offset_x > 0 or self.ui_offset_y > 0:
            colors = self.get_theme_colors()
            border_color = colors["fg"]  # Use main theme color (PURPLE for PURPLE theme)
            border_size = 2  # Small 2-pixel border
            
            # Draw border around the entire UI area (external to the UI)
            ui_rect = pygame.Rect(self.ui_offset_x - border_size, self.ui_offset_y - border_size,
                                self.ui_width + 2 * border_size, self.ui_height + 2 * border_size)
            pygame.draw.rect(surface, border_color, ui_rect, width=border_size)
            
        # Draw global highlight at scaled position
        self.draw_global_highlight(surface)
        
        # Draw tooltip at scaled position
        if self.active_tooltip:
            self.active_tooltip.draw(surface)
    
    def set_focused_component(self, component):
        """Set focus to a specific component"""
        if component not in self.focusable_components:
            return False
            
        component_index = self.focusable_components.index(component)
        
        # Clear focus from current component
        if self.focused_index >= 0:
            old_component = self.focusable_components[self.focused_index]
            old_component.focused = False
            old_component.needs_redraw = True
            if hasattr(old_component, 'on_focus_lost'):
                old_component.on_focus_lost()
        
        # Set focus to new component
        self.focused_index = component_index
        component.focused = True
        component.needs_redraw = True
        if hasattr(component, 'on_focus_gained'):
            component.on_focus_gained()
            
        # Update highlight
        target_rect = component.rect
        if hasattr(component, 'get_focused_sub_rect'):
            sub_rect = component.get_focused_sub_rect()
            target_rect = sub_rect
                
        self.start_global_highlight_animation(None, target_rect)
        return True
    
    def set_mouse_mode(self):
        """Explicitly set the UI to mouse mode"""
        self.keyboard_navigation_mode = False
        self.last_keyboard_action_time = 0
        self.highlight_visible = True
        
    def load_sprite_integer_scaling(self, prefix, name, suffix=None):
        """
        Load a sprite that uses integer scaling for UI elements.
        
        Uses pattern: assets/ui/{prefix}_{name}[_{suffix}]_{scale_factor}.png
        Where scale_factor comes from the current sprite scale.
        
        Special handling for 3x UI scale: loads 2x sprite and resizes to 3x.
        
        Args:
            prefix (str): Sprite category (e.g., "Status", "Training", "Battle")
            name (str): Sprite name (e.g., "Heart", "Empty", "Energy")
            suffix (str, optional): Additional suffix (e.g., "Highlight", "Selected")
            
        Returns:
            pygame.Surface: Loaded sprite surface, or None if file not found
        """
        sprite_scale = self.get_sprite_scale()
        
        # Build filename based on pattern
        if suffix:
            filename = f"{prefix}_{name}_{suffix}_{sprite_scale}.png"
        else:
            filename = f"{prefix}_{name}_{sprite_scale}.png"
            
        filepath = f"assets/ui/{filename}"
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Loading integer-scaled sprite: {filepath} (UI scale: {self.ui_scale})")
        
        try:
            sprite = pygame.image.load(filepath)
            
            # Special case for 3x UI scale: resize 2x sprite to 3x
            if self.ui_scale == 3 and sprite_scale == 2:
                original_size = sprite.get_size()
                # Scale by 1.5x to go from 2x sprite to 3x UI scale
                scale_factor = 1.5
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                sprite = pygame.transform.scale(sprite, new_size)
                if DEBUG_SCALE:
                    runtime_globals.game_console.log(f"[UIManager] Resized 2x sprite from {original_size} to {new_size} for 3x UI scale")
            
            if DEBUG_SCALE:
                runtime_globals.game_console.log(f"[UIManager] Successfully loaded sprite: {filepath}")
            return sprite
        except pygame.error as e:
            if DEBUG_SCALE:
                runtime_globals.game_console.log(f"[UIManager] Failed to load sprite {filepath}: {e}")
            return None
    
    def load_sprite_non_integer_scaling(self, base_path, scale_factor=None):
        """
        Load a sprite that uses non-integer scaling for pets, flags, and other elements.
        
        Loads the base sprite and scales it by the provided scale factor or current UI scale.
        Used for sprites that don't have pre-scaled versions on disk.
        
        Args:
            base_path (str): Path to the base sprite file (e.g., "assets/pets/agumon.png")
            scale_factor (float, optional): Custom scale factor. If None, uses current UI scale
            
        Returns:
            pygame.Surface: Scaled sprite surface, or None if file not found
        """
        if scale_factor is None:
            scale_factor = self.scale
            
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Loading non-integer scaled sprite: {base_path} with scale {scale_factor}")
        
        try:
            # Load base sprite
            base_sprite = pygame.image.load(base_path)
            
            # If scale is 1.0, return original
            if scale_factor == 1.0:
                if DEBUG_SCALE:
                    runtime_globals.game_console.log(f"[UIManager] Returning original sprite (scale 1.0): {base_path}")
                return base_sprite
            
            # Scale the sprite
            original_size = base_sprite.get_size()
            new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
            scaled_sprite = pygame.transform.scale(base_sprite, new_size)
            
            if DEBUG_SCALE:
                runtime_globals.game_console.log(f"[UIManager] Successfully scaled sprite from {original_size} to {new_size}: {base_path}")
            return scaled_sprite
            
        except pygame.error as e:
            if DEBUG_SCALE:
                runtime_globals.game_console.log(f"[UIManager] Failed to load sprite {base_path}: {e}")
            return None
    
    # ========================================
    # Centralized Shape Drawing Methods
    # ========================================
    
    def draw_rounded_rectangle(self, surface, color, rect, border_color=None, border_width=None, border_radius=None):
        """
        Draw a rounded rectangle with optional border using scaled values.
        
        Args:
            surface: Pygame surface to draw on
            color: Fill color (RGB tuple)
            rect: Rectangle (x, y, width, height) in base coordinates
            border_color: Border color (RGB tuple), optional
            border_width: Border width in base pixels, optional (auto-scaled)
            border_radius: Border radius in base pixels, optional (auto-scaled)
        """
        # Scale the rectangle
        scaled_rect = self.scale_rect(pygame.Rect(rect))
        
        # Set defaults if not provided
        if border_radius is None:
            border_radius = self.get_border_size()
        else:
            border_radius = self.scale_value(border_radius)
            
        if border_width is None:
            border_width = self.get_border_size()
        else:
            border_width = self.scale_value(border_width)
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Drawing rounded rectangle: rect={scaled_rect}, radius={border_radius}, border_width={border_width}")
        
        # Draw border if specified
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, scaled_rect, width=border_width, border_radius=border_radius)
        
        # Draw filled rectangle
        if border_width > 0 and border_color:
            # Inset the fill rectangle by border width
            fill_rect = scaled_rect.inflate(-border_width * 2, -border_width * 2)
            fill_radius = max(0, border_radius - border_width)
        else:
            fill_rect = scaled_rect
            fill_radius = border_radius
            
        pygame.draw.rect(surface, color, fill_rect, border_radius=fill_radius)
    
    def draw_cut_corner_polygon(self, surface, color, rect, border_color=None, border_width=None, cut_corners=None, cut_size=None):
        """
        Draw a polygon with cut corners (like buttons) using scaled values.
        
        Args:
            surface: Pygame surface to draw on
            color: Fill color (RGB tuple)
            rect: Rectangle (x, y, width, height) in base coordinates
            border_color: Border color (RGB tuple), optional
            border_width: Border width in base pixels, optional (auto-scaled)
            cut_corners: Dict with keys 'tl', 'tr', 'bl', 'br' indicating which corners to cut
            cut_size: Cut size in base pixels, optional (auto-scaled)
        """
        # Scale the rectangle
        scaled_rect = self.scale_rect(pygame.Rect(rect))
        
        # Set defaults
        if cut_corners is None:
            cut_corners = {'tl': False, 'tr': False, 'bl': False, 'br': False}
        if cut_size is None:
            cut_size = self.scale_value(8)  # 8px base cut size
        else:
            cut_size = self.scale_value(cut_size)
        if border_width is None:
            border_width = self.get_border_size()
        else:
            border_width = self.scale_value(border_width)
        
        x, y, w, h = scaled_rect.x, scaled_rect.y, scaled_rect.width, scaled_rect.height
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Drawing cut corner polygon: rect={scaled_rect}, cut_size={cut_size}, corners={cut_corners}")
        
        # Build polygon points for border
        border_points = []
        
        # Top-left corner
        if cut_corners.get('tl'):
            border_points.extend([(x + cut_size, y), (x, y + cut_size)])
        else:
            border_points.append((x, y))
        
        # Bottom-left corner
        if cut_corners.get('bl'):
            border_points.extend([(x, y + h - cut_size), (x + cut_size, y + h)])
        else:
            border_points.append((x, y + h))
        
        # Bottom-right corner
        if cut_corners.get('br'):
            border_points.extend([(x + w - cut_size, y + h), (x + w, y + h - cut_size)])
        else:
            border_points.append((x + w, y + h))
        
        # Top-right corner
        if cut_corners.get('tr'):
            border_points.extend([(x + w, y + cut_size), (x + w - cut_size, y)])
        else:
            border_points.append((x + w, y))
        
        # Draw border polygon if specified
        if border_color and border_width > 0 and len(border_points) >= 3:
            pygame.draw.polygon(surface, border_color, border_points)
        
        # Build inset points for fill
        if border_width > 0 and border_color:
            inset = border_width
            fill_points = []
            
            # Top-left corner
            if cut_corners.get('tl'):
                fill_points.extend([(x + cut_size, y + inset), (x + inset, y + cut_size)])
            else:
                fill_points.append((x + inset, y + inset))
            
            # Bottom-left corner
            if cut_corners.get('bl'):
                fill_points.extend([(x + inset, y + h - cut_size - inset), (x + cut_size, y + h - inset)])
            else:
                fill_points.append((x + inset, y + h - inset))
            
            # Bottom-right corner
            if cut_corners.get('br'):
                fill_points.extend([(x + w - cut_size - inset, y + h - inset), (x + w - inset, y + h - cut_size - inset)])
            else:
                fill_points.append((x + w - inset, y + h - inset))
            
            # Top-right corner
            if cut_corners.get('tr'):
                fill_points.extend([(x + w - inset, y + cut_size), (x + w - cut_size - inset, y + inset)])
            else:
                fill_points.append((x + w - inset, y + inset))
            
            if len(fill_points) >= 3:
                pygame.draw.polygon(surface, color, fill_points)
        else:
            # No border, just draw the main polygon
            if len(border_points) >= 3:
                pygame.draw.polygon(surface, color, border_points)
    
    def draw_hexagon(self, surface, color, center, radius, border_color=None, border_width=None):
        """
        Draw a hexagon using scaled values.
        
        Args:
            surface: Pygame surface to draw on
            color: Fill color (RGB tuple)
            center: Center point (x, y) in base coordinates
            radius: Hexagon radius in base pixels (auto-scaled)
            border_color: Border color (RGB tuple), optional
            border_width: Border width in base pixels, optional (auto-scaled)
        """
        # Scale center and radius
        scaled_center = self.scale_position(center[0], center[1])
        scaled_radius = self.scale_value(radius)
        
        if border_width is None:
            border_width = self.get_border_size()
        else:
            border_width = self.scale_value(border_width)
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Drawing hexagon: center={scaled_center}, radius={scaled_radius}, border_width={border_width}")
        
        # Calculate hexagon points
        points = []
        for i in range(6):
            angle = (math.pi / 3 * i) + (math.pi / 6)  # 60 degrees * i + 30 degrees rotation
            x = scaled_center[0] + scaled_radius * math.cos(angle)
            y = scaled_center[1] + scaled_radius * math.sin(angle)
            points.append((int(x), int(y)))
        
        # Draw filled hexagon
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
        
        # Draw border if specified
        if border_color and border_width > 0 and len(points) >= 3:
            pygame.draw.polygon(surface, border_color, points, border_width)
    
    def draw_arrow_polygon(self, surface, color, rect, direction="right", border_color=None, border_width=None):
        """
        Draw an arrow polygon using scaled values.
        
        Args:
            surface: Pygame surface to draw on
            color: Fill color (RGB tuple)
            rect: Rectangle (x, y, width, height) in base coordinates defining arrow bounds
            direction: Arrow direction ("up", "down", "left", "right")
            border_color: Border color (RGB tuple), optional
            border_width: Border width in base pixels, optional (auto-scaled)
        """
        # Scale the rectangle
        scaled_rect = self.scale_rect(pygame.Rect(rect))
        
        if border_width is None:
            border_width = self.get_border_size()
        else:
            border_width = self.scale_value(border_width)
        
        x, y, w, h = scaled_rect.x, scaled_rect.y, scaled_rect.width, scaled_rect.height
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Drawing arrow polygon: rect={scaled_rect}, direction={direction}")
        
        # Calculate arrow points based on direction
        if direction == "right":
            points = [(x, y), (x + w * 0.7, y), (x + w, y + h // 2), (x + w * 0.7, y + h), (x, y + h)]
        elif direction == "left":
            points = [(x + w, y), (x + w * 0.3, y), (x, y + h // 2), (x + w * 0.3, y + h), (x + w, y + h)]
        elif direction == "up":
            points = [(x, y + h), (x, y + h * 0.3), (x + w // 2, y), (x + w, y + h * 0.3), (x + w, y + h)]
        elif direction == "down":
            points = [(x, y), (x, y + h * 0.7), (x + w // 2, y + h), (x + w, y + h * 0.7), (x + w, y)]
        else:
            # Default to right arrow
            points = [(x, y), (x + w * 0.7, y), (x + w, y + h // 2), (x + w * 0.7, y + h), (x, y + h)]
        
        # Draw filled arrow
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
        
        # Draw border if specified
        if border_color and border_width > 0 and len(points) >= 3:
            pygame.draw.polygon(surface, border_color, points, border_width)
    
    def draw_simple_rectangle(self, surface, color, rect, border_color=None, border_width=None):
        """
        Draw a simple rectangle (no rounded corners) using scaled values.
        
        Args:
            surface: Pygame surface to draw on
            color: Fill color (RGB tuple)
            rect: Rectangle (x, y, width, height) in base coordinates
            border_color: Border color (RGB tuple), optional
            border_width: Border width in base pixels, optional (auto-scaled)
        """
        # Scale the rectangle
        scaled_rect = self.scale_rect(pygame.Rect(rect))
        
        if border_width is None:
            border_width = self.get_border_size()
        else:
            border_width = self.scale_value(border_width)
        
        if DEBUG_SCALE:
            runtime_globals.game_console.log(f"[UIManager] Drawing simple rectangle: rect={scaled_rect}, border_width={border_width}")
        
        # Draw border if specified
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, scaled_rect, width=border_width)
        
        # Draw filled rectangle
        if border_width > 0 and border_color:
            # Inset the fill rectangle by border width
            fill_rect = scaled_rect.inflate(-border_width * 2, -border_width * 2)
        else:
            fill_rect = scaled_rect
            
        pygame.draw.rect(surface, color, fill_rect)
