#!/usr/bin/env python3
"""
Monster Stage Fixer
Fixes incorrect stage assignments and template data in monster.json by reading the correct
stage from source character JSON files and applying appropriate template values.
"""

import os
import json
import re
from glob import glob

# Configuration
ROOT_FOLDER = r'D:\Digimon\DIMS\Sprites2'
INPUT_NAMES_JSON = 'character_names.json'
INPUT_MONSTER_JSON = 'monster.json'
OUTPUT_MONSTER_JSON = 'monster_fixed.json'

# Template values by stage (from PetTemplates.cs)
STAGE_TEMPLATES = {
    0: {
        "time": 1, "poop_timer": 0, "energy": 0, "min_weight": 99, "evol_weight": 0,
        "stomach": 0, "hunger_loss": 0, "strength_loss": 0, "heal_doses": 1,
        "condition_hearts": 0, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": None, "wakes": None
    },
    1: {
        "time": 10, "poop_timer": 3, "energy": 0, "min_weight": 5, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 3, "strength_loss": 3, "heal_doses": 1,
        "condition_hearts": 1, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    2: {
        "time": 720, "poop_timer": 60, "energy": 0, "min_weight": 10, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 30, "strength_loss": 30, "heal_doses": 1,
        "condition_hearts": 2, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    3: {
        "time": 1440, "poop_timer": 120, "energy": 20, "min_weight": 20, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 48, "strength_loss": 48, "heal_doses": 1,
        "condition_hearts": 3, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    4: {
        "time": 2160, "poop_timer": 120, "energy": 30, "min_weight": 30, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    5: {
        "time": 2400, "poop_timer": 120, "energy": 40, "min_weight": 40, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": True, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    6: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    },
    7: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "critical_turn": 0,
        "sleeps": "21:00", "wakes": "09:00"
    }
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

def find_character_files(data_folder):
    """Find all character_*.json files in the data folder."""
    pattern = os.path.join(data_folder, 'character_*.json')
    files = glob(pattern)
    # Sort by the numeric suffix
    def keyfn(p):
        m = re.search(r'character_(\d+)\.json$', p)
        return int(m.group(1)) if m else 999
    return sorted(files, key=keyfn)

def get_character_stage_from_source(folder_name, character_number):
    """Get the correct stage from the source character JSON file."""
    folder_path = os.path.join(ROOT_FOLDER, folder_name)
    data_folder = os.path.join(folder_path, 'data')
    
    if not os.path.exists(data_folder):
        print(f"⚠️  Warning: Data folder not found for {folder_name}")
        return None
    
    char_file = os.path.join(data_folder, f'character_{character_number:02d}.json')
    if not os.path.exists(char_file):
        print(f"⚠️  Warning: Character file not found: {char_file}")
        return None
    
    char_data = load_json(char_file)
    if not char_data:
        return None
    
    # Get stage from source and add 1 (as per your requirement)
    source_stage = char_data.get('stage', 0)
    corrected_stage = source_stage + 1
    
    print(f"📊 {folder_name} char_{character_number:02d}: source stage {source_stage} → corrected stage {corrected_stage}")
    
    return corrected_stage

def build_character_lookup(characters_data):
    """Build a lookup table from character names to their folder/character info."""
    lookup = {}
    
    for char_info in characters_data:
        char_name = char_info.get('character_name')
        if char_name:
            # Handle potential duplicates by using a list
            if char_name not in lookup:
                lookup[char_name] = []
            lookup[char_name].append({
                'folder_name': char_info['folder_name'],
                'character_number': char_info['character_number']
            })
    
    return lookup

def fix_monster_entry(monster, char_lookup):
    """Fix a single monster entry by correcting stage and applying template."""
    monster_name = monster.get('name', '')
    current_stage = monster.get('stage', 0)
    
    # Skip stage 0 monsters (eggs and starters)
    if current_stage == 0:
        print(f"⏭️  Skipping stage 0 monster: {monster_name}")
        return monster, False
    
    # Skip egg monsters (additional safety check)
    if monster_name.endswith(' Egg'):
        print(f"⏭️  Skipping egg monster: {monster_name}")
        return monster, False
    
    # Fix underscore naming format (e.g., "Ravmon_ Burst Mode" -> "Ravmon: Burst Mode")
    search_name = monster_name
    if '_' in monster_name and ' ' in monster_name:
        # Check if it's a format like "Name_ Something Mode"
        parts = monster_name.split('_', 1)
        if len(parts) == 2 and parts[1].strip():
            search_name = f"{parts[0].strip()}: {parts[1].strip()}"
            print(f"🔄 Converted name format: '{monster_name}' → '{search_name}'")
    
    # Find character info
    if search_name not in char_lookup:
        print(f"⚠️  Warning: No character info found for monster: {monster_name} (searched as: {search_name})")
        return monster, False
    
    char_options = char_lookup[search_name]
    
    # If multiple options, we need to pick the right one based on version
    # For now, use the first one (this could be improved with version matching)
    char_info = char_options[0]
    if len(char_options) > 1:
        print(f"⚠️  Multiple character options for {search_name}, using first: {char_info}")
    
    # Get correct stage from source
    correct_stage = get_character_stage_from_source(
        char_info['folder_name'], 
        char_info['character_number']
    )
    
    if correct_stage is None:
        print(f"❌ Could not determine correct stage for {monster_name}")
        return monster, False
    
    # Update stage
    old_stage = monster.get('stage', 0)
    monster['stage'] = correct_stage
    
    # Apply template values for the correct stage
    if correct_stage in STAGE_TEMPLATES:
        template = STAGE_TEMPLATES[correct_stage]
        
        # Only update fields that should come from template (not from source data)
        template_fields = [
            'time', 'poop_timer', 'energy', 'min_weight', 'evol_weight',
            'stomach', 'hunger_loss', 'strength_loss', 'heal_doses',
            'condition_hearts', 'jogress_avaliable', 'critical_turn',
            'sleeps', 'wakes'
        ]
        
        updated_fields = []
        for field in template_fields:
            if field in template:
                old_value = monster.get(field)
                new_value = template[field]
                if old_value != new_value:
                    monster[field] = new_value
                    updated_fields.append(f"{field}: {old_value} → {new_value}")
        
        print(f"✅ Fixed {monster_name}: stage {old_stage} → {correct_stage}")
        if updated_fields:
            print(f"   Updated template fields: {', '.join(updated_fields)}")
        
        return monster, True
    else:
        print(f"❌ No template found for stage {correct_stage}")
        return monster, False

def main():
    """Main function to fix monster stages and template data."""
    print("Monster Stage Fixer")
    print("=" * 50)
    
    # Get script directory for input/output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    names_path = os.path.join(script_dir, INPUT_NAMES_JSON)
    monster_path = os.path.join(script_dir, INPUT_MONSTER_JSON)
    output_path = os.path.join(script_dir, OUTPUT_MONSTER_JSON)
    
    # Check if files exist
    if not os.path.exists(names_path):
        print(f"❌ Character names file not found: {names_path}")
        return 1
    
    if not os.path.exists(monster_path):
        print(f"❌ Monster JSON file not found: {monster_path}")
        return 1
    
    if not os.path.exists(ROOT_FOLDER):
        print(f"❌ Root folder not found: {ROOT_FOLDER}")
        return 1
    
    print(f"📁 Source data: {ROOT_FOLDER}")
    print(f"📄 Character names: {names_path}")
    print(f"📄 Input monster JSON: {monster_path}")
    print(f"📄 Output monster JSON: {output_path}")
    print()
    
    # Load data
    print("📥 Loading data files...")
    names_data = load_json(names_path)
    monster_data = load_json(monster_path)
    
    if not names_data:
        print("❌ Failed to load character names data")
        return 1
    
    if not monster_data:
        print("❌ Failed to load monster data")
        return 1
    
    if 'characters' not in names_data:
        print("❌ No 'characters' key found in names data")
        return 1
    
    if 'monster' not in monster_data:
        print("❌ No 'monster' key found in monster data")
        return 1
    
    print(f"📊 Found {len(names_data['characters'])} character entries")
    print(f"📊 Found {len(monster_data['monster'])} monster entries")
    print()
    
    # Build character lookup
    print("🔍 Building character lookup table...")
    char_lookup = build_character_lookup(names_data['characters'])
    print(f"📊 Built lookup for {len(char_lookup)} unique character names")
    print()
    
    # Process monsters
    print("🔧 Processing monster entries...")
    monsters = monster_data['monster']
    fixed_count = 0
    skipped_count = 0
    stage0_skipped = 0
    error_count = 0
    
    for i, monster in enumerate(monsters):
        try:
            # Track stage 0 skips separately
            current_stage = monster.get('stage', 0)
            
            updated_monster, was_fixed = fix_monster_entry(monster, char_lookup)
            monsters[i] = updated_monster
            
            if was_fixed:
                fixed_count += 1
            else:
                skipped_count += 1
                if current_stage == 0:
                    stage0_skipped += 1
                
        except Exception as e:
            print(f"❌ Error processing monster {i}: {e}")
            error_count += 1
    
    print()
    print("📊 Processing Summary:")
    print(f"   • Fixed monsters: {fixed_count}")
    print(f"   • Skipped monsters: {skipped_count}")
    print(f"     - Stage 0 (eggs/starters): {stage0_skipped}")
    print(f"     - Other (missing data/variants): {skipped_count - stage0_skipped}")
    print(f"   • Errors: {error_count}")
    print(f"   • Total processed: {len(monsters)}")
    
    # Save fixed data
    if fixed_count > 0:
        print(f"\n💾 Saving fixed monster data to: {output_path}")
        try:
            save_json(output_path, monster_data)
            print("✅ Successfully saved fixed monster data!")
            
            # Show stage distribution
            stage_counts = {}
            for monster in monsters:
                stage = monster.get('stage', 0)
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
            print(f"\n📈 Stage distribution after fixes:")
            for stage in sorted(stage_counts.keys()):
                print(f"   Stage {stage}: {stage_counts[stage]} monsters")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error saving fixed data: {e}")
            return 1
    else:
        print("\n⚠️  No monsters were fixed, not saving output file")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())