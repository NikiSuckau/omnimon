import pygame
from components.ui.ui_manager import UIManager
from core import runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_shadow


class ShakeDetector:
    """
    Detects shake gestures from mouse/touch input for devices without accelerometer.
    Uses rapid left-right movement patterns to simulate shake gestures.
    """
    
    def __init__(self):
        self.positions = []  # Store recent mouse positions
        self.max_history = 10  # Keep last 10 positions
        self.shake_threshold = 50  # Minimum distance for shake detection
        self.direction_changes = 0  # Count direction changes
        self.min_direction_changes = 3  # Minimum changes to detect shake
        self.last_direction = None
        self.shake_cooldown = 0  # Prevent too frequent shake detection
        
    def update(self):
        """Update the shake detector each frame."""
        if self.shake_cooldown > 0:
            self.shake_cooldown -= 1
            
    def add_mouse_position(self, pos):
        """Add a mouse position and check for shake patterns."""
        if self.shake_cooldown > 0:
            return False
            
        self.positions.append(pos)
        
        # Keep only recent positions
        if len(self.positions) > self.max_history:
            self.positions.pop(0)
            
        # Need at least 3 positions to detect direction changes
        if len(self.positions) < 3:
            return False
            
        # Check for rapid left-right movement
        return self._detect_shake_pattern()
        
    def _detect_shake_pattern(self):
        """Analyze recent positions for shake patterns."""
        if len(self.positions) < 3:
            return False
            
        # Calculate horizontal movement direction changes
        direction_changes = 0
        total_distance = 0
        
        for i in range(1, len(self.positions)):
            prev_pos = self.positions[i-1]
            curr_pos = self.positions[i]
            
            # Calculate horizontal movement
            dx = curr_pos[0] - prev_pos[0]
            total_distance += abs(dx)
            
            # Determine direction (only care about significant movement)
            if abs(dx) > 5:  # Minimum movement threshold
                current_direction = 1 if dx > 0 else -1
                
                if self.last_direction is not None and current_direction != self.last_direction:
                    direction_changes += 1
                    
                self.last_direction = current_direction
        
        # Check if we have enough rapid direction changes and sufficient distance
        if direction_changes >= self.min_direction_changes and total_distance > self.shake_threshold:
            self._trigger_shake()
            return True
            
        return False
        
    def _trigger_shake(self):
        """Trigger a shake event and set cooldown."""
        self.positions.clear()
        self.direction_changes = 0
        self.last_direction = None
        self.shake_cooldown = 15  # Prevent rapid re-triggering (about 0.5 seconds at 30fps)
        
    def handle_pygame_event(self, event):
        """Handle pygame events for shake detection."""
        shake_detected = False
        
        # Handle mouse movement
        if event.type == pygame.MOUSEMOTION:
            shake_detected = self.add_mouse_position(event.pos)
            
        # Handle touch events (if available)
        elif hasattr(pygame, 'FINGERMOTION') and event.type == pygame.FINGERMOTION:
            # Convert normalized touch coordinates to screen coordinates
            touch_x = int(event.x * constants.SCREEN_WIDTH)
            touch_y = int(event.y * constants.SCREEN_HEIGHT)
            shake_detected = self.add_mouse_position((touch_x, touch_y))
            
        return shake_detected


class CountMatch:
    """
    Count Match minigame - displays ready and count sprites based on pet attribute.
    Handles the visual display and input for the counting phase.
    """
    
    def __init__(self, ui_manager: UIManager, pet=None):
        """Initialize the count match minigame."""
        self.ui_manager = ui_manager
        if self.ui_manager is None:
            raise ValueError("UIManager cannot be None")
            
        self.pet = pet
        self.phase = "ready"  # ready, count
        self.press_counter = 0
        self.rotation_index = 3
        
        # Shake detection for mouse/touch fallback
        self.shake_detector = ShakeDetector()
        
        # Load and cache sprites with integer scaling
        self._sprite_cache = {}
        # Cache for scaled semi-transparent overlay sprites
        self._overlay_cache = {}
        self.load_sprites()

    def load_sprites(self):
        """Load ready and count sprites using UI manager for integer scaling."""
        # Load ready sprites using UI manager (Ready0, Ready1, Ready2, Ready3 for different attributes)
        self._sprite_cache['ready'] = {}
        ready_names = ["Ready0", "Ready1", "Ready2", "Ready3"]
        for i, name in enumerate(ready_names):
            sprite = self.ui_manager.load_sprite_integer_scaling(name=name, prefix="Training")
            self._sprite_cache['ready'][i] = sprite
        
        # Load count sprites using UI manager (Count1, Count2, Count3, Count4 for different states)
        self._sprite_cache['count'] = {}
        count_names = ["Count1", "Count2", "Count3", "Count4"]
        for i, name in enumerate(count_names, 1):
            sprite = self.ui_manager.load_sprite_integer_scaling(name=name, prefix="Training")
            self._sprite_cache['count'][i] = sprite

    def _draw_overlay_background(self, surface: pygame.Surface, base_sprite: pygame.Surface, cache_key: str):
        """Draw a semi-transparent, proportionally scaled overlay of the given sprite to cover the screen.
        - Only active when ui scale >= 2
        - Cached per (cache_key, screen size)
        - Applies blur effect for atmospheric background
        """
        try:
            if not base_sprite or not self.ui_manager or getattr(self.ui_manager, 'ui_scale', 1) < 2:
                return

            key = (cache_key, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
            overlay = self._overlay_cache.get(key)
            if overlay is None:
                sw, sh = base_sprite.get_width(), base_sprite.get_height()
                if sw <= 0 or sh <= 0:
                    return
                scale = max(constants.SCREEN_WIDTH / sw, constants.SCREEN_HEIGHT / sh)
                new_size = (int(sw * scale), int(sh * scale))
                overlay = pygame.transform.smoothscale(base_sprite, new_size)
                
                # Apply blur effect by downscaling and upscaling multiple times
                blur_iterations = 4
                blur_factor = 0.15  # Scale down to 15% for blur effect
                
                for _ in range(blur_iterations):
                    # Downscale for blur
                    blur_w = max(1, int(overlay.get_width() * blur_factor))
                    blur_h = max(1, int(overlay.get_height() * blur_factor))
                    overlay = pygame.transform.smoothscale(overlay, (blur_w, blur_h))
                    # Upscale back to original size
                    overlay = pygame.transform.smoothscale(overlay, new_size)
                
                # Set 50% opacity
                overlay = overlay.convert_alpha()
                overlay.set_alpha(128)
                self._overlay_cache[key] = overlay

            rect = overlay.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
            surface.blit(overlay, rect)
        except Exception as e:
            runtime_globals.game_console.log(f"[CountMatch] Overlay draw error for {cache_key}: {e}")

    def get_pet_attribute_color(self):
        """Get the color index (1-3) based on pet's attribute to match Ready1-Ready3 sprites."""
        if not self.pet:
            return 1
            
        attr = getattr(self.pet, "attribute", "")
        
        if attr in ["", "Va"]:
            return 1  # Default/Vaccine -> Ready1
        elif attr == "Da":
            return 2  # Data -> Ready2
        elif attr == "Vi":
            return 3  # Virus -> Ready3
        else:
            return 1

    def set_phase(self, phase):
        """Set the current phase (ready or count)."""
        self.phase = phase
        if phase == "count":
            # Reset counters when starting count phase
            self.press_counter = 0
            self.rotation_index = 3

    def handle_event(self, input_action):
        """Handle input events for the minigame."""
        if self.phase == "count" and input_action in ("Y", "SHAKE"):
            self.press_counter += 1
            if self.press_counter % 2 == 0:
                self.rotation_index -= 1
                if self.rotation_index < 1:
                    self.rotation_index = 3
            return True
        return False
        
    def handle_pygame_event(self, event):
        """Handle pygame events including shake detection."""
        if self.phase == "count":
            # Check for shake gestures via mouse/touch
            shake_detected = self.shake_detector.handle_pygame_event(event)
            if shake_detected:
                # Directly trigger shake event
                return self.handle_event("SHAKE")
        return False
        
    def update(self):
        """Update the minigame state each frame."""
        self.shake_detector.update()
        
        # Fallback: Process current mouse position for shake detection if in count phase
        if self.phase == "count":
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos != getattr(self, '_last_mouse_pos', None):
                # Create a fake mouse motion event
                fake_event = type('Event', (), {'type': pygame.MOUSEMOTION, 'pos': mouse_pos})()
                self.handle_pygame_event(fake_event)
                self._last_mouse_pos = mouse_pos

    def get_press_counter(self):
        """Get the current press counter."""
        return self.press_counter

    def get_rotation_index(self):
        """Get the current rotation index."""
        return self.rotation_index

    def draw(self, surface):
        """Draw the count match minigame components."""
        # Background is handled by the caller (training class)
        
        if self.phase == "ready":
            self.draw_ready(surface)
        elif self.phase == "count":
            self.draw_count(surface)

    def draw_ready(self, surface):
        """Draw the ready sprite based on pet attribute."""
        attr_color = self.get_pet_attribute_color()
        
        if attr_color not in self._sprite_cache['ready']:
            return
            
        sprite = self._sprite_cache['ready'][attr_color]
        
        if sprite:
            # Draw semi-transparent background overlay at high UI scales
            self._draw_overlay_background(surface, sprite, f'ready_{attr_color}')
            
            # Center the sprite on screen
            x = (constants.SCREEN_WIDTH - sprite.get_width()) // 2
            y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
            
            blit_with_shadow(surface, sprite, (x, y))

    def draw_count(self, surface):
        """Draw the count sprite based on current rotation."""
        # Use count sprite 4 if no presses yet, otherwise use rotation index
        sprite_index = 4 if self.press_counter == 0 else self.rotation_index
        sprite = self._sprite_cache['count'][sprite_index]
        
        if sprite:
            # Draw semi-transparent background overlay at high UI scales
            self._draw_overlay_background(surface, sprite, f'count_{sprite_index}')
            
            # Center the sprite on screen
            x = (constants.SCREEN_WIDTH - sprite.get_width()) // 2
            y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
            
            blit_with_shadow(surface, sprite, (x, y))