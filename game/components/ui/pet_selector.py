"""
Pet Selector Component - Displays pets in hexagonal cells arranged horizontally
"""
import pygame
import math
from components.ui.component import UIComponent
from core import runtime_globals
from core.utils.pet_utils import get_selected_pets
from game.core.animation import PetFrame


class PetSelector(UIComponent):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        
        # Pet data
        self.pets = []
        self.enabled_pets = []  # List of pet indices that are enabled
        self.selected_pets = []  # List of pet indices that are selected
        
        # Base visual settings (will be scaled by manager)
        self.base_cell_size = 48  # Base hexagon size
        self.base_cell_padding = 4  # Base space between hexagons
        self.base_border_width = 2  # Base border width
        
        # Scaled visual settings (set in on_manager_set)
        self.cell_size = self.base_cell_size
        self.cell_padding = self.base_cell_padding
        self.border_width = self.base_border_width
        
        # State
        self.hovered_cell = -1
        self.focused_cell = -1
        self.is_interactive = False  # Can be toggled for different scenes
        
        # Layout (positions in base coordinates)
        self.cell_positions = []
        
        # Cache
        self.cached_surface = None
        self.needs_layout_update = True
        
        # Setup initial layout
        self.update_layout()
        
    def get_highlight_shape(self):
        """Return custom hexagonal highlight shape for the focused pet"""
        if not self.is_interactive or self.focused_cell < 0 or self.focused_cell >= len(self.cell_positions):
            return None
            
        # Get the focused cell position and radius
        base_center = self.cell_positions[self.focused_cell]
        radius = (self.calculated_cell_size // 2) if hasattr(self, 'calculated_cell_size') else (self.base_cell_size // 2)
        
        # Convert to screen coordinates
        if self.manager:
            screen_center = self.manager.scale_position(base_center[0], base_center[1])
            screen_center = (screen_center[0] + self.rect.x, screen_center[1] + self.rect.y)
            scaled_radius = self.manager.scale_value(radius)
        else:
            screen_center = (base_center[0] + self.rect.x, base_center[1] + self.rect.y)
            scaled_radius = radius
        
        # Calculate hexagon points for highlight (slightly larger than the pet hexagon)
        highlight_radius = scaled_radius + self.manager.scale_value(4) if self.manager else radius + 4
        points = []
        for i in range(6):
            angle = (math.pi / 3 * i) + (math.pi / 6)  # 60 degrees * i + 30 degrees rotation
            x = screen_center[0] + highlight_radius * math.cos(angle)
            y = screen_center[1] + highlight_radius * math.sin(angle)
            points.append((int(x), int(y)))
        
        return points
        
    def set_pets(self, pets):
        """Set the list of pets to display"""
        self.pets = pets[:]
        self.enabled_pets = list(range(len(pets)))  # All enabled by default
        self.selected_pets = []
        self.needs_layout_update = True
        self.needs_redraw = True
        
    def set_enabled_pets(self, enabled_pet_indices):
        """Set which pets are enabled (others will be shown as disabled)"""
        self.enabled_pets = enabled_pet_indices[:]
        self.needs_redraw = True
        
    def set_interactive(self, interactive):
        """Enable/disable interactivity (mouse hover, selection, etc.)"""
        self.is_interactive = interactive
        if not interactive:
            self.hovered_cell = -1
            self.focused_cell = -1
            
    def update_layout(self):
        """Calculate positions and sizes for all hexagonal cells in base coordinates"""
        if not self.pets:
            self.cell_positions = []
            self.needs_layout_update = False
            return
            
        # Work in base coordinates - the UI manager will handle scaling
        available_width = self.base_rect.width
        available_height = self.base_rect.height
        num_pets = len(self.pets)
        
        #runtime_globals.game_console.log(f"[PetSelector] update_layout: {num_pets} pets, available_width={available_width}, available_height={available_height}")
        
        if num_pets == 0:
            self.cell_positions = []
            self.needs_layout_update = False
            return
            
        # Step 1: Calculate maximum possible hexagon radius based on height
        # Hexagon height = 2 * radius, leave some padding
        max_radius_from_height = (available_height - 4) // 2  # 2px padding top/bottom
        
        # Step 2: Calculate hexagon spacing for touching hexagons
        # For regular pointy-top hexagons touching side by side, the distance between centers is √3 * radius ≈ 1.732 * radius
        # Total width needed = (num_pets - 1) * √3 * radius + 2 * radius
        # Simplified: total_width = radius * ((num_pets - 1) * √3 + 2)
        
        import math
        sqrt3 = math.sqrt(3)  # ≈ 1.732
        
        # Calculate maximum radius that fits all hexagons horizontally
        if num_pets == 1:
            max_radius_from_width = available_width // 2
        else:
            # total_width = radius * ((num_pets - 1) * √3 + 2)
            # radius = total_width / ((num_pets - 1) * √3 + 2)
            width_factor = (num_pets - 1) * sqrt3 + 2
            max_radius_from_width = int(available_width / width_factor)
        
        # Step 3: Choose the limiting factor (height or width)
        max_radius = min(max_radius_from_height, max_radius_from_width)
        
        # Apply minimum and maximum radius limits
        base_max_radius = 32  # Max radius limit at base scale (64x64 hexagon)
        base_min_radius = 12  # Min radius limit at base scale (24x24 hexagon)
        
        radius = min(max_radius, base_max_radius)
        radius = max(radius, base_min_radius)
        
        #runtime_globals.game_console.log(f"[PetSelector] radius calculation: max_from_height={max_radius_from_height}, max_from_width={max_radius_from_width}, final={radius} (limits: {base_min_radius}-{base_max_radius})")
        
        # Step 4: Calculate actual layout with touching hexagons
        if num_pets == 1:
            total_width = radius * 2
            center_spacing = 0
        else:
            # Use more precise floating point calculation, then round to nearest pixel
            precise_spacing = sqrt3 * radius  # ≈ 1.732 * radius
            center_spacing = round(precise_spacing)
            total_width = (num_pets - 1) * center_spacing + 2 * radius
        
        # Step 5: Calculate starting position to center the hexagon group
        # If total_width exceeds available_width, start from the edge
        if total_width <= available_width:
            start_x = (available_width - total_width) // 2 + radius  # Add radius to get to first center
        else:
            start_x = radius  # Start from left edge plus radius
        center_y = available_height // 2
        
        #runtime_globals.game_console.log(f"[PetSelector] layout: total_width={total_width}, start_x={start_x}, center_y={center_y}, center_spacing={center_spacing}")
        
        # Step 6: Calculate positions for each hexagon center
        self.cell_positions = []
        for i in range(num_pets):
            if num_pets == 1:
                cell_x = available_width // 2  # Center single hexagon
            else:
                cell_x = start_x + (i * center_spacing)
            cell_y = center_y
            self.cell_positions.append((cell_x, cell_y))
            #runtime_globals.game_console.log(f"[PetSelector] cell {i}: base_pos=({cell_x}, {cell_y})")
            
        # Debug: Show final layout bounds
        if self.cell_positions:
            leftmost = min(pos[0] for pos in self.cell_positions) - radius
            rightmost = max(pos[0] for pos in self.cell_positions) + radius
            #runtime_globals.game_console.log(f"[PetSelector] final bounds: left={leftmost}, right={rightmost}, available_width={available_width}")
            
        # Store the calculated radius for this layout (convert to diameter for compatibility)
        self.calculated_cell_size = radius * 2
        
        self.needs_layout_update = False
        self.needs_redraw = True
        

        
    def update_colors_from_theme(self):
        """Update colors based on current UI theme"""
        if self.manager:
            theme_colors = self.manager.get_theme_colors()
            # Use theme's background color for hexagon fill
            self.hexagon_color = theme_colors.get("bg", (40, 40, 80))
            # Use theme's foreground color for enabled borders  
            self.enabled_color = theme_colors.get("fg", (255, 255, 255))
            # Use grey for disabled borders
            self.disabled_color = theme_colors.get("grey", (128, 128, 128))
            # Use black for main borders
            self.border_color = theme_colors.get("black", (0, 0, 0))
            # Use theme's highlight color for selection
            self.selected_color = theme_colors.get("highlight", (255, 255, 0))
            # Create hover color as slightly brighter version of hexagon color
            self.hover_color = (
                min(255, self.hexagon_color[0] + 40),
                min(255, self.hexagon_color[1] + 40), 
                min(255, self.hexagon_color[2] + 40)
            )
            self.needs_redraw = True
            
    def on_manager_set(self):
        """Called when component is added to UI manager"""
        # Scale visual settings based on UI scale
        if self.manager:
            self.cell_size = self.manager.scale_value(self.base_cell_size)
            self.cell_padding = self.manager.scale_value(self.base_cell_padding)
            self.border_width = self.manager.scale_value(self.base_border_width)
        
        self.update_colors_from_theme()
        self.needs_layout_update = True
        
    def update(self):
        """Update component state"""
        if self.needs_layout_update:
            self.update_layout()
            
        # Update colors if theme changed
        if self.manager:
            self.update_colors_from_theme()
            
    def get_cell_at_position(self, pos):
        """Get the cell index at the given position, or -1 if none"""
        if not self.is_interactive or not self.cell_positions:
            return -1
            
        # Convert to local coordinates
        local_x = pos[0] - self.rect.x
        local_y = pos[1] - self.rect.y
        
        # Check each hexagon using distance calculation
        radius = (self.calculated_cell_size // 2) if hasattr(self, 'calculated_cell_size') else (self.base_cell_size // 2)
        if self.manager:
            scaled_radius = self.manager.scale_value(radius)
        else:
            scaled_radius = radius
            
        for i, base_pos in enumerate(self.cell_positions):
            # Convert base position to screen coordinates
            if self.manager:
                screen_pos = self.manager.scale_position(base_pos[0], base_pos[1])
            else:
                screen_pos = base_pos
                
            # Calculate distance from click to hexagon center
            dx = local_x - screen_pos[0]
            dy = local_y - screen_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            # Use a slightly smaller radius for better click detection
            if distance <= scaled_radius * 0.9:
                return i
                
        return -1
        

        
    def handle_mouse_motion(self, pos):
        """Handle mouse motion for hover effects"""
        if not self.is_interactive:
            return False
            
        old_hovered = self.hovered_cell
        self.hovered_cell = self.get_cell_at_position(pos)
        
        if old_hovered != self.hovered_cell:
            self.needs_redraw = True
            
        return self.hovered_cell != -1
        
    def handle_mouse_click(self, pos, button):
        """Handle mouse clicks for selection"""
        if not self.is_interactive:
            return False
            
        cell = self.get_cell_at_position(pos)
        if cell != -1 and cell in self.enabled_pets:
            # Toggle selection
            if cell in self.selected_pets:
                self.selected_pets.remove(cell)
            else:
                self.selected_pets.append(cell)
            self.needs_redraw = True
            return True
            
        return False
        
    def render(self):
        """Render the component using the render-based pattern"""
        if not self.pets or not self.cell_positions:
            return pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            
        # Create the surface for this component
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Get the radius for hexagons (from calculated size or fallback)
        radius = (self.calculated_cell_size // 2) if hasattr(self, 'calculated_cell_size') else (self.base_cell_size // 2)
        
        # Draw each pet cell
        for i, pet in enumerate(self.pets):
            if i >= len(self.cell_positions):
                continue
                
            base_center = self.cell_positions[i]
            is_enabled = i in self.enabled_pets
            is_selected = i in self.selected_pets
            is_hovered = i == self.hovered_cell and self.is_interactive
            is_focused = i == self.focused_cell and self.is_interactive
            
            # Determine colors
            if is_selected:
                fill_color = self.selected_color
                border_color = self.border_color
            elif is_hovered or is_focused:
                fill_color = self.hover_color
                border_color = self.border_color
            elif is_enabled:
                fill_color = self.hexagon_color
                border_color = self.enabled_color
            else:
                fill_color = self.disabled_color
                border_color = self.enabled_color
                
            # Convert base center to local surface coordinates 
            # (base_center is relative to component, we need scaled coordinates for local surface)
            local_center = (base_center[0], base_center[1])
            
            # Draw hexagon directly on the local surface using scaled values (no offset)
            scaled_center = (
                self.manager.scale_value(local_center[0]) if self.manager else local_center[0],
                self.manager.scale_value(local_center[1]) if self.manager else local_center[1]
            )
            scaled_radius = self.manager.scale_value(radius) if self.manager else radius
            scaled_border_width = self.manager.scale_value(self.base_border_width) if self.manager else self.base_border_width
            
            # Calculate hexagon points for local surface
            points = []
            for i in range(6):
                angle = (math.pi / 3 * i) + (math.pi / 6)  # 60 degrees * i + 30 degrees rotation
                x = scaled_center[0] + scaled_radius * math.cos(angle)
                y = scaled_center[1] + scaled_radius * math.sin(angle)
                points.append((int(x), int(y)))
            
            # Draw filled hexagon on local surface
            if len(points) >= 3:
                pygame.draw.polygon(surface, fill_color, points)
                if border_color:
                    pygame.draw.polygon(surface, border_color, points, scaled_border_width)

            # Draw pet sprite
            if hasattr(pet, 'get_sprite'):
                try:
                    sprite = pet.get_sprite(PetFrame.NAP2.value if pet.state == "nap" else PetFrame.IDLE1.value)
                    if sprite:
                        # Use the same scaled center we calculated for the hexagon (local surface coordinates)
                        sprite_center = scaled_center
                        sprite_radius = scaled_radius
                        
                        sprite_rect = sprite.get_rect()
                        
                        # Calculate sprite padding (leave some space around sprite in hexagon)
                        sprite_padding = max(4, sprite_radius // 8)
                        available_radius = sprite_radius - sprite_padding
                        
                        # Scale sprite to fit in hexagon with padding
                        sprite_scale_factor = min(
                            (available_radius * 2) / sprite_rect.width,
                            (available_radius * 2) / sprite_rect.height
                        )
                        
                        if sprite_scale_factor < 1.0:
                            # Scale down the sprite
                            new_width = max(1, int(sprite_rect.width * sprite_scale_factor))
                            new_height = max(1, int(sprite_rect.height * sprite_scale_factor))
                            sprite = pygame.transform.scale(sprite, (new_width, new_height))
                            sprite_rect = sprite.get_rect()
                            
                        # Center sprite in hexagon
                        sprite_rect.center = sprite_center
                        
                        # Apply transparency for disabled pets
                        if not is_enabled:
                            sprite = sprite.copy()
                            sprite.set_alpha(100)  # Semi-transparent
                            
                        surface.blit(sprite, sprite_rect)
                except Exception as e:
                    # Fallback if sprite loading fails
                    runtime_globals.game_console.log(f"[PetSelector] Failed to load sprite for pet {i}: {e}")
                    pass
                
        return surface
        
    def handle_event(self, event):
        """Handle pygame events"""
        if not self.is_interactive:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            return self.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self.handle_mouse_click(event.pos, event.button)
                
        return False
        
    def get_selected_pets(self):
        """Get list of currently selected pets"""
        return [self.pets[i] for i in self.selected_pets if i < len(self.pets)]
        
    def get_enabled_pets(self):
        """Get list of currently enabled pets"""
        return [self.pets[i] for i in self.enabled_pets if i < len(self.pets)]
        
    def clear_selection(self):
        """Clear all selections"""
        if self.selected_pets:
            self.selected_pets = []
            self.needs_redraw = True
            
    def select_all_enabled(self):
        """Select all enabled pets"""
        old_selection = self.selected_pets[:]
        self.selected_pets = self.enabled_pets[:]
        if old_selection != self.selected_pets:
            self.needs_redraw = True