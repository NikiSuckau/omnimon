"""
Omnipet Virtual Pet Game - Main Entry Point for Nuitka Builds
Handles pygame initialization with explicit video driver setup for embedded/low-power devices.
The game logic is handled by the VirtualPetGame class in game/vpet.py
"""

import sys
import os
import pygame
import json
import platform
import logging
from datetime import datetime

# Game Version
VERSION = "0.9.8"

# Global scaling variables
render_surface = None
final_screen = None
scale_to_screen = False
native_width = 0
native_height = 0


def load_display_config():
    """Load display configuration with auto-detection for embedded systems"""
    if platform.system() == "Linux":
        if os.path.exists("/usr/bin/batocera-info"):
            display_config = "config/config.json"
        elif os.path.exists("/boot/config.txt"):
            display_config = "config/config.json"
        else:
            display_config = "config/config.json"
    elif platform.system() == "Windows":
        display_config = "config/config.json"
    elif platform.system() == "Darwin":
        display_config = "config/config.json"
    else:
        display_config = "config/config.json"

    try:
        with open(display_config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        config = {
            "SCREEN_WIDTH": 240,
            "SCREEN_HEIGHT": 240,
            "FULLSCREEN": False,
            "AUTO_RESOLUTION": False
        }
    
    return config


def get_screen_resolution():
    """Get the current screen resolution"""
    try:
        pygame.display.init()
        info = pygame.display.Info()
        return info.current_w, info.current_h
    except:
        return 1920, 1080  # Default fallback


def try_set_video_driver():
    """Try a list of SDL video drivers in order until one works."""
    drivers = []
    if platform.system() == "Linux":
        if os.path.exists("/usr/bin/batocera-info"):
            drivers = ["kmsdrm", "x11", "wayland", "fbcon"]
        else:
            drivers = ["x11", "wayland", "fbcon"]
    elif platform.system() == "Windows":
        drivers = ["windows"]
    elif platform.system() == "Darwin":
        drivers = ["cocoa"]
    else:
        drivers = ["x11", "wayland", "fbcon"]

    for driver in drivers:
        os.environ["SDL_VIDEODRIVER"] = driver
        try:
            pygame.display.init()
            return driver
        except pygame.error:
            continue
    raise RuntimeError("No compatible SDL video driver found!")


def setup_pygame():
    """Initialize pygame with appropriate settings"""
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")  # Center window on desktop systems
    
    # Check Pygame version for compatibility
    PYGAME_VERSION = tuple(map(int, pygame.version.ver.split('.')))
    IS_PYGAME2 = PYGAME_VERSION >= (2, 0, 0)
    
    # Only set video driver if not already set
    if not os.getenv("SDL_VIDEODRIVER"):
        try:
            chosen_driver = try_set_video_driver()
            logging.info(f"[Display] Using SDL video driver: {chosen_driver}")
        except RuntimeError as e:
            logging.error(f"[Display] {e}")
            sys.exit(1)
    else:
        pygame.display.init()

    # Initialize Pygame with version-specific mixer setup
    if IS_PYGAME2:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=128)

    pygame.init()
    
    if not IS_PYGAME2:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=128)


def apply_config_to_constants(config):
    """Apply configuration values to constants module"""
    # Import after pygame init to avoid circular dependencies
    from game.core import constants
    
    # Apply frame rate
    frame_rate = config.get("FRAME_RATE", 30)
    if frame_rate < 3:
        frame_rate = 3
    constants.FRAME_RATE = frame_rate
    
    # Apply max pets
    max_pets = config.get("MAX_PETS", 4)
    if max_pets < 1:
        max_pets = 1
    constants.MAX_PETS = max_pets
    
    # Apply debug settings
    constants.DEBUG_MODE = config.get("DEBUG_MODE", config.get("DEBUG", False))
    constants.DEBUG_FILE_LOGGING = config.get("DEBUG_FILE_LOGGING", config.get("LOGGING", False))
    constants.SHOW_FPS = config.get("SHOW_FPS", False)
    constants.DEBUG_BLIT_LOGGING = config.get("DEBUG_BLIT_LOGGING", config.get("LOG_BLITS", False))
    constants.DEBUG_BATTLE_INFO = config.get("DEBUG_BATTLE_INFO", False)
    
    # Update legacy aliases
    constants.DEBUG = constants.DEBUG_MODE
    constants.LOGGING = constants.DEBUG_FILE_LOGGING
    constants.LOG_BLITS = constants.DEBUG_BLIT_LOGGING
    
    logging.info(f"[Config] Applied: FRAME_RATE={constants.FRAME_RATE}, MAX_PETS={constants.MAX_PETS}, DEBUG_MODE={constants.DEBUG_MODE}")


def setup_display():
    """Setup the display window with proper resolution and fullscreen detection"""
    global render_surface, final_screen, scale_to_screen, native_width, native_height

    config = load_display_config()
    
    # Apply configuration to constants module
    apply_config_to_constants(config)
    
    # Determine if we should run in fullscreen
    fullscreen_requested = (
        "--fullscreen" in sys.argv or
        "-f" in sys.argv or
        os.getenv("OMNIPET_FULLSCREEN", "").lower() in ("1", "true", "yes") or
        config.get("FULLSCREEN", False) or
        os.getenv("SDL_VIDEODRIVER") == "kmsdrm" or
        (platform.system() == "Linux" and os.path.exists("/usr/bin/batocera-info"))
    )
    
    # Determine screen resolution
    if config.get("AUTO_RESOLUTION", False) and fullscreen_requested:
        # Use native screen resolution
        screen_width, screen_height = get_screen_resolution()
        logging.info(f"[Display] Auto-resolution enabled: {screen_width}x{screen_height}")
        scale_to_screen = False
    else:
        screen_width = config.get("SCREEN_WIDTH", 240)
        # Same sanity checks as in constants.py and main.py
        if not screen_width:
            screen_width = 240
        if screen_width < 100:
            screen_width = 100
        screen_height = config.get("SCREEN_HEIGHT", 240)
        if not screen_height:
            screen_height = 240
        if screen_height < 100:
            screen_height = 100
        logging.info(f"[Display] Using config resolution: {screen_width}x{screen_height}")

        if fullscreen_requested:
            native_width, native_height = get_screen_resolution()
            scale_to_screen = True
            logging.info(f"[Display] Scaling {screen_width}x{screen_height} -> {native_width}x{native_height}")
        else:
            scale_to_screen = False

    # Import constants here after pygame is initialized
    from game.core import constants
    
    # Update game constants with base resolution
    constants.update_resolution_constants(width=screen_width, height=screen_height)

    # Check Pygame version for compatibility
    PYGAME_VERSION = tuple(map(int, pygame.version.ver.split('.')))
    IS_PYGAME2 = PYGAME_VERSION >= (2, 0, 0)

    if fullscreen_requested:
        screen_mode = pygame.FULLSCREEN | pygame.DOUBLEBUF
        logging.info(f"[Display] Running in fullscreen mode")
    else:
        screen_mode = 0
        logging.info(f"[Display] Running in windowed mode")

    bit_depth = 32 if IS_PYGAME2 else 16

    # The final screen always uses native resolution if scaling is enabled
    final_screen = pygame.display.set_mode(
        (native_width if scale_to_screen else screen_width,
         native_height if scale_to_screen else screen_height),
        screen_mode,
        bit_depth
    )

    # Create the render surface if scaling
    render_surface = pygame.Surface((screen_width, screen_height)) if scale_to_screen else final_screen

    pygame.display.set_caption(f"Omnipet {VERSION}")
    pygame.mouse.set_visible(False)
    pygame.event.set_allowed([
        pygame.QUIT, 
        pygame.KEYDOWN,
        pygame.JOYBUTTONDOWN,
        pygame.JOYBUTTONUP,
        pygame.JOYAXISMOTION,
        pygame.JOYHATMOTION,
        pygame.JOYDEVICEADDED,
        pygame.JOYDEVICEREMOVED
    ])
    return render_surface, screen_width, screen_height


def main():
    """Main function to initialize and run the game"""
    logging.info("[Init] Starting Omnipet Virtual Pet Game...")
    
    # Setup pygame and display
    setup_pygame()
    screen, screen_width, screen_height = setup_display()
    
    # Import game modules after pygame setup
    from game.core import constants
    from game.vpet import VirtualPetGame
    
    # Initialize and run the game
    try:
        game = VirtualPetGame()
        
        # Build module documentation
        try:
            from game.core.utils.document_utils import build_module_documentation
            project_root = os.path.dirname(__file__)
            logging.info("[Init] Building module documentation...")
            build_module_documentation(project_root)
        except Exception as e:
            logging.warning(f"[Init] Failed to build module documentation: {e}")
        
        logging.info("[Init] Game initialized successfully")
        logging.info("[Game] Starting main game loop...")
        
        running = True
        clock = pygame.time.Clock()
        
        while running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.save()
                    running = False
                else:
                    game.handle_event(event)
            
            # Update game state
            game.update()
            
            # Draw game
            game.draw(screen, clock)

            # If scaling, blit scaled render surface to fullscreen display
            if scale_to_screen:
                pygame.transform.scale(screen, (native_width, native_height), final_screen)

            pygame.display.flip()
            
            # Maintain framerate
            clock.tick(constants.FRAME_RATE)
        
        logging.info("[Game] Shutting down...")
        
    except Exception as e:
        logging.critical("An unhandled exception occurred in the main loop.", exc_info=True)
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        logging.info("[Game] Goodbye!")


if __name__ == "__main__":
    # Determine if the application is running in a "frozen" state (e.g., compiled by Nuitka).
    # Nuitka sets sys.frozen=True and may also set sys._MEIPASS for extraction directory
    is_frozen = getattr(sys, 'frozen', False)
    
    # For Nuitka debugging - let's check multiple possible indicators
    nuitka_indicators = {
        'sys.frozen': getattr(sys, 'frozen', 'Not set'),
        'sys._MEIPASS': getattr(sys, '_MEIPASS', 'Not set'),
        'sys.executable': sys.executable,
        '__file__': __file__ if '__file__' in globals() else 'Not set',
        'os.path.basename(sys.executable)': os.path.basename(sys.executable),
        'hasattr(sys, "_getframe")': hasattr(sys, "_getframe"),
        '__compiled__' in globals(): '__compiled__' in globals()
    }
    
    print(f"[Debug] Nuitka detection indicators:")
    for key, value in nuitka_indicators.items():
        print(f"[Debug]   {key}: {value}")

    # Improved frozen detection for Nuitka
    # Nuitka doesn't always set sys.frozen, so we need multiple detection methods
    possible_frozen_indicators = [
        getattr(sys, 'frozen', False),  # Standard frozen attribute
        '__compiled__' in globals(),     # Nuitka specific global
        os.path.basename(sys.executable).lower().endswith('.exe'),  # Running from .exe
        not __file__.endswith('.py') if '__file__' in globals() else False  # Not running from .py file
    ]
    
    is_frozen = any(possible_frozen_indicators)
    print(f"[Debug] Final frozen determination: {is_frozen} (based on: {possible_frozen_indicators})")

    # Try multiple methods to detect the correct base directory
    if is_frozen:
        # For Nuitka builds, check if there's an extraction directory first
        if hasattr(sys, '_MEIPASS'):
            # Nuitka with temporary extraction
            base_dir = sys._MEIPASS
            print(f"[Nuitka] Using temporary extraction directory: {base_dir}")
        elif '__compiled__' in globals():
            # Nuitka specific: use the compiled module's directory
            try:
                import __main__
                base_dir = __main__.__compiled__.containing_dir
                print(f"[Nuitka] Using __compiled__.containing_dir: {base_dir}")
            except:
                base_dir = os.path.dirname(sys.executable)
                print(f"[Nuitka-fallback] Using executable directory: {base_dir}")
        else:
            # Standard frozen executable directory
            base_dir = os.path.dirname(sys.executable)
            print(f"[Frozen] Using executable directory: {base_dir}")
    else:
        # If not frozen, it's running as a script, so the base is the script's directory.
        # BUT: If we're running from a Nuitka executable that doesn't set frozen properly,
        # we need to detect this case
        if os.path.basename(sys.executable).lower() == 'omnipet.exe':
            # We're likely running from a Nuitka executable
            base_dir = os.path.dirname(sys.executable)
            print(f"[Nuitka-Alt] Detected Nuitka executable, using executable directory: {base_dir}")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[Script] Using script directory: {base_dir}")

    # Change the current working directory to the base directory.
    # This is crucial for ensuring that relative paths for assets or configs are resolved correctly.
    os.chdir(base_dir)

    # CRITICAL: Set up Python path IMMEDIATELY to handle both source and compiled structures
    # Add directories to Python path to support both absolute and relative imports
    # Add base directory for top-level imports
    sys.path.insert(0, base_dir)
    
    # For Nuitka, we need to check multiple possible locations for the game directory
    possible_game_dirs = [
        os.path.join(base_dir, 'game'),
        # Nuitka might extract to a subdirectory
        os.path.join(base_dir, 'main_nuitka.dist', 'game'),
        # Or to a temporary directory we haven't found yet
    ]
    
    # Also try to find the game directory in sys.path or Python's import system
    try:
        import game
        game_module_path = game.__file__
        if game_module_path:
            game_dir = os.path.dirname(game_module_path)
            possible_game_dirs.insert(0, game_dir)
            print(f"[Import] Found game module at: {game_dir}")
    except ImportError:
        print(f"[Import] Could not import game module to find location")
    
    game_dir = None
    for potential_dir in possible_game_dirs:
        if os.path.exists(potential_dir):
            game_dir = potential_dir
            print(f"[Path] Found game directory: {game_dir}")
            break
    
    if game_dir:
        # CRITICAL FIX: Add the parent directory of game/, not game/ itself
        # This allows 'import game.core' to work correctly
        game_parent_dir = os.path.dirname(game_dir)
        sys.path.insert(0, game_parent_dir)
        print(f"[Path] Added game parent directory: {game_parent_dir}")
        
        # For backward compatibility and relative imports inside game package,
        # also add the game directory itself
        sys.path.insert(0, game_dir)
        print(f"[Path] Added game directory: {game_dir}")
        
        # Add the game/core directory to support 'from core import' style imports
        # (though these should be converted to absolute imports)
        core_dir = os.path.join(game_dir, 'core')
        if os.path.exists(core_dir):
            sys.path.insert(0, core_dir)
            print(f"[Path] Added core directory: {core_dir}")
        else:
            print(f"[Warning] Core directory not found: {core_dir}")
    else:
        print(f"[Error] Could not find game directory in any of these locations:")
        for potential_dir in possible_game_dirs:
            print(f"[Error]   - {potential_dir}")
    
    # Debug output for troubleshooting
    print(f"[Debug] Working directory: {os.getcwd()}")
    print(f"[Debug] Python path entries: {[p for p in sys.path if 'game' in p or p == base_dir]}")

    # Setup logging
    log_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(filename=os.path.join(log_dir, 'omnipet.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Application starting...")
    
    # Log system information
    PYGAME_VERSION = tuple(map(int, pygame.version.ver.split('.')))
    IS_PYGAME2 = PYGAME_VERSION >= (2, 0, 0)
    
    logging.info(f"[System] Omnipet Virtual Pet v{VERSION}")
    logging.info(f"[System] Detected Pygame version: {pygame.version.ver}")
    logging.info(f"[System] Platform: {platform.system()} {platform.release()}")
    
    main()
