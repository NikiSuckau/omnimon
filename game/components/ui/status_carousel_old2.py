"""
Status Carousel Component - Horizontal scrollable carousel of status boxes
Inherits from BaseList and adds status icon rendering and auto-scrolling functionality.
"""
import pygame
import os
from components.ui.base_list import BaseList
from core import runtime_globals


class StatusCarousel(BaseList):
    def __init__(self, x, y, width, height, pet_data=None):
        """Initialize the enhanced status carousel with horizontal orientation"""
        super().__init__(x, y, width, height, orientation="horizontal")
        
        # Status-specific settings
        self.pet_data = pet_data or {}
        
        # Custom settings for status carousel
        self.base_item_size = 60     # Width of each status box at 1x scale
        self.base_item_spacing = 8   # Spacing between boxes
        self.base_arrow_size = 24    # Width of arrow buttons (hidden but functional)
        self.base_margin = 4         # Margin around content
        
        # Auto-scroll settings
        self.auto_scroll_enabled = True
        self.auto_scroll_speed = 20  # pixels per second
        self.auto_scroll_delay = 2000  # Delay before starting auto-scroll (ms)
        self.last_auto_scroll_time = 0
        self.auto_scroll_direction = 1  # 1 for forward, -1 for backward
        
        # Status icon cache
        self.status_icons = {}
        
        # Build initial status boxes
        self._rebuild_status_boxes()
        
    def set_pet_data(self, pet_data):
        """Update the pet data and rebuild status boxes"""
        self.pet_data = pet_data or {}
        self._rebuild_status_boxes()
        
    def _rebuild_status_boxes(self):
        """Rebuild the status boxes based on current pet data"""
        boxes = []
        
        if not self.pet_data:
            self.set_items(boxes)
            return
        
        # Get module info for visible stats and configuration
        module = self.pet_data.get('module')
        visible_stats = self.pet_data.get('visible_stats', [])
        use_condition_hearts = self.pet_data.get('use_condition_hearts', False)
        condition_heart_meter_visible = self.pet_data.get('condition_heart_meter_visible', False)
        
        # Define available status types
        status_types = [
            ("trophies", "Trophies", "trophies", "Trophies"),
            ("vital_values", "Vital Values", "vital_values", "Vital Values"),
            ("mistakes", "Mistakes", "mistakes", "Mistakes/Condition Hearts"),
            ("sleep_disturbances", "Sleep Disturbances", "sleep_disturbances", "Sleep Disturbances"),
            ("overfeed", "Overfeed", "overfeed", "Overfeed"),
            ("injuries", "Injuries", "injuries", "Injuries"),
            ("evolution_timer", "Evolution Timer", "evolution_timer", "Evolution Timer"),
            ("sleeps", "Sleeps", "sleeps", "Sleeps"),
            ("wakes", "Wakes", "wakes", "Wakes"),
            ("poop_time", "Poop Time", "poop_time", "Poop Time"),
            ("feed_time", "Feed Time", "feed_time", "Feed Time"),
        ]
        
        # Create boxes for available stats based on visible_stats
        for stat_id, display_name, data_key, visible_stat_name in status_types:
            # Check if this stat should be visible
            if visible_stat_name not in visible_stats:
                continue
                
            # Special handling for Trophies and Vital Values - only show if Level is also visible
            if stat_id in ["trophies", "vital_values"] and "Level" not in visible_stats:
                continue
                
            # Special handling for Mistakes/Condition Hearts
            if stat_id == "mistakes":
                # Skip condition hearts if dedicated condition heart meter is visible
                if use_condition_hearts and condition_heart_meter_visible:
                    continue
                    
                if use_condition_hearts:
                    # Use condition hearts instead of mistakes
                    if "Mistakes/Condition Hearts" in visible_stats:
                        raw_value = self.pet_data.get('condition_hearts', 0)
                        value = self._format_status_value("Heart", raw_value, self.pet_data)
                        icon_name = "Heart"  # Will use Heart Full icon
                        boxes.append({
                            'id': 'condition_hearts',
                            'name': icon_name,
                            'value': value,
                            'icon': None  # Will be loaded on demand
                        })
                    continue
                else:
                    # Use mistakes with Mistakes icon
                    if "Mistakes/Condition Hearts" in visible_stats:
                        raw_value = self.pet_data.get('mistakes', 0)
                        value = self._format_status_value("Mistakes", raw_value, self.pet_data)
                        icon_name = "Mistakes"
                        boxes.append({
                            'id': stat_id,
                            'name': icon_name,
                            'value': value,
                            'icon': None  # Will be loaded on demand
                        })
                    continue
            
            try:
                # Get raw value and format it
                raw_value = self.pet_data.get(data_key, 0)
                value = self._format_status_value(display_name, raw_value, self.pet_data)
                
                boxes.append({
                    'id': stat_id,
                    'name': display_name,
                    'value': value,
                    'icon': None  # Will be loaded on demand
                })
            except (KeyError, AttributeError, TypeError):
                # Skip stats that aren't available
                continue
        
        self.set_items(boxes)
        
    def _format_status_value(self, display_name, raw_value, pet_data):
        """Format a status value for display"""
        try:
            if display_name in ["Evolution Timer", "Poop Time", "Feed Time"]:
                # Format time values
                if raw_value <= 0:
                    return "0:00"
                minutes = raw_value // 60
                seconds = raw_value % 60
                return f"{minutes}:{seconds:02d}"
            elif display_name == "Vital Values":
                # Special formatting for vital values
                return f"{raw_value}"
            else:
                # Default formatting for numeric values
                return str(int(raw_value) if isinstance(raw_value, (int, float)) else raw_value)
        except (ValueError, TypeError):
            return "0"
            
    def _load_status_icon(self, box):
        """Load icon for a status box"""
        if not box or 'name' not in box:
            return None
            
        icon_name = box['name']
        
        # Check cache first
        if icon_name in self.status_icons:
            return self.status_icons[icon_name]
            
        try:
            # Calculate icon size
            icon_size = max(16, self.item_size - 20) if hasattr(self, 'item_size') else 32
            
            # Try to load icon from assets
            icon_path = os.path.join("assets", f"{icon_name}.png")
            if not os.path.exists(icon_path):
                # Try variations
                for variant in [f"{icon_name} Full.png", f"{icon_name}Icon.png"]:
                    variant_path = os.path.join("assets", variant)
                    if os.path.exists(variant_path):
                        icon_path = variant_path
                        break
                        
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path).convert_alpha()
                icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                self.status_icons[icon_name] = icon
                return icon
            else:
                # Create placeholder icon
                placeholder = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                placeholder.fill((128, 128, 128, 128))  # Gray placeholder
                self.status_icons[icon_name] = placeholder
                return placeholder
                
        except Exception as e:
            runtime_globals.game_console.log(f"[StatusCarousel] Error loading icon {icon_name}: {e}")
            # Create error placeholder
            icon_size = max(16, self.item_size - 20) if hasattr(self, 'item_size') else 32
            placeholder = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            placeholder.fill((255, 0, 0, 128))  # Red error placeholder
            self.status_icons[icon_name] = placeholder
            return placeholder
            
    def update(self):
        """Update component including auto-scroll functionality"""
        super().update()
        
        # Handle auto-scroll
        if self.auto_scroll_enabled and len(self.items) > self.get_visible_item_count():
            current_time = pygame.time.get_ticks()
            
            if self.last_auto_scroll_time == 0:
                self.last_auto_scroll_time = current_time
                
            if current_time - self.last_auto_scroll_time > self.auto_scroll_delay:
                # Perform auto-scroll
                dt = (current_time - self.last_scroll_time) / 1000.0 if self.last_scroll_time > 0 else 0
                scroll_distance = self.auto_scroll_speed * dt * self.auto_scroll_direction
                
                new_scroll = self.target_scroll_offset + scroll_distance
                
                # Check boundaries and reverse direction if needed
                max_scroll = max(0, (len(self.items) - self.get_visible_item_count()) * (self.item_size + self.item_spacing))
                
                if new_scroll >= max_scroll:
                    new_scroll = max_scroll
                    self.auto_scroll_direction = -1
                elif new_scroll <= 0:
                    new_scroll = 0
                    self.auto_scroll_direction = 1
                    
                self.target_scroll_offset = new_scroll
                
    def _draw_items(self, surface):
        """Draw status boxes with icons and values"""
        if not self.items or not self.items_rect:
            return
            
        colors = self.manager.get_theme_colors()
        
        # Calculate visible range
        item_total_size = self.item_size + self.item_spacing
        first_visible = max(0, int(self.scroll_offset // item_total_size))
        last_visible = min(len(self.items), first_visible + self.get_visible_item_count() + 2)
        
        for i in range(first_visible, last_visible):
            if i >= len(self.items):
                break
                
            box = self.items[i]
            
            # Calculate box position
            box_x = self.items_rect.x + (i * item_total_size) - self.scroll_offset
            box_y = self.items_rect.y
            box_rect = pygame.Rect(box_x, box_y, self.item_size, self.items_rect.height)
            
            # Skip if completely outside visible area
            if box_x + self.item_size < self.items_rect.x or box_x > self.items_rect.right:
                continue
                
            # Determine box state and colors
            is_selected = (i == self.selected_index)
            is_hovered = (i == self.mouse_over_index)
            
            if is_selected and self.focused:
                bg_color = colors["highlight"]
                text_color = colors["bg"]
                border_color = colors["bg"]
            elif is_selected or is_hovered:
                bg_color = colors["bg"]
                text_color = colors["highlight"]
                border_color = colors["highlight"]
            else:
                bg_color = colors["bg"]
                text_color = colors["fg"]
                border_color = colors["fg"]
                
            # Draw box background
            pygame.draw.rect(surface, bg_color, box_rect, border_radius=self.manager.get_border_size())
            pygame.draw.rect(surface, border_color, box_rect, width=self.manager.get_border_size(), 
                           border_radius=self.manager.get_border_size())
            
            # Draw status icon
            icon = self._load_status_icon(box)
            if icon:
                icon_rect = icon.get_rect()
                icon_rect.centerx = box_rect.centerx
                icon_rect.centery = box_rect.centery - 8  # Move up for value space
                surface.blit(icon, icon_rect)
            
            # Draw status value below icon
            if 'value' in box:
                font = self.get_font("text", custom_size=12)  # Use smaller font for values
                if font:
                    value_surface = font.render(str(box['value']), True, text_color)
                    value_rect = value_surface.get_rect()
                    value_rect.centerx = box_rect.centerx
                    value_rect.bottom = box_rect.bottom - 2
                    surface.blit(value_surface, value_rect)
                    
    def _on_item_activated(self, index):
        """Called when a status box is activated"""
        if 0 <= index < len(self.items):
            box = self.items[index]
            runtime_globals.game_console.log(f"[StatusCarousel] Activated status: {box.get('name', 'Unknown')}")
            # Pause auto-scroll temporarily when user interacts
            self.last_auto_scroll_time = pygame.time.get_ticks()
            
    def handle_input_action(self, action):
        """Override to pause auto-scroll on user input"""
        result = super().handle_input_action(action)
        if result:
            # Pause auto-scroll when user navigates manually
            self.last_auto_scroll_time = pygame.time.get_ticks()
        return result
        
    def _handle_mouse_click(self, mouse_pos):
        """Override to pause auto-scroll on mouse interaction"""
        result = super()._handle_mouse_click(mouse_pos)
        if result:
            # Pause auto-scroll when user interacts with mouse
            self.last_auto_scroll_time = pygame.time.get_ticks()
        return result