"""
Grid Component - A grid layout for displaying items with pagination and cursor selection
"""
import pygame
import math
from components.ui.component import UIComponent
from core import runtime_globals


class GridItem:
    """Represents an item in the grid"""
    def __init__(self, sprite=None, text="", data=None):
        self.sprite = sprite
        self.text = text
        self.data = data  # Any additional data associated with this item


class Grid(UIComponent):
    """A grid component that displays items in a grid layout with pagination and cursor selection"""
    
    def __init__(self, x, y, width, height, rows=2, columns=2):
        super().__init__(x, y, width, height)
        self.rows = rows
        self.columns = columns
        self.items = []  # List of GridItem objects
        self.current_page = 0
        self.cursor_row = 0  # Currently focused item (for navigation)
        self.cursor_col = 0
        self.selected_row = -1  # Currently selected item (for highlighting) - -1 means no selection
        self.selected_col = -1
        self.selected_item_index = -1  # Global index of selected item across all pages
        self.items_per_page = rows * columns
        self.focusable = True
        
        # Visual properties
        self.cell_padding = 5  # Padding around each cell content
        self.cursor_color = (255, 255, 255)  # White cursor
        self.cursor_thickness = 2
        self.text_color = (255, 255, 255)  # White text
        self.background_color = None  # Transparent background
        
        # Calculate cell dimensions
        self.cell_width = (width - (self.cell_padding * (columns + 1))) // columns
        self.cell_height = (height - (self.cell_padding * (rows + 1))) // rows
        
        # Callbacks
        self.on_selection_change = None  # Callback when cursor moves
        self.on_page_change = None  # Callback when page changes
        
    def set_items(self, items):
        """Set the items to display in the grid"""
        self.items = items
        self.current_page = 0
        self.cursor_row = 0
        self.cursor_col = 0
        self.selected_row = -1
        self.selected_col = -1
        self.selected_item_index = -1
        self.needs_redraw = True
        
        # Trigger page change callback
        if self.on_page_change:
            self.on_page_change(self.current_page, self.get_total_pages())
            
    def add_item(self, sprite=None, text="", data=None):
        """Add an item to the grid"""
        item = GridItem(sprite, text, data)
        self.items.append(item)
        self.needs_redraw = True
        
    def get_total_pages(self):
        """Get the total number of pages"""
        if not self.items:
            return 0
        return math.ceil(len(self.items) / self.items_per_page)
        
    def get_current_page_items(self):
        """Get the items for the current page"""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.items[start_idx:end_idx]
        
    def get_selected_item(self):
        """Get the currently selected item"""
        current_items = self.get_current_page_items()
        item_index = self.cursor_row * self.columns + self.cursor_col
        
        if 0 <= item_index < len(current_items):
            return current_items[item_index]
        return None
        
    def select_current_item(self):
        """Select the currently focused item (for highlighting)"""
        self.selected_row = self.cursor_row
        self.selected_col = self.cursor_col
        
        # Calculate global item index
        item_index = self.cursor_row * self.columns + self.cursor_col
        self.selected_item_index = self.current_page * self.items_per_page + item_index
        
        self.needs_redraw = True
        
    def clear_selection(self):
        """Clear the current selection"""
        self.selected_row = -1
        self.selected_col = -1
        self.selected_item_index = -1
        self.needs_redraw = True
        
    def move_cursor(self, dx, dy):
        """Move the cursor by the given delta"""
        old_row, old_col = self.cursor_row, self.cursor_col
        
        new_col = self.cursor_col + dx
        new_row = self.cursor_row + dy
        
        # Clamp to grid bounds
        new_col = max(0, min(self.columns - 1, new_col))
        new_row = max(0, min(self.rows - 1, new_row))
        
        # Check if the new position has a valid item
        current_items = self.get_current_page_items()
        item_index = new_row * self.columns + new_col
        
        if 0 <= item_index < len(current_items):
            self.cursor_row = new_row
            self.cursor_col = new_col
            self.needs_redraw = True
            
            # Trigger selection change callback
            if self.on_selection_change:
                self.on_selection_change(self.get_selected_item())
                
            return True
        return False
        
    def change_page(self, delta):
        """Change the page by the given delta"""
        total_pages = self.get_total_pages()
        if total_pages <= 1:
            return False
            
        new_page = self.current_page + delta
        new_page = max(0, min(total_pages - 1, new_page))
        
        if new_page != self.current_page:
            self.current_page = new_page
            
            # Check if the globally selected item is on this page
            if self.selected_item_index >= 0:
                # Calculate which page the selected item is on
                selected_page = self.selected_item_index // self.items_per_page
                
                if selected_page == self.current_page:
                    # Selected item is on this page, restore local selection
                    local_item_index = self.selected_item_index % self.items_per_page
                    self.selected_row = local_item_index // self.columns
                    self.selected_col = local_item_index % self.columns
                else:
                    # Selected item is not on this page, clear local selection but keep global selection
                    self.selected_row = -1
                    self.selected_col = -1
            else:
                # No global selection, ensure local selection is cleared
                self.selected_row = -1
                self.selected_col = -1
            
            # Reset cursor to top-left and ensure it's on a valid item
            self.cursor_row = 0
            self.cursor_col = 0
            
            # Find first valid item position on new page
            current_items = self.get_current_page_items()
            if current_items:
                self.needs_redraw = True
                
                # Trigger callbacks
                if self.on_page_change:
                    self.on_page_change(self.current_page, total_pages)
                if self.on_selection_change:
                    self.on_selection_change(self.get_selected_item())
                    
                return True
        return False
        
    def handle_event(self, event):
        """Handle input events for the grid component"""
        if not self.visible or not self.focusable:
            return False
            
        # Handle string events from the input manager
        if isinstance(event, str):
            if event == "UP":
                runtime_globals.game_sound.play("menu")
                return self.move_cursor(0, -1)
            elif event == "DOWN":
                runtime_globals.game_sound.play("menu")
                return self.move_cursor(0, 1)
            elif event == "LEFT":
                runtime_globals.game_sound.play("menu")
                return self.move_cursor(-1, 0)
            elif event == "RIGHT":
                runtime_globals.game_sound.play("menu")
                return self.move_cursor(1, 0)
            elif event == "L":  # Page left
                runtime_globals.game_sound.play("menu")
                return self.change_page(-1)
            elif event == "R":  # Page right
                runtime_globals.game_sound.play("menu")
                return self.change_page(1)
            elif event == "A":  # Select item
                selected_item = self.get_selected_item()
                if selected_item:
                    runtime_globals.game_sound.play("menu")
                    # Actually select the current item for highlighting
                    self.select_current_item()
                    # Trigger selection change callback to notify parent of selection
                    if self.on_selection_change:
                        self.on_selection_change(selected_item)
                    return True
        
        # Handle mouse events
        elif hasattr(event, 'type'):
            return self.handle_mouse_event(event)
            
        return False
        
    def handle_mouse_event(self, event):
        """Handle mouse events for grid interaction"""
        if event.type == pygame.MOUSEMOTION:
            # Update cursor position on hover (focus) but don't trigger selection change
            mouse_x, mouse_y = event.pos
            relative_x = mouse_x - self.rect.x
            relative_y = mouse_y - self.rect.y
            
            if 0 <= relative_x < self.rect.width and 0 <= relative_y < self.rect.height:
                cell_x = relative_x // (self.cell_width + self.cell_padding)
                cell_y = relative_y // (self.cell_height + self.cell_padding)
                
                if 0 <= cell_x < self.columns and 0 <= cell_y < self.rows:
                    # Check if this cell has a valid item
                    current_items = self.get_current_page_items()
                    item_index = cell_y * self.columns + cell_x
                    
                    if 0 <= item_index < len(current_items):
                        if self.cursor_row != cell_y or self.cursor_col != cell_x:
                            self.cursor_row = cell_y
                            self.cursor_col = cell_x
                            self.needs_redraw = True
                            # Don't trigger selection change callback on hover, only on actual selection
                            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Select the currently focused item on click
            current_items = self.get_current_page_items()
            item_index = self.cursor_row * self.columns + self.cursor_col
            
            if 0 <= item_index < len(current_items):
                self.select_current_item()
                # Trigger selection change callback only on actual click/selection
                if self.on_selection_change:
                    self.on_selection_change(self.get_selected_item())
                return True
        return False
        
    def render(self):
        """Render the grid component"""
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw background if specified
        if self.background_color:
            surface.fill(self.background_color)
            
        current_items = self.get_current_page_items()
        
        # Draw grid cells
        for row in range(self.rows):
            for col in range(self.columns):
                item_index = row * self.columns + col
                
                # Calculate cell position
                cell_x = self.cell_padding + col * (self.cell_width + self.cell_padding)
                cell_y = self.cell_padding + row * (self.cell_height + self.cell_padding)
                
                # Draw cell background
                cell_rect = pygame.Rect(cell_x, cell_y, self.cell_width, self.cell_height)
                
                # Check if this is the focused cell (cursor position) for border highlight
                is_focused = row == self.cursor_row and col == self.cursor_col and self.focused
                # Check if this is the selected cell (clicked/chosen) for background highlight
                is_selected = row == self.selected_row and col == self.selected_col
                
                # Check if this cell has an item
                if item_index < len(current_items):
                    item = current_items[item_index]
                    
                    # Draw highlight background for selected cell
                    if is_selected and self.manager:
                        # Get theme highlight color
                        colors = self.manager.get_theme_colors()
                        highlight_color = colors.get("highlight", (200, 200, 200))  # Default light gray
                        # Create a lighter version of the highlight color
                        light_highlight = tuple(min(255, c + 50) for c in highlight_color)
                        pygame.draw.rect(surface, light_highlight, cell_rect)
                    
                    # Draw sprite if available
                    if item.sprite:
                        # Calculate scaled sprite size to fill cell while maintaining aspect ratio
                        sprite_rect = item.sprite.get_rect()
                        original_width = sprite_rect.width
                        original_height = sprite_rect.height
                        
                        # Reserve space for text if it exists
                        available_height = self.cell_height
                        if item.text:
                            available_height -= 16  # Reserve space for text at bottom
                        
                        # Calculate scaling factors for width and height
                        scale_x = (self.cell_width - 4) / original_width  # -4 for padding
                        scale_y = available_height / original_height
                        
                        # Use the smaller scale to maintain aspect ratio
                        scale = min(scale_x, scale_y)
                        
                        # Calculate new dimensions
                        new_width = int(original_width * scale)
                        new_height = int(original_height * scale)
                        
                        # Scale the sprite
                        scaled_sprite = pygame.transform.scale(item.sprite, (new_width, new_height))
                        
                        # Center the scaled sprite in the cell (or in available space if text exists)
                        sprite_rect = scaled_sprite.get_rect()
                        sprite_rect.centerx = cell_rect.centerx
                        
                        if item.text:
                            # Position sprite in upper part of cell, leaving space for text
                            sprite_rect.centery = cell_rect.y + (available_height // 2)
                        else:
                            # Center sprite in entire cell
                            sprite_rect.centery = cell_rect.centery
                        
                        surface.blit(scaled_sprite, sprite_rect)
                    
                    # Draw text if available (below sprite or centered if no sprite)
                    if item.text and self.manager:
                        # Get font for text rendering
                        font = self.get_font("text")
                        
                        # Calculate available text width
                        available_text_width = self.cell_width - 4  # -4 for padding
                        
                        # Choose text color based on selection state
                        text_color = (0, 0, 0) if is_selected else self.text_color  # Black if selected, white if not
                        
                        # Render text initially to check size
                        text_surface = font.render(item.text, True, text_color)
                        text_rect = text_surface.get_rect()
                        
                        # If text is too wide, create a truncated version
                        if text_surface.get_width() > available_text_width:
                            # Create a surface with the available width
                            truncated_surface = pygame.Surface((available_text_width, text_surface.get_height()), pygame.SRCALPHA)
                            # Blit only the portion that fits
                            truncated_surface.blit(text_surface, (0, 0))
                            text_surface = truncated_surface
                            text_rect = text_surface.get_rect()
                        
                        if item.sprite:
                            # Position text below sprite
                            text_rect.centerx = cell_rect.centerx
                            text_rect.bottom = cell_rect.bottom - 2
                        else:
                            # Center text in cell
                            text_rect.center = cell_rect.center
                            
                        surface.blit(text_surface, text_rect)
                
                # Draw border cursor if this is the focused cell (for navigation)
                if is_focused:
                    # Draw a subtle border around the focused cell
                    pygame.draw.rect(surface, self.cursor_color, cell_rect, 1)  # Thin border
                    
        return surface
        
    def get_focused_sub_rect(self):
        """Get the rect of the currently focused cell"""
        return None
        
    def get_mouse_sub_rect(self, mouse_pos):
        """Get the rect of the cell under the mouse (return None to disable mouse highlighting)"""
        return None
        
    def on_manager_set(self):
        """Called when the UI manager is set"""
        # Recalculate cell dimensions if manager scale has changed
        if self.manager:
            # Cell dimensions are already calculated in base coordinates
            self.needs_redraw = True