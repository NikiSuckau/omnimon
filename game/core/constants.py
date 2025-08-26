import json
import os
import pygame

#=====================================================================
# Pygame Version Compatibility
#=====================================================================
PYGAME_VERSION = tuple(map(int, pygame.version.ver.split('.')))
IS_PYGAME2 = PYGAME_VERSION >= (2, 0, 0)
# Use SRCALPHA for both versions - it's compatible
COMPATIBLE_SRCALPHA = pygame.SRCALPHA

#=====================================================================
# Load config values
#=====================================================================
CONFIG_PATH = "config/config.json"
DEFAULT_CONFIG = {
    "SCREEN_WIDTH": 240,
    "SCREEN_HEIGHT": 240,
    "FRAME_RATE": 30,
    "MAX_PETS": 4,
    "FULLSCREEN": False,
    "DEBUG_MODE": False,
    "DEBUG_FILE_LOGGING": False,
    "SHOW_FPS": False,
    "DEBUG_BLIT_LOGGING": False,
    "DEBUG_BATTLE_INFO": False
}

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_config = json.load(f)
except Exception:
    user_config = {}

SCREEN_WIDTH = user_config.get("SCREEN_WIDTH", DEFAULT_CONFIG["SCREEN_WIDTH"])
# Same sanity logic needed in main.py setup_display()
if not SCREEN_WIDTH:
    SCREEN_WIDTH = 240
if SCREEN_WIDTH < 32:
    SCREEN_WIDTH = 32
SCREEN_HEIGHT = user_config.get("SCREEN_HEIGHT", DEFAULT_CONFIG["SCREEN_HEIGHT"])
# Same sanity logic needed in main.py setup_display()
if not SCREEN_HEIGHT:
    SCREEN_HEIGHT = 240
if SCREEN_HEIGHT < 32:
    SCREEN_HEIGHT = 32
FRAME_RATE = user_config.get("FRAME_RATE", DEFAULT_CONFIG["FRAME_RATE"])
# Bare minimum required in game_pet.py update_idle_movement() to not divide by zero
if FRAME_RATE < 3:
    FRAME_RATE = 3
MAX_PETS = user_config.get("MAX_PETS", DEFAULT_CONFIG["MAX_PETS"])
# Required to not divide by zero
if MAX_PETS < 1:
    MAX_PETS = 1
FULLSCREEN = user_config.get("FULLSCREEN", DEFAULT_CONFIG["FULLSCREEN"])

# Debug and logging configuration
DEBUG_MODE = user_config.get("DEBUG_MODE", user_config.get("DEBUG", DEFAULT_CONFIG["DEBUG_MODE"]))  # Backward compatibility
DEBUG_FILE_LOGGING = user_config.get("DEBUG_FILE_LOGGING", user_config.get("LOGGING", DEFAULT_CONFIG["DEBUG_FILE_LOGGING"]))  # Backward compatibility
SHOW_FPS = user_config.get("SHOW_FPS", DEFAULT_CONFIG["SHOW_FPS"])
DEBUG_BLIT_LOGGING = user_config.get("DEBUG_BLIT_LOGGING", user_config.get("LOG_BLITS", DEFAULT_CONFIG["DEBUG_BLIT_LOGGING"]))  # Backward compatibility
DEBUG_BATTLE_INFO = user_config.get("DEBUG_BATTLE_INFO", DEFAULT_CONFIG["DEBUG_BATTLE_INFO"])

# Legacy aliases for backward compatibility
DEBUG = DEBUG_MODE
LOGGING = DEBUG_FILE_LOGGING
LOG_BLITS = DEBUG_BLIT_LOGGING

FRAME_SIZE = 48  # Original pet sprite frame size

#=====================================================================
# Screen and Window Constants
#=====================================================================
# SCREEN_WIDTH, SCREEN_HEIGHT = 240, 240
# FRAME_SIZE = 48  # Original pet sprite frame size
# FRAME_RATE = 30  # Frames per second

#=====================================================================
# Pet Constants
#=====================================================================
PET_WIDTH = PET_HEIGHT = SCREEN_HEIGHT // MAX_PETS
# MAX_PETS = 4
STAGES = [
    "0-Egg", "I-Fresh", "II-In-Training", "III-Rookie",
    "IV-Champion", "V-Ultimate", "VI-Mega", "VII-Super Ultimate"
]
ATTR_COLORS = {
            "Da": (66, 165, 245),
            "Va": (102, 187, 106),
            "Vi": (237, 83, 80),
            "": (171, 71, 188),
            "???": (0, 0, 0)
        }
#=====================================================================
# Game Mechanics
#=====================================================================
MOVE_SPEED = 0.5  # Movement speed in subpixels/frame
IDLE_PROBABILITY = 0.2  # 20% chance of idle vs. moving
CLEANING_SPEED = 6  # Speed of cleaning animation
SLEEP_RECOVERY_HOURS = 8  # Hours needed to fully recover
SLEEP_MANUAL_DURATION_HOURS = 1  # Duration when manually sleeping
SLEEP_DISTURBANCE_THRESHOLD_SECONDS = 7200  # 2 hours threshold for disturbance detection
BOOT_TIMER_FRAMES = int(150 * (FRAME_RATE / 30)) 

MAX_LEVEL = {0: 0, 1: 1, 2: 3, 3: 4, 4: 6, 5: 8, 6: 10, 7: 10, 8: 10}
EXPERIENCE_LEVEL = {0: 0, 1: 0, 2: 50, 3: 150, 4: 500, 5: 800, 6: 1000, 7: 1500, 8: 2000, 9: 3000, 10:5000}
HP_LEVEL = {
    0: 0,    # Egg
    1: 0,    # Fresh
    2: 10,   # In-Training
    3: 10,   # Rookie
    4: 12,   # Champion
    5: 15,   # Ultimate
    6: 18,   # Mega
    7: 20,   # Super Ultimate
    8: 20    # (If used, for extra stage)
}
ATK_LEVEL = {
    0: 0,   # Egg
    1: 0,   # Fresh
    2: 2,   # In-Training (10 // 4 = 2)
    3: 2,   # Rookie      (10 // 4 = 2)
    4: 3,   # Champion    (12 // 4 = 3)
    5: 3,   # Ultimate    (15 // 4 = 3)
    6: 4,   # Mega        (18 // 4 = 4)
    7: 5,   # Super Ultimate (20 // 4 = 5)
    8: 5    # Extra stage (20 // 4 = 5)
}
#=====================================================================
# UI Settings
#=====================================================================
# UI Settings - scale proportionally to a 240x240 reference screen
UI_SCALE = SCREEN_HEIGHT / 240

MENU_ICON_SIZE = int(24 * UI_SCALE)         # Icon size (24x24 at 240x240)
OPTION_ICON_SIZE = int(48 * UI_SCALE)       # Option icon size (48x48 at 240x240)
OPTION_FRAME_WIDTH = int(96 * UI_SCALE)     # Option frame width (96 at 240x240)
OPTION_FRAME_HEIGHT = int(116 * UI_SCALE)   # Option frame height (116 at 240x240)
PET_ICON_SIZE = int(48 * UI_SCALE)

FONT_SIZE_SMALL = int(24 * UI_SCALE)
FONT_SIZE_MEDIUM = int(28 * UI_SCALE)
FONT_SIZE_MEDIUM_LARGE = int(30 * UI_SCALE)
FONT_SIZE_LARGE = int(40 * UI_SCALE)

FONT_COLOR_DEFAULT = (255, 255, 255)
FONT_COLOR_GRAY = (150, 150, 150)
FONT_COLOR_GREEN = (0, 231, 58)
FONT_COLOR_RED = (237, 83, 80)
FONT_COLOR_YELLOW = (255, 255, 0)
FONT_COLOR_BLUE = (0, 0, 255)
FONT_COLOR_ORANGE = (255, 200, 50)
BACKGROUND_COLOR = (198, 203, 173)

#=====================================================================
# Paths: General Resources
#=====================================================================
MODULES_FOLDER = "modules"
ARROW_IMAGE_PATH = "assets/Arrow.png"
FOOD_SHEET_PATH = "assets/FoodVitamin.png"
ATK_FOLDER = "assets/atk"

#=====================================================================
# Paths: UI Sprites
#=====================================================================
SELECTION_OFF_PATH = "assets/SelectionOff.png"
SELECTION_ON_PATH = "assets/SelectionOn.png"
MENU_BACKGROUND_PATH = "assets/MenuBackground.png"
PET_SELECTION_BACKGROUND_PATH = "assets/PetSelectionBack.png"
PET_SELECTION_SMALL_ON_PATH = "assets/PetSelectionSmallOn.png"
PET_SELECTION_SMALL_OFF_PATH = "assets/PetSelectionSmallOff.png"
GIFT_PATH = "assets/Gift.png"
ALERT_ICON_PATH = "assets/Alert.png"
CALL_SIGN_INVERSE_PATH = "assets/CallSignInverted.png"

#=====================================================================
# Paths: Battle & Training Sprites
#=====================================================================
BATTLE_BACKGROUND_PATH = "assets/BattleBackground.png"
TRAINING_BACKGROUND_PATH = "assets/TrainingBackground.png"
HEADTRAINING_PATH = "assets/HeadTraining.png"
VS_PATH = "assets/Vs.png"
STRIKES_BACK_PATH = "assets/StrikesBar.png"
STRIKE_PATH = "assets/Strike.png"
BATTLE_ICON_PATH = "assets/BattleIcon.png"
NEXT_BATTLE_ICON_PATH = "assets/NextBattle.png"
RESTART_BATTLE_ICON_PATH = "assets/RestartBattle.png"
HEAD_TRAINING_ICON_PATH = "assets/HeadTrainingIcon.png"
VERSUS_BATTLE_ICON_PATH = "assets/VersusBattle.png"
JOGRESS_ICON_PATH = "assets/Jogress.png"
ARMOR_EVOLUTION_ICON_PATH = "assets/ArmorEvolution.png"
DUMMY_TRAINING_ICON_PATH = "assets/BagIcon.png"
SHAKE_MATCH_ICON_PATH = "assets/CountTrainingIcon.png"
EXCITE_MATCH_ICON_PATH = "assets/ExciteTrainingIcon.png"
PUNCH_MATCH_ICON_PATH = "assets/PunchTrainingIcon.png"
XAIARROW_ICON_PATH = "assets/XaiArrow.png"
BOSS_MULTIPLIER = 1.5 

#=====================================================================
# Paths: Pet Sprites
#=====================================================================
DEAD_FRAME_PATH = "assets/Dead.png"
AGE_ICON_PATH = "assets/Age.png"
WEIGHT_ICON_PATH = "assets/Scale.png"
MODULE_ICON_PATH = "assets/Module.png"
VERSION_ICON_PATH = "assets/Version.png"
MISTAKES_ICON_PATH = "assets/Mistakes.png"
TRAITED_ICON_PATH = "assets/Traited.png"
SPECIAL_ICON_PATH = "assets/Special.png"
SHINY_ICON_PATH = "assets/Shiny.png"
SHOOK_ICON_PATH = "assets/Shook.png"
OVERFEED_ICON_PATH = "assets/Overfeed.png"
SICK_ICON_PATH = "assets/Sick1.png"
SLEEP_DISTURBANCES_ICON_PATH = "assets/SleepDisturbances.png"
XAI_ICON_PATH = "assets/Xai.png"
TROPHIES_ICON_PATH = "assets/Trophies.png"
VITAL_VALUES_ICON_PATH = "assets/vitalvalues.png"
DIGIDEX_ICON_PATH = "assets/DigidexIcon.png"
FREEZER_ICON_PATH = "assets/FreezerIcon.png"


#=====================================================================
# Paths: UI Icons
#=====================================================================
HEART_EMPTY_ICON_PATH = "assets/Heart Empty.png"
HEART_HALF_ICON_PATH = "assets/Heart Half.png"
HEART_FULL_ICON_PATH = "assets/Heart Full.png"
ENERGY_BAR_ICON_PATH = "assets/Energy Bar Count - Green.png"
ENERGY_BAR_BACK_ICON_PATH = "assets/Energy Bar.png"
LEVEL_ICON_PATH = "assets/Level.png"
EXP_ICON_PATH = "assets/Exp.png"

#=====================================================================
# Paths: Scene Backgrounds
#=====================================================================
SPLASH_PATH = "assets/Splash.png"
MAIN_MENU_PATH = "assets/Menu.png"
DIGIDEX_BACKGROUND_PATH = "assets/Digidex.png"

#=====================================================================
# Paths: Battle Scene Sprites
#=====================================================================
BATTLE_SPRITE_PATH = "assets/Battle.png"
BATTLE_LEVEL_SPRITE_PATH = "assets/BattleLevel.png"
BAR_BACK_PATH = "assets/StrengthBarBack.png"
BAR_PIECE_PATH = "assets/StrengthBar.png"
TRAINING_MAX_PATH = "assets/TrainingMax.png"
ALERT_SPRITE_PATH = "assets/Alert.png"
GO_SPRITE_PATH = "assets/Go.png"
BAD_SPRITE_PATH = "assets/Bad.png"
GOOD_SPRITE_PATH = "assets/Good.png"
GREAT_SPRITE_PATH = "assets/Great.png"
EXCELLENT_SPRITE_PATH = "assets/Excellent.png"
READY_SPRITE_PATH = "assets/Ready.png"
BATTLE1_PATH = "assets/Battle1.png"
BATTLE2_PATH = "assets/Battle2.png"
BAG1_PATH = "assets/Bag1.png"
BAG2_PATH = "assets/Bag2.png"
BRICK1_PATH = "assets/Brick1.png"
BRICK2_PATH = "assets/Brick2.png"
ROCK1_PATH = "assets/Rock1.png"
ROCK2_PATH = "assets/Rock2.png"
TREE1_PATH = "assets/Tree1.png"
TREE2_PATH = "assets/Tree2.png"


#=====================================================================
# Paths: Training Sprites
#=====================================================================
READY_SPRITES_PATHS = {
    1: "assets/Ready1.png",
    2: "assets/Ready2.png",
    3: "assets/Ready3.png"
}

COUNT_SPRITES_PATHS = {
    4: "assets/Count4.png",
    3: "assets/Count3.png",
    2: "assets/Count2.png",
    1: "assets/Count1.png"
}

MEGA_HIT_PATH = "assets/MegaHit.png"
CLEAR1_PATH = "assets/Clear1.png"
CLEAR2_PATH = "assets/Clear2.png"
WARNING1_PATH = "assets/Warning1.png"
WARNING2_PATH = "assets/Warning2.png"
HIT_ANIMATION_PATH = "assets/Hit.png"

ITEM_SPRITESHEET = "assets/Items.png"
ITEM_SPRITE_SIZE = 48  # Each cell is 48x48 in a 5x7 grid

#=====================================================================
# Paths: Additional Resources (previously hardcoded)
#=====================================================================
FONT_TTF_PATH = "assets/vpet_font.TTF"
FONT_ALT_TTF_PATH = "assets/vpet_font_alt.ttf"
ICON_ON_PATH = "assets/IconOn.png"
ICON_OFF_PATH = "assets/IconOff.png"
OMNI_WIFI_PATH = "assets/OmniWifi.png"
SLEEP_ICON_PATH = "assets/SleepIcon.png"
WAKE_ICON_PATH = "assets/WakeIcon.png"
EVO1_PATH = "assets/Evo1.png"
EVO2_PATH = "assets/Evo2.png" 
EVO3_PATH = "assets/Evo3.png"
EVO5_PATH = "assets/Evo5.png"
FOG_PATH = "assets/Fog.png"
ORB_PATH = "assets/Orb.png"
LIGHT_SOURCE_PATH = "assets/LightSource.png"
LIGHT_PARTICLE_PATH = "assets/LightParticle.png"
DNA_PATH = "assets/Dna.png"
UNKNOWN_SPRITE_PATH = "assets/Unknown.png"
TRAITED_EGG_PATH = "assets/TraitedEgg.png"
OMNIMON_LOGO_PATH = "assets/OmnimonLogo.png"
CONTROLLERS_PC_PATH = "assets/ControllersPC.png"
CONTROLLERS_BATO_PATH = "assets/ControllersBato.png"
CONTROLLERS_PI_PATH = "assets/ControllersPi.png"
CONTROLLERS_JOY_PATH = "assets/ControllersJoy.png"
DMC_SOUNDS_PATH = "assets/dmc_sounds"

def update_resolution_constants(width, height):
    global SCREEN_WIDTH, SCREEN_HEIGHT, UI_SCALE, PET_WIDTH, PET_HEIGHT
    global MENU_ICON_SIZE, OPTION_ICON_SIZE, OPTION_FRAME_WIDTH, OPTION_FRAME_HEIGHT, PET_ICON_SIZE
    global FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_MEDIUM_LARGE, FONT_SIZE_LARGE

    SCREEN_WIDTH = width
    SCREEN_HEIGHT = height
    UI_SCALE = SCREEN_HEIGHT / 240  # Or your preferred base value

    MENU_ICON_SIZE = int(24 * UI_SCALE)
    OPTION_ICON_SIZE = int(48 * UI_SCALE)
    OPTION_FRAME_WIDTH = int(96 * UI_SCALE)
    OPTION_FRAME_HEIGHT = int(116 * UI_SCALE)
    PET_ICON_SIZE = int(48 * UI_SCALE)

    FONT_SIZE_SMALL = int(24 * UI_SCALE)
    FONT_SIZE_MEDIUM = int(28 * UI_SCALE)
    FONT_SIZE_MEDIUM_LARGE = int(30 * UI_SCALE)
    FONT_SIZE_LARGE = int(40 * UI_SCALE)

    # Prevent oversized sprites when MAX_PETS == 1
    PET_WIDTH = PET_HEIGHT = SCREEN_HEIGHT // max(MAX_PETS, 2)

    # Also update combat constants
    try:
        import game.core.combat.combat_constants as battle_constants
        if hasattr(battle_constants, "update_combat_constants"):
            battle_constants.update_combat_constants()
    except ImportError:
        pass
