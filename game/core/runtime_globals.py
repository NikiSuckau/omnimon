import random

from core.game_console import GameConsole
from core.game_item import GameItem
from core.game_message import GameMessage
from core.game_sound import GameSound
from core.input.i2c_utils import I2CUtils
from core.input.input_manager import InputManager
from core.input.shake_detector import ShakeDetector

#=====================================================================
# Runtime (Non-Persistent) Global Variables
#=====================================================================

# --- Scene and State Control ---
game_state = "boot"
game_state_update = False

# --- Main Menu Navigation ---
main_menu_index = -1

# --- Menu Selections ---
food_index = 0
strategy_index = 0
training_index = 0
battle_index = {}

# --- Runtime-only Assets and Selections ---
feeding_frames = []
selected_pets = []
misc_sprites = {}
battle_enemies = {}
pet_sprites = {}
evolution_data = []
evolution_pet = None
last_headtohead_pattern = random.randint(0, 5)
special_encounter = []

# --- Global Managers ---
game_sound = GameSound()
game_console = GameConsole()
game_message = GameMessage()
game_input = InputManager()
game_modules = {}
game_module_flag = {}
game_pet_eating = {}

default_items = {
    "protein": GameItem(
        id="default-protein",
        name="Protein",
        description="Basic food. Replenishes hunger.",
        sprite_name="Protein.png",
        module="core",
        effect="status_change",
        status="hunger",
        amount=1,
        boost_time=0,
        component_item=""
    ),
    "vitamin": GameItem(
        id="default-vitamin",
        name="Vitamin",
        description="Basic food. Replenishes strength.",
        sprite_name="Vitamin.png",
        module="core",
        effect="status_change",
        status="strength",
        amount=1,
        boost_time=0,
        component_item=""
    )
}

# --- Pet/Gameplay Flags ---
pet_alert = False
show_hearts = False
check_shaking = False

# --- Ruleset Flags ---
dmc_enabled = False
penc_enabled = False
dmx_enabled = False
vb_enabled = False

# --- Hardware/Input ---
i2c = I2CUtils()
shake_detector = ShakeDetector(i2c)
last_input_frame = 0