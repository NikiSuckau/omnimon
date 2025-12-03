import pygame
import core.constants as constants
from core import runtime_globals
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow, get_font, sprite_load_percent


class WindowHorizontalMenu:
    def __init__(self, options, get_selected_index_callback):
        """
        options: List of (label, icon_surface or icon_path, [optional] amount)
        get_selected_index_callback: Function returning the current selected index
        """
        self.options = options
        self.get_index = get_selected_index_callback

        # Precompute and cache scaled icons and frames
        self._cache_surfaces()

        # Fonts
        self.font_large = get_font(constants.FONT_SIZE_SMALL)
        self.font_small = get_font(int(constants.FONT_SIZE_SMALL * 0.75))

        # Cache for draw layout
        self._last_screen_size = (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self._layout_cache = {}
        self._last_selected_index = None  # Cache for selected index
        self._sprite_cache = {}  # Cache for pre-rendered sprites
        
        # Mouse navigation variables
        self._arrow_hover = None
        self._left_arrow_rect = None
        self._right_arrow_rect = None

    def _cache_surfaces(self):
        # Pre-scale icons using the new method
        self.scaled_options = {
            "normal": [
                (label, sprite_load_percent(icon if isinstance(icon, str) else None,
                                            percent=(constants.OPTION_ICON_SIZE / constants.SCREEN_HEIGHT) * 100,
                                            keep_proportion=True,
                                            base_on="height") if isinstance(icon, str)
                 else pygame.transform.smoothscale(icon, (constants.OPTION_ICON_SIZE, constants.OPTION_ICON_SIZE)),
                 amount if len(opt) > 2 else None)
                for opt in self.options
                for label, icon, *amount in [opt]
            ],
            "small": [
                (label, sprite_load_percent(icon if isinstance(icon, str) else None,
                                            percent=(int(constants.OPTION_ICON_SIZE * 0.75) / constants.SCREEN_HEIGHT) * 100,
                                            keep_proportion=True,
                                            base_on="height") if isinstance(icon, str)
                 else pygame.transform.smoothscale(icon, (int(constants.OPTION_ICON_SIZE * 0.75), int(constants.OPTION_ICON_SIZE * 0.75))),
                 amount if len(opt) > 2 else None)
                for opt in self.options
                for label, icon, *amount in [opt]
            ]
        }

        # Pre-scale frames using the new method
        self.selection_on = sprite_load_percent(constants.SELECTION_ON_PATH, percent=(constants.OPTION_FRAME_HEIGHT / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self.selection_off = sprite_load_percent(constants.SELECTION_OFF_PATH, percent=(constants.OPTION_FRAME_HEIGHT / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")

        self.selection_on_small = pygame.transform.smoothscale(
            self.selection_on, (int(constants.OPTION_FRAME_WIDTH * 0.75), int(constants.OPTION_FRAME_HEIGHT * 0.75)))
        self.selection_off_small = pygame.transform.smoothscale(
            self.selection_off, (int(constants.OPTION_FRAME_WIDTH * 0.75), int(constants.OPTION_FRAME_HEIGHT * 0.75)))

    def _precompute_layout(self, y, spacing):
        # Only recompute if screen size or option count changes
        try:
            current_index = self.get_index()
            if current_index is None:
                current_index = 0
        except:
            current_index = 0
            
        cache_key = (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, len(self.options), y, spacing, current_index)
        if self._layout_cache.get("key") == cache_key:
            return self._layout_cache["layout"]

        layout = []
        total = len(self.options)
        if total == 1:
            center_x = constants.SCREEN_WIDTH // 2 - constants.OPTION_FRAME_WIDTH // 2
            layout.append(("normal", 0, center_x, y, True))
        elif total == 2:
            total_width = constants.OPTION_FRAME_WIDTH * 2 + spacing
            left_margin = (constants.SCREEN_WIDTH - total_width) // 2
            for i in range(total):
                offset_x = left_margin + i * (constants.OPTION_FRAME_WIDTH + spacing)
                layout.append(("normal", i, offset_x, y, i == current_index))
        elif total > 2:
            center_x = constants.SCREEN_WIDTH // 2 - constants.OPTION_FRAME_WIDTH // 2
            selected_index = current_index
            prev_index = (selected_index - 1) % total
            next_index = (selected_index + 1) % total

            # Previous (left) option
            prev_x = center_x - spacing - (self.selection_on.get_width() // 2) + (7 * constants.UI_SCALE)
            layout.append(("small", prev_index, prev_x, y + int(10 * constants.UI_SCALE), False))

            # Next (right) option
            next_x = center_x + constants.OPTION_FRAME_WIDTH - (2 * constants.UI_SCALE)
            layout.append(("small", next_index, next_x, y + int(10 * constants.UI_SCALE), False))

            # Current (center) option
            layout.append(("normal", selected_index, center_x, y, True))

        self._layout_cache["key"] = cache_key
        self._layout_cache["layout"] = layout
        return layout

    def _cache_draw_sprites(self, layout):
        """
        Pre-render sprites for the current layout to minimize per-frame rendering.
        """
        self._sprite_cache = {}
        for size, idx, draw_x, draw_y, selected in layout:
            try:
                if idx >= len(self.scaled_options[size]):
                    runtime_globals.game_console.log(f"[WindowHorizontalMenu] Warning: idx {idx} out of range for {size} options (length: {len(self.scaled_options[size])})")
                    continue
                    
                label, icon, amount = self.scaled_options[size][idx]
                frame = (
                    self.selection_on if selected else self.selection_off
                ) if size == "normal" else (
                    self.selection_on_small if selected else self.selection_off_small
                )
                font = self.font_large if size == "normal" else self.font_small

                # Render frame and icon
                frame_surface = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                blit_with_shadow(frame_surface, frame, (0, 0))
                icon_x = (frame.get_width() - icon.get_width()) // 2
                icon_y = int(20 * constants.UI_SCALE)
                blit_with_shadow(frame_surface, icon, (icon_x, icon_y))

                # Render label
                text_surface = font.render(label, True, constants.FONT_COLOR_DEFAULT)
                text_x = (frame.get_width() - text_surface.get_width()) // 2
                text_y = icon_y + icon.get_height() + int(6 * constants.UI_SCALE)
                blit_with_shadow(frame_surface, text_surface, (text_x, text_y))

                # Render amount if present
                if amount is not None:
                    if isinstance(amount, (list, tuple)):
                        amount_value = amount[0]  # Extract first value if iterable
                    else:
                        amount_value = amount

                    if amount_value > 0:  # Perform comparison only on valid numeric values
                        amount_font = self.font_small if size == "normal" else get_font(int(constants.FONT_SIZE_SMALL * 0.6))
                        amount_surface = amount_font.render(f"x{amount_value}", True, constants.FONT_COLOR_GREEN)
                        amount_x = frame.get_width() - amount_surface.get_width() - int(8 * constants.UI_SCALE)
                        amount_y = int(8 * constants.UI_SCALE)
                        blit_with_shadow(frame_surface, amount_surface, (amount_x, amount_y))

                self._sprite_cache[idx] = (frame_surface, draw_x, draw_y)
                
            except Exception as e:
                runtime_globals.game_console.log(f"[WindowHorizontalMenu] Error in _cache_draw_sprites for idx {idx}: {e}")
                continue

    def draw(self, surface: pygame.Surface, x: int, y: int, spacing: int = 16):
        try:
            selected_index = self.get_index()
            if self._last_selected_index != selected_index:
                layout = self._precompute_layout(y, spacing)
                self._cache_draw_sprites(layout)
                self._last_selected_index = selected_index

            for idx, (sprite, draw_x, draw_y) in self._sprite_cache.items():
                #surface.blit(sprite, (draw_x, draw_y))
                blit_with_cache(surface, sprite, (draw_x, draw_y))
                
            # Draw navigation arrows for multi-option menus
            if len(self.options) > 2 and runtime_globals.game_input.mouse_enabled:
                self._draw_navigation_arrows(surface)
        except Exception as e:
            runtime_globals.game_console.log(f"[WindowHorizontalMenu] Error in draw: {e}")
            # Draw a simple fallback
            font = get_font(constants.FONT_SIZE_SMALL)
            text = font.render("Menu Error", True, constants.FONT_COLOR_DEFAULT)
            surface.blit(text, (x, y))

    def draw_option(self, surface, x, y, label, icon, selected, large=True, amount=None):
        frame = (
            self.selection_on if selected else self.selection_off
        ) if large else (
            self.selection_on_small if selected else self.selection_off_small
        )

        font = self.font_large if large else self.font_small

        # Draw frame
        blit_with_shadow(surface, frame, (int(x), int(y)))

        # Draw icon centered in frame
        icon_x = int(x) + (frame.get_width() - icon.get_width()) // 2
        icon_y = int(y) + int(20 * constants.UI_SCALE)
        blit_with_shadow(surface, icon, (icon_x, icon_y))

        # Draw label centered under icon
        text_surface = font.render(label, True, constants.FONT_COLOR_DEFAULT)
        text_x = int(x) + (frame.get_width() - text_surface.get_width()) // 2
        text_y = icon_y + icon.get_height() + int(6 * constants.UI_SCALE)
        blit_with_shadow(surface, text_surface, (text_x, text_y))

        # Draw amount if present and valid
        if amount is not ModuleNotFoundError:
            if isinstance(amount, (list, tuple)):
                amount_value = amount[0]
            else:
                amount_value = amount

            if amount_value is None or amount_value <= 0:
                return

            amount_font = self.font_small if large else get_font(int(constants.FONT_SIZE_SMALL * 0.6))
            amount_surface = amount_font.render(f"x{amount_value}", True, constants.FONT_COLOR_GREEN)
            amount_x = int(x) + frame.get_width() - amount_surface.get_width() - int(8 * constants.UI_SCALE)
            amount_y = int(y) + int(8 * constants.UI_SCALE)
            blit_with_shadow(surface, amount_surface, (amount_x, amount_y))

    def set_option_label(self, index, new_label):
        """
        Dynamically update the label for an option at the given index.
        """
        for size in self.scaled_options:
            icon = self.scaled_options[size][index][1]
            amount = self.scaled_options[size][index][2] if len(self.scaled_options[size][index]) > 2 else None
            self.scaled_options[size][index] = (new_label, icon, amount)
        self.options[index] = (new_label, self.options[index][1]) if len(self.options[index]) == 2 else (new_label, self.options[index][1], self.options[index][2])
        # Invalidate layout and sprite cache to force redraw
        self._layout_cache.clear()
        self._sprite_cache.clear()
        self._last_selected_index = None  # <-- Add this line

    def update(self):
        """Update method for mouse hover detection and navigation"""
        if not runtime_globals.game_input.mouse_enabled:
            return
            
        try:
            mouse_x, mouse_y = runtime_globals.game_input.get_mouse_position()
            total_options = len(self.options)
            current_index = self.get_index()
            
            # If only 2 options or less, handle direct hover switching
            if total_options <= 2:
                # Calculate option rectangles based on current layout
                layout = self._precompute_layout(16, 16)  # Using default y and spacing
                
                option_rects = []
                for size, idx, draw_x, draw_y, selected in layout:
                    frame = (
                        self.selection_on if selected else self.selection_off
                    ) if size == "normal" else (
                        self.selection_on_small if selected else self.selection_off_small
                    )
                    option_rects.append((draw_x, draw_y, frame.get_width(), frame.get_height()))
                
                # Check which option is being hovered
                hovered_index = runtime_globals.game_input.is_mouse_hovering_option(option_rects)
                if hovered_index != -1 and hovered_index != current_index:
                    # Switch to hovered option - let the callback handle the actual value setting
                    self._set_hover_index(hovered_index)
                        
            elif total_options > 2:
                # For more than 2 options, handle navigation arrows
                # Calculate navigation arrow positions based on layout
                layout = self._precompute_layout(16, 16)  # Using default y and spacing
                
                # Find the main (center) option position
                center_option = None
                for size, idx, draw_x, draw_y, selected in layout:
                    if selected and size == "normal":
                        center_option = (draw_x, draw_y)
                        break
                        
                if center_option:
                    x, y = center_option
                    arrow_size = int(20 * constants.UI_SCALE)
                    
                    # Left arrow (previous) - positioned to the left of center option
                    left_arrow_rect = (
                        x - int(30 * constants.UI_SCALE), 
                        y + int(20 * constants.UI_SCALE), 
                        arrow_size, 
                        arrow_size
                    )
                    
                    # Right arrow (next) - positioned to the right of center option
                    right_arrow_rect = (
                        x + constants.OPTION_FRAME_WIDTH + int(10 * constants.UI_SCALE), 
                        y + int(20 * constants.UI_SCALE), 
                        arrow_size, 
                        arrow_size
                    )
                    
                    # Check if mouse is hovering over navigation arrows
                    if runtime_globals.game_input.is_mouse_in_rect(left_arrow_rect):
                        self._arrow_hover = "left"
                    elif runtime_globals.game_input.is_mouse_in_rect(right_arrow_rect):
                        self._arrow_hover = "right"
                    else:
                        self._arrow_hover = None
                        
                    # Store arrow positions for drawing
                    self._left_arrow_rect = left_arrow_rect
                    self._right_arrow_rect = right_arrow_rect
        except Exception as e:
            runtime_globals.game_console.log(f"[WindowHorizontalMenu] Error in update: {e}")

    def _set_hover_index(self, new_index):
        """Set the hover index - this is a generic helper that can be overridden by specific scenes"""
        try:
            # This is a generic implementation - scenes should override this or provide specific logic
            # For now, we'll try to detect which global variable to update based on common patterns
            if hasattr(runtime_globals, 'food_index') and 'food' in str(self.get_index).lower():
                runtime_globals.food_index = new_index
            elif hasattr(runtime_globals, 'training_index') and 'training' in str(self.get_index).lower():
                runtime_globals.training_index = new_index
            elif hasattr(runtime_globals, 'battle_index'):
                # This is more complex as battle_index is a dict
                # For now, just skip this case
                pass
            else:
                # Default fallback - try to find a global variable that matches
                if hasattr(runtime_globals, 'food_index'):
                    runtime_globals.food_index = new_index
        except Exception as e:
            runtime_globals.game_console.log(f"[WindowHorizontalMenu] Error in _set_hover_index: {e}")

    def handle_mouse_click(self, mouse_pos):
        """Handle mouse clicks on navigation arrows for multi-option menus"""
        if not runtime_globals.game_input.mouse_enabled or len(self.options) <= 2:
            return False
            
        # Check if click was on navigation arrows
        if hasattr(self, '_left_arrow_rect') and runtime_globals.game_input.is_mouse_in_rect(self._left_arrow_rect):
            # Navigate left (previous option)
            current_index = self.get_index()
            new_index = (current_index - 1) % len(self.options)
            self._set_hover_index(new_index)
            runtime_globals.game_sound.play("menu")
            return True
            
        if hasattr(self, '_right_arrow_rect') and runtime_globals.game_input.is_mouse_in_rect(self._right_arrow_rect):
            # Navigate right (next option)
            current_index = self.get_index()
            new_index = (current_index + 1) % len(self.options)
            self._set_hover_index(new_index)
            runtime_globals.game_sound.play("menu")
            return True
            
        return False

    def _draw_navigation_arrows(self, surface):
        """Draw navigation arrows for multi-option menus"""
        if not hasattr(self, '_left_arrow_rect') or not hasattr(self, '_right_arrow_rect'):
            return
            
        arrow_color = constants.FONT_COLOR_BLUE if hasattr(self, '_arrow_hover') else constants.FONT_COLOR_GRAY
        hover_alpha = 128 if hasattr(self, '_arrow_hover') else 64
        
        # Create arrow surfaces with transparency
        arrow_surface = pygame.Surface((int(20 * constants.UI_SCALE), int(20 * constants.UI_SCALE)), pygame.SRCALPHA)
        
        # Draw left arrow
        if hasattr(self, '_arrow_hover') and self._arrow_hover == "left":
            arrow_surface.set_alpha(255)
            color = constants.FONT_COLOR_BLUE
        else:
            arrow_surface.set_alpha(hover_alpha)
            color = constants.FONT_COLOR_GRAY
            
        # Simple triangle pointing left
        points = [
            (int(15 * constants.UI_SCALE), int(5 * constants.UI_SCALE)),   # top right
            (int(5 * constants.UI_SCALE), int(10 * constants.UI_SCALE)),   # left point
            (int(15 * constants.UI_SCALE), int(15 * constants.UI_SCALE))   # bottom right
        ]
        pygame.draw.polygon(arrow_surface, color, points)
        surface.blit(arrow_surface, (self._left_arrow_rect[0], self._left_arrow_rect[1]))
        
        # Draw right arrow
        arrow_surface.fill((0, 0, 0, 0))  # Clear surface
        if hasattr(self, '_arrow_hover') and self._arrow_hover == "right":
            arrow_surface.set_alpha(255)
            color = constants.FONT_COLOR_BLUE
        else:
            arrow_surface.set_alpha(hover_alpha)
            color = constants.FONT_COLOR_GRAY
            
        # Simple triangle pointing right
        points = [
            (int(5 * constants.UI_SCALE), int(5 * constants.UI_SCALE)),    # top left
            (int(15 * constants.UI_SCALE), int(10 * constants.UI_SCALE)),  # right point
            (int(5 * constants.UI_SCALE), int(15 * constants.UI_SCALE))    # bottom left
        ]
        pygame.draw.polygon(arrow_surface, color, points)
        surface.blit(arrow_surface, (self._right_arrow_rect[0], self._right_arrow_rect[1]))

    def _draw_navigation_arrows(self, surface):
        """Draw semi-transparent navigation arrows for multi-option menus"""
        if not hasattr(self, '_left_arrow_rect') or not hasattr(self, '_right_arrow_rect'):
            return
            
        arrow_color = constants.FONT_COLOR_BLUE if hasattr(self, '_arrow_hover') else constants.FONT_COLOR_GRAY
        hover_alpha = 180 if hasattr(self, '_arrow_hover') else 120
        
        # Left arrow (◀)
        left_rect = self._left_arrow_rect
        arrow_surface = pygame.Surface((left_rect[2], left_rect[3]), pygame.SRCALPHA)
        arrow_color_with_alpha = (*arrow_color[:3], hover_alpha if self._arrow_hover == "left" else 120)
        
        # Draw left arrow triangle
        points = [
            (left_rect[2] - 5, 5),  # top right
            (5, left_rect[3] // 2),  # middle left  
            (left_rect[2] - 5, left_rect[3] - 5)  # bottom right
        ]
        pygame.draw.polygon(arrow_surface, arrow_color_with_alpha[:3], points)
        arrow_surface.set_alpha(arrow_color_with_alpha[3])
        surface.blit(arrow_surface, (left_rect[0], left_rect[1]))
        
        # Right arrow (▶)
        right_rect = self._right_arrow_rect
        arrow_surface = pygame.Surface((right_rect[2], right_rect[3]), pygame.SRCALPHA)
        arrow_color_with_alpha = (*arrow_color[:3], hover_alpha if self._arrow_hover == "right" else 120)
        
        # Draw right arrow triangle
        points = [
            (5, 5),  # top left
            (right_rect[2] - 5, right_rect[3] // 2),  # middle right
            (5, right_rect[3] - 5)  # bottom left
        ]
        pygame.draw.polygon(arrow_surface, arrow_color_with_alpha[:3], points)
        arrow_surface.set_alpha(arrow_color_with_alpha[3])
        surface.blit(arrow_surface, (right_rect[0], right_rect[1]))
