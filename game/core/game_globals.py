import datetime
import os
import pickle
import random
import time

#=====================================================================
# Game Global State
#=====================================================================

SAVE_FILE = "save/save_data.dat"
SAVE_DIR = "save"
MAX_BACKUPS = 10  # Keep 10 backup files

# Persistent variables
game_background = None
background_module_name = None
background_high_res = False

pet_list = []
poop_list = []
traited = []
gcell_fragments = []
unlocks = {}
showClock = True
sound = 3
battle_area = {}
battle_round = {}
last_adventure_module = None  # Track last played adventure module
rotated = False
xai = 1
xai_date = datetime.date.today()
inventory = {}
battle_effects = {}
wake_time = None
sleep_time = None
screen_timeout = 60
quests = []
event = None
event_time = None
sprite_resolution_preference = 0

# Internal timer for autosave
_last_save_time = time.time()
AUTOSAVE_INTERVAL_SECONDS = 60  # 5 minutes

def get_next_save_number():
    """Get the next save file number for backup rotation (1 to MAX_BACKUPS)."""
    if not os.path.exists(SAVE_DIR):
        return 1

    # Get the highest number and increment by 1
    latest_save = get_latest_save_file()
    if latest_save == None:
        next_number = 1
    else:
        latest_save = os.path.basename(latest_save)
        next_number = int(latest_save.replace("save_data_", "").replace(".dat", "")) + 1
    
    # If we exceed MAX_BACKUPS, wrap around to 1
    if next_number > MAX_BACKUPS:
        return 1
    
    return next_number

def get_latest_save_file():
    """Get the path to the most recent save file."""
    if not os.path.exists(SAVE_DIR):
        return None
    
    # Check if old save_data.dat exists and migrate it first
    old_save_path = os.path.join(SAVE_DIR, "save_data.dat")
    if os.path.exists(old_save_path):
        new_save_path = os.path.join(SAVE_DIR, "save_data_1.dat")
        try:
            os.rename(old_save_path, new_save_path)
            print(f"[Save] Migrated save_data.dat to save_data_1.dat")
        except Exception as e:
            print(f"[Save] Failed to migrate save_data.dat: {e}")
    
    # Find existing numbered save files
    save_files = []
    for filename in os.listdir(SAVE_DIR):
        if filename.startswith("save_data_") and filename.endswith(".dat"):
            try:
                number_part = filename.replace("save_data_", "").replace(".dat", "")
                full_path = os.path.join(SAVE_DIR, filename)
                save_files.append((int(number_part), full_path))
            except ValueError:
                continue
    
    if not save_files:
        return None

    # Return the most recent file
    save_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
    return save_files[0][1]

def cleanup_old_saves():
    """Remove old backup saves beyond MAX_BACKUPS."""
    if not os.path.exists(SAVE_DIR):
        return
    
    # Find all numbered save files
    save_files = []
    for filename in os.listdir(SAVE_DIR):
        if filename.startswith("save_data_") and filename.endswith(".dat"):
            try:
                number_part = filename.replace("save_data_", "").replace(".dat", "")
                full_path = os.path.join(SAVE_DIR, filename)
                save_files.append((int(number_part), full_path))
            except ValueError:
                continue
    
    # Keep only the most recent MAX_BACKUPS files
    if len(save_files) > MAX_BACKUPS:
        save_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
        files_to_remove = save_files[MAX_BACKUPS:]
        
        for _, file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"[Save] Removed old backup: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"[Save] Failed to remove old backup {file_path}: {e}")

def save() -> None:
    """
    Saves the current global game state to a file with backup rotation.
    """
    # Ensure save directory exists
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
            print(f"[Save] Created save directory: {SAVE_DIR}")
        except Exception as e:
            print(f"[Save] Failed to create save directory: {e}")
            return

    data = {
        "pet_list": pet_list,
        "poop_list": poop_list,
        "traited": traited,
        "gcell_fragments": gcell_fragments,
        "game_background": game_background,
        "battle_area": battle_area,
        "battle_round": battle_round,
        "last_adventure_module": last_adventure_module,
        "background_module_name": background_module_name,
        "unlocks": unlocks,
        "showClock": showClock,
        "sound": sound,
        "xai": xai,
        "xai_date": xai_date,
        "inventory": inventory,
        "battle_effects": battle_effects,
        "background_high_res": background_high_res,
        "wake_time": wake_time,
        "sleep_time": sleep_time,
        "screen_timeout": screen_timeout,
        "quests": quests,
        "event": event,
        "event_time": event_time,
        "sprite_resolution_preference": sprite_resolution_preference,
    }

    # Get the next save number and create the filename
    save_number = get_next_save_number()
    save_path = os.path.join(SAVE_DIR, f"save_data_{save_number}.dat")

    try:
        with open(save_path, "wb") as f:
            pickle.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        
        print(f"[Save] Game saved successfully to: {os.path.basename(save_path)}")
        
        # Clean up old saves
        cleanup_old_saves()
        
    except Exception as e:
        print(f"[Save] Failed to save game: {e}")

def load() -> None:
    """
    Loads the global game state from the most recent save file, with fallback to previous saves.
    """
    global pet_list, poop_list, traited, gcell_fragments, unlocks, battle_area, battle_round, last_adventure_module, xai, xai_date, background_high_res
    global game_background, background_module_name, showClock, sound, inventory, battle_effects
    global wake_time, sleep_time, screen_timeout, sprite_resolution_preference
    global quests, event, event_time

    # Get all available save files in order (newest first)
    save_files_to_try = []
    
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
            print(f"[Save] Created save directory: {SAVE_DIR}")
        except Exception as e:
            print(f"[Save] Failed to create save directory: {e}")
            return

    # Check if old save_data.dat exists and migrate it first
    old_save_path = os.path.join(SAVE_DIR, "save_data.dat")
    if os.path.exists(old_save_path):
        new_save_path = os.path.join(SAVE_DIR, "save_data_1.dat")
        try:
            os.rename(old_save_path, new_save_path)
            print(f"[Save] Migrated save_data.dat to save_data_1.dat")
        except Exception as e:
            print(f"[Save] Failed to migrate save_data.dat: {e}")

    # Find all numbered save files
    all_saves = []
    for filename in os.listdir(SAVE_DIR):
        if filename.startswith("save_data_") and filename.endswith(".dat"):
            try:
                number_part = filename.replace("save_data_", "").replace(".dat", "")
                full_path = os.path.join(SAVE_DIR, filename)
                all_saves.append((int(number_part), full_path))
            except ValueError:
                continue
    
    # Sort by modification time (newest first)
    all_saves.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
    save_files_to_try = [save_path for _, save_path in all_saves]

    # Try to load each save file in order
    for save_path in save_files_to_try:
        try:
            with open(save_path, "rb") as f:
                data = pickle.load(f)

                # Load pet list with error handling
                loaded_pet_list = data.get("pet_list", [])
                valid_pets = []
                
                for pet in loaded_pet_list:
                    if pet is None:
                        continue
                        
                    try:
                        # Test basic pet attributes safely
                        if (hasattr(pet, 'name') and hasattr(pet, 'module') and 
                            hasattr(pet, 'stage') and hasattr(pet, 'state')):
                            
                            # Initialize missing attributes for compatibility
                            if not hasattr(pet, 'trophies'):
                                pet.trophies = 0
                            if not hasattr(pet, 'vital_values'):
                                pet.vital_values = 0
                            # Ensure PvP counters exist for compatibility with older saves
                            if not hasattr(pet, 'pvp_battles'):
                                pet.pvp_battles = 0
                            if not hasattr(pet, 'pvp_wins'):
                                pet.pvp_wins = 0
                            
                            # Apply any patches from the pet class
                            if hasattr(pet, 'patch'):
                                pet.patch()
                                
                            valid_pets.append(pet)
                            print(f"[Game] Successfully loaded pet: {pet.name}")
                        else:
                            print(f"[Game] Pet missing required attributes, skipping")
                            continue
                            
                    except Exception as e:
                        print(f"[Game] Failed to load pet (removing from save): {e}")
                        continue
                
                pet_list = valid_pets
                poop_list = data.get("poop_list", [])
                for poop in poop_list:
                    poop.patch()  # Ensure all poops have necessary attributes

                traited = data.get("traited", [])
                gcell_fragments = data.get("gcell_fragments", [])
                game_background = data.get("game_background", None)
                battle_area = data.get("battle_area", {})
                battle_round = data.get("battle_round", {})
                last_adventure_module = data.get("last_adventure_module", None)
                background_module_name = data.get("background_module_name", None)
                unlocks = data.get("unlocks", {})
                showClock = data.get("showClock", True)
                sound = data.get("sound", 1)
                xai = data.get("xai", random.randint(1, 7))
                xai_date = data.get("xai_date", datetime.date.today())
                inventory = data.get("inventory", {})
                battle_effects = data.get("battle_effects", {})
                background_high_res = data.get("background_high_res", False)
                wake_time = data.get("wake_time", None)
                sleep_time = data.get("sleep_time", None)
                screen_timeout = data.get("screen_timeout", 60)
                quests = data.get("quests", [])
                event = data.get("event", None)
                event_time = data.get("event_time", None)
                sprite_resolution_preference = data.get("sprite_resolution_preference", 0)

                print(f"[Game] Successfully loaded save file: {os.path.basename(save_path)} with {len(pet_list)} valid pets")
                return  # Successfully loaded, exit the function
                
        except Exception as e:
            print(f"[Game] Failed to load save file {os.path.basename(save_path)}: {e}")
            continue  # Try the next save file
    
    # If we get here, all save files failed to load
    print(f"[Game] All save files failed to load. Starting with fresh game state.")
    # Reset to default values
    pet_list = []
    poop_list = []
    traited = []
    gcell_fragments = []
    game_background = None
    battle_area = {}
    battle_round = {}
    last_adventure_module = None
    background_module_name = None
    unlocks = {}
    showClock = True
    sound = 1
    xai = random.randint(1, 7)
    xai_date = datetime.date.today()
    inventory = {}
    battle_effects = {}
    background_high_res = False
    wake_time = None
    sleep_time = None
    screen_timeout = 60

def autosave() -> None:
    """
    Automatically saves the game if the autosave interval has passed.
    """
    global _last_save_time
    now = time.time()

    if now - _last_save_time >= AUTOSAVE_INTERVAL_SECONDS:
        save()
        _last_save_time = now
