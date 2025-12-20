"""
Scene Connect - Network connectivity and battles (Modern UI version)
Refactored to use the new UI system with dark red theme.
"""
import pygame
import random
import string
import socket
import threading
import json
import time
import copy
import traceback

from components.ui.ui_manager import UIManager
from components.ui.background import Background
from components.ui.title_scene import TitleScene
from components.ui.button import Button
from components.ui.label import Label
from components.ui.pet_selector import PetSelector
from components.ui.menu import Menu
from components.ui.code_entry import CodeEntry
from components.ui.ui_constants import BASE_RESOLUTION
from components.window_background import WindowBackground
from core import game_globals, runtime_globals
import core.constants as constants
from core.utils.pet_utils import get_battle_pvp_targets
from core.utils.scene_utils import change_scene
from core.utils.pygame_utils import blit_with_shadow, get_font

# Import for Discord HTTP client
import requests


#=====================================================================
# Simple Discord Client (inline implementation)
#=====================================================================
class DiscordModule:
    """Simple Discord client for online battles."""
    
    def __init__(self):
        """Initialize Discord client."""
        self.bot_url = getattr(constants, 'DISCORD_BOT_URL', 'http://localhost:5000').rstrip('/')
        self.client = self
        self.is_connected = False
        self.linked_account = None
        self.account_name = None
        self.user_id = None
        self.current_room_id = None
        
        # Load saved data
        self._load_data()
        runtime_globals.game_console.log(f"[DiscordModule] Initialized with bot URL: {self.bot_url}")
    
    def _get_save_path(self):
        import os
        return os.path.join("save", "discord_data.json")
    
    def _save_data(self):
        """Save linked account data."""
        try:
            import os
            if not os.path.exists("save"):
                os.makedirs("save")
            data = {
                "linked_account": self.linked_account,
                "account_name": self.account_name,
                "user_id": self.user_id
            }
            with open(self._get_save_path(), 'w') as f:
                json.dump(data, f)
            runtime_globals.game_console.log("[DiscordModule] Saved account data")
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Failed to save: {e}")
    
    def _load_data(self):
        """Load linked account data."""
        try:
            import os
            path = self._get_save_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.linked_account = data.get("linked_account")
                    self.account_name = data.get("account_name")
                    self.user_id = data.get("user_id")
                    if self.linked_account:
                        runtime_globals.game_console.log(f"[DiscordModule] Loaded saved login: {self.account_name}")
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Failed to load: {e}")
    
    def check_connection(self) -> bool:
        """Check if Discord bot is reachable."""
        try:
            response = requests.get(f"{self.bot_url}/health", timeout=2)
            is_ok = response.status_code == 200
            runtime_globals.game_console.log(f"[DiscordModule] Connection check: {is_ok}")
            return is_ok
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Connection failed: {e}")
            return False
    
    def get_account_name(self):
        """Get linked Discord account name."""
        return self.account_name
    
    def login(self, pairing_code: str) -> bool:
        """Link account with Discord."""
        try:
            runtime_globals.game_console.log(f"[DiscordModule] Linking with code: {pairing_code}")
            response = requests.post(
                f"{self.bot_url}/link",
                json={"code": pairing_code},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                self.linked_account = pairing_code.upper()
                self.account_name = data.get('username')
                self.user_id = data.get('user_id')
                self._save_data()
                runtime_globals.game_console.log(f"[DiscordModule] Linked as: {self.account_name}")
                return True
            else:
                runtime_globals.game_console.log(f"[DiscordModule] Link failed: {response.text}")
                return False
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Link exception: {e}")
            return False
    
    def logout(self):
        """Unlink account."""
        self.linked_account = None
        self.account_name = None
        self.user_id = None
        try:
            import os
            path = self._get_save_path()
            if os.path.exists(path):
                os.remove(path)
                runtime_globals.game_console.log("[DiscordModule] Saved data deleted")
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Failed to delete data: {e}")
    
    def create_room(self, room_name: str):
        """Create a battle room."""
        try:
            if not self.linked_account:
                return None, "Not logged in"
            
            runtime_globals.game_console.log(f"[DiscordModule] Creating room: {room_name}")
            response = requests.post(
                f"{self.bot_url}/room",
                json={
                    'name': room_name,
                    'host': self.account_name,
                    'max_players': 2,
                    'user_id': self.user_id
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_room_id = data.get('room_id')
                runtime_globals.game_console.log(f"[DiscordModule] Room created: {self.current_room_id}")
                return self.current_room_id, None
            else:
                error = response.json().get('error', 'Unknown error')
                runtime_globals.game_console.log(f"[DiscordModule] Create room failed: {error}")
                return None, error
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Create room exception: {e}")
            return None, str(e)
    
    def get_available_rooms(self):
        """Get list of available rooms."""
        try:
            response = requests.get(f"{self.bot_url}/rooms", timeout=5)
            if response.status_code == 200:
                rooms = response.json()
                runtime_globals.game_console.log(f"[DiscordModule] Found {len(rooms)} rooms")
                return rooms
            return []
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Get rooms exception: {e}")
            return []
    
    def join_room(self, room_id: str) -> bool:
        """Join a room."""
        try:
            if not self.linked_account:
                return False
            
            runtime_globals.game_console.log(f"[DiscordModule] Joining room: {room_id}")
            response = requests.post(
                f"{self.bot_url}/room/{room_id}/join",
                json={
                    'player': self.account_name,
                    'user_id': self.user_id
                },
                timeout=5
            )
            
            if response.status_code == 200:
                self.current_room_id = room_id
                runtime_globals.game_console.log(f"[DiscordModule] Joined room: {room_id}")
                return True
            else:
                runtime_globals.game_console.log(f"[DiscordModule] Join failed: {response.text}")
                return False
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Join exception: {e}")
            return False
    
    def send_data(self, data: dict) -> bool:
        """Send data to current room."""
        try:
            if not self.current_room_id:
                runtime_globals.game_console.log("[DiscordModule] No room to send to")
                return False
            
            runtime_globals.game_console.log(f"[DiscordModule] Sending data to {self.current_room_id}: {data.get('type')}")
            response = requests.post(
                f"{self.bot_url}/room/{self.current_room_id}/data",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                runtime_globals.game_console.log("[DiscordModule] Data sent successfully")
                return True
            else:
                runtime_globals.game_console.log(f"[DiscordModule] Send failed: {response.status_code}")
                return False
        except Exception as e:
            runtime_globals.game_console.log(f"[DiscordModule] Send exception: {e}")
            return False
    
    def poll_room(self):
        """Poll current room for updates."""
        try:
            if not self.current_room_id:
                return None
            
            response = requests.get(
                f"{self.bot_url}/room/{self.current_room_id}/status",
                timeout=0.5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            # Don't log every poll failure, too spammy
            return None


#=====================================================================
# SceneConnect
#=====================================================================
class SceneConnect:
    """
    Scene for network connectivity and battles.
    """

    def __init__(self) -> None:
        """
        Initializes the connect scene with modern UI system.
        """
        try:
            runtime_globals.game_console.log("[SceneConnect] Starting initialization...")
            
            # Global background (animated)
            self.window_background = WindowBackground(False)
            runtime_globals.game_console.log("[SceneConnect] Background created")
            
            # UI Manager with DARK RED theme
            self.ui_manager = UIManager(theme="RED_DARK_VARIANT")
            self.ui_manager.set_input_manager(runtime_globals.game_input)
            runtime_globals.game_console.log("[SceneConnect] UI Manager created with DARK_RED theme")
            
            # Discord Module (inline implementation)
            self.discord = DiscordModule()
            
            # Phase management
            self.phase = "menu"  # menu, pet_selection, host_join_menu, hosting, joining, device_list, module_check, battle_confirm, connecting
            
            # Selected pets list
            self.selected_pets = []
            self.pets = []  # Actual pet objects for network battle
            
            # UI Components (will be created in _setup_ui)
            self.background = None
            self.title_scene = None
            self.wifi_button = None
            self.online_button = None
            self.discord_link_button = None  # Top-right link button
            self.menu_exit_button = None

            self.pet_selector = None
            self.pet_select_instructions = None
            self.pet_select_confirm_button = None
            self.pet_select_back_button = None
            
            # Host/Join menu (modern UI component)
            self.host_join_menu = None
            
            # Device list menu (modern UI component)
            self.device_list_menu = None
            self.discovered_devices = []
            
            # Network components
            self.host_code = ""
            self.network_thread = None
            self.server_socket = None
            self.client_socket = None
            self.connection_socket = None
            self.is_host = False
            self.connection_established = False
            self.is_online_mode = False
            
            # Battle data
            self.enemy_pet_count = 0
            self.enemy_modules = []
            self.missing_modules = []
            self.enemies = []
            self.chosen_module = None
            self.battle_simulation_data = None
            
            # Hosting/Discovery/Battle UI components (will be created in _setup_ui)
            self.hosting_title_label = None
            self.hosting_code_label = None
            self.hosting_wait_label = None
            self.hosting_cancel_button = None
            self.discovery_title_label = None
            self.discovery_status_label = None
            self.discovery_back_button = None
            self.module_error_title = None
            self.module_error_subtitle = None
            self.module_error_labels = []
            self.module_error_button = None
            self.battle_ready_label = None
            self.battle_enemy_label = None
            self.battle_confirm_button = None
            self.battle_cancel_button = None
            self.connecting_label = None
            self.connecting_wait_label = None

            # Setup UI
            self._setup_ui()

            runtime_globals.game_console.log("[SceneConnect] Connect scene initialized with UI system (DARK_RED theme).")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Initialization error: {e}")
            runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
            raise
    
    def _setup_ui(self):
        """Setup UI components for all phases."""
        ui_width = ui_height = BASE_RESOLUTION
        
        # Background (black, always visible)
        self.background = Background(ui_width, ui_height)
        self.background.set_regions([(0, ui_height, "black")])
        self.ui_manager.add_component(self.background)
        
        # Title
        self.title_scene = TitleScene(0, 5, "CONNECT")
        self.ui_manager.add_component(self.title_scene)
        
        # Setup phase-specific UI components
        self._setup_main_menu_ui()
        self._setup_pet_selection_ui()
        self._setup_hosting_ui()
        self._setup_discovery_ui()
        self._setup_module_error_ui()
        self._setup_battle_confirm_ui()
        self._setup_module_error_ui()
        self._setup_battle_confirm_ui()
        self._setup_connecting_ui()
        self._setup_link_dialog_ui()
        self._setup_discord_browser_ui()
        self._setup_discord_browser_ui()
        self._setup_discord_hosting_ui()
        
        # Initial status update
        self._update_discord_button_text()
    
    def _setup_main_menu_ui(self):
        """Setup UI for the main menu phase."""
        button_width = 160
        button_height = 60
        button_x = (BASE_RESOLUTION - button_width) // 2
        button_y = 60
        
        # Link Button (Top Right)
        link_w = 40
        link_h = 24
        link_x = BASE_RESOLUTION - link_w - 5
        link_y = 5
        
        self.discord_link_button = Button(
            link_x, link_y, link_w, link_h, "Link", 
            self._on_discord_button_clicked,
            shadow_mode="component"
        )
        self.ui_manager.add_component(self.discord_link_button)
        
        self.wifi_button = Button(
            button_x, button_y, button_width, button_height,
            "LOCAL BATTLE", self._on_wifi_selected
        )
        self.ui_manager.add_component(self.wifi_button)
        
        # Online battle button
        online_y = button_y + button_height + 10
        self.online_button = Button(
            button_x, online_y, button_width, button_height,
            "ONLINE BATTLE", self._on_online_selected
        )
        self.ui_manager.add_component(self.online_button)
        
        exit_width = 100
        exit_height = 40
        exit_x = (BASE_RESOLUTION - exit_width) // 2
        exit_y = 195
        
        self.menu_exit_button = Button(
            exit_x, exit_y, exit_width, exit_height,
            "EXIT", self._on_main_menu_exit
        )
        self.ui_manager.add_component(self.menu_exit_button)
    
    def _setup_pet_selection_ui(self):
        """Setup UI for pet selection phase."""
        selector_width = 220
        selector_height = 120
        selector_x = (BASE_RESOLUTION - selector_width) // 2
        selector_y = 40
        
        self.pet_selector = PetSelector(selector_x, selector_y, selector_width, selector_height)
        self.pet_selector.set_pets(get_battle_pvp_targets())
        self.pet_selector.set_interactive(True)
        # PetSelector supports multiple selections by default
        self.pet_selector.visible = False
        self.ui_manager.add_component(self.pet_selector)
        
        self.pet_select_instructions = Label(
            10, 165, "Select pets. Press START when ready.", is_title=False
        )
        self.pet_select_instructions.visible = False
        self.ui_manager.add_component(self.pet_select_instructions)
        
        confirm_width = 100
        confirm_height = 35
        confirm_x = 20
        confirm_y = 195
        
        self.pet_select_confirm_button = Button(
            confirm_x, confirm_y, confirm_width, confirm_height,
            "CONFIRM", self._on_pet_selection_confirm
        )
        self.pet_select_confirm_button.visible = False
        self.ui_manager.add_component(self.pet_select_confirm_button)
        
        back_width = 80
        back_height = 35
        back_x = BASE_RESOLUTION - back_width - 20
        back_y = 195
        
        self.pet_select_back_button = Button(
            back_x, back_y, back_width, back_height,
            "BACK", self._on_pet_selection_back
        )
        self.pet_select_back_button.visible = False
        self.ui_manager.add_component(self.pet_select_back_button)
    
    def _setup_hosting_ui(self):
        """Setup UI for hosting phase."""
        # Note: Label doesn't support centered parameter, position manually
        self.hosting_title_label = Label(
            10, 60, "Hosting Network Battle", is_title=False
        )
        self.hosting_title_label.visible = False
        self.ui_manager.add_component(self.hosting_title_label)
        
        self.hosting_code_label = Label(
            10, 100, "Host Code: ----", is_title=False
        )
        self.hosting_code_label.visible = False
        self.ui_manager.add_component(self.hosting_code_label)
        
        self.hosting_wait_label = Label(
            10, 140, "Waiting for other device...", is_title=False
        )
        self.hosting_wait_label.visible = False
        self.ui_manager.add_component(self.hosting_wait_label)
        
        cancel_width = 100
        cancel_height = 35
        cancel_x = (BASE_RESOLUTION - cancel_width) // 2
        cancel_y = 190
        
        self.hosting_cancel_button = Button(
            cancel_x, cancel_y, cancel_width, cancel_height,
            "CANCEL", self._on_hosting_cancel
        )
        self.hosting_cancel_button.visible = False
        self.ui_manager.add_component(self.hosting_cancel_button)
    
    def _setup_discovery_ui(self):
        """Setup UI for device discovery phase."""
        self.discovery_title_label = Label(
            10, 60, "Searching for devices...", is_title=False
        )
        self.discovery_title_label.visible = False
        self.ui_manager.add_component(self.discovery_title_label)
        
        self.discovery_status_label = Label(
            10, 100, "Please wait...", is_title=False
        )
        self.discovery_status_label.visible = False
        self.ui_manager.add_component(self.discovery_status_label)
        
        back_width = 100
        back_height = 35
        back_x = (BASE_RESOLUTION - back_width) // 2
        back_y = 190
        
        self.discovery_back_button = Button(
            back_x, back_y, back_width, back_height,
            "CANCEL", self._on_discovery_cancel
        )
        self.discovery_back_button.visible = False
        self.ui_manager.add_component(self.discovery_back_button)
    
    def _setup_module_error_ui(self):
        """Setup UI for module compatibility error phase."""
        self.module_error_title = Label(
            10, 60, "Module Error!", is_title=False
        )
        self.module_error_title.visible = False
        self.ui_manager.add_component(self.module_error_title)
        
        self.module_error_subtitle = Label(
            10, 90, "Missing modules:", is_title=False
        )
        self.module_error_subtitle.visible = False
        self.ui_manager.add_component(self.module_error_subtitle)
        
        for i in range(5):
            label = Label(
                10, 120 + (i * 20), "", is_title=False
            )
            label.visible = False
            self.module_error_labels.append(label)
            self.ui_manager.add_component(label)
        
        button_width = 100
        button_height = 35
        button_x = (BASE_RESOLUTION - button_width) // 2
        button_y = 190
        
        self.module_error_button = Button(
            button_x, button_y, button_width, button_height,
            "CONTINUE", self._on_module_error_continue
        )
        self.module_error_button.visible = False
        self.ui_manager.add_component(self.module_error_button)
    
    def _setup_battle_confirm_ui(self):
        """Setup UI for battle confirmation phase."""
        self.battle_ready_label = Label(
            10, 70, "Connection Established!", is_title=False
        )
        self.battle_ready_label.visible = False
        self.ui_manager.add_component(self.battle_ready_label)
        
        self.battle_enemy_label = Label(
            10, 110, "Enemy has X pets", is_title=False
        )
        self.battle_enemy_label.visible = False
        self.ui_manager.add_component(self.battle_enemy_label)
        
        confirm_width = 85
        confirm_height = 35
        confirm_x = 25
        confirm_y = 190
        
        self.battle_confirm_button = Button(
            confirm_x, confirm_y, confirm_width, confirm_height,
            "START", self._on_battle_confirm
        )
        self.battle_confirm_button.visible = False
        self.ui_manager.add_component(self.battle_confirm_button)
        
        cancel_width = 85
        cancel_height = 35
        cancel_x = 130
        cancel_y = 190
        
        self.battle_cancel_button = Button(
            cancel_x, cancel_y, cancel_width, cancel_height,
            "GIVE UP", self._on_battle_cancel
        )
        self.battle_cancel_button.visible = False
        self.ui_manager.add_component(self.battle_cancel_button)
    
    def _setup_connecting_ui(self):
        """Setup UI for connecting phase."""
        self.connecting_label = Label(
            10, 100, "Connecting...", is_title=False
        )
        self.connecting_label.visible = False
        self.ui_manager.add_component(self.connecting_label)
        
        self.connecting_wait_label = Label(
            10, 140, "Waiting for opponent confirmation", is_title=False
        )
        self.connecting_wait_label.visible = False
        self.ui_manager.add_component(self.connecting_wait_label)
    
        self.connecting_wait_label.visible = False
        self.ui_manager.add_component(self.connecting_wait_label)

    def _setup_link_dialog_ui(self):
        """Setup UI for Discord link dialog."""
        # Dialog Background (simple centered box)
        # For now, just labels and components on top of dimmed background
        
        self.link_title = Label(
            0, 40, "Enter Pairing Code", is_title=True
        )
        self.link_title.visible = False
        self.ui_manager.add_component(self.link_title)
        
        # Code Entry
        self.code_entry = CodeEntry(
            (BASE_RESOLUTION - 190) // 2, 80, length=4
        )
        self.code_entry.visible = False
        self.ui_manager.add_component(self.code_entry)
        
        # Helper text
        self.link_instruction = Label(
            0, 140, "Use !link in Discord to get code", is_title=False
        )
        self.link_instruction.visible = False
        self.ui_manager.add_component(self.link_instruction)
        
        # Buttons
        btn_y = 170
        btn_w = 80
        btn_h = 30
        gap = 20
        
        self.link_confirm_btn = Button(
            (BASE_RESOLUTION // 2) - btn_w - (gap//2), btn_y, btn_w, btn_h,
            "Confirm", self._on_link_confirm
        )
        self.link_confirm_btn.visible = False
        self.ui_manager.add_component(self.link_confirm_btn)
        
        self.link_cancel_btn = Button(
            (BASE_RESOLUTION // 2) + (gap//2), btn_y, btn_w, btn_h,
            "Cancel", self._on_link_cancel
        )
        self.link_cancel_btn.visible = False
        self.ui_manager.add_component(self.link_cancel_btn)

    def _setup_discord_browser_ui(self):
        """Setup UI for browsing Discord rooms."""
        self.browser_title = Label(
            0, 40, "Online Rooms", is_title=True
        )
        self.browser_title.visible = False
        self.ui_manager.add_component(self.browser_title)
        
        self.browser_status = Label(
            0, 70, "Searching...", is_title=False
        )
        self.browser_status.visible = False
        self.ui_manager.add_component(self.browser_status)
        
        # Using Menu component as the list
        self.room_list_menu = Menu(
            width=BASE_RESOLUTION-40, height=110
        )
        # Open with callbacks (auto_center=False to keep manual position)
        self.room_list_menu.open(
            options=[],
            on_select=self._on_room_selected,
            auto_center=False
        )
        
        # Position manually
        self.room_list_menu.set_position(20, 90)
        
        self.room_list_menu.visible = False
        self.ui_manager.add_component(self.room_list_menu)
        
        self.browser_refresh_btn = Button(
            20, 205, 80, 30, "Refresh", self._on_browser_refresh
        )
        self.browser_refresh_btn.visible = False
        self.ui_manager.add_component(self.browser_refresh_btn)
        
        self.browser_back_btn = Button(
            BASE_RESOLUTION - 100, 205, 80, 30, "Back", self._on_browser_back
        )
        self.browser_back_btn.visible = False
        self.ui_manager.add_component(self.browser_back_btn)

    def _setup_discord_hosting_ui(self):
        """Setup UI for Discord hosting phase."""
        self.discord_host_title = Label(
            0, 40, "Hosting Room...", is_title=True
        )
        self.discord_host_title.visible = False
        self.ui_manager.add_component(self.discord_host_title)
        
        self.discord_host_status = Label(
            0, 80, "Creating Room...", is_title=False
        )
        self.discord_host_status.visible = False
        self.ui_manager.add_component(self.discord_host_status)
        
        self.discord_host_cancel = Button(
            (BASE_RESOLUTION - 120)//2, 180, 120, 30, "Cancel", self._on_discord_hosting_cancel
        )
        self.discord_host_cancel.visible = False
        self.ui_manager.add_component(self.discord_host_cancel)
    
    # Button Callbacks
    def _on_wifi_selected(self):
        """Called when WIFI BATTLE button is clicked."""
        runtime_globals.game_console.log("[SceneConnect] WiFi battle selected")
        self.is_online_mode = False
        self.set_phase("pet_selection")
        self._show_phase_components("pet_selection")
    
    def _on_online_selected(self):
        """Called when ONLINE BATTLE button is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Online battle selected")
        
        # Ensure connection check is performed if needed
        self._ensure_discord_connection()
        
        # Check if user is logged in
        if not self.discord or not self.discord.get_account_name():
            runtime_globals.game_console.log("[SceneConnect] Not logged in, showing link dialog")
            self.is_online_mode = True  # Set mode before showing link dialog
            self.set_phase("link_dialog")
            self._show_phase_components("link_dialog")
            return
        
        self.is_online_mode = True
        self.set_phase("pet_selection")
        self._show_phase_components("pet_selection")
    
    def _on_discord_button_clicked(self):
        """Called when Discord Link/Unlink button is clicked."""
        if not self.discord:
            runtime_globals.game_console.log("[SceneConnect] Discord module not available")
            return
            
        if self.discord.get_account_name():
            # Already linked -> Unlink confirmation
            # For now, just unlink immediately or show simple confirmation
            runtime_globals.game_console.log("[SceneConnect] Unlinking account...")
            self.discord.logout()
            self._update_discord_button_text()
        else:
            # Not linked -> Link dialog
            self.set_phase("link_dialog")
            self._show_phase_components("link_dialog")
            
    def _on_link_confirm(self):
        """Called when Confirm button on link dialog is clicked."""
        code = self.code_entry.get_text()
        runtime_globals.game_console.log(f"[SceneConnect] Linking with code: {code}")
        
        # Link account
        if self.discord:
            success = self.discord.login(code)
            if success:
                runtime_globals.game_console.log("[SceneConnect] Link successful!")
                self._update_discord_button_text()
                
                # If we came here from online battle selection, continue to pet selection
                if self.is_online_mode:
                    self.set_phase("pet_selection")
                    self._show_phase_components("pet_selection")
                else:
                    # Otherwise return to menu
                    self.set_phase("menu")
                    self._show_phase_components("menu")
            else:
                runtime_globals.game_console.log("[SceneConnect] Link failed")
                # TODO: Show error
                self.link_instruction.set_text("Link Failed! Try again.")
    
    def _on_link_cancel(self):
        """Called when Cancel button on link dialog is clicked."""
        self.set_phase("menu")
        self._show_phase_components("menu")
            
    def _update_discord_button_text(self):
        """Updates the text of the Discord button based on connection status."""
        if not self.discord_link_button:
            return
            
        if self.discord and self.discord.get_account_name():
            self.discord_link_button.set_text("Unlink")
            # Optional: Change color to indicate connected (e.g. Green)
        else:
            self.discord_link_button.set_text("Link")
    
    def _on_main_menu_exit(self):
        """Called when EXIT button on main menu is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Exiting to main menu")
        change_scene("game")
    
    def _on_pet_selection_confirm(self):
        """Called when CONFIRM button on pet selection is clicked."""
        self.selected_pets = self.pet_selector.get_selected_pets()
        if self.selected_pets:
            runtime_globals.game_console.log(f"[SceneConnect] Pets selected: {len(self.selected_pets)}")
            # Set self.pets for compatibility with network methods
            self.pets = self.selected_pets
            self.set_phase("host_join_menu")
            self._show_phase_components("host_join_menu")
        else:
            runtime_globals.game_console.log("[SceneConnect] No pets selected")
    
    def _on_pet_selection_back(self):
        """Called when BACK button on pet selection is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Back to main menu")
        self.set_phase("menu")
        self._show_phase_components("menu")
    
    def _on_hosting_cancel(self):
        """Called when CANCEL button on hosting screen is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Hosting cancelled")
        self.stop_networking()
        self.set_phase("host_join_menu")
        self._show_phase_components("host_join_menu")
    
    def _on_discovery_cancel(self):
        """Called when CANCEL button on discovery screen is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Discovery cancelled")
        self.stop_networking()
        self.set_phase("host_join_menu")
        self._show_phase_components("host_join_menu")
    
    def _on_module_error_continue(self):
        """Called when CONTINUE button on module error screen is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Continuing despite module error")
        self.set_phase("menu")
        self._show_phase_components("menu")
    
    def _on_battle_confirm(self):
        """Called when START button on battle confirm is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Battle confirmed - starting")
        
        if self.is_online_mode and hasattr(self, 'discord') and self.discord:
             runtime_globals.game_console.log("[SceneConnect] Confirmed Ready for Discord Battle")
             self.discord_ready = True
             msg = {"type": "ready", "sender": "host" if self.is_host else "guest"}
             self.discord.send_data(msg)
             # Update UI to show waiting
             self.battle_confirm_button.visible = False
             self.battle_ready_label.set_text("Waiting for opponent...")
             self.battle_ready_label.visible = True
             
             # If host, check complete
             self._check_start_discord_sim()
        else:
             self.set_phase("connecting")
             self._show_phase_components("connecting")
             self._pending_start_battle = True
             self._pending_start_time = time.time()
    
    def _on_battle_cancel(self):
        """Called when GIVE UP button on battle confirm is clicked."""
        runtime_globals.game_console.log("[SceneConnect] Battle cancelled")
        self.stop_networking()
        self.set_phase("menu")
        self._show_phase_components("menu")
    
    def _on_host_join_select(self, option_index):
        """Called when an option is selected from the host/join menu."""
        option = self.host_join_menu.options[option_index]
        runtime_globals.game_console.log(f"[SceneConnect] Host/Join selected: {option}, Online Mode: {self.is_online_mode}")
        
        # Close menu
        if self.host_join_menu:
            self.host_join_menu.close()
            # Reset active menu so it doesn't eat inputs
            if self.ui_manager.active_menu == self.host_join_menu:
                self.ui_manager.active_menu = None
        
        if option == "Host":
            if self.is_online_mode:
                self.is_host = True  # Set host flag for Discord hosting
                self.set_phase("discord_hosting")
                self._show_phase_components("discord_hosting")
            else:
                self.start_hosting()
        elif option == "Join":
            if self.is_online_mode:
                self.is_host = False  # Set guest flag for Discord joining
                self.set_phase("discord_browser")
                self._show_phase_components("discord_browser")
            else:
                self.start_joining()
        elif option == "Back":
            runtime_globals.game_sound.play("cancel")
            self.set_phase("pet_selection")
            self._show_phase_components("pet_selection")
    
    def _on_host_join_cancel(self):
        """Called when host/join menu is cancelled."""
        runtime_globals.game_console.log("[SceneConnect] Host/Join menu cancelled")
        self.set_phase("pet_selection")
        self._show_phase_components("pet_selection")
    
    def _on_device_selected(self, option_index):
        """Called when a device is selected from the device list."""
        if option_index < len(self.discovered_devices):
            device_info = self.discovered_devices[option_index]
            runtime_globals.game_console.log(f"[SceneConnect] Device selected: {device_info['host_code']}")
            
            # Run connection in a separate thread to avoid blocking UI
            connection_thread = threading.Thread(target=self.connect_to_device, args=(device_info,), daemon=True)
            connection_thread.start()
    
    def _on_device_list_cancel(self):
        """Called when device list menu is cancelled."""
        runtime_globals.game_console.log("[SceneConnect] Device list cancelled")
        self.stop_networking()
        self.set_phase("host_join_menu")
        self._show_phase_components("host_join_menu")
    
    def _show_phase_components(self, phase: str):
        """Show components for the given phase, hide all others."""
        self._hide_all_phase_components()
        
        if phase == "menu":
            self.wifi_button.visible = True
            self.online_button.visible = True
            self.discord_link_button.visible = True
            self.menu_exit_button.visible = True
            self._update_discord_button_text()
        
        elif phase == "link_dialog":
            self.link_title.visible = True
            self.code_entry.visible = True
            self.link_instruction.visible = True
            self.link_confirm_btn.visible = True
            self.link_cancel_btn.visible = True
            
            # Reset instruction and code entry
            self.link_instruction.set_text("Use !link in Discord to get code")
            # Reset code entry to default state (all 'A's)
            self.code_entry.chars = ['A'] * self.code_entry.length
            self.code_entry.cursor_pos = 0
            self.code_entry.needs_redraw = True
            
            # Give focus to code entry so it can receive keyboard input
            self.ui_manager.set_focused_component(self.code_entry)
        
        elif phase == "pet_selection":
            self.pet_selector.visible = True
            self.pet_select_instructions.visible = True
            self.pet_select_confirm_button.visible = True
            self.pet_select_back_button.visible = True
        
        elif phase == "host_join_menu":
            # Create and show the host/join menu
            self.show_host_join_menu()
        
        elif phase == "hosting":
            self.hosting_title_label.visible = True
            self.hosting_code_label.visible = True
            self.hosting_code_label.set_text(f"Host Code: {self.host_code or '----'}")
            self.hosting_wait_label.visible = True
            self.hosting_cancel_button.visible = True
        
        elif phase == "joining":
            self.discovery_title_label.visible = True
            self.discovery_status_label.visible = True
            self.discovery_back_button.visible = True
        
        elif phase == "device_list":
            # Device list is shown via the Menu component (device_list_menu)
            # No additional UI components needed - menu handles everything
            pass
        
        elif phase == "module_check":
            self.module_error_title.visible = True
            self.module_error_subtitle.visible = True
            for i, module_name in enumerate(self.missing_modules[:5]):
                if i < len(self.module_error_labels):
                    self.module_error_labels[i].set_text(module_name)
                    self.module_error_labels[i].visible = True
            self.module_error_button.visible = True
        
        elif phase == "battle_confirm":
            self.battle_ready_label.visible = True
            self.battle_enemy_label.visible = True
            self.battle_enemy_label.set_text(f"Enemy has {self.enemy_pet_count} pets")
            self.battle_confirm_button.visible = True
            self.battle_cancel_button.visible = True
        
        elif phase == "connecting":
            self.connecting_label.visible = True
            self.connecting_wait_label.visible = True
            
        elif phase == "discord_browser":
            self.browser_title.visible = True
            self.browser_status.visible = True
            self.room_list_menu.visible = True
            self.browser_refresh_btn.visible = True
            self.browser_back_btn.visible = True
            
            # Start refreshing rooms
            self._refresh_discord_rooms()
            
        elif phase == "discord_hosting":
            self.discord_host_title.visible = True
            self.discord_host_status.visible = True
            self.discord_host_cancel.visible = True
            
            # Initiate hosting
            self._start_discord_hosting()
            
    def _ensure_discord_connection(self):
        """Ensure we have checked connection status at least once."""
        if self.discord and not self.discord.is_connected:
            runtime_globals.game_console.log("[SceneConnect] Checking Discord connection on demand...")
            if self.discord.client:
                self.discord.is_connected = self.discord.client.check_connection()
                if self.discord.is_connected:
                     runtime_globals.game_console.log("[SceneConnect] Connected!")
                else:
                     runtime_globals.game_console.log("[SceneConnect] Failed to connect")
    
    def _hide_all_phase_components(self):
        """Hide all phase-specific components."""
        # Menu
        self.wifi_button.visible = False
        self.online_button.visible = False
        self.discord_link_button.visible = False
        self.menu_exit_button.visible = False
        
        # Link Dialog
        if hasattr(self, 'link_title'): self.link_title.visible = False
        if hasattr(self, 'code_entry'): self.code_entry.visible = False
        if hasattr(self, 'link_instruction'): self.link_instruction.visible = False
        if hasattr(self, 'link_confirm_btn'): self.link_confirm_btn.visible = False
        if hasattr(self, 'link_cancel_btn'): self.link_cancel_btn.visible = False
        
        # Pet Selection
        self.pet_selector.visible = False
        self.pet_select_instructions.visible = False
        self.pet_select_confirm_button.visible = False
        self.pet_select_back_button.visible = False
        
        # Hosting
        if self.hosting_title_label:
            self.hosting_title_label.visible = False
            self.hosting_code_label.visible = False
            self.hosting_wait_label.visible = False
            self.hosting_cancel_button.visible = False
        
        # Discovery
        if self.discovery_title_label:
            self.discovery_title_label.visible = False
            self.discovery_status_label.visible = False
            self.discovery_back_button.visible = False
        
        # Module Error
        if self.module_error_title:
            self.module_error_title.visible = False
            self.module_error_subtitle.visible = False
            for label in self.module_error_labels:
                label.visible = False
            self.module_error_button.visible = False
        
        # Battle Confirm
        if self.battle_ready_label:
            self.battle_ready_label.visible = False
            self.battle_enemy_label.visible = False
            self.battle_confirm_button.visible = False
            self.battle_cancel_button.visible = False
        
        # Connecting
        if self.connecting_label:
            self.connecting_label.visible = False
            self.connecting_wait_label.visible = False

        # Discord Browser
        if hasattr(self, 'browser_title'): self.browser_title.visible = False
        if hasattr(self, 'browser_status'): self.browser_status.visible = False
        if hasattr(self, 'room_list_menu'): self.room_list_menu.visible = False
        if hasattr(self, 'browser_refresh_btn'): self.browser_refresh_btn.visible = False
        if hasattr(self, 'browser_back_btn'): self.browser_back_btn.visible = False

        # Discord Hosting
        if hasattr(self, 'discord_host_title'): self.discord_host_title.visible = False
        if hasattr(self, 'discord_host_status'): self.discord_host_status.visible = False
        if hasattr(self, 'discord_host_cancel'): self.discord_host_cancel.visible = False

    def update(self) -> None:
        """
        Updates the connect scene with UI manager.
        """
        # Update UI manager (handles button hovers, etc.)
        self.ui_manager.update()
        
        # Discord network updates
        if self.is_online_mode and hasattr(self, 'discord') and self.discord:
             self._update_discord_networking()
        
        # Handle phase changes from network threads
        if hasattr(self, '_phase_changed'):
            delattr(self, '_phase_changed')
            
        # Handle async room updates
        if getattr(self, '_rooms_updated', False):
            self._rooms_updated = False
            rooms = getattr(self, '_fetched_rooms', [])
            self._current_rooms = rooms # Keep reference
            
            if not rooms:
                self.browser_status.set_text("No rooms found.")
                # Clear menu
                self.room_list_menu.update_options([], auto_center=False)
            else:
                 self.browser_status.set_text(f"Found {len(rooms)} rooms")
                 room_labels = [f"{r.get('host', '?')}" for r in rooms]
                 self.room_list_menu.open(
                     options=room_labels,
                     on_select=self._on_room_selected,
                     auto_center=False
                 )
        
        # Handle async hosting updates
        if getattr(self, '_hosting_created', False):
            self._hosting_created = False
            room_id = getattr(self, '_hosting_room_id', 'Unknown')
            # For Discord, the room ID is the code. Join it ourselves to listen.
            # self.discord.join_room(room_id) # Auto-join as host? The API might assume host is joined.
            
            # Show status
            self.discord_host_status.set_text("Room Created!\nWaiting for opponent...")
            
            # Store room ID and initialize polling flag
            self._hosting_room_id = room_id
            self._polling = False  # Ensure flag is initialized
            
            # Now we wait for POLL updates to see if someone joined
            # Polling is handled by _update_discord_networking() in the update loop

        if getattr(self, '_hosting_error', None):
            error = self._hosting_error
            self._hosting_error = None
            self.discord_host_status.set_text(f"Error: {error}")
            
        # Handle async polling (someone joined)
        if getattr(self, '_discord_opponent_found', False):
             self._discord_opponent_found = False
             # Determine who is player 1 vs 2 based on room data?
             # For now assume host is player 1, guest is player 2
             runtime_globals.game_console.log("Opponent found! Starting battle...")
             self.set_phase("connecting")
             self._pending_start_battle = True
             self._pending_start_time = time.time()
        
        # If a battle start was requested from the input handler, wait a small
        # amount of time to allow the UI to draw the "connecting" state, then
        # actually start the PvP sequence.
        if getattr(self, "_pending_start_battle", False):
            current_time = time.time()
            start_time = getattr(self, "_pending_start_time", 0)
            elapsed = current_time - start_time
            
            # require a short delay so draw has a chance to run at least once
            if elapsed >= 0.05:
                try:
                    runtime_globals.game_console.log(f"[SceneConnect] ===== EXECUTING PENDING BATTLE (elapsed: {elapsed:.3f}s) =====")
                    runtime_globals.game_console.log(f"[SceneConnect] Phase: {self.phase}, Online: {self.is_online_mode}, Host: {self.is_host}")
                    # clear flag before calling to avoid re-entrancy
                    self._pending_start_battle = False
                    delattr(self, "_pending_start_time")
                    runtime_globals.game_console.log("[SceneConnect] Calling start_pvp_battle()...")
                    self.start_pvp_battle()
                    runtime_globals.game_console.log("[SceneConnect] start_pvp_battle() returned")
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] ===== ERROR in pending PvP battle: {e} =====")
                    import traceback
                    runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
                    self._pending_start_battle = False
                    self.phase = "menu"
                    delattr(self, "_pending_start_time")
                    if self.is_online_mode and hasattr(self, 'discord') and self.discord:
                        self.start_discord_battle_sequence()
                    else:
                        self.start_pvp_battle()
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Error starting pending PvP battle: {e}")
                    import traceback
                    runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
                    self._pending_start_battle = False
                    self.phase = "menu"
            

    def set_phase(self, new_phase: str) -> None:
        """Safely sets a new phase and invalidates cache."""
        if self.phase != new_phase:
            runtime_globals.game_console.log(f"[SceneConnect] ===== PHASE CHANGE: {self.phase} -> {new_phase} =====")
            runtime_globals.game_console.log(f"[SceneConnect] Online mode: {self.is_online_mode}, Host: {self.is_host}")
            self.phase = new_phase
            self._phase_changed = True
            self._cache_surface = None

    def __del__(self):
        """Cleanup when scene is destroyed."""
        runtime_globals.game_console.log("[SceneConnect] Scene being destroyed")
        self.stop_networking()
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the connect scene with UI manager.
        """
        try:
            # Draw window background (NOT managed by UI manager)
            self.window_background.draw(surface)
            
            # Draw UI components (includes host_join_menu which is now a UI component)
            self.ui_manager.draw(surface)
            
            # Draw legacy device_list_menu if still using old WindowMenu
            if self.phase == "device_list" and self.device_list_menu:
                self.device_list_menu.draw(surface)
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Draw error: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")

    def handle_event(self, event) -> None:
        """
        Handles keyboard and GPIO button inputs for the connect scene.
        """
        if not isinstance(event, tuple) or len(event) != 2:
            return False
        
        event_type, event_data = event
        runtime_globals.game_console.log(f"[SceneConnect] Input received: {event_type} in phase: {self.phase}")
        
        # Let UI manager handle events (it will check for mouse internally)
        if self.ui_manager.handle_event(event):
            runtime_globals.game_console.log("[SceneConnect] UI component handled event")
            return
        
        # Phase-specific keyboard/button input
        if self.phase == "menu":
            self.handle_menu_input(event_type)
        elif self.phase == "pet_selection":
            self.handle_pet_selection_input(event_type)
        elif self.phase == "host_join_menu":
            self.handle_host_join_input(event_type)
        elif self.phase == "hosting":
            self.handle_hosting_input(event_type)
        elif self.phase == "joining" or self.phase == "device_list":
            self.handle_device_list_input(event_type)
        elif self.phase == "module_check":
            self.handle_module_check_input(event_type)
        elif self.phase == "battle_confirm":
            self.handle_battle_confirm_input(event_type)
        elif self.phase == "link_dialog":
            self.handle_link_dialog_input(event_type)
        elif self.phase == "discord_browser":
            self.handle_discord_browser_input(event_type)
        elif self.phase == "discord_hosting":
            self.handle_discord_hosting_input(event_type)

    def handle_menu_input(self, input_action) -> None:
        """Handles input for the main menu phase (keyboard navigation)."""
        runtime_globals.game_console.log(f"[SceneConnect] Menu input: {input_action}")
        
        if input_action == "B":  # ESC button - exit to main game
            self._on_main_menu_exit()
        elif input_action == "A":  # Select WIFI BATTLE
            self._on_wifi_selected()

    def handle_pet_selection_input(self, input_action) -> None:
        """Handles input for pet selection phase (keyboard navigation)."""
        runtime_globals.game_console.log(f"[SceneConnect] Pet selection input: {input_action}")
        if input_action == "B":
            # Handled by back button callback
            self._on_pet_selection_back()
        elif input_action in ("LEFT", "RIGHT", "UP", "DOWN"):
            # Navigate pet selector
            self.pet_selector.handle_input(input_action)
        elif input_action == "A":
            # Toggle pet selection
            self.pet_selector.handle_input(input_action)
        elif input_action == "START":
            # Confirm selection (same as CONFIRM button)
            self._on_pet_selection_confirm()

    def handle_host_join_input(self, input_action) -> None:
        """Handles input for host/join menu - menu handles input through UI manager."""
        # The Menu component handles all input through the UI manager and callbacks
        # This method is kept for logging purposes only
        runtime_globals.game_console.log(f"[SceneConnect] Host/Join menu active, input: {input_action}")

    def handle_hosting_input(self, input_action) -> None:
        """Handles input while hosting (waiting for connections)."""
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.stop_networking()
            self.phase = "host_join_menu"

    def handle_device_list_input(self, input_action) -> None:
        """Handles input for device list selection."""
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.stop_networking()
            self.phase = "host_join_menu"
        elif self.device_list_menu and len(self.discovered_devices) > 0:
            if input_action in ("UP", "DOWN"):
                self.device_list_menu.handle_event(input_action)
            elif input_action == "A":
                selected_device = self.discovered_devices[self.device_list_menu.menu_index]
                self.connect_to_device(selected_device)

    def handle_module_check_input(self, input_action) -> None:
        """Handles input for module compatibility error screen."""
        if input_action == "A" or input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.stop_networking()
            self.phase = "menu"

    def handle_link_dialog_input(self, input_action) -> None:
        """Handles input for Discord link dialog."""
        # B cancels, START confirms
        if input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self._on_link_cancel()
        elif input_action == "START":
            runtime_globals.game_sound.play("menu")
            self._on_link_confirm()
        # All other input (LEFT/RIGHT/A/UP/DOWN) goes to code_entry via UI manager

    def handle_battle_confirm_input(self, input_action) -> None:
        """Handles input for battle confirmation screen."""
        runtime_globals.game_console.log(f"[SceneConnect] Battle confirm input: {input_action}, phase={self.phase}, online={self.is_online_mode}, host={self.is_host}")
        if input_action == "A":
            runtime_globals.game_sound.play("menu")
            
            if self.is_online_mode and hasattr(self, 'discord') and self.discord:
                runtime_globals.game_console.log("[SceneConnect] ===== DISCORD BATTLE START =====")
                runtime_globals.game_console.log(f"[SceneConnect] Role: {'HOST' if self.is_host else 'GUEST'}")
                runtime_globals.game_console.log(f"[SceneConnect] Pets: {len(self.pets)}")
                self.discord_ready = True
                msg = {"type": "ready", "sender": "host" if self.is_host else "guest"}
                runtime_globals.game_console.log(f"[SceneConnect] Sending ready message: {msg}")
                self.discord.send_data(msg)
                
                # If host, check complete
                self._check_start_discord_sim()
            else:
                runtime_globals.game_console.log("[SceneConnect] ===== WIFI BATTLE START =====")
                runtime_globals.game_console.log(f"[SceneConnect] Role: {'HOST' if self.is_host else 'CLIENT'}")
                runtime_globals.game_console.log(f"[SceneConnect] Pets: {len(self.pets)}")
                runtime_globals.game_console.log(f"[SceneConnect] Setting phase to connecting and pending flag")
                # Use flag-based approach - let update() handle the actual start
                self.set_phase("connecting")
                self._show_phase_components("connecting")
                self._pending_start_battle = True
                self._pending_start_time = time.time()
                runtime_globals.game_console.log(f"[SceneConnect] Pending flag set at {self._pending_start_time}")
        elif input_action == "B":
            runtime_globals.game_sound.play("cancel")
            self.stop_networking()
            self.phase = "menu"

    def confirm_selection(self) -> None:
        """
        Handles the selection of a menu option.
        """
        if self.selected_index == 0:  # Wifi option
            runtime_globals.game_sound.play("menu")
            runtime_globals.game_console.log(f"[SceneConnect] Transitioning to pet selection. Available pets: {len(get_battle_pvp_targets())}")
            self.phase = "pet_selection"
            self.pet_list_window.selection_label = "Network Battle"
            self.pet_list_window.select_mode = True
            self.pet_list_window.max_selection = len(get_battle_pvp_targets())  # Allow selecting all pets
            runtime_globals.game_console.log("[SceneConnect] WiFi option selected - entering pet selection")

    def show_host_join_menu(self) -> None:
        """Shows the Host/Join menu after pet selection."""
        runtime_globals.game_console.log("[SceneConnect] Opening host/join menu")
        
        # Create menu if it doesn't exist
        if not self.host_join_menu:
            self.host_join_menu = Menu(width=120, height=120)
            self.ui_manager.add_component(self.host_join_menu)
        
        # Open with callbacks
        self.host_join_menu.open(
            options=["Host", "Join", "Back"],
            on_select=self._on_host_join_select,
            on_cancel=self._on_host_join_cancel
        )
        
        # Set as active menu so UIManager gives it event priority
        self.ui_manager.active_menu = self.host_join_menu
        
        self.phase = "host_join_menu"

    def start_hosting(self) -> None:
        """Starts hosting mode with a host code."""
        runtime_globals.game_sound.play("menu")
        self.is_host = True
        self.host_code = self.generate_host_code()
        self.phase = "hosting"
        
        # Show hosting UI
        self._show_phase_components("hosting")
        
        # Start network thread for hosting
        self.network_thread = threading.Thread(target=self.host_network, daemon=True)
        self.network_thread.start()
        
        runtime_globals.game_console.log(f"[SceneConnect] Started hosting with code: {self.host_code}")

    def start_joining(self) -> None:
        """Starts joining mode to discover available hosts."""
        runtime_globals.game_sound.play("menu")
        self.is_host = False
        self.phase = "joining"
        self.discovered_devices = []
        
        # Show discovery UI
        self._show_phase_components("joining")
        
        # Start network thread for discovery
        self.network_thread = threading.Thread(target=self.discover_devices, daemon=True)
        self.network_thread.start()
        
        runtime_globals.game_console.log("[SceneConnect] Started device discovery...")
        
    def _refresh_discord_rooms(self):
        """Fetch available rooms from Discord."""
        if not self.discord:
            return
            
        self.browser_status.set_text("Fetching rooms...")
        
        # Run in thread to avoid blocking UI
        def fetch_thread():
            try:
                rooms = self.discord.get_available_rooms()
                # Schedule update on main thread (simple way: store in self)
                self._fetched_rooms = rooms
                self._rooms_updated = True
            except Exception as e:
                runtime_globals.game_console.log(f"[SceneConnect] Error fetching rooms: {e}")
                self._fetched_rooms = []
                self._rooms_updated = True
        
        threading.Thread(target=fetch_thread, daemon=True).start()

    def _on_browser_refresh(self):
        runtime_globals.game_sound.play("menu")
        self._refresh_discord_rooms()
        
    def _on_browser_back(self):
        runtime_globals.game_sound.play("cancel")
        self.set_phase("menu")
        self._show_phase_components("menu")

    def _on_room_selected(self, index, option_text=None):
        """Called when a room is selected from the menu."""
        runtime_globals.game_console.log(f"[SceneConnect] ===== ROOM SELECTED (index={index}) =====")
        if not hasattr(self, '_current_rooms') or index >= len(self._current_rooms):
            runtime_globals.game_console.log(f"[SceneConnect] ERROR: Invalid room index or no rooms")
            return
            
        selected_room = self._current_rooms[index]
        room_id = selected_room.get('id')
        host_name = selected_room.get('host', 'Unknown')
        
        runtime_globals.game_sound.play("menu")
        runtime_globals.game_console.log(f"[SceneConnect] Room ID: {room_id}")
        runtime_globals.game_console.log(f"[SceneConnect] Host: {host_name}")
        runtime_globals.game_console.log(f"[SceneConnect] My pets: {len(self.pets)}")
        
        # Join logic
        self.is_host = False # Force Guest Role
        runtime_globals.game_console.log(f"[SceneConnect] Attempting to join room...")
        success = self.discord.join_room(room_id)
        if success:
             runtime_globals.game_console.log("[SceneConnect] ===== JOIN SUCCESS - SHOWING CONFIRMATION =====")
             # Set enemy count (we don't know yet, but show 1 for now)
             self.enemy_pet_count = 1
             self.battle_enemy_label.set_text(f"Opponent: {host_name}")
             runtime_globals.game_console.log(f"[SceneConnect] Setting phase to battle_confirm")
             # Go to battle_confirm phase (not connecting yet)
             self.set_phase("battle_confirm")
             self._show_phase_components("battle_confirm")
             runtime_globals.game_console.log(f"[SceneConnect] Phase changed to: {self.phase}")
        else:
             runtime_globals.game_console.log("[SceneConnect] ===== JOIN FAILED =====")
             self.browser_status.set_text("Failed to join!")

    def handle_discord_browser_input(self, input_action) -> None:
        """Handles input for discord browser."""
        if input_action == "B":
            self._on_browser_back()
            return
            
        # Menu navigation
        if hasattr(self, 'room_list_menu') and self.room_list_menu.visible:
             if self.room_list_menu.handle_event(input_action):
                 return

        # Explicit button nav (Refresh/Back)
        # For simple version, just use Menu for main nav, and special keys for Refresh
        if input_action == "Y": # Refresh
             self._on_browser_refresh()
             
    def _start_discord_hosting(self):
        """Creates a new Discord room."""
        if not self.discord:
            return
            
        self.discord_host_status.set_text("Requesting room...")
        
        def host_thread():
            self.is_host = True # Force Host Role
            try:
                # Use Tamer name from Discord or fallback
                tamer_name = self.discord.get_account_name() or "Tamer"
                room_name = f"{tamer_name}'s Battle"
                room_id, error = self.discord.create_room(room_name)
                
                if room_id:
                    self._hosting_room_id = room_id
                    self._hosting_created = True
                else:
                    self._hosting_error = f"Error: {error}"
            except Exception as e:
                runtime_globals.game_console.log(f"[SceneConnect] Hosting error: {e}")
                self._hosting_error = str(e)
                
        threading.Thread(target=host_thread, daemon=True).start()
        
    def _on_discord_hosting_cancel(self):
        """Cancel Discord hosting."""
        runtime_globals.game_sound.play("cancel")
        # TODO: Send delete room request?
        self.set_phase("host_join_menu")
        self._show_phase_components("host_join_menu")

    def handle_discord_hosting_input(self, input_action) -> None:
        """Handles input while hosting on Discord."""
        if input_action == "B":
            self._on_discord_hosting_cancel()

    def _start_discord_poll(self, room_id):
        """Polls Discord room for updates (guest join)."""
        def poll_thread():
            self._polling = True
            errors = 0
            while self._polling:
                if errors > 5:
                    self._hosting_error = "Too many polling errors"
                    break
                    
                try:
                    status = self.discord.poll_room()
                    if status and status.get('status') == 'ready':
                        # Someone joined!
                        guests = status.get('guests', [])
                        if len(guests) > 0:
                            runtime_globals.game_console.log(f"[SceneConnect] Guest joined: {guests[0]}")
                            self._discord_opponent_found = True
                            self._polling = False
                            break
                    time.sleep(2) # Poll every 2s
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Poll error: {e}")
                    errors += 1
                    time.sleep(5)
                    
        threading.Thread(target=poll_thread, daemon=True).start()
        
    def stop_networking(self) -> None:
        """Stops all networking components."""
        try:
            runtime_globals.game_console.log("[SceneConnect] Stopping networking components...")
            
            self._polling = False
            
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
                
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
                
            if self.connection_socket:
                try:
                    self.connection_socket.close()
                except:
                    pass
                self.connection_socket = None
                
            if self.device_list_menu:
                self.device_list_menu.close()
                self.device_list_menu = None
                
            # Wait for network thread to finish
            if self.network_thread and self.network_thread.is_alive():
                try:
                    self.network_thread.join(timeout=2.0)
                except:
                    pass
                
            self.connection_established = False
            self.discovered_devices = []
            self.host_code = ""
            
            runtime_globals.game_console.log("[SceneConnect] Network cleanup completed")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Cleanup error: {e}")

    def generate_host_code(self) -> str:
        """Generates a random 4-character host code."""
        return ''.join(random.choices(string.ascii_uppercase, k=4))

    def get_selected_modules(self) -> list:
        """Gets the list of modules for selected pets."""
        modules = set()
        for pet in self.pets:
            modules.add(pet.module)
        return list(modules)

    def check_module_compatibility(self, enemy_modules: list) -> bool:
        """Checks if both devices have all required modules."""
        my_modules = set(runtime_globals.game_modules.keys())
        enemy_module_set = set(enemy_modules)
        
        # Check what modules we're missing that the enemy has
        self.missing_modules = list(enemy_module_set - my_modules)
        
        return len(self.missing_modules) == 0

    def create_battle_data(self) -> dict:
        """Creates battle data to send to other device."""
        return {
                "pet_count": len(self.pets),
            "modules": self.get_selected_modules(),
            "host_code": self.host_code if self.is_host else ""
        }

    def host_network(self) -> None:
        """Network thread function for hosting."""
        try:
            # Start TCP server for connections
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to all interfaces on port 12345
            self.server_socket.bind(('0.0.0.0', 12345))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)  # Allow periodic checking
            
            # Start UDP server for discovery responses
            discovery_thread = threading.Thread(target=self.handle_discovery_requests, daemon=True)
            discovery_thread.start()
            
            runtime_globals.game_console.log("[SceneConnect] Host listening for connections...")
            
            while self.phase == "hosting":
                try:
                    self.connection_socket, addr = self.server_socket.accept()
                    runtime_globals.game_console.log(f"[SceneConnect] Connection from {addr}")
                    
                    # Exchange battle data
                    battle_data = self.create_battle_data()
                    runtime_globals.game_console.log(f"[SceneConnect] Sending battle data to client: {battle_data}")
                    self.connection_socket.send(json.dumps(battle_data).encode())
                    
                    # Set timeout for receiving enemy data
                    self.connection_socket.settimeout(10.0)
                    
                    # Receive enemy data
                    enemy_data_raw = self.connection_socket.recv(1024).decode()
                    runtime_globals.game_console.log(f"[SceneConnect] Received enemy battle data: {enemy_data_raw}")
                    enemy_data = json.loads(enemy_data_raw)
                    self.enemy_pet_count = enemy_data["pet_count"]
                    self.enemy_modules = enemy_data["modules"]
                    
                    if self.check_module_compatibility(self.enemy_modules):
                        self.set_phase("battle_confirm")
                        self._show_phase_components("battle_confirm")
                        self.connection_established = True
                    else:
                        self.set_phase("module_check")
                        self._show_phase_components("module_check")
                        self.connection_socket.close()
                        self.connection_socket = None
                    break
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Host error: {e}")
                    break
                    
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Host setup error: {e}")

    def handle_discovery_requests(self) -> None:
        """Handles UDP discovery requests while hosting."""
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(('0.0.0.0', 12346))
            udp_socket.settimeout(1.0)
            
            runtime_globals.game_console.log("[SceneConnect] UDP discovery listener started on port 12346")
            
            while self.phase == "hosting":
                try:
                    data, addr = udp_socket.recvfrom(1024)
                    message = json.loads(data.decode())
                    
                    runtime_globals.game_console.log(f"[SceneConnect] Received UDP message from {addr}: {message}")
                    
                    if message.get("type") == "discovery" and message.get("request") == "omnipet_hosts":
                        # Respond with our host information
                        response = {
                            "type": "host_announce",
                            "host_code": self.host_code,
                            "pet_count": len(self.pets)
                        }
                        udp_socket.sendto(json.dumps(response).encode(), addr)
                        runtime_globals.game_console.log(f"[SceneConnect] Sent discovery response to {addr}: {response}")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Discovery response error: {e}")
                    runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
                    
            runtime_globals.game_console.log("[SceneConnect] UDP discovery listener stopped")
            udp_socket.close()
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Discovery UDP setup error: {e}")

    def discover_devices(self) -> None:
        """Network thread function for discovering devices."""
        try:
            # Broadcast discovery message
            broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_sock.settimeout(1.0)
            
            discovery_message = json.dumps({"type": "discovery", "request": "omnipet_hosts"})
            
            runtime_globals.game_console.log("[SceneConnect] Starting device discovery...")
            
            # Try to discover devices for 10 seconds
            start_time = time.time()
            while time.time() - start_time < 10 and self.phase == "joining":
                try:
                    # Broadcast discovery message to multiple targets
                    # Try localhost first (for same machine testing)
                    broadcast_sock.sendto(discovery_message.encode(), ('127.0.0.1', 12346))
                    # Try broadcast address for network
                    broadcast_sock.sendto(discovery_message.encode(), ('<broadcast>', 12346))
                    # Try specific subnet broadcast (e.g., 192.168.1.255)
                    try:
                        broadcast_sock.sendto(discovery_message.encode(), ('255.255.255.255', 12346))
                    except:
                        pass
                    
                    runtime_globals.game_console.log("[SceneConnect] Sent discovery broadcasts, waiting for responses...")
                    
                    # Listen for responses
                    data, addr = broadcast_sock.recvfrom(1024)
                    response = json.loads(data.decode())
                    
                    if response.get("type") == "host_announce":
                        device_info = {
                            "host_code": response["host_code"],
                            "address": addr[0],
                            "pet_count": response["pet_count"]
                        }
                        
                        # Add unique devices only
                        if not any(d["host_code"] == device_info["host_code"] for d in self.discovered_devices):
                            self.discovered_devices.append(device_info)
                            runtime_globals.game_console.log(f"[SceneConnect] Found device: {device_info['host_code']}")
                            
                            # Update phase to show device list
                            if self.phase == "joining":
                                self.set_phase("device_list")
                                self.create_device_list_menu()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Discovery error: {e}")
                    
            # If discovery timeout reached and no devices found
            if self.phase == "joining" and len(self.discovered_devices) == 0:
                runtime_globals.game_console.log("[SceneConnect] No devices discovered, returning to host/join menu")
                self.set_phase("host_join_menu")
                    
            broadcast_sock.close()
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Discovery setup error: {e}")

    def create_device_list_menu(self) -> None:
        """Creates the device selection menu using modern Menu component."""
        if self.discovered_devices:
            runtime_globals.game_console.log(f"[SceneConnect] Creating device list menu with {len(self.discovered_devices)} devices")
            
            # Create menu if it doesn't exist
            if not self.device_list_menu:
                self.device_list_menu = Menu(width=160, height=120)
                self.ui_manager.add_component(self.device_list_menu)
            
            # Format device options
            device_options = [f"{device['host_code']} ({device['pet_count']} pets)" for device in self.discovered_devices]
            
            # Open with callbacks
            self.device_list_menu.open(
                options=device_options,
                on_select=self._on_device_selected,
                on_cancel=self._on_device_list_cancel
            )
            
            # Set as active menu
            self.ui_manager.active_menu = self.device_list_menu
            
            runtime_globals.game_console.log("[SceneConnect] Device list menu created and opened")

    def connect_to_device(self, device_info: dict) -> None:
        """Connects to a selected device."""
        try:
            runtime_globals.game_console.log(f"[SceneConnect] Connecting to {device_info['host_code']}...")
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((device_info["address"], 12345))
            
            # Receive host battle data
            host_data_raw = self.client_socket.recv(1024).decode()
            runtime_globals.game_console.log(f"[SceneConnect] Received host battle data: {host_data_raw}")  # LOG
            host_data = json.loads(host_data_raw)
            self.enemy_pet_count = host_data["pet_count"]
            self.enemy_modules = host_data["modules"]
            
            # Send our battle data
            battle_data = self.create_battle_data()
            runtime_globals.game_console.log(f"[SceneConnect] Sending battle data to host: {battle_data}")  # LOG
            self.client_socket.send(json.dumps(battle_data).encode())
            
            if self.check_module_compatibility(self.enemy_modules):
                self.set_phase("battle_confirm")
                self._show_phase_components("battle_confirm")
                self.connection_established = True
                # Set the connection socket for later use
                self.connection_socket = self.client_socket
                runtime_globals.game_console.log("[SceneConnect] Module compatibility check passed - ready for battle")
            else:
                self.set_phase("module_check")
                self._show_phase_components("module_check")
                self.connection_established = False
                if self.client_socket:
                    self.client_socket.close()
                    self.client_socket = None
                runtime_globals.game_console.log(f"[SceneConnect] Module compatibility failed - missing: {self.missing_modules}")
                
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Connection error: {e}")
            runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
            self.set_phase("device_list")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None

    def stop_networking(self) -> None:
        """Stops all networking components."""
        try:
            runtime_globals.game_console.log("[SceneConnect] Stopping networking components...")
            
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
                self.server_socket = None
                
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
                
            if self.connection_socket:
                try:
                    self.connection_socket.close()
                except:
                    pass
                self.connection_socket = None
                
            if self.device_list_menu:
                self.device_list_menu.close()
                self.device_list_menu = None
                
            # Wait for network thread to finish
            if self.network_thread and self.network_thread.is_alive():
                try:
                    self.network_thread.join(timeout=2.0)
                except:
                    pass
                
            self.connection_established = False
            self.discovered_devices = []
            self.host_code = ""
            
            runtime_globals.game_console.log("[SceneConnect] Network cleanup completed")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Cleanup error: {e}")

    def draw_pet_selection(self, surface: pygame.Surface) -> None:
        """Draws the pet selection phase."""
        self.pet_list_window.draw(surface)
        
        # Show START prompt if pets are selected
        if len(self.pets) > 0:
            font = get_font(int(20 * runtime_globals.UI_SCALE))
            text = font.render(f"Press START when ready ({len(self.pets)})", True, constants.FONT_COLOR_GREEN)
            text_x = (runtime_globals.SCREEN_WIDTH - text.get_width()) // 2
            text_y = runtime_globals.SCREEN_HEIGHT - int(120 * runtime_globals.UI_SCALE)
            blit_with_shadow(surface, text, (text_x, text_y))

    def draw_hosting_screen(self, surface: pygame.Surface) -> None:
        """Draws the hosting waiting screen."""
        font_large = get_font(int(24 * runtime_globals.UI_SCALE))
        font_small = get_font(int(18 * runtime_globals.UI_SCALE))
        
        # Host code display
        title_text = font_large.render("Hosting Network Battle", True, constants.FONT_COLOR_DEFAULT)
        code_text = font_large.render(f"Host Code: {self.host_code}", True, constants.FONT_COLOR_GREEN)
        wait_text = font_small.render("Waiting for other device to connect...", True, constants.FONT_COLOR_DEFAULT)
        cancel_text = font_small.render("Press B to cancel", True, constants.FONT_COLOR_GRAY)
        
        # Center text on screen
        title_x = (runtime_globals.SCREEN_WIDTH - title_text.get_width()) // 2
        code_x = (runtime_globals.SCREEN_WIDTH - code_text.get_width()) // 2
        wait_x = (runtime_globals.SCREEN_WIDTH - wait_text.get_width()) // 2
        cancel_x = (runtime_globals.SCREEN_WIDTH - cancel_text.get_width()) // 2
        
        base_y = runtime_globals.SCREEN_HEIGHT // 3
        blit_with_shadow(surface, title_text, (title_x, base_y))
        blit_with_shadow(surface, code_text, (code_x, base_y + int(40 * runtime_globals.UI_SCALE)))
        blit_with_shadow(surface, wait_text, (wait_x, base_y + int(80 * runtime_globals.UI_SCALE)))
        blit_with_shadow(surface, cancel_text, (cancel_x, base_y + int(120 * runtime_globals.UI_SCALE)))

    def draw_device_discovery(self, surface: pygame.Surface) -> None:
        """Draws the device discovery screen."""
        font_large = get_font(int(24 * runtime_globals.UI_SCALE))
        font_small = get_font(int(18 * runtime_globals.UI_SCALE))
        
        if self.phase == "joining":
            # Still discovering
            title_text = font_large.render("Discovering Devices...", True, constants.FONT_COLOR_DEFAULT)
            wait_text = font_small.render("Looking for available hosts...", True, constants.FONT_COLOR_DEFAULT)
            cancel_text = font_small.render("Press B to cancel", True, constants.FONT_COLOR_GRAY)
            
            title_x = (runtime_globals.SCREEN_WIDTH - title_text.get_width()) // 2
            wait_x = (runtime_globals.SCREEN_WIDTH - wait_text.get_width()) // 2
            cancel_x = (runtime_globals.SCREEN_WIDTH - cancel_text.get_width()) // 2
            
            base_y = runtime_globals.SCREEN_HEIGHT // 3
            blit_with_shadow(surface, title_text, (title_x, base_y))
            blit_with_shadow(surface, wait_text, (wait_x, base_y + int(40 * runtime_globals.UI_SCALE)))
            blit_with_shadow(surface, cancel_text, (cancel_x, base_y + int(80 * runtime_globals.UI_SCALE)))
        
        elif self.phase == "device_list":
            if self.device_list_menu and len(self.discovered_devices) > 0:
                # Show device selection menu
                title_text = font_large.render("Available Devices", True, constants.FONT_COLOR_DEFAULT)
                title_x = (runtime_globals.SCREEN_WIDTH - title_text.get_width()) // 2
                blit_with_shadow(surface, title_text, (title_x, int(20 * runtime_globals.UI_SCALE)))
                
                self.device_list_menu.draw(surface)
                
                cancel_text = font_small.render("Press B to cancel", True, constants.FONT_COLOR_GRAY)
                cancel_x = (runtime_globals.SCREEN_WIDTH - cancel_text.get_width()) // 2
                blit_with_shadow(surface, cancel_text, (cancel_x, runtime_globals.SCREEN_HEIGHT - int(30 * runtime_globals.UI_SCALE)))
            else:
                # No devices found
                title_text = font_large.render("No Devices Found", True, constants.FONT_COLOR_DEFAULT)
                subtitle_text = font_small.render("Make sure the host is ready", True, constants.FONT_COLOR_DEFAULT)
                cancel_text = font_small.render("Press B to try again", True, constants.FONT_COLOR_GRAY)
                
                title_x = (runtime_globals.SCREEN_WIDTH - title_text.get_width()) // 2
                subtitle_x = (runtime_globals.SCREEN_WIDTH - subtitle_text.get_width()) // 2
                cancel_x = (runtime_globals.SCREEN_WIDTH - cancel_text.get_width()) // 2
                
                base_y = runtime_globals.SCREEN_HEIGHT // 3
                blit_with_shadow(surface, title_text, (title_x, base_y))
                blit_with_shadow(surface, subtitle_text, (subtitle_x, base_y + int(40 * runtime_globals.UI_SCALE)))
                blit_with_shadow(surface, cancel_text, (cancel_x, base_y + int(80 * runtime_globals.UI_SCALE)))

    def draw_module_error(self, surface: pygame.Surface) -> None:
        """Draws the module compatibility error screen."""
        font_large = get_font(int(20 * runtime_globals.UI_SCALE))
        font_small = get_font(int(16 * runtime_globals.UI_SCALE))
        
        error_text = font_large.render("Module Compatibility Error!", True, constants.FONT_COLOR_RED)
        missing_text = font_small.render("Missing modules:", True, constants.FONT_COLOR_DEFAULT)
        
        error_x = (runtime_globals.SCREEN_WIDTH - error_text.get_width()) // 2
        missing_x = (runtime_globals.SCREEN_WIDTH - missing_text.get_width()) // 2
        
        base_y = runtime_globals.SCREEN_HEIGHT // 3
        blit_with_shadow(surface, error_text, (error_x, base_y))
        blit_with_shadow(surface, missing_text, (missing_x, base_y + int(40 * runtime_globals.UI_SCALE)))
        
        # List missing modules
        y_offset = base_y + int(70 * runtime_globals.UI_SCALE)
        for module in self.missing_modules:
            module_text = font_small.render(f"• {module}", True, constants.FONT_COLOR_YELLOW)
            module_x = (runtime_globals.SCREEN_WIDTH - module_text.get_width()) // 2
            blit_with_shadow(surface, module_text, (module_x, y_offset))
            y_offset += int(25 * runtime_globals.UI_SCALE)
        
        # Continue prompt
        continue_text = font_small.render("Press A or B to continue", True, constants.FONT_COLOR_GRAY)
        continue_x = (runtime_globals.SCREEN_WIDTH - continue_text.get_width()) // 2
        blit_with_shadow(surface, continue_text, (continue_x, y_offset + int(20 * runtime_globals.UI_SCALE)))

    def start_pvp_battle(self) -> None:
        """Step 9-14: Initiates the PvP battle sequence."""
        if self.is_host:
            # Step 9: Host receives enemy pet data
            self.request_team2_data()
        else:
            # Client sends pet data to host
            self.send_team2_data_to_host()

    def request_team2_data(self) -> None:
        """Step 9: Host requests detailed pet data from team2 (non-host)."""
        try:
            runtime_globals.game_console.log("[SceneConnect] ===== HOST: REQUEST_TEAM2_DATA =====")
            runtime_globals.game_console.log(f"[SceneConnect] Connection socket exists: {self.connection_socket is not None}")
            runtime_globals.game_console.log(f"[SceneConnect] Connection established: {self.connection_established}")
            
            request = {"type": "request_pet_data"}
            runtime_globals.game_console.log(f"[SceneConnect] Sending request: {request}")
            
            if not self.connection_socket:
                runtime_globals.game_console.log("[SceneConnect] ERROR: No connection socket available!")
                self.phase = "menu"
                return
                
            self.connection_socket.send(json.dumps(request).encode())
            
            # Set timeout for receiving data
            self.connection_socket.settimeout(10.0)
            
            # Receive enemy pet data
            data = self.connection_socket.recv(4096).decode()
            runtime_globals.game_console.log(f"[SceneConnect] Received enemy pet data: {data}")
            enemy_data = json.loads(data)
            
            if enemy_data.get("type") == "pet_data":
                self.enemies = enemy_data["team2"]  # Client sent team2 data
                runtime_globals.game_console.log(f"[SceneConnect] Received team2 data: {len(self.enemies)} pets")
                
                # Step 10: Choose battle module
                self.choose_battle_module()
            else:
                runtime_globals.game_console.log(f"[SceneConnect] Unexpected data type: {enemy_data.get('type')}")
                self.phase = "menu"
            
        except socket.timeout:
            runtime_globals.game_console.log("[SceneConnect] Timeout waiting for enemy pet data")
            self.stop_networking()
            self.phase = "menu"
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error requesting pet data: {e}")
            self.stop_networking()
            self.phase = "menu"

    def send_team2_data_to_host(self) -> None:
        """Step 9: Non-host sends pet data to host when requested."""
        try:
            runtime_globals.game_console.log("[SceneConnect] ===== CLIENT: SEND_TEAM2_DATA =====")
            runtime_globals.game_console.log(f"[SceneConnect] Client socket exists: {self.client_socket is not None}")
            runtime_globals.game_console.log(f"[SceneConnect] Connection established: {self.connection_established}")
            
            if not self.client_socket:
                runtime_globals.game_console.log("[SceneConnect] ERROR: No client socket available!")
                self.phase = "menu"
                return
                
            # Set timeout for receiving request
            self.client_socket.settimeout(10.0)
            
            # Wait for pet data request
            data = self.client_socket.recv(1024).decode()
            runtime_globals.game_console.log(f"[SceneConnect] Received pet data request: {data}")
            request = json.loads(data)
            
            if request.get("type") == "request_pet_data":
                # Prepare pet data  
                pet_data = self.create_pet_data()
                response = {
                    "type": "pet_data",
                    "team2": pet_data  # Client pets become team2 in simulation
                }
                runtime_globals.game_console.log(f"[SceneConnect] Sending team2 data to host: {len(pet_data)} pets")
                self.client_socket.send(json.dumps(response).encode())
                
                # Wait for battle module selection and simulation
                self.wait_for_battle_setup()
            else:
                runtime_globals.game_console.log(f"[SceneConnect] Unexpected request type: {request.get('type')}")
                self.phase = "menu"
            
        except socket.timeout:
            runtime_globals.game_console.log("[SceneConnect] Timeout waiting for pet data request")
            self.stop_networking()
            self.phase = "menu"
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error sending pet data: {e}")
            self.stop_networking()
            self.phase = "menu"

    def create_pet_data(self) -> list:
        """Creates detailed pet data for network transmission."""
        pet_data = []
        for pet in self.pets:
            data = {
                "name": pet.name,
                "stage": pet.stage,
                "level": pet.level,
                "hp": pet.get_hp() if hasattr(pet, "get_hp") else getattr(pet, "hp", 100),
                "power": pet.get_power() if hasattr(pet, "get_power") else getattr(pet, "power", 1),
                "attribute": pet.attribute,
                "atk_main": pet.atk_main,
                "atk_alt": pet.atk_alt,
                "module": pet.module,
                "sick": getattr(pet, "sick", 0) > 0,
                "traited": getattr(pet, "traited", False),
                "shook": getattr(pet, "shook", False),
                "mini_game": getattr(pet, "strength", 0)
            }
            pet_data.append(data)
        return pet_data

    def choose_battle_module(self) -> None:
        """Step 10: Host chooses battle module from all participant modules."""
        try:
            all_modules = set(self.get_selected_modules())
            for pet_data in self.enemies:  # enemies = team2 data
                all_modules.add(pet_data["module"])
            
            runtime_globals.game_console.log(f"[SceneConnect] All modules required: {list(all_modules)}")
            runtime_globals.game_console.log(f"[SceneConnect] Available modules: {list(runtime_globals.game_modules.keys())}")
            
            # Choose random module from available ones
            available_modules = list(all_modules.intersection(runtime_globals.game_modules.keys()))
            if available_modules:
                self.chosen_module = random.choice(available_modules)
                runtime_globals.game_console.log(f"[SceneConnect] Chosen battle module: {self.chosen_module}")
                
                # Step 11: Send module choice to other device
                self.send_module_choice()
            else:
                runtime_globals.game_console.log("[SceneConnect] No compatible modules found")
                self.stop_networking()
                self.phase = "menu"
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error choosing battle module: {e}")
            self.stop_networking()
            self.phase = "menu"

    def send_module_choice(self) -> None:
        """Step 11: Send chosen module to other device."""
        try:
            if not self.connection_socket:
                runtime_globals.game_console.log("[SceneConnect] No connection socket available")
                self.phase = "menu"
                return
                
            module_data = {
                "type": "module_choice",
                "module": self.chosen_module
            }
            runtime_globals.game_console.log(f"[SceneConnect] Sending module choice: {module_data}")
            self.connection_socket.send(json.dumps(module_data).encode())
            
            # Step 12: Simulate the battle
            self.simulate_pvp_battle()
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error sending module choice: {e}")
            self.stop_networking()
            self.phase = "menu"

    def wait_for_battle_setup(self) -> None:
        """Client waits for module choice and battle simulation data."""
        try:
            if not self.client_socket:
                runtime_globals.game_console.log("[SceneConnect] No client socket available")
                self.phase = "menu"
                return
                
            # Set timeout for receiving data
            self.client_socket.settimeout(30.0)  # Longer timeout for battle simulation
            
            # Wait for module choice
            data = self.client_socket.recv(1024).decode()
            runtime_globals.game_console.log(f"[SceneConnect] Received module choice: {data}")
            module_data = json.loads(data)
            
            if module_data.get("type") == "module_choice":
                self.chosen_module = module_data["module"]
                runtime_globals.game_console.log(f"[SceneConnect] Received battle module: {self.chosen_module}")
                
                # Wait for battle simulation data
                runtime_globals.game_console.log("[SceneConnect] Waiting for battle simulation data...")
                # Receive possibly-large simulation payload. TCP is a stream and
                # a single recv() may return a partial message, so accumulate
                # chunks until we can successfully parse JSON or the socket
                # closes/timeout occurs.
                data = ""
                sim_data = None
                try:
                    while True:
                        chunk = self.client_socket.recv(8192)
                        if not chunk:
                            # Connection closed by peer
                            break
                        data += chunk.decode()
                        try:
                            sim_data = json.loads(data)
                            break
                        except json.JSONDecodeError:
                            # Incomplete JSON, loop to receive more
                            continue
                except socket.timeout:
                    runtime_globals.game_console.log("[SceneConnect] Timeout while receiving battle simulation data")
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Error receiving simulation data chunks: {e}")

                runtime_globals.game_console.log(f"[SceneConnect] Received battle simulation data: {len(data)} bytes")
                if sim_data is None:
                    # Could not parse incoming payload
                    runtime_globals.game_console.log("[SceneConnect] Failed to parse battle simulation JSON payload")
                    self.stop_networking()
                    self.phase = "menu"
                    return
                
                if sim_data.get("type") == "battle_simulation":
                    self.battle_simulation_data = sim_data["data"]
                    runtime_globals.game_console.log("[SceneConnect] Battle simulation data loaded successfully")

                    # Attempt to deserialize the serialized BattleResult into an
                    # in-memory object so the client has completed the same
                    # preprocessing work the host did prior to entering the
                    # battle scene. This minimizes work that would otherwise
                    # happen during scene initialization and allows a simple
                    # ready/ack handshake below.
                    try:
                        # Use central deserializer helper from sim.models
                        from core.combat.sim.models import battle_result_from_serialized
                        serialized = self.battle_simulation_data.get('battle_log', {})
                        try:
                            self.original_battle_log = battle_result_from_serialized(serialized)
                        except Exception:
                            # Fallback: try whole payload shape (host may have sent full BattleResult dict)
                            self.original_battle_log = battle_result_from_serialized(self.battle_simulation_data)
                    except Exception as e:
                        runtime_globals.game_console.log(f"[SceneConnect] Warning: failed to pre-deserialize battle log: {e}")
                        self.original_battle_log = None

                    # Send a ready ack back to the host so both devices can
                    # enter the battle scene simultaneously. The client sends
                    # this after it has performed its preprocessing.
                    try:
                        ready_msg = {"type": "sim_ready"}
                        self.client_socket.send(json.dumps(ready_msg).encode())
                        runtime_globals.game_console.log("[SceneConnect] Sent simulation ready ack to host")
                    except Exception as e:
                        runtime_globals.game_console.log(f"[SceneConnect] Failed to send ready ack: {e}")
                        self.stop_networking()
                        self.phase = "menu"
                        return

                    # Step 14: Start battle scene for client (team2)
                    self.start_battle_scene(is_host=False)
                elif sim_data.get("type") == "battle_error":
                    runtime_globals.game_console.log(f"[SceneConnect] Battle error from host: {sim_data.get('error')}")
                    self.stop_networking()
                    self.phase = "menu"
                else:
                    runtime_globals.game_console.log(f"[SceneConnect] Unexpected simulation data type: {sim_data.get('type')}")
                    self.stop_networking()
                    self.phase = "menu"
            else:
                runtime_globals.game_console.log(f"[SceneConnect] Unexpected module data type: {module_data.get('type')}")
                self.phase = "menu"
            
        except socket.timeout:
            runtime_globals.game_console.log("[SceneConnect] Timeout waiting for battle setup data")
            self.stop_networking()
            self.phase = "menu"
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error in battle setup: {e}")
            self.stop_networking()
            self.phase = "menu"

    def simulate_pvp_battle(self) -> None:
        """Step 12: Host simulates the battle with both teams."""
        try:
            runtime_globals.game_console.log("[SceneConnect] Starting battle simulation...")
            
            # Import battle encounter 
            try:
                from core.combat.battle_encounter import BattleEncounter
            except ImportError:
                runtime_globals.game_console.log("[SceneConnect] Could not import BattleEncounter")
                self.stop_networking()
                self.phase = "menu"
                return
                
            # Create temporary battle encounter for simulation
            battle = BattleEncounter(self.chosen_module, area=0, round=0, version=1, pvp_mode=True)
            
            # Setup teams - host is team1, enemy is team2
            battle.setup_pvp_teams(self.pets, self.enemies)
            
            runtime_globals.game_console.log(f"[SceneConnect] Teams setup - Team1: {len(battle.battle_player.team1)}, Team2: {len(battle.battle_player.team2)}")
            
            # Run simulation
            battle.simulate_global_combat()
            
            runtime_globals.game_console.log(f"[SceneConnect] Battle simulation complete - Winner: {battle.victory_status}")
            
            # Store the original battle log object for local battle scene
            original_battle_log = getattr(battle, 'global_battle_log', [])
            
            # Serialize battle log only for network transmission
            if hasattr(original_battle_log, 'to_dict'):
                # If it's a BattleResult object, serialize it
                battle_log_serialized = original_battle_log.to_dict()
            elif isinstance(original_battle_log, list) and original_battle_log and hasattr(original_battle_log[0], 'to_dict'):
                # If it's a list of objects with to_dict method
                battle_log_serialized = [entry.to_dict() for entry in original_battle_log]
            else:
                # Fallback to original data
                battle_log_serialized = original_battle_log
            
            # Store simulation data with serialized battle log (for network transmission)
            # Use consistent team1/team2 naming: team1 = host, team2 = non-host
            self.battle_simulation_data = {
                "battle_log": battle_log_serialized,
                "team1": self.create_pet_data(),  # host pets
                "team2": self.enemies,            # non-host pets
                "module": self.chosen_module,
                "victory_status": getattr(battle, 'victory_status', 'Victory')
            }
            
            # Store original battle log for local battle scene use
            self.original_battle_log = original_battle_log
            
            #runtime_globals.game_console.log(f"[SceneConnect] Simulation data created with {len(self.battle_simulation_data['battle_log'])} log entries")
            
            # Step 13: Send simulation data to client
            self.send_simulation_data()
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error simulating battle: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
            
            # Send error response to client before closing connection
            try:
                if self.connection_socket:
                    error_message = {
                        "type": "battle_error",
                        "error": f"Battle simulation failed: {str(e)}"
                    }
                    self.connection_socket.send(json.dumps(error_message).encode())
                    runtime_globals.game_console.log("[SceneConnect] Error response sent to client")
            except:
                pass  # Connection might be broken already
                
            self.stop_networking()
            self.phase = "menu"

    def send_simulation_data(self) -> None:
        """Step 13: Send simulation data to client."""
        try:
            if not self.connection_socket:
                runtime_globals.game_console.log("[SceneConnect] No connection socket available")
                self.phase = "menu"
                return
            # Prepare a deep copy of the simulation data so we don't modify the
            # host's local original. We will swap device1/device2 in the serialized
            # battle log so the client receives the log from its local perspective
            # and doesn't need to perform additional adjustments before playback.
            sim_payload = copy.deepcopy(self.battle_simulation_data)
            
            # Encapsulate in 'data' key as expected by protocol
            message = {
                "type": "battle_simulation",
                "data": sim_payload
            }
            
            self.connection_socket.send(json.dumps(message).encode())
            runtime_globals.game_console.log("[SceneConnect] Sent RAW battle simulation data to client")
            
            # Wait for client acknowledgment
            runtime_globals.game_console.log("[SceneConnect] Waiting for client's sim_ready ack...")
            self.connection_socket.settimeout(10.0)
            resp_raw = self.connection_socket.recv(1024).decode()
            runtime_globals.game_console.log(f"[SceneConnect] Received post-sim response: {resp_raw}")
            
            try:
                resp = json.loads(resp_raw)
            except Exception:
                resp = {}

            if resp.get('type') == 'sim_ready':
                runtime_globals.game_console.log("[SceneConnect] Client ready - starting host battle scene")
            else:
                runtime_globals.game_console.log(f"[SceneConnect] Unexpected response: {resp}, starting anyway")
            
            # Step 14: Start battle scene for host
            self.start_battle_scene(is_host=True)
            return

            def _swap_serialized_battle_log(bl):
                # Handle dict-shaped BattleResult.to_dict() output
                try:
                    if isinstance(bl, dict) and 'battle_log' in bl:
                        swapped = bl.copy()
                        # Swap winner
                        if swapped.get('winner') == 'device1':
                            swapped['winner'] = 'device2'
                        elif swapped.get('winner') == 'device2':
                            swapped['winner'] = 'device1'

                        # Swap final device states
                        if 'device1_final' in swapped and 'device2_final' in swapped:
                            t = swapped['device1_final']
                            swapped['device1_final'] = swapped['device2_final']
                            swapped['device2_final'] = t

                        # Swap entries in battle_log
                        for turn in swapped.get('battle_log', []):
                            if isinstance(turn, dict):
                                if 'device1_status' in turn and 'device2_status' in turn:
                                    t = turn['device1_status']
                                    turn['device1_status'] = turn['device2_status']
                                    turn['device2_status'] = t
                                if 'attacks' in turn:
                                    for attack in turn['attacks']:
                                        if attack.get('device') == 'device1':
                                            attack['device'] = 'device2'
                                        elif attack.get('device') == 'device2':
                                            attack['device'] = 'device1'
                        return swapped

                    # Handle list-shaped logs: list of turn dicts
                    if isinstance(bl, list):
                        swapped_list = []
                        for turn in bl:
                            if isinstance(turn, dict):
                                if 'device1_status' in turn and 'device2_status' in turn:
                                    t = turn['device1_status']
                                    turn['device1_status'] = turn['device2_status']
                                    turn['device2_status'] = t
                                if 'attacks' in turn:
                                    for attack in turn['attacks']:
                                        if attack.get('device') == 'device1':
                                            attack['device'] = 'device2'
                                        elif attack.get('device') == 'device2':
                                            attack['device'] = 'device1'
                            swapped_list.append(turn)
                        return swapped_list
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneConnect] Error swapping serialized battle log: {e}")
                return bl

            # Swap the serialized battle log for client perspective so they don't
            # need to do extra work when starting the battle.
            # REMOVED: No longer swapping battle log - both devices use same log
            # if 'battle_log' in sim_payload:
            #     sim_payload['battle_log'] = _swap_serialized_battle_log(sim_payload['battle_log'])
            #     sim_payload['pre_swapped'] = True
                
                # Also swap the victory status for client perspective
                # REMOVED: No longer swapping victory status - handled in battle scene
                # vs = sim_payload.get('victory_status', 'Victory')
                # if vs == "Victory":
                #     sim_payload['victory_status'] = "Defeat"
                # elif vs == "Defeat":
                #     sim_payload['victory_status'] = "Victory"

            sim_message = {
                "type": "battle_simulation",
                "data": sim_payload
            }
            message_json = json.dumps(sim_message)
            runtime_globals.game_console.log(f"[SceneConnect] Sending battle simulation data: {len(message_json)} bytes")
            self.connection_socket.send(message_json.encode())
            
            runtime_globals.game_console.log("[SceneConnect] Battle simulation data sent successfully")
            
            # Wait for client to acknowledge that it has received and
            # preprocessed the simulation data. This keeps both devices in
            # sync: host will not transition to the battle scene until the
            # client signals readiness. We use a short timeout to avoid
            # indefinite blocking in case of network issues.
            try:
                self.connection_socket.settimeout(10.0)
                runtime_globals.game_console.log("[SceneConnect] Waiting for client's sim_ready ack...")
                resp_raw = self.connection_socket.recv(1024).decode()
                runtime_globals.game_console.log(f"[SceneConnect] Received post-sim response: {resp_raw}")
                try:
                    resp = json.loads(resp_raw)
                except Exception:
                    resp = {}

                if resp.get('type') == 'sim_ready':
                    runtime_globals.game_console.log("[SceneConnect] Client ready - starting host battle scene")
                    # Step 14: Start battle scene for host (team1)
                    self.start_battle_scene(is_host=True)
                else:
                    runtime_globals.game_console.log(f"[SceneConnect] Unexpected response after simulation: {resp}")
                    # Fallback: still start but log warning
                    self.start_battle_scene(is_host=True)
            except socket.timeout:
                runtime_globals.game_console.log("[SceneConnect] Timeout waiting for client's sim_ready ack - proceeding to start battle")
                self.start_battle_scene(is_host=True)
            except Exception as e:
                runtime_globals.game_console.log(f"[SceneConnect] Error waiting for sim_ready ack: {e}")
                self.start_battle_scene(is_host=True)
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error sending simulation data: {e}")
            self.stop_networking()
            self.phase = "menu"

    def start_battle_scene(self, is_host: bool) -> None:
        """Step 14: Start the battle scene with simulation data."""
        try:
            runtime_globals.game_console.log(f"[SceneConnect] Preparing to start PvP battle scene (host: {is_host})")
            
            # Validate simulation data
            if not self.battle_simulation_data:
                runtime_globals.game_console.log("[SceneConnect] No battle simulation data available")
                self.stop_networking()
                self.phase = "menu"
                return

            # Both devices use same team structure: team1 = host, team2 = non-host
            # Data flipping will happen in battle scene for non-host perspective
            if is_host:
                # Host: my pets are team1, enemy pets are team2
                my_team_data = self.battle_simulation_data["team1"]
                enemy_team_data = self.battle_simulation_data["team2"]
            else:
                # Non-host: host pets are team1, my pets are team2
                my_team_data = self.battle_simulation_data["team2"] 
                enemy_team_data = self.battle_simulation_data["team1"]

            if not my_team_data or not enemy_team_data:
                runtime_globals.game_console.log("[SceneConnect] Missing team data in simulation")
                self.stop_networking()
                self.phase = "menu"
                return
            
            # Store PvP battle data in runtime globals for the battle scene
            # Get player names for alert screen
            my_player_name = "YOU"
            enemy_player_name = "ENEMY"
            if self.is_online_mode and hasattr(self, 'discord') and self.discord:
                my_player_name = self.discord.get_account_name() or "YOU"
                # Enemy name would be from the handshake data if we stored it
                # For now default to ENEMY for WiFi, or could be extracted from discord room
                enemy_player_name = "ENEMY"
            
            runtime_globals.pvp_battle_data = {
                "simulation_data": self.battle_simulation_data,
                "original_battle_log": getattr(self, 'original_battle_log', None),
                "is_host": is_host,
                "my_pets": self.pets,  # Always the current device's pets
                "my_team_data": my_team_data,
                "enemy_team_data": enemy_team_data,
                "module": self.chosen_module,
                "my_player_name": my_player_name,
                "enemy_player_name": enemy_player_name,
                "is_online_mode": self.is_online_mode
            }
            
            runtime_globals.game_console.log(f"[SceneConnect] PvP battle data configured:")
            runtime_globals.game_console.log(f"  - Is Host: {is_host}")
            runtime_globals.game_console.log(f"  - My pets: {len(self.pets)}")
            runtime_globals.game_console.log(f"  - My team data: {len(my_team_data)}")
            runtime_globals.game_console.log(f"  - Enemy team data: {len(enemy_team_data)}")
            runtime_globals.game_console.log(f"  - Module: {self.chosen_module}")
            runtime_globals.game_console.log(f"  - Battle log entries: {len(self.battle_simulation_data.get('battle_log', []))}")
            
            # Clean up networking before changing scenes
            self.stop_networking()
            
            # Change to battle scene
            runtime_globals.game_console.log("[SceneConnect] Changing to PvP battle scene...")
            change_scene("battle_pvp")
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Error starting battle scene: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneConnect] Traceback: {traceback.format_exc()}")
            self.stop_networking()
            self.phase = "menu"

    def draw_battle_confirmation(self, surface: pygame.Surface) -> None:
        """Draws the battle confirmation screen."""
        font_large = get_font(int(24 * runtime_globals.UI_SCALE))
        font_small = get_font(int(18 * runtime_globals.UI_SCALE))
        
        ready_text = font_large.render("Connection Established!", True, constants.FONT_COLOR_GREEN)
        enemy_text = font_small.render(f"Enemy has {self.enemy_pet_count} pets", True, constants.FONT_COLOR_DEFAULT)
        if getattr(self, 'discord_ready', False):
            confirm_text = font_small.render("Waiting for opponent...", True, constants.FONT_COLOR_YELLOW)
        elif getattr(self, 'opponent_ready', False):
            confirm_text = font_small.render("Opponent Ready! Press A!", True, constants.FONT_COLOR_GREEN)
        else:
            confirm_text = font_small.render("Press A to start battle", True, constants.FONT_COLOR_DEFAULT)
        cancel_text = font_small.render("Press B to give up", True, constants.FONT_COLOR_RED)
        
        ready_x = (runtime_globals.SCREEN_WIDTH - ready_text.get_width()) // 2
        enemy_x = (runtime_globals.SCREEN_WIDTH - enemy_text.get_width()) // 2
        confirm_x = (runtime_globals.SCREEN_WIDTH - confirm_text.get_width()) // 2
        cancel_x = (runtime_globals.SCREEN_WIDTH - cancel_text.get_width()) // 2
        
        base_y = runtime_globals.SCREEN_HEIGHT // 3
        blit_with_shadow(surface, ready_text, (ready_x, base_y))
        blit_with_shadow(surface, enemy_text, (enemy_x, base_y + int(40 * runtime_globals.UI_SCALE)))
        blit_with_shadow(surface, confirm_text, (confirm_x, base_y + int(80 * runtime_globals.UI_SCALE)))
        blit_with_shadow(surface, cancel_text, (cancel_x, base_y + int(110 * runtime_globals.UI_SCALE)))

    def draw_connecting_screen(self, surface: pygame.Surface) -> None:
        """Draws the connecting/waiting screen."""
        font_large = get_font(int(24 * runtime_globals.UI_SCALE))
        font_small = get_font(int(18 * runtime_globals.UI_SCALE))
        
        connecting_text = font_large.render("Connecting...", True, constants.FONT_COLOR_YELLOW)
        wait_text = font_small.render("Waiting for opponent confirmation", True, constants.FONT_COLOR_DEFAULT)
        
        connecting_x = (runtime_globals.SCREEN_WIDTH - connecting_text.get_width()) // 2
        wait_x = (runtime_globals.SCREEN_WIDTH - wait_text.get_width()) // 2
        
        base_y = runtime_globals.SCREEN_HEIGHT // 2 - int(40 * runtime_globals.UI_SCALE)
        blit_with_shadow(surface, connecting_text, (connecting_x, base_y))
        blit_with_shadow(surface, wait_text, (wait_x, base_y + int(40 * constants.UI_SCALE)))

    # ==========================================
    # Discord Network Logic (Added for fix)
    # ==========================================

    def _update_discord_networking(self):
        """Polls Discord room for data and handles battle sequence."""
        if not self.phase in ["discord_hosting", "connecting", "battle_confirm"]:
             return
             
        # Throttle polling to every 2 seconds
        now = time.time()
        if now - getattr(self, '_last_discord_poll', 0) < 2.0:
             return
        self._last_discord_poll = now
        
        status = self.discord.poll_room()
        if not status:
             runtime_globals.game_console.log("[SceneConnect] Poll returned None")
             return
        
        runtime_globals.game_console.log(f"[SceneConnect] Poll status: {status.get('status')}, guests: {status.get('guests')}")
             
        # Check players (Handshake Phase 1)
        players = status.get('guests', [])
        host = status.get('host')
        if host: players.append(host)
        
        # If hosting and guest joined
        if self.phase == "discord_hosting":
             guests = status.get('guests', [])
             # Filter out yourself from the guests list (Discord bot bug includes host in guests)
             # Only remove ONE instance of your name (in case someone joins with same account for testing)
             my_name = self.discord.get_account_name() if self.discord else None
             actual_guests = guests.copy()
             if my_name and my_name in actual_guests:
                 actual_guests.remove(my_name)  # Remove only first instance
             runtime_globals.game_console.log(f"[SceneConnect] Hosting phase, raw guests: {guests}, actual guests: {actual_guests}")
             if len(actual_guests) > 0:
                  runtime_globals.game_console.log("[SceneConnect] Guest joined! Starting battle sequence...")
                  # Ensure we set is_host correctly (should already be set)
                  self.is_host = True 
                  self.start_discord_battle_sequence()
                  # Don't set _discord_opponent_found - that's for WiFi battles only!
                  
        # Process Message Queue (Handshake Phase 2)
        queue = status.get('data_queue', [])
        
        # Initialize last timestamp to None on first run
        if not hasattr(self, '_last_msg_ts'):
            self._last_msg_ts = None
        
        # DEBUG: Log queue stats
        if len(queue) > 0:
             runtime_globals.game_console.log(f"[SceneConnect] Polling... Queue: {len(queue)}, LastTS: {self._last_msg_ts}")

        for msg in queue:
             ts = msg.get('ts')
             
             # Skip already processed messages
             if self._last_msg_ts and ts <= self._last_msg_ts: 
                 runtime_globals.game_console.log(f"[SceneConnect] Skipping old msg: {ts} <= {self._last_msg_ts}")
                 continue
             
             runtime_globals.game_console.log(f"[SceneConnect] Processing new msg! Type: {msg.get('data', {}).get('type')}, TS: {ts}")
             self._last_msg_ts = ts
             self._process_discord_message(msg.get('data', {}))

    def start_discord_battle_sequence(self):
        """Initiates Discord battle by sending local pet data."""
        runtime_globals.game_console.log("[SceneConnect] ===== START DISCORD BATTLE SEQUENCE =====")
        runtime_globals.game_console.log(f"[SceneConnect] Current phase: {self.phase}")
        
        self.set_phase("connecting")
        runtime_globals.game_console.log(f"[SceneConnect] Changed phase to: {self.phase}")
        
        # Send my pet data
        my_data = self.create_pet_data()
        
        # Determine role
        am_i_host = getattr(self, 'is_host', False)
        role = "host" if am_i_host else "guest"
        
        runtime_globals.game_console.log(f"[SceneConnect] Role: {role}")
        runtime_globals.game_console.log(f"[SceneConnect] My pets: {len(self.pets)}")
        runtime_globals.game_console.log(f"[SceneConnect] Sending handshake...")
        
        msg = {
            "type": "battle_handshake",
            "sender": role,
            "pets": my_data,
            "pet_count": len(self.pets)
        }
        
        result = self.discord.send_data(msg)
        runtime_globals.game_console.log(f"[SceneConnect] Handshake sent, result: {result}")




    def _process_discord_message(self, data):
        """Handle incoming Discord battle messages."""
        msg_type = data.get('type')
        runtime_globals.game_console.log(f"[SceneConnect] Processing Msg Type: {msg_type} from {data.get('sender')}")
        sender = data.get('sender')
        
        # Ignore my own messages
        am_i_host = getattr(self, 'is_host', False)
        my_role = "host" if am_i_host else "guest"
        if sender == my_role:
             return

        runtime_globals.game_console.log(f"[SceneConnect] Received Discord Msg: {msg_type} from {sender}")

        if msg_type == "battle_handshake":
             # Received enemy pets
             self.enemies = data.get('pets', [])
             self.enemy_pet_count = len(self.enemies)
             runtime_globals.game_console.log(f"[SceneConnect] Enemy has {self.enemy_pet_count} pets")
             
             # Extract modules from enemy pets to ensure compatibility check (or at least storage)
             self.enemy_modules = []
             for pet_dict in self.enemies:
                 if 'module' in pet_dict:
                     self.enemy_modules.append(pet_dict['module'])
             
             runtime_globals.game_console.log(f"[SceneConnect] Enemy modules: {self.enemy_modules}")
             
             # Transition to confirmation screen
             self.set_phase("battle_confirm")
             # Ensure UI is updated
             self._show_phase_components("battle_confirm")
             self.connection_established = True
             
             # If I am guest, I must send my handshake back so Host knows my pets
             if not am_i_host and not getattr(self, 'handshake_sent', False):
                 runtime_globals.game_console.log("[SceneConnect] Guest responding to handshake...")
                 self.start_discord_battle_sequence() # This sends the handshake
                 self.handshake_sent = True

        elif msg_type == "ready":
             # Opponent is ready
             runtime_globals.game_console.log("[SceneConnect] Opponent is READY")
             self.opponent_ready = True
             self._check_start_discord_sim()

        elif msg_type == "battle_sim":
             # Received simulation result (Guest only)
             self.battle_simulation_data = data.get('data')
             # Need to set module for guest context
             self.chosen_module = self.battle_simulation_data.get('module', 'dm_classic')
             runtime_globals.game_console.log("[SceneConnect] Received Battle Sim! Starting Battle.")
             self.start_battle_scene(is_host=False)

    def _check_start_discord_sim(self):
        """Host checks if both are ready to simulate."""
        if not getattr(self, 'is_host', False):
            return
            
        if getattr(self, 'discord_ready', False) and getattr(self, 'opponent_ready', False):
             runtime_globals.game_console.log("[SceneConnect] Both ready - Simulating!")
             self._run_discord_simulation()

    def _run_discord_simulation(self):
        """Host runs simulation and sends result."""
        try:
            from core.combat.battle_encounter import BattleEncounter
            
            # Use the module of the first pet, or fallback to a safe default if needed
            if self.pets and hasattr(self.pets[0], 'module'):
                self.chosen_module = self.pets[0].module
            else:
                # Retrieve first available module key as fallback
                self.chosen_module = next(iter(runtime_globals.game_modules.keys())) if runtime_globals.game_modules else "dm_classic"
            
            # Setup teams
            battle = BattleEncounter(self.chosen_module, area=0, round=0, version=1, pvp_mode=True)
            battle.setup_pvp_teams(self.pets, self.enemies)
            battle.simulate_global_combat()
            
            # Serialize Log
            # Keep the full BattleResult object for local host usage (BattleEncounter expects it)
            result_obj = getattr(battle, 'global_battle_log', [])
            self.original_battle_log = result_obj

            # Prepare serialized version for Guest (JSON)
            if hasattr(result_obj, 'battle_log'):
                log_list = result_obj.battle_log
            else:
                log_list = result_obj
                
            serialized_log = [x.to_dict() if hasattr(x, 'to_dict') else x for x in log_list]
            
            sim_data = {
                 "battle_log": serialized_log,
                 "team1": self.create_pet_data(),
                 "team2": self.enemies,
                 "module": self.chosen_module,
                 # Ensure victory status is a string
                 "victory_status": str(battle.victory_status) if battle.victory_status else "Defeat"
            }
            
            self.battle_simulation_data = sim_data
            
            # Send to Guest
            msg = {
                 "type": "battle_sim",
                 "sender": "host",
                 "data": sim_data
            }
            self.discord.send_data(msg)
            
            # Start Local
            self.start_battle_scene(is_host=True)
            
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneConnect] Sim error: {e}")
            import traceback
            runtime_globals.game_console.log(traceback.format_exc())
            
            # Show error on UI
            if hasattr(self, 'battle_enemy_label'):
                 self.battle_enemy_label.set_text(f"Error: {str(e)[:20]}")
                 self.battle_enemy_label.visible = True