import pygame
import platform
import json
import os

# Try to import gpiozero, but handle gracefully if not available (e.g., desktop)
try:
    from gpiozero import Button  # type: ignore
    HAS_GPIO = True
except ImportError:
    Button = None
    HAS_GPIO = False

CONFIG_PATH = "config/input_config.json"
if platform.system() == "Linux":
        if os.path.exists("/usr/bin/batocera-info"):
            input_config = "config/input_config_batocera.json"
        elif os.path.exists("/boot/config.txt"):
            input_config = "config/input_config_raspberry.json"
        else:
            input_config = "config/input_config_python_desktop.json"
elif platform.system() == "Windows":
    input_config = "config/input_config_windows.json"
elif platform.system() == "Darwin":
    input_config = "config/input_config_python_desktop.json"
else:
    input_config = CONFIG_PATH

def load_input_config():
    # Load and parse the config file
    with open(input_config, "r") as f:
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

        # Mouse configuration
        self.mouse_enabled = mouse_config.get("enabled", False)
        self.mouse_left_action = mouse_config.get("left_click", "A")
        self.mouse_right_action = mouse_config.get("right_click", "B")
        self.mouse_position = (0, 0)

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
        # --- Keyboard ---
        if event.type == pygame.KEYDOWN and event.key in self.key_map:
            return self.key_map[event.key]

        # --- Joystick Buttons ---
        if event.type == pygame.JOYBUTTONDOWN:
            jid = self._event_instance_id(event)
            btn = event.button
            action = self.joystick_button_maps.get(jid, {}).get(btn)
            if action:
                # Only trigger if not already active to prevent duplicates
                if action not in self.joystick_active_inputs:
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
            jid = self._event_instance_id(event)
            hat_x, hat_y = event.value  # (-1,0,+1)
            self._update_hat_state(jid, hat_x, hat_y)
            return None  # actions emitted via state change

        # --- Joystick Axis (analog sticks) ---
        elif event.type == pygame.JOYAXISMOTION:
            jid = self._event_instance_id(event)
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
                        return action
                elif event.button == 3:  # Right click
                    action = self.mouse_right_action
                    if action not in self.mouse_active_inputs:
                        self.mouse_just_pressed.add(action)
                        self.mouse_active_inputs.add(action)
                        return action

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.mouse_enabled:
                self.mouse_position = event.pos
                if event.button == 1:  # Left click
                    action = self.mouse_left_action
                    self.mouse_active_inputs.discard(action)
                elif event.button == 3:  # Right click
                    action = self.mouse_right_action
                    self.mouse_active_inputs.discard(action)
            return None

        elif event.type == pygame.MOUSEMOTION:
            if self.mouse_enabled:
                self.mouse_position = event.pos
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
