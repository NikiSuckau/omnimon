import pygame
import platform
import json
import os

from core.utils.asset_utils import open_json

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
    # Mouse: configuration
    mouse_config = config.get("mouse", {})
    return key_map, reverse_key_map, pin_map, joystick_button_map, mouse_config

class InputManager:
    """
    Unified input layer for keyboard, GPIO, and joystick/controller input.
    Joystick events are normalized + stateful to avoid duplicates and ghost releases.
    """

    def __init__(self, analog_deadzone=0.1):
        self.device = "PC" if platform.system() != "Linux" else "Pi"

        # --- Load mappings from config ---
        key_map, reverse_key_map, pin_map, joystick_button_map, mouse_config = load_input_config()
        self.key_map = key_map
        self.reverse_key_map = reverse_key_map
        self.pin_map = pin_map
        self.default_joystick_button_map = joystick_button_map

        # Mouse configuration - defer detection until pygame video is ready
        self.mouse_force_disabled = mouse_config.get("force_disabled", False)
        self.mouse_enabled = False  # Will be set during first update/event
        self.mouse_detection_done = False
        self.mouse_left_action = mouse_config.get("left_click", "LCLICK")
        self.mouse_right_action = mouse_config.get("right_click", "RCLICK")
        self.mouse_position = (0, 0)
        self.mouse_drag_start = None
        self.mouse_dragging = False
        self.drag_threshold = mouse_config.get("drag_threshold", 5)
        
        # Touch/click states
        self.touch_start_pos = None
        self.is_touching = False

        # We’ll populate per‑joystick button maps after init (allows overrides).
        self.joystick_button_maps = {}  # joy_id -> {button_index: action}

        # --- State tracking sets (GPIO + joystick + mouse unified) ---
        self.just_pressed_gpio = set()
        self.active_gpio_inputs = set()

        self.joystick_just_pressed = set()
        self.joystick_active_inputs = set()
        
        self.mouse_just_pressed = set()
        self.mouse_active_inputs = set()

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

    def get_mouse_just_pressed(self):
        """Returns only mouse inputs (used internally by process_event)"""
        pressed = list(self.mouse_just_pressed)
        self.mouse_just_pressed.clear()
        return pressed

    def get_mouse_position(self):
        """Get the current mouse position."""
        return self.mouse_position

    def _ensure_mouse_detection(self):
        """Ensure mouse detection has been performed"""
        if not self.mouse_detection_done:
            self.mouse_enabled = self._detect_mouse_support() and not self.mouse_force_disabled
            self.mouse_detection_done = True
    
    def is_mouse_enabled(self):
        """Check if mouse/touch input is enabled."""
        self._ensure_mouse_detection()
        return self.mouse_enabled

    def force_disable_mouse(self, disabled=True):
        """Force disable mouse for testing purposes."""
        self.mouse_force_disabled = disabled
        self._ensure_mouse_detection()
        old_enabled = self.mouse_enabled
        self.mouse_enabled = self._detect_mouse_support() and not self.mouse_force_disabled
        
        if old_enabled != self.mouse_enabled:
            status = "disabled" if disabled else "enabled"
            print(f"[Input] Mouse/touch support forcefully {status}")
        
        return self.mouse_enabled

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
    # Event processing
    # ------------------------------------------------------------------
    def process_event(self, event):
        # Ensure mouse detection is done when we start processing events
        self._ensure_mouse_detection()
        
        # Check if we need to end an active drag due to other input
        should_end_drag = False
        
        # --- Keyboard ---
        if event.type == pygame.KEYDOWN and event.key in self.key_map:
            if self.mouse_dragging:
                should_end_drag = True
            action = self.key_map[event.key]
            
            if should_end_drag:
                self._end_drag()
                # Process the keyboard action after ending drag
                return action
            return action

        # --- Joystick Buttons ---
        if event.type == pygame.JOYBUTTONDOWN:
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
                    return action

        elif event.type == pygame.JOYBUTTONUP:
            jid = self._event_instance_id(event)
            btn = event.button
            action = self.joystick_button_maps.get(jid, {}).get(btn)
            if action:
                self._joy_release(action)
            return None

        # --- Joystick Hat (D‑pad) ---
        elif event.type == pygame.JOYHATMOTION:
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
            # Only end drag if axis moved significantly
            if self.mouse_dragging and abs(event.value) > self.analog_deadzone:
                should_end_drag = True
                
            jid = self._event_instance_id(event)
            
            if should_end_drag:
                self._end_drag()
                
            self._update_axis_state(jid, event.axis, event.value)
            return None

        # --- Mouse ---
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.mouse_enabled:
                self.mouse_position = event.pos
                
                if event.button == 1:  # Left click
                    action = self.mouse_left_action
                    if action not in self.mouse_active_inputs:
                        self.mouse_just_pressed.add(action)
                        self.mouse_active_inputs.add(action)
                        # Start potential drag
                        self.touch_start_pos = event.pos
                        self.is_touching = True
                        return action
                        
                elif event.button == 3:  # Right click
                    # End any active drag when right clicking
                    if self.mouse_dragging:
                        self._end_drag()
                        
                    action = self.mouse_right_action
                    if action not in self.mouse_active_inputs:
                        self.mouse_just_pressed.add(action)
                        self.mouse_active_inputs.add(action)
                        return action

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.mouse_enabled:
                self.mouse_position = event.pos
                
                if event.button == 1:  # Left click release
                    action = self.mouse_left_action
                    self.mouse_active_inputs.discard(action)
                    
                    # End drag if dragging
                    if self.mouse_dragging:
                        self._end_drag()
                        return "DRAG_END"
                    
                    self.is_touching = False
                    self.touch_start_pos = None
                    
                elif event.button == 3:  # Right click release
                    action = self.mouse_right_action
                    self.mouse_active_inputs.discard(action)
            return None

        elif event.type == pygame.MOUSEMOTION:
            if self.mouse_enabled:
                self.mouse_position = event.pos
                
                # Check for drag start
                if self.is_touching and not self.mouse_dragging and self.touch_start_pos:
                    dx = abs(event.pos[0] - self.touch_start_pos[0])
                    dy = abs(event.pos[1] - self.touch_start_pos[1])
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    
                    if distance > self.drag_threshold:
                        self.mouse_dragging = True
                        self.mouse_drag_start = self.touch_start_pos
                        self.mouse_just_pressed.add("DRAG_START")
                        return "DRAG_START"
                
                # Emit drag motion if dragging
                if self.mouse_dragging:
                    self.mouse_just_pressed.add("DRAG_MOTION")
                    return "DRAG_MOTION"
                    
            return None

        elif event.type == pygame.MOUSEWHEEL:
            if self.mouse_enabled:
                # End any active drag when scrolling
                if self.mouse_dragging:
                    self._end_drag()
                    
                if event.y > 0:  # Scroll up
                    self.mouse_just_pressed.add("SCROLL_UP")
                    return "SCROLL_UP"
                elif event.y < 0:  # Scroll down
                    self.mouse_just_pressed.add("SCROLL_DOWN")
                    return "SCROLL_DOWN"
            return None

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
            self.mouse_just_pressed.add("DRAG_END")

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
