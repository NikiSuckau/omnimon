"""
Input Manager - Unified input handling for keyboard, GPIO, joystick, mouse/touch, and sensors

Android Accelerometer Support:
- Uses plyer.accelerometer (requires 'plyer' in buildozer.spec requirements)
- Accelerometer is enabled on initialization when IS_ANDROID is True
- poll_accelerometer() should be called each frame to check for shake events
- No pygame events are used - polling-based approach for Android compatibility

Raspberry Pi Accelerometer Support:
- Uses I2C hardware accelerometer via shake_detector
- Polled via runtime_globals.shake_detector.check_for_shake()
"""

import pygame
import platform
import json
import os

from core.utils.asset_utils import open_json
from core.game_input.input_event import (
    InputEventType,
    create_simple_event,
    create_click_event,
    create_motion_event,
    create_drag_start_event,
    create_drag_motion_event,
    create_drag_end_event,
    create_scroll_event
)

# Try to import gpiozero, but handle gracefully if not available (e.g., desktop)
try:
    from gpiozero import Button  # type: ignore
    HAS_GPIO = True
except ImportError:
    Button = None
    HAS_GPIO = False

CONFIG_PATH = "config/input_config.json"

def load_input_config():
    # Load and parse the config file    from core.utils.asset_utils import open_json
    with open_json(CONFIG_PATH) as f:
        config = json.load(f)
    # Keyboard: convert string to pygame constant
    key_map = {}
    for action, key_str in config.get("keyboard", {}).items():
        if key_str.startswith("K_"):
            key_map[getattr(pygame, key_str)] = action
    # Add debug keys (F1-F12)
    for i in range(1, 13):
        key_map[getattr(pygame, f"K_F{i}")] = f"F{i}"
    reverse_key_map = {v: k for k, v in key_map.items()}
    # GPIO: pin to action
    pin_map = {int(pin): action for pin, action in config.get("gpio", {}).items()}
    # Joystick: button index to action
    joystick_button_map = {int(btn): action for btn, action in config.get("joystick", {}).items()}
    return key_map, reverse_key_map, pin_map, joystick_button_map

class InputManager:
    """
    Unified input layer for keyboard, GPIO, and joystick/controller input.
    Joystick events are normalized + stateful to avoid duplicates and ghost releases.
    """

    def __init__(self, analog_deadzone=0.1):
        self.device = "PC" if platform.system() != "Linux" else "Pi"

        # --- Load mappings from config ---
        key_map, reverse_key_map, pin_map, joystick_button_map = load_input_config()
        self.key_map = key_map
        self.reverse_key_map = reverse_key_map
        self.pin_map = pin_map
        self.default_joystick_button_map = joystick_button_map

        # Mouse configuration - defer detection until pygame video is ready
        self.mouse_enabled = False  # Will be set during first update/event
        self.mouse_detection_done = False
        self.mouse_position = (0, 0)
        self.mouse_drag_start = None
        self.mouse_dragging = False
        self.drag_threshold = 5
        
        # Touch/click states
        self.touch_start_pos = None
        self.is_touching = False
        self._last_motion_pos = (0, 0)  # Track last mouse position for motion detection
        
        # Display size for touch coordinate conversion (may differ from game resolution)
        self.display_width = None
        self.display_height = None

        # Global click region registry (screen-space rectangles for hit-testing).
        # These rects are in the same coordinate system as mouse_position
        # (runtime_globals.SCREEN_WIDTH / SCREEN_HEIGHT), after any scaling
        # done by the platform-specific entry point (e.g. Android main).
        #
        # Each entry: {"name": str, "rect": pygame.Rect, "priority": int}
        self.click_regions = []

        # Android accelerometer support (using plyer) for shake detection
        self.android_accel_enabled = False
        self.android_accel_previous_x = None
        self.android_accel_threshold = 1.5
        self.android_accel_last_shake_time = 0
        self.android_accel_cooldown = 0.1
        
        # Initialize Android accelerometer if running on Android
        from core import runtime_globals
        if runtime_globals.IS_ANDROID:
            try:
                from plyer import accelerometer # type: ignore
                accelerometer.enable()
                self.android_accel_enabled = True
                print("[Input] Android accelerometer enabled via plyer")
            except Exception as e:
                print(f"[Input] Failed to enable Android accelerometer: {e}")

        # We’ll populate per‑joystick button maps after init (allows overrides).
        self.joystick_button_maps = {}  # joy_id -> {button_index: action}

        # --- State tracking sets (GPIO + joystick + mouse unified) ---
        self.just_pressed_gpio = set()
        self.active_gpio_inputs = set()

        self.joystick_just_pressed = set()
        self.joystick_active_inputs = set()

        # Track directional states separately so we emit clean changes
        self.axis_state = {}   # joy_id -> {"x": -1/0/+1, "y": 0}
        self.hat_state = {}    # joy_id -> (hat_x, hat_y) raw

        self.analog_deadzone = analog_deadzone

        # Initialize joysticks
        self.init_joysticks()

        # GPIO setup
        self.buttons = {}
        if self.device == "Pi" and HAS_GPIO:
            for pin, action in self.pin_map.items():
                try:
                    btn = Button(pin, pull_up=True, bounce_time=0.05)
                    btn.when_pressed = self.make_gpio_handler(action, True)
                    btn.when_released = self.make_gpio_handler(action, False)
                    self.buttons[pin] = btn
                except Exception:
                    pass  # ignore missing pins

    def _detect_mouse_support(self):
        """Auto-detect mouse/touch support"""
        try:
            # Check if running on Android first - disable mouse to prevent double input
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                print("[Input] Mouse support disabled: Android platform (using touch events only)")
                return False
            
            # Check if mouse is available
            pygame.mouse.get_pressed()
            
            # Platform-specific detection
            if platform.system() == "Windows":
                print("[Input] Mouse support detected: Windows platform")
                return True  # Windows always has mouse support
            elif platform.system() == "Darwin":
                print("[Input] Mouse support detected: macOS platform")
                return True  # macOS always has mouse support
            elif platform.system() == "Linux":
                # Check for desktop environment or touch device
                import subprocess
                try:
                    # Check if running on desktop with display
                    display = os.environ.get('DISPLAY')
                    wayland = os.environ.get('WAYLAND_DISPLAY')
                    if display or wayland:
                        print(f"[Input] Mouse support detected: Linux desktop (DISPLAY={display}, WAYLAND={wayland})")
                        return True
                    
                    # Check for touch devices
                    result = subprocess.run(['find', '/dev/input', '-name', 'event*'], 
                                         capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and result.stdout:
                        print("[Input] Touch/mouse input devices detected on Linux")
                        return True
                except:
                    pass
                    
                # Default for Pi: check if it's not headless
                has_config = os.path.exists("/boot/config.txt")
                has_ssh = os.path.exists("/boot/ssh")
                if has_config and not has_ssh:
                    print("[Input] Touch support detected: Raspberry Pi with display")
                    return True
                print("[Input] No mouse/touch support detected: headless Linux")
                return False
            else:
                print(f"[Input] Unknown platform {platform.system()}, defaulting to no mouse")
                return False  # Conservative default
        except Exception as e:
            print(f"[Input] Error detecting mouse support: {e}")
            return False

    # ------------------------------------------------------------------
    # GPIO helpers
    # ------------------------------------------------------------------
    def make_gpio_handler(self, action, pressed):
        def handler():
            self.handle_gpio_input(action, pressed)
        return handler

    def handle_gpio_input(self, action, pressed):
        if pressed:
            if action not in self.active_gpio_inputs:
                self.just_pressed_gpio.add(action)
            self.active_gpio_inputs.add(action)
        else:
            self.active_gpio_inputs.discard(action)

    # ------------------------------------------------------------------
    # Joystick init + mapping
    # ------------------------------------------------------------------
    def init_joysticks(self):
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        print(f"[Input] Found {count} joystick(s)")

        self.joysticks = {}
        self.joystick_button_maps.clear()
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                jid = joy.get_instance_id() if hasattr(joy, "get_instance_id") else i
                name = joy.get_name()
                axes = joy.get_numaxes()
                buttons = joy.get_numbuttons()
                hats = joy.get_numhats()
                self.joysticks[jid] = joy
                self.axis_state[jid] = {"x": 0, "y": 0}
                self.hat_state[jid] = (0, 0)
                # Use config mapping for all joysticks by default
                self.joystick_button_maps[jid] = dict(self.default_joystick_button_map)

                print(f"[Input] Joystick {i} (id={jid}): {name}")
                print(f"[Input]   Axes={axes} Buttons={buttons} Hats={hats}")
            except Exception as e:
                print(f"[Input] Failed to init joystick {i}: {e}")

    # ------------------------------------------------------------------
    # Unified "report action pressed/released" (joystick path)
    # ------------------------------------------------------------------
    def _joy_press(self, action):
        if action not in self.joystick_active_inputs:
            self.joystick_just_pressed.add(action)
            self.joystick_active_inputs.add(action)

    def _joy_release(self, action):
        self.joystick_active_inputs.discard(action)
        # We do not emit "just pressed" on release

    # ------------------------------------------------------------------
    # Accessor used by game loop
    # ------------------------------------------------------------------
    def get_gpio_just_pressed(self):
        """Returns only GPIO inputs to avoid duplicate joystick events"""
        pressed = list(self.just_pressed_gpio)
        self.just_pressed_gpio.clear()
        return pressed
    
    def get_just_pressed_joystick(self):
        """Returns only joystick inputs (used internally by process_event)"""
        pressed = list(self.joystick_just_pressed)
        self.joystick_just_pressed.clear()
        return pressed

    def get_mouse_position(self):
        """Get the current mouse position."""
        return self.mouse_position

    def _ensure_mouse_detection(self):
        """Ensure mouse detection has been performed"""
        if not self.mouse_detection_done:
            self.mouse_enabled = self._detect_mouse_support()
            self.mouse_detection_done = True
    
    def is_mouse_enabled(self):
        """Check if mouse/touch input is enabled."""
        self._ensure_mouse_detection()
        return self.mouse_enabled

    def force_disable_mouse(self, disabled=True):
        """Deprecated - use runtime_globals.INPUT_MODE_FORCED instead."""
        from core import runtime_globals
        if disabled:
            runtime_globals.INPUT_MODE = runtime_globals.KEYBOARD_MODE
            runtime_globals.INPUT_MODE_FORCED = True
        else:
            runtime_globals.INPUT_MODE_FORCED = False
        return not disabled

    def is_dragging(self):
        """Check if currently dragging."""
        return self.mouse_dragging

    def get_drag_start(self):
        """Get the starting position of current drag."""
        return self.mouse_drag_start

    def get_drag_distance(self):
        """Get the distance dragged from start position."""
        if not self.mouse_dragging or not self.mouse_drag_start:
            return 0
        dx = self.mouse_position[0] - self.mouse_drag_start[0]
        dy = self.mouse_position[1] - self.mouse_drag_start[1]
        return (dx ** 2 + dy ** 2) ** 0.5

    def is_mouse_in_rect(self, rect):
        """Check if mouse position is inside a rectangle (x, y, width, height)."""
        if not self.mouse_enabled:
            return False
        mouse_x, mouse_y = self.mouse_position
        x, y, width, height = rect
        return x <= mouse_x <= x + width and y <= mouse_y <= y + height

    def is_mouse_hovering_option(self, options_rects):
        """
        Check which option the mouse is hovering over.
        options_rects: List of tuples (x, y, width, height) for each option
        Returns: Index of hovered option or -1 if none
        """
        if not self.mouse_enabled:
            return -1
        for i, rect in enumerate(options_rects):
            if self.is_mouse_in_rect(rect):
                return i
        return -1

    # ------------------------------------------------------------------
    # Global click-region registry (screen-space hitboxes)
    # ------------------------------------------------------------------
    def clear_click_regions(self, name: str | None = None) -> None:
        """Clear registered click regions.

        If name is None, clears all regions. Otherwise removes only regions
        with the given name (useful for scenes/windows cleaning up their
        own hitboxes without affecting others).
        """
        if name is None:
            self.click_regions.clear()
        else:
            self.click_regions = [r for r in self.click_regions if r.get("name") != name]

    def register_click_region(self, name: str, rect, priority: int = 0) -> None:
        """Register a screen-space click region.

        Args:
            name: Logical identifier for the region (e.g. "main_menu_0").
            rect: pygame.Rect or (x, y, w, h) in screen/game coordinates.
            priority: Higher values are returned first from hit tests.
        """
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(*rect)
        self.click_regions.append({"name": name, "rect": rect, "priority": priority})

    def hit_test_click_regions(self, pos):
        """Return a list of regions whose rect contains pos, sorted by priority.

        pos is expected to be in the same coordinate system as mouse_position
        (SCREEN_WIDTH/SCREEN_HEIGHT). Returns a list of region dicts.
        """
        hits = [r for r in self.click_regions if r["rect"].collidepoint(pos)]
        hits.sort(key=lambda r: r.get("priority", 0), reverse=True)
        return hits
    
    def poll_accelerometer(self):
        """
        Poll Android accelerometer for shake detection.
        Returns "SHAKE" action if shake detected, None otherwise.
        Only works on Android with plyer accelerometer enabled.
        """
        if not self.android_accel_enabled:
            return None
        
        try:
            from plyer import accelerometer # type: ignore
            acceleration = accelerometer.acceleration
            
            if acceleration is None:
                return None
            
            x, y, z = acceleration
            if x is None:
                return None
            
            # Check for shake using directional change detection
            if self.android_accel_previous_x is not None and abs(x) > self.android_accel_threshold:
                # Check if direction flipped (indicates shake)
                if ((self.android_accel_previous_x < 0 and x > 0) or 
                    (self.android_accel_previous_x > 0 and x < 0)):
                    
                    import time
                    now = time.time()
                    if (now - self.android_accel_last_shake_time) > self.android_accel_cooldown:
                        self.android_accel_last_shake_time = now
                        self.android_accel_previous_x = x
                        from core import runtime_globals
                        runtime_globals.game_console.log(f"[Input] Android SHAKE detected (x={x:.2f})")
                        return "SHAKE"
            
            self.android_accel_previous_x = x
            return None
            
        except Exception as e:
            # Silently ignore errors to avoid spamming console
            return None

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------
    def process_event(self, event):
        # Ensure mouse detection is done when we start processing events
        self._ensure_mouse_detection()
        
        # Check if we need to end an active drag due to other input
        should_end_drag = False
        
        # --- Keyboard ---
        if event.type == pygame.KEYDOWN and event.key in self.key_map:
            # Auto-detect keyboard input mode
            from core import runtime_globals
            if not runtime_globals.INPUT_MODE_FORCED:
                runtime_globals.INPUT_MODE = runtime_globals.KEYBOARD_MODE
            
            if self.mouse_dragging:
                should_end_drag = True
            action = self.key_map[event.key]
            
            # Log keyboard input
            runtime_globals.game_console.log(f"[Input] Keyboard: {action}")
            
            if should_end_drag:
                self._end_drag()
                # Process the keyboard action after ending drag
                return create_simple_event(action)
            return create_simple_event(action)

        # --- Joystick Buttons ---
        if event.type == pygame.JOYBUTTONDOWN:
            # Auto-detect keyboard input mode (joystick counts as keyboard)
            from core import runtime_globals
            if not runtime_globals.INPUT_MODE_FORCED:
                runtime_globals.INPUT_MODE = runtime_globals.KEYBOARD_MODE
            
            if self.mouse_dragging:
                should_end_drag = True
                
            jid = self._event_instance_id(event)
            btn = event.button
            action = self.joystick_button_maps.get(jid, {}).get(btn)
            if action:
                # Only trigger if not already active to prevent duplicates
                if action not in self.joystick_active_inputs:
                    if should_end_drag:
                        self._end_drag()
                    self._joy_press(action)
                    return create_simple_event(action)

        elif event.type == pygame.JOYBUTTONUP:
            jid = self._event_instance_id(event)
            btn = event.button
            action = self.joystick_button_maps.get(jid, {}).get(btn)
            if action:
                self._joy_release(action)
            return None

        # --- Joystick Hat (D‑pad) ---
        elif event.type == pygame.JOYHATMOTION:
            # Auto-detect keyboard input mode (hat counts as keyboard)
            from core import runtime_globals
            if not runtime_globals.INPUT_MODE_FORCED and event.value != (0, 0):
                runtime_globals.INPUT_MODE = runtime_globals.KEYBOARD_MODE
            
            # Only end drag if hat actually moved to a non-zero position
            if self.mouse_dragging and event.value != (0, 0):
                should_end_drag = True
                
            jid = self._event_instance_id(event)
            hat_x, hat_y = event.value  # (-1,0,+1)
            
            if should_end_drag:
                self._end_drag()
                
            self._update_hat_state(jid, hat_x, hat_y)
            return None  # actions emitted via state change

        # --- Joystick Axis (analog sticks) ---
        elif event.type == pygame.JOYAXISMOTION:
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                return None  # ignore motion-mapped axes completely

            # Auto-detect keyboard input mode (axis counts as keyboard)
            if not runtime_globals.INPUT_MODE_FORCED and abs(event.value) > self.analog_deadzone:
                runtime_globals.INPUT_MODE = runtime_globals.KEYBOARD_MODE

            if self.mouse_dragging and abs(event.value) > self.analog_deadzone:
                self._end_drag()

            jid = self._event_instance_id(event)
            self._update_axis_state(jid, event.axis, event.value)
            return None

        # --- Mouse ---
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Skip mouse events on Android to prevent double input (use touch events instead)
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                return None
                
            if self.mouse_enabled:
                # Auto-detect mouse input mode
                if not runtime_globals.INPUT_MODE_FORCED:
                    runtime_globals.INPUT_MODE = runtime_globals.MOUSE_MODE
                
                self.mouse_position = event.pos
                
                if event.button == 1:  # Left click
                    # Start potential drag
                    self.touch_start_pos = event.pos
                    self.is_touching = True
                    # Don't return click yet - wait for button up
                    return None
                        
                elif event.button == 3:  # Right click
                    # End any active drag when right clicking
                    if self.mouse_dragging:
                        self._end_drag()
                    # Don't return click yet - wait for button up
                    return None

        elif event.type == pygame.MOUSEBUTTONUP:
            # Skip mouse events on Android to prevent double input (use touch events instead)
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                return None
                
            if self.mouse_enabled:
                self.mouse_position = event.pos
                
                if event.button == 1:  # Left click release
                    # End drag if dragging
                    if self.mouse_dragging:
                        runtime_globals.game_console.log(f"[Input] DRAG_END at {event.pos}")
                        drag_end_event = create_drag_end_event(event.pos, self.mouse_drag_start)
                        self._end_drag()
                        return drag_end_event
                    
                    from core import runtime_globals
                    runtime_globals.game_console.log(f"[Input] LCLICK at {event.pos}")
                    self.is_touching = False
                    self.touch_start_pos = None

                    # Attach any matching global click regions (if registered)
                    hits = self.hit_test_click_regions(event.pos)
                    extra = {}
                    if hits:
                        extra["hit_regions"] = [h["name"] for h in hits]
                        extra["hit"] = hits[0]["name"]
                    return create_click_event(InputEventType.LCLICK, event.pos, extra)
                    
                elif event.button == 3:  # Right click release
                    from core import runtime_globals
                    runtime_globals.game_console.log(f"[Input] RCLICK at {event.pos}")
                    # Right-click currently does not use global regions, but we
                    # keep the same extension point for future use.
                    return create_click_event(InputEventType.RCLICK, event.pos)
            return None

        elif event.type == pygame.MOUSEMOTION:
            # Skip mouse events on Android to prevent double input (use touch events instead)
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                return None
                
            if self.mouse_enabled:
                # Auto-detect mouse input mode (only on significant movement)
                if not runtime_globals.INPUT_MODE_FORCED:
                    # Only switch to mouse mode if mouse moved significantly
                    if hasattr(self, '_last_motion_pos'):
                        dx = abs(event.pos[0] - self._last_motion_pos[0])
                        dy = abs(event.pos[1] - self._last_motion_pos[1])
                        if dx > 5 or dy > 5:
                            runtime_globals.INPUT_MODE = runtime_globals.MOUSE_MODE
                    self._last_motion_pos = event.pos
                
                self.mouse_position = event.pos
                
                # Check for drag start
                if self.is_touching and not self.mouse_dragging and self.touch_start_pos:
                    dx = abs(event.pos[0] - self.touch_start_pos[0])
                    dy = abs(event.pos[1] - self.touch_start_pos[1])
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    
                    if distance > self.drag_threshold:
                        from core import runtime_globals
                        runtime_globals.game_console.log(f"[Input] DRAG_START at {self.touch_start_pos}")
                        self.mouse_dragging = True
                        self.mouse_drag_start = self.touch_start_pos
                        return create_drag_start_event(self.touch_start_pos)
                
                # Emit drag motion if dragging
                if self.mouse_dragging:
                    dx = abs(event.pos[0] - self.mouse_drag_start[0])
                    dy = abs(event.pos[1] - self.mouse_drag_start[1])
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    return create_drag_motion_event(event.pos, self.mouse_drag_start, distance)
                
                # Return motion event for hover handling
                return create_motion_event(event.pos)
                    
            return None

        elif event.type == pygame.MOUSEWHEEL:
            # Skip mouse events on Android to prevent double input
            from core import runtime_globals
            if runtime_globals.IS_ANDROID:
                return None
                
            if self.mouse_enabled:
                # Auto-detect mouse input mode
                if not runtime_globals.INPUT_MODE_FORCED:
                    runtime_globals.INPUT_MODE = runtime_globals.MOUSE_MODE
                
                # End any active drag when scrolling
                if self.mouse_dragging:
                    self._end_drag()
                
                # event.y is positive for scroll up, negative for scroll down
                from core import runtime_globals
                direction = "UP" if event.y > 0 else "DOWN"
                runtime_globals.game_console.log(f"[Input] SCROLL {direction} amount={abs(event.y)}")
                return create_scroll_event(abs(event.y), direction)
            return None
        
        # --- Touch Events (Android/Mobile) ---
        elif event.type == pygame.FINGERDOWN:
            # Handle touch down as mouse down
            from core import runtime_globals
            if not runtime_globals.INPUT_MODE_FORCED:
                runtime_globals.INPUT_MODE = runtime_globals.TOUCH_MODE
            
            # Get display size on first touch event (pygame.display must be initialized)
            if self.display_width is None:
                display_surface = pygame.display.get_surface()
                if display_surface:
                    self.display_width, self.display_height = display_surface.get_size()
                    runtime_globals.game_console.log(f"[Input] Display size detected: {self.display_width}x{self.display_height}")
                else:
                    # Fallback to game resolution
                    self.display_width = runtime_globals.SCREEN_WIDTH
                    self.display_height = runtime_globals.SCREEN_HEIGHT
            
            # Convert normalized touch coordinates to display coordinates, then scale to game coordinates
            display_x = int(event.x * self.display_width)
            display_y = int(event.y * self.display_height)
            
            # Scale from display coordinates to game coordinates
            game_x = int(display_x * runtime_globals.SCREEN_WIDTH / self.display_width)
            game_y = int(display_y * runtime_globals.SCREEN_HEIGHT / self.display_height)
            
            self.mouse_position = (game_x, game_y)
            self.touch_start_pos = (game_x, game_y)
            self.is_touching = True
            
            runtime_globals.game_console.log(f"[Input] Touch DOWN: display=({display_x},{display_y}) game=({game_x},{game_y})")
            
            # Don't return event yet - wait for finger up
            return None
        
        elif event.type == pygame.FINGERUP:
            # Handle touch up as mouse up
            from core import runtime_globals
            
            # Ensure display size is initialized
            if self.display_width is None:
                display_surface = pygame.display.get_surface()
                if display_surface:
                    self.display_width, self.display_height = display_surface.get_size()
                else:
                    self.display_width = runtime_globals.SCREEN_WIDTH
                    self.display_height = runtime_globals.SCREEN_HEIGHT
            
            # Convert normalized touch coordinates to display coordinates, then scale to game coordinates
            display_x = int(event.x * self.display_width)
            display_y = int(event.y * self.display_height)
            
            # Scale from display coordinates to game coordinates
            game_x = int(display_x * runtime_globals.SCREEN_WIDTH / self.display_width)
            game_y = int(display_y * runtime_globals.SCREEN_HEIGHT / self.display_height)
            
            self.mouse_position = (game_x, game_y)
            
            # End drag if dragging
            if self.mouse_dragging:
                runtime_globals.game_console.log(f"[Input] Touch DRAG_END: display=({display_x},{display_y}) game=({game_x},{game_y})")
                drag_end_event = create_drag_end_event((game_x, game_y), self.mouse_drag_start)
                self._end_drag()
                return drag_end_event
            
            self.is_touching = False
            self.touch_start_pos = None
            
            # Return as left click event
            runtime_globals.game_console.log(f"[Input] Touch LCLICK: display=({display_x},{display_y}) game=({game_x},{game_y})")
            hits = self.hit_test_click_regions((game_x, game_y))
            extra = {}
            if hits:
                extra["hit_regions"] = [h["name"] for h in hits]
                extra["hit"] = hits[0]["name"]
            return create_click_event(InputEventType.LCLICK, (game_x, game_y), extra)
        
        elif event.type == pygame.FINGERMOTION:
            # Handle touch motion as mouse motion
            from core import runtime_globals
            
            # Ensure display size is initialized
            if self.display_width is None:
                display_surface = pygame.display.get_surface()
                if display_surface:
                    self.display_width, self.display_height = display_surface.get_size()
                else:
                    self.display_width = runtime_globals.SCREEN_WIDTH
                    self.display_height = runtime_globals.SCREEN_HEIGHT
            
            # Convert normalized touch coordinates to display coordinates, then scale to game coordinates
            display_x = int(event.x * self.display_width)
            display_y = int(event.y * self.display_height)
            
            # Scale from display coordinates to game coordinates
            game_x = int(display_x * runtime_globals.SCREEN_WIDTH / self.display_width)
            game_y = int(display_y * runtime_globals.SCREEN_HEIGHT / self.display_height)
            
            self.mouse_position = (game_x, game_y)
            
            # Check for drag start
            if self.is_touching and not self.mouse_dragging and self.touch_start_pos:
                dx = abs(game_x - self.touch_start_pos[0])
                dy = abs(game_y - self.touch_start_pos[1])
                distance = (dx ** 2 + dy ** 2) ** 0.5
                
                if distance > self.drag_threshold:
                    runtime_globals.game_console.log(f"[Input] Touch DRAG_START at {self.touch_start_pos}")
                    self.mouse_dragging = True
                    self.mouse_drag_start = self.touch_start_pos
                    return create_drag_start_event(self.touch_start_pos)
            
            # Emit drag motion if dragging
            if self.mouse_dragging:
                dx = abs(game_x - self.mouse_drag_start[0])
                dy = abs(game_y - self.mouse_drag_start[1])
                distance = (dx ** 2 + dy ** 2) ** 0.5
                return create_drag_motion_event((game_x, game_y), self.mouse_drag_start, distance)
            
            # Return as motion event for hover handling
            return create_motion_event((game_x, game_y))

        # --- Device add/remove ---
        elif event.type == pygame.JOYDEVICEADDED:
            print(f"[Input] Joystick connected: {event.device_index}")
            self.init_joysticks()
        elif event.type == pygame.JOYDEVICEREMOVED:
            inst = getattr(event, "instance_id", None)
            print(f"[Input] Joystick disconnected: {inst}")
            # purge
            if inst in self.joysticks:
                del self.joysticks[inst]
                self.axis_state.pop(inst, None)
                self.hat_state.pop(inst, None)
                self.joystick_button_maps.pop(inst, None)

        return None

    def _end_drag(self):
        """Helper method to cleanly end drag operations"""
        if self.mouse_dragging:
            self.mouse_dragging = False
            self.mouse_drag_start = None
            self.is_touching = False
            self.touch_start_pos = None

    # ------------------------------------------------------------------
    # Helpers: decode instance id (compat w/old pygame)
    # ------------------------------------------------------------------
    def _event_instance_id(self, event):
        # Pygame 2 exposes instance_id; fallback to event.joy index
        return getattr(event, "instance_id", getattr(event, "joy", 0))

    # ------------------------------------------------------------------
    # Hat → actions
    # ------------------------------------------------------------------
    def _update_hat_state(self, jid, hat_x, hat_y):
        old_x, old_y = self.hat_state.get(jid, (0, 0))
        self.hat_state[jid] = (hat_x, hat_y)

        # X change
        if hat_x != old_x:
            if old_x == -1:
                self._joy_release("LEFT")
            elif old_x == +1:
                self._joy_release("RIGHT")
            if hat_x == -1:
                self._joy_press("LEFT")
            elif hat_x == +1:
                self._joy_press("RIGHT")

        # Y change
        if hat_y != old_y:
            if old_y == +1:   # NOTE: hat_y +1 is UP
                self._joy_release("UP")
            elif old_y == -1:
                self._joy_release("DOWN")
            if hat_y == +1:
                self._joy_press("UP")
            elif hat_y == -1:
                self._joy_press("DOWN")

    # ------------------------------------------------------------------
    # Axis → digital directions (left stick only, axes 0/1)
    # ------------------------------------------------------------------
    def _update_axis_state(self, jid, axis, value):
        # ensure entry
        st = self.axis_state.setdefault(jid, {"x": 0, "y": 0})
        from core import runtime_globals
        if runtime_globals.IS_ANDROID:
            return;

        if axis == 0:  # X
            new_dir = -1 if value < -self.analog_deadzone else +1 if value > self.analog_deadzone else 0
            old_dir = st["x"]
            if new_dir != old_dir:
                if old_dir == -1:
                    self._joy_release("ANALOG_LEFT")
                elif old_dir == +1:
                    self._joy_release("ANALOG_RIGHT")
                if new_dir == -1:
                    self._joy_press("ANALOG_LEFT")
                elif new_dir == +1:
                    self._joy_press("ANALOG_RIGHT")
                st["x"] = new_dir

        elif axis == 1:  # Y
            new_dir = -1 if value < -self.analog_deadzone else +1 if value > self.analog_deadzone else 0
            old_dir = st["y"]
            if new_dir != old_dir:
                if old_dir == -1:
                    self._joy_release("ANALOG_UP")
                elif old_dir == +1:
                    self._joy_release("ANALOG_DOWN")
                if new_dir == -1:
                    self._joy_press("ANALOG_UP")
                elif new_dir == +1:
                    self._joy_press("ANALOG_DOWN")
                st["y"] = new_dir

        # ignore other axes for now (add right stick if needed)
