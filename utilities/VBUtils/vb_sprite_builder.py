#!/usr/bin/env python3
"""
VB Sprite Builder - Part 2 of 2
Builds monster.json and sprite ZIP files using the character names from OCR extraction.
Requires character_names.json from vb_ocr_extractor.py
"""

import os
import json
import re
import zipfile
from PIL import Image
from glob import glob

# Configuration
ROOT_FOLDER = r'D:\Digimon\DIMS\SpriteB'
INPUT_NAMES_JSON = 'character_names.json'
OUTPUT_MONSTER_JSON = 'monster.json'
OUTPUT_SPRITES_FOLDER = 'monsters'

# Default values by stage (from PetTemplates.cs and existing monster.json)
DEFAULT_VALUES_BY_STAGE = {
    0: {
        "time": 1, "poop_timer": 0, "energy": 0, "min_weight": 99, "evol_weight": 0,
        "stomach": 0, "hunger_loss": 0, "strength_loss": 0, "heal_doses": 1,
        "condition_hearts": 0, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": None, "wakes": None
    },
    1: {
        "time": 10, "poop_timer": 3, "energy": 0, "min_weight": 5, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 3, "strength_loss": 3, "heal_doses": 1,
        "condition_hearts": 1, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    2: {
        "time": 720, "poop_timer": 60, "energy": 0, "min_weight": 10, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 30, "strength_loss": 30, "heal_doses": 1,
        "condition_hearts": 2, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    3: {
        "time": 1440, "poop_timer": 120, "energy": 20, "min_weight": 20, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 48, "strength_loss": 48, "heal_doses": 1,
        "condition_hearts": 3, "jogress_avaliable": False, "hp": 10, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    4: {
        "time": 2160, "poop_timer": 120, "energy": 30, "min_weight": 30, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 12, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    5: {
        "time": 2400, "poop_timer": 120, "energy": 40, "min_weight": 40, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": True, "hp": 15, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    6: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 18, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    7: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 20, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    }
}

# Character sprite mapping (zip_file_index -> sprite_file_number)
CHARACTER_SPRITE_MAPPING = {
    0: 3, 1: 4, 2: 9, 3: 11, 4: 1, 5: 11, 6: 1, 7: 11, 8: 1, 9: 9, 10: 1, 11: 10, 12: 10, 13: 10, 14: 10
}

def load_json(path):
    """Load JSON file with error handling."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {path}: {e}")
        return None

def save_json(path, data):
    """Save data to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_int(d, keys):
    """Extract integer value from dictionary using multiple possible keys."""
    for k in keys:
        if k in d:
            try:
                return int(d[k])
            except Exception:
                try:
                    return int(float(d[k]))
                except Exception:
                    pass
    return None

def normalize_value(v):
    """Normalize values coming from character files: 65535 means 0 in our system."""
    if v is None:
        return None
    try:
        iv = int(v)
    except Exception:
        return None
    return 0 if iv == 65535 else iv

def convert_small_attack(v):
    """Convert smallAttack to atk_main: 65535 -> 0, else value+1"""
    nv = normalize_value(v)
    if nv is None:
        return None
    return 1 if nv == 0 else nv + 1

def convert_big_attack(v):
    """Convert bigAttack to atk_alt: 65535 -> 0, else value+1+40 (i.e. +41)"""
    nv = normalize_value(v)
    if nv is None:
        return None
    return 41 if nv == 0 else nv + 41

def get_attribute_string(attr_num):
    """Convert attribute number to string."""
    attr_map = {1: 'Vi', 2: 'Da', 3: 'Va'}
    return attr_map.get(attr_num, '')

def resolve_duplicate_names(folder_characters):
    """Resolve duplicate names within a folder by adding numbers."""
    name_counts = {}
    name_mapping = {}  # original_name -> final_name
    changes_made = []
    
    # First pass: count occurrences and identify duplicates
    for char_data in folder_characters:
        char_number = char_data['character_number']
        # Prioritize character_name over manual_name, but handle both cases
        original_name = char_data.get('character_name')
        if not original_name:
            original_name = char_data.get('manual_name')
        if not original_name:
            original_name = f"Character_{char_number:02d}"
        
        if original_name not in name_counts:
            name_counts[original_name] = []
        name_counts[original_name].append((char_number, char_data))
    
    # Second pass: resolve duplicates
    for original_name, char_list in name_counts.items():
        if len(char_list) > 1:
            # Only add numbers to stages 1 and 2 (characters 0-1), leave others unchanged
            stage_1_2_chars = []
            other_chars = []
            
            for char_number, char_data in char_list:
                # Only consider characters 0-1 as stages 1-2 that need numbering
                if char_number <= 1:  # Characters 0 and 1 are usually stages 1-2
                    stage_1_2_chars.append((char_number, char_data))
                else:
                    other_chars.append((char_number, char_data))
            
            # Add numbers only to stage 1-2 characters (0-1)
            if len(stage_1_2_chars) > 1:
                for i, (char_number, char_data) in enumerate(stage_1_2_chars, 1):
                    final_name = f"{original_name} {i}"
                    name_mapping[f"{char_data['folder_name']}_{char_number}"] = final_name
                    changes_made.append({
                        'folder': char_data['folder_name'],
                        'character_number': char_number,
                        'original_name': original_name,
                        'final_name': final_name
                    })
            else:
                # If only one stage 1-2 character, still map it
                for char_number, char_data in stage_1_2_chars:
                    name_mapping[f"{char_data['folder_name']}_{char_number}"] = original_name
            
            # Keep other characters unchanged but still map them
            for char_number, char_data in other_chars:
                name_mapping[f"{char_data['folder_name']}_{char_number}"] = original_name
        else:
            # Single occurrence, no change needed
            char_number, char_data = char_list[0]
            name_mapping[f"{char_data['folder_name']}_{char_number}"] = original_name
    
    return name_mapping, changes_made

def find_remaining_duplicates(all_monsters):
    """Find any remaining duplicate names across all monsters."""
    name_counts = {}
    duplicates = []
    
    for monster in all_monsters:
        name = monster.get('name', '')
        version = monster.get('version', 0)
        stage = monster.get('stage', 0)
        
        if name not in name_counts:
            name_counts[name] = []
        name_counts[name].append({
            'name': name,
            'version': version,
            'stage': stage
        })
    
    for name, entries in name_counts.items():
        if len(entries) > 1:
            duplicates.append({
                'name': name,
                'count': len(entries),
                'entries': entries
            })
    
    return duplicates

def find_orphaned_monsters(all_monsters):
    """Find monsters with no evolutions and no incoming evolutions (orphaned records)."""
    # Build a mapping of all monster names
    monster_names = set()
    evolution_targets = set()
    
    for monster in all_monsters:
        name = monster.get('name', '')
        monster_names.add(name)
        
        # Collect all evolution targets
        evolutions = monster.get('evolve', [])
        for evo in evolutions:
            target = evo.get('to', '')
            if target:
                evolution_targets.add(target)
    
    orphaned = []
    
    for monster in all_monsters:
        name = monster.get('name', '')
        version = monster.get('version', 0)
        stage = monster.get('stage', 0)
        evolutions = monster.get('evolve', [])
        
        # Check if monster has no outgoing evolutions
        has_outgoing_evolutions = len(evolutions) > 0
        
        # Check if monster has incoming evolutions (is an evolution target)
        has_incoming_evolutions = name in evolution_targets
        
        # Orphaned if it has neither outgoing nor incoming evolutions
        if not has_outgoing_evolutions and not has_incoming_evolutions:
            orphaned.append({
                'name': name,
                'version': version,
                'stage': stage
            })
    
    return orphaned

def find_character_files(data_folder):
    """Find all character_*.json files in the data folder."""
    pattern = os.path.join(data_folder, 'character_*.json')
    files = glob(pattern)
    # Sort by the numeric suffix
    def keyfn(p):
        m = re.search(r'character_(\d+)\.json$', p)
        return int(m.group(1)) if m else 999
    return sorted(files, key=keyfn)

def create_egg_monster(folder_name, version, first_stage_name=None):
    """Create egg monster entry with evolution to first stage."""
    defaults = DEFAULT_VALUES_BY_STAGE[0]
    
    evolve = []
    if first_stage_name:
        evolve.append({"to": first_stage_name})
    
    return {
        "name": f"{folder_name} Egg",
        "stage": 0,
        "version": version,
        "special": False,
        "special_key": "",
        "atk_main": 0,
        "atk_alt": 0,
        **defaults,
        "evolve": evolve
    }

def process_egg_sprites(folder_name, sprites_folder, output_folder):
    """Process egg sprites similar to vb_egg_maker."""
    sprite_dir = os.path.join(sprites_folder, 'system', 'other')
    egg_files = ['egg_00.png', 'egg_01.png', 'egg_07.png']
    output_images = []
    
    for idx, egg_file in enumerate(egg_files):
        egg_path = os.path.join(sprite_dir, egg_file)
        if not os.path.exists(egg_path):
            output_images.append(None)
            continue
            
        try:
            img = Image.open(egg_path).convert('RGBA')
            datas = img.getdata()
            newData = []
            
            # Remove green background (0,255,0)
            for item in datas:
                if item[0] == 0 and item[1] == 255 and item[2] == 0:
                    newData.append((0, 0, 0, 0))
                else:
                    newData.append(item)
            
            img.putdata(newData)
            
            # Create new 54x48 canvas
            canvas = Image.new('RGBA', (54, 48), (0, 0, 0, 0))
            
            # Center horizontally, bottom align
            x = (54 - img.width) // 2
            y = 48 - img.height
            canvas.paste(img, (x, y), img)
            
            output_images.append(canvas)
            
        except Exception as e:
            print(f"Error processing egg sprite {egg_file}: {e}")
            output_images.append(None)
    
    # Save images as 0.png, 1.png, 2.png in a zip
    safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
    zip_name = f"{safe_folder_name}_dmc.zip"
    zip_path = os.path.join(output_folder, zip_name)
    
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for idx, img in enumerate(output_images):
                if img:
                    temp_path = os.path.join(output_folder, f"temp_{safe_folder_name}_{idx}.png")
                    img.save(temp_path)
                    zipf.write(temp_path, arcname=f"{idx}.png")
                    os.remove(temp_path)
        print(f"Created egg sprite: {zip_name}")
    except Exception as e:
        print(f"Error creating egg sprite zip {zip_name}: {e}")

def process_character_sprites(char_name, char_number, sprites_folder, output_folder):
    """Process character sprites using the mapping with background removal."""
    char_sprite_dir = os.path.join(sprites_folder, 'characters', f'character_{char_number:02d}')
    
    if not os.path.exists(char_sprite_dir):
        print(f"Character sprite directory not found: {char_sprite_dir}")
        return
    
    # Clean character name for filename
    safe_char_name = re.sub(r'[<>:"/\\|?*]', '_', char_name)
    zip_name = f"{safe_char_name}_dmc.zip"
    zip_path = os.path.join(output_folder, zip_name)
    
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for zip_idx, sprite_num in CHARACTER_SPRITE_MAPPING.items():
                sprite_file = f"sprite_{sprite_num:02d}.png"
                sprite_path = os.path.join(char_sprite_dir, sprite_file)
                
                if os.path.exists(sprite_path):
                    try:
                        # Load and process the sprite (remove green background)
                        img = Image.open(sprite_path).convert('RGBA')
                        datas = img.getdata()
                        newData = []
                        
                        # Remove green background (0,255,0)
                        for item in datas:
                            if item[0] == 0 and item[1] == 255 and item[2] == 0:
                                newData.append((0, 0, 0, 0))
                            else:
                                newData.append(item)
                        
                        img.putdata(newData)
                        
                        # Save processed sprite to temp file, then add to zip
                        temp_path = os.path.join(output_folder, f"temp_{safe_char_name}_{zip_idx}.png")
                        img.save(temp_path)
                        zipf.write(temp_path, arcname=f"{zip_idx}.png")
                        os.remove(temp_path)
                        
                    except Exception as e:
                        print(f"Error processing sprite {sprite_path}: {e}")
                        # Fallback: use original file
                        zipf.write(sprite_path, arcname=f"{zip_idx}.png")
                else:
                    # Try fallback to sprite_01.png
                    fallback_sprite = f"sprite_01.png"
                    fallback_path = os.path.join(char_sprite_dir, fallback_sprite)
                    
                    if os.path.exists(fallback_path):
                        print(f"Using fallback sprite_01.png for missing {sprite_file}")
                        try:
                            # Load and process the fallback sprite
                            img = Image.open(fallback_path).convert('RGBA')
                            datas = img.getdata()
                            newData = []
                            
                            # Remove green background (0,255,0)
                            for item in datas:
                                if item[0] == 0 and item[1] == 255 and item[2] == 0:
                                    newData.append((0, 0, 0, 0))
                                else:
                                    newData.append(item)
                            
                            img.putdata(newData)
                            
                            # Save processed sprite to temp file, then add to zip
                            temp_path = os.path.join(output_folder, f"temp_{safe_char_name}_{zip_idx}.png")
                            img.save(temp_path)
                            zipf.write(temp_path, arcname=f"{zip_idx}.png")
                            os.remove(temp_path)
                            
                        except Exception as e:
                            print(f"Error processing fallback sprite {fallback_path}: {e}")
                    else:
                        print(f"Warning: Neither {sprite_file} nor fallback sprite_01.png found for character {char_number}")
        
        print(f"Created character sprite: {zip_name}")
    except Exception as e:
        print(f"Error creating character sprite zip {zip_name}: {e}")

def build_evolutions(char_data, file_idx_to_name, current_stage=3):
    """Build evolution data from character JSON."""
    evolutions = []
    
    # Attribute mapping
    attr_map = {1: 'Vi', 2: 'Da', 3: 'Va', 4: 'Free'}
    fusion_keys = ['type1', 'type2', 'type3', 'type4']
    
    # Transformations
    for t in char_data.get('transformations', []):
        tgt_idx = t.get('evolveTo')
        tgt_name = file_idx_to_name.get(tgt_idx)
        if not tgt_name:
            continue
            
        battles = t.get('battlesRequirement', 0)
        win_ratio = t.get('winRatioRequirement', 0)
        trophies = t.get('ppRequirement', 0)
        vital_values = t.get('vitalityRequirement', 0)
        
        evo = {"to": tgt_name}
        
        # Only include conditions with nonzero minimums
        if battles != 0:
            evo["battles"] = [battles, 999999]
        if win_ratio != 0:
            evo["win_ratio"] = [win_ratio, 100]
        if trophies != 0:
            evo["trophies"] = [trophies, 999999]
        if vital_values != 0:
            evo["vital_values"] = [vital_values, 999999]
            
        evolutions.append(evo)
    
    # AttributeFusions (Jogress)
    fusions = char_data.get('attributeFusions', {})
    for i, k in enumerate(fusion_keys):
        tgt_idx = fusions.get(k)
        if tgt_idx is None or tgt_idx == 0:
            continue
            
        tgt_name = file_idx_to_name.get(tgt_idx)
        if not tgt_name:
            continue
            
        evo = {
            "to": tgt_name,
            "stage": current_stage,
            "attribute": attr_map.get(i+1),
            "jogress": "PenC"
        }
        evolutions.append(evo)
    
    return evolutions

def create_monster_from_character(char_data, char_number, char_name, version, file_idx_to_name):
    """Create monster entry from character JSON data."""
    # Extract basic stats
    hp = extract_int(char_data, ['hp', 'HP'])
    star = extract_int(char_data, ['stars', 'star', 'Stars'])
    power = extract_int(char_data, ['bp', 'BP', 'power'])
    attribute_num = extract_int(char_data, ['attribute', 'Attribute'])
    
    # Convert attacks
    raw_small = extract_int(char_data, ['smallAttack', 'small_attack', 'smallAtk', 'small'])
    raw_big = extract_int(char_data, ['bigAttack', 'big_attack', 'bigAtk', 'big'])
    ap = extract_int(char_data, ['ap', 'AP', 'attack'])
    
    # Normalize values
    hp = normalize_value(hp) if hp is not None else 0
    star = normalize_value(star) if star is not None else 0
    power = normalize_value(power) if power is not None else 0
    atk_main = convert_small_attack(raw_small) if raw_small is not None else 0
    atk_alt = convert_big_attack(raw_big) if raw_big is not None else 0
    attack = normalize_value(ap) if ap is not None else 0
    
    # Determine stage based on stats (rough estimation)
    if hp == 0 and power == 0:
        stage = 1  # Baby/Fresh
    elif hp <= 10:
        stage = 2  # In-Training
    elif hp <= 15:
        stage = 3  # Rookie
    elif hp <= 20:
        stage = 4  # Champion
    elif hp <= 25:
        stage = 5  # Ultimate
    else:
        stage = 6  # Mega
    
    # Get defaults for the stage
    defaults = DEFAULT_VALUES_BY_STAGE.get(stage, DEFAULT_VALUES_BY_STAGE[3])
    
    # Build evolutions
    evolutions = build_evolutions(char_data, file_idx_to_name, stage)
    
    monster = {
        "name": char_name,
        "stage": stage,
        "version": version,
        "special": False,
        "special_key": "",
        "atk_main": atk_main,
        "atk_alt": atk_alt,
        "hp": hp,
        "star": star,
        "power": power,
        "attack": attack,
        "attribute": get_attribute_string(attribute_num),
        "evolve": evolutions,
        **{k: v for k, v in defaults.items() if k not in ['hp', 'star', 'attack']}
    }
    
    return monster

def process_folder(folder_path, version, output_sprites_folder, folder_character_names):
    """Process a single folder using pre-extracted character names."""
    folder_name = os.path.basename(folder_path)
    data_folder = os.path.join(folder_path, 'data')
    sprites_folder = os.path.join(folder_path, 'sprites')
    
    print(f"Processing folder: {folder_name} (Version {version})")
    
    monsters = []
    
    # Resolve duplicate names first
    name_mapping, changes_made = resolve_duplicate_names(folder_character_names)
    
    # Find first stage name for egg evolution
    first_stage_name = None
    for char_name_data in folder_character_names:
        if char_name_data['character_number'] == 0:
            first_stage_name = name_mapping.get(f"{folder_name}_{0}")
            break
    
    # 2.1 Create egg monster with evolution to first stage
    egg_monster = create_egg_monster(folder_name, version, first_stage_name)
    monsters.append(egg_monster)
    
    # 2.2 Create egg sprite
    process_egg_sprites(f"{folder_name} Egg", sprites_folder, output_sprites_folder)
    
    # 2.3 Process character files
    if not os.path.exists(data_folder):
        print(f"Data folder not found: {data_folder}")
        return monsters, changes_made
    
    char_files = find_character_files(data_folder)
    file_idx_to_name = {}
    
    # Build mapping from resolved character names
    for char_name_data in folder_character_names:
        char_number = char_name_data['character_number']
        final_name = name_mapping.get(f"{folder_name}_{char_number}")
        
        if not final_name:
            print(f"⚠️  Warning: No final name for character {char_number:02d} in {folder_name}, skipping")
            continue
        
        # Clean the name for file system compatibility (preserve Japanese characters)
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', final_name)
        clean_name = clean_name.strip()
        
        if not clean_name:
            print(f"⚠️  Warning: Empty name after cleaning for character {char_number:02d}, using fallback")
            clean_name = f"Character_{char_number:02d}"
        
        file_idx_to_name[char_number] = clean_name
    
    # Process character files with pre-extracted names
    for char_file in char_files:
        match = re.search(r'character_(\d+)\.json$', char_file)
        if not match:
            continue
            
        char_number = int(match.group(1))
        char_data = load_json(char_file)
        
        if char_data is None:
            continue
        
        char_name = file_idx_to_name.get(char_number)
        if not char_name:
            print(f"⚠️  Warning: No name found for character {char_number:02d} in {folder_name}, skipping")
            continue
        
        # Create monster entry
        monster = create_monster_from_character(char_data, char_number, char_name, version, file_idx_to_name)
        monsters.append(monster)
        
        # Create character sprite
        process_character_sprites(char_name, char_number, sprites_folder, output_sprites_folder)
    
    return monsters, changes_made

def main():
    """Main function to build sprites and monster.json using pre-extracted character names."""
    print("VB Sprite Builder - Part 2 of 2")
    print("=" * 50)
    
    # Get script directory for input/output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_names_path = os.path.join(script_dir, INPUT_NAMES_JSON)
    output_json_path = os.path.join(script_dir, OUTPUT_MONSTER_JSON)
    output_sprites_folder = os.path.join(script_dir, OUTPUT_SPRITES_FOLDER)
    
    # Check if character names JSON exists
    if not os.path.exists(input_names_path):
        print(f"❌ Character names JSON not found: {input_names_path}")
        print(f"Please run vb_ocr_extractor.py first to extract character names.")
        return 1
    
    # Load character names data
    names_data = load_json(input_names_path)
    if not names_data:
        print(f"❌ Failed to load character names from {input_names_path}")
        return 1
    
    if not os.path.exists(ROOT_FOLDER):
        print(f"❌ Root folder not found: {ROOT_FOLDER}")
        return 1
    
    print(f"📁 Source: {ROOT_FOLDER}")
    print(f"📄 Input Names JSON: {input_names_path}")
    print(f"📄 Output JSON: {output_json_path}")
    print(f"🎨 Output Sprites: {output_sprites_folder}")
    print()
    
    # Show extraction summary
    extraction_info = names_data.get('extraction_info', {})
    print(f"📊 Character Names Summary:")
    print(f"   • Total folders: {extraction_info.get('total_folders', 'Unknown')}")
    print(f"   • Total characters: {extraction_info.get('total_characters', 'Unknown')}")
    print(f"   • Success rate: {extraction_info.get('success_rate', 'Unknown')}")
    print()
    
    # Group character data by folder
    characters_by_folder = {}
    for char_data in names_data.get('characters', []):
        folder_name = char_data['folder_name']
        if folder_name not in characters_by_folder:
            characters_by_folder[folder_name] = []
        characters_by_folder[folder_name].append(char_data)
    
    all_monsters = []
    all_name_changes = []
    version = 1
    processed_folders = 0
    
    try:
        # Get folder order from character_names.json to preserve custom ordering
        folder_order = []
        seen_folders = set()
        for char_data in names_data.get('characters', []):
            folder_name = char_data['folder_name']
            if folder_name not in seen_folders:
                folder_order.append(folder_name)
                seen_folders.add(folder_name)
        
        # Verify these folders exist in the file system
        all_folders = [f for f in os.listdir(ROOT_FOLDER) if os.path.isdir(os.path.join(ROOT_FOLDER, f))]
        folders = [f for f in folder_order if f in all_folders]
        
        if not folders:
            print("❌ No matching subfolders found in ROOT_FOLDER")
            return 1
        
        print(f"📁 Processing folders in character_names.json order:")
        for i, folder in enumerate(folders, 1):
            print(f"   {i:2d}. {folder}")
        print()
        
        for folder in folders:
            if folder not in characters_by_folder:
                print(f"⚠️  Warning: No character names found for folder {folder}, skipping")
                continue
            
            try:
                folder_path = os.path.join(ROOT_FOLDER, folder)
                folder_character_names = characters_by_folder[folder]
                
                monsters, changes_made = process_folder(folder_path, version, output_sprites_folder, folder_character_names)
                all_monsters.extend(monsters)
                all_name_changes.extend(changes_made)
                processed_folders += 1
                print(f"✅ {folder}: Created {len(monsters)} entries")
                version += 1
                
            except Exception as e:
                print(f"❌ Error processing {folder}: {e}")
                continue
        
        if not all_monsters:
            print("❌ No monsters were created.")
            return 1
        
        # Create final monster.json
        monster_data = {"monster": all_monsters}
        
        try:
            save_json(output_json_path, monster_data)
            print(f"\n✅ Processing complete!")
            print(f"📊 Summary:")
            print(f"   • Processed folders: {processed_folders}/{len(folders)}")
            print(f"   • Total monsters: {len(all_monsters)}")
            print(f"   • Monster data: {output_json_path}")
            print(f"   • Sprites folder: {output_sprites_folder}")
            
            # Show breakdown by version
            version_counts = {}
            for monster in all_monsters:
                v = monster.get('version', 1)
                version_counts[v] = version_counts.get(v, 0) + 1
            
            print(f"\n📈 Breakdown by version:")
            for v in sorted(version_counts.keys()):
                print(f"   Version {v}: {version_counts[v]} monsters")
            
            # Report name changes
            if all_name_changes:
                print(f"\n🔄 Name Changes Made:")
                print(f"   Total changes: {len(all_name_changes)}")
                for change in all_name_changes:
                    print(f"   • {change['folder']} #{change['character_number']:02d}: '{change['original_name']}' → '{change['final_name']}'")
            else:
                print(f"\n✅ No duplicate names found - no changes needed")
            
            # Find remaining duplicates
            remaining_duplicates = find_remaining_duplicates(all_monsters)
            if remaining_duplicates:
                print(f"\n⚠️  Remaining Duplicate Names:")
                print(f"   Found {len(remaining_duplicates)} sets of duplicate names:")
                for dup in remaining_duplicates:
                    print(f"   • '{dup['name']}' appears {dup['count']} times:")
                    for entry in dup['entries']:
                        print(f"     - Version {entry['version']}, Stage {entry['stage']}")
            else:
                print(f"\n✅ No remaining duplicate names found")
            
            # Find orphaned monsters
            orphaned_monsters = find_orphaned_monsters(all_monsters)
            if orphaned_monsters:
                print(f"\n🔗 Orphaned Monsters (No Evolutions In or Out):")
                print(f"   Found {len(orphaned_monsters)} orphaned monsters:")
                
                # Group by version for better readability
                orphaned_by_version = {}
                for orphan in orphaned_monsters:
                    version = orphan['version']
                    if version not in orphaned_by_version:
                        orphaned_by_version[version] = []
                    orphaned_by_version[version].append(orphan)
                
                for version in sorted(orphaned_by_version.keys()):
                    print(f"   📦 Version {version}:")
                    for orphan in orphaned_by_version[version]:
                        print(f"     - '{orphan['name']}' (Stage {orphan['stage']})")
            else:
                print(f"\n✅ No orphaned monsters found - all monsters are connected to evolution chains")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error saving monster.json: {e}")
            return 1
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())