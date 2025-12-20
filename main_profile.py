"""
Omnipet Virtual Pet Game - Main Entry Point with Performance Profiling
Handles pygame initialization, video/audio setup, and display management.
The game logic is handled by the VirtualPetGame class in game/vpet.py

This version includes cProfile performance profiling to identify bottlenecks.
Run with: python main_profile.py
"""

import platform
import pygame
import os
import sys
import json
import cProfile
import pstats
import io

import sys, os

from core import constants
from core.utils.document_utils import build_module_documentation
# sys.stderr = open(os.devnull, 'w')  # Commented out to allow error stack traces

# Add game directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'game'))

from vpet import VirtualPetGame
from core.constants import *

# Game Version
VERSION = "0.9.9"

# Check Pygame version for compatibility
PYGAME_VERSION = tuple(map(int, pygame.version.ver.split('.')))
IS_PYGAME2 = PYGAME_VERSION >= (2, 0, 0)

print(f"[System] Omnipet Virtual Pet v{VERSION} (PROFILING BUILD)")
print(f"[System] Detected Pygame version: {pygame.version.ver}")
print(f"[System] Platform: {platform.system()} {platform.release()}")

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
    
    # Only set video driver if not already set
    if not os.getenv("SDL_VIDEODRIVER"):
        try:
            chosen_driver = try_set_video_driver()
            print(f"[Display] Using SDL video driver: {chosen_driver}")
        except RuntimeError as e:
            print(f"[Display] {e}")
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
    from core import constants
    
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
    
    print(f"[Config] Applied: FRAME_RATE={constants.FRAME_RATE}, MAX_PETS={constants.MAX_PETS}, DEBUG_MODE={constants.DEBUG_MODE}")


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
        print(f"[Display] Auto-resolution enabled: {screen_width}x{screen_height}")
        scale_to_screen = False
    else:
        screen_width = config.get("SCREEN_WIDTH", 240)
        # Same sanity checks as in constants.py and main_nuitka.py
        if not screen_width:
            screen_width = 240
        if screen_width < 100:
            screen_width = 100
        screen_height = config.get("SCREEN_HEIGHT", 240)
        if not screen_height:
            screen_height = 240
        if screen_height < 100:
            screen_height = 100
        print(f"[Display] Using config resolution: {screen_width}x{screen_height}")

        if fullscreen_requested:
            native_width, native_height = get_screen_resolution()
            scale_to_screen = True
            print(f"[Display] Scaling {screen_width}x{screen_height} -> {native_width}x{native_height}")
        else:
            scale_to_screen = False

    # Update game constants with base resolution
    from core import runtime_globals
    runtime_globals.update_resolution_constants(width=screen_width, height=screen_height)

    if fullscreen_requested:
        screen_mode = pygame.FULLSCREEN | pygame.DOUBLEBUF
        print(f"[Display] Running in fullscreen mode")
    else:
        screen_mode = 0
        print(f"[Display] Running in windowed mode")

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

    pygame.display.set_caption(f"Omnipet {VERSION} [PROFILING]")
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


def run_game_loop():
    """Main game loop - separated for profiling"""
    screen, screen_width, screen_height = setup_display()
    
    # Initialize game
    game = VirtualPetGame()
    
    # Build module documentation
    try:
        project_root = os.path.dirname(__file__)
        print("[Init] Building module documentation...")
        build_module_documentation(project_root)
    except Exception as e:
        print(f"[Init] Failed to build module documentation: {e}")
    
    print("[Init] Game initialized successfully")
    print("[Game] Starting main game loop...")
    
    running = True
    clock = pygame.time.Clock()
    frame_count = 0
    
    # Profile for limited time or frames (configurable)
    max_frames = int(os.getenv("PROFILE_FRAMES", "9000"))  # Default: 60 seconds at 30fps
    print(f"[Profile] Will profile for {max_frames} frames (or until quit)")
    
    while running and frame_count < max_frames:
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
        frame_count += 1
        
        # Show progress every 300 frames
        if frame_count % 300 == 0:
            print(f"[Profile] Profiled {frame_count}/{max_frames} frames...")
    
    print(f"[Profile] Profiling complete after {frame_count} frames")
    return frame_count


def main():
    """Main function to initialize and run the game with profiling"""
    print("[Init] Starting Omnipet Virtual Pet Game with Performance Profiling...")
    print("[Profile] Press Ctrl+C or close window to stop profiling early")
    print("[Profile] Results will be saved to 'profile_results.txt' and 'profile_stats.prof'")
    
    # Setup pygame
    setup_pygame()
    
    # Create profiler
    profiler = cProfile.Profile()
    
    try:
        # Run game loop with profiling
        print("[Profile] Starting profiler...")
        profiler.enable()
        
        frame_count = run_game_loop()
        
        profiler.disable()
        print("[Profile] Profiler stopped")
        
        # Save detailed stats to file
        print("[Profile] Saving profile data...")
        profiler.dump_stats('profile_stats.prof')
        
        # Create human-readable report
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        
        # Sort by cumulative time and print top functions
        s.write("="*80 + "\n")
        s.write("TOP 50 FUNCTIONS BY CUMULATIVE TIME\n")
        s.write("="*80 + "\n")
        ps.sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(50)
        
        s.write("\n" + "="*80 + "\n")
        s.write("TOP 50 FUNCTIONS BY TOTAL TIME (INTERNAL)\n")
        s.write("="*80 + "\n")
        ps.sort_stats(pstats.SortKey.TIME)
        ps.print_stats(50)
        
        s.write("\n" + "="*80 + "\n")
        s.write("TOP 20 CALLERS\n")
        s.write("="*80 + "\n")
        ps.sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_callers(20)
        
        # Write to file
        with open('profile_results.txt', 'w') as f:
            f.write(f"Performance Profile - {frame_count} frames\n")
            f.write(s.getvalue())
        
        print("[Profile] Results saved to 'profile_results.txt'")
        print("[Profile] Binary stats saved to 'profile_stats.prof'")
        print("\n[Profile] Quick Summary:")
        
        # Print quick summary to console
        ps.sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(10)
        
        print("\n[Profile] Analysis Tips:")
        print("  - Check 'profile_results.txt' for detailed analysis")
        print("  - Use snakeviz for visualization: pip install snakeviz && snakeviz profile_stats.prof")
        print("  - Look for functions with high 'cumtime' (cumulative time)")
        print("  - Focus on optimizing functions called frequently (ncalls)")
        
    except KeyboardInterrupt:
        print("\n[Profile] Interrupted by user")
        profiler.disable()
        profiler.dump_stats('profile_stats_interrupted.prof')
        print("[Profile] Partial results saved to 'profile_stats_interrupted.prof'")
        
    except Exception as e:
        print(f"[Error] Game encountered an error: {e}")
        import traceback
        traceback.print_exc()
        profiler.disable()
        profiler.dump_stats('profile_stats_error.prof')
        
    finally:
        pygame.quit()
        print("[Game] Goodbye!")


if __name__ == "__main__":
    main()
