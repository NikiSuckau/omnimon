#!/usr/bin/env python3
"""
Character Names Correction Script
Fixes incorrect character names in monster.json, battle.json, and renames corresponding ZIP files.
"""

import os
import json
import shutil
from pathlib import Path

# Configuration
MONSTER_JSON_PATH = r'e:\Omnimon\modules\VBE\monster.json'
BATTLE_JSON_PATH = r'e:\Omnimon\modules\VBE\battle.json'
MONSTERS_HIDEF_PATH = r'e:\Omnimon\assets\monsters_hidef'

# Name corrections mapping (wrong name -> correct name)
NAME_CORRECTIONS = {
    "Cerberumon": "Cerberusmon",
    "Fenrilogarmon: Takemikazuchi": "Fenriloogamon: Takemikazuchi",
    "Fenrilogarmon": "Fenriloogamon",
    "Fladramon": "Flamedramon",
    "GrappuLeomon": "GrapLeomon",
    "Hackmon": "Huckmon",
    "HerakleKabuterimon": "HerculesKabuterimon",
    "Holsmon": "Halsemon",
    "HolyAngemon": "MagnaAngemon",
    "Holydramon": "Magnadramon",
    "Hououmon": "Phoenixmon",
    "KaratukiNumemon": "ShellNumemon",
    "MarinChimairamon": "MarineChimairamon",
    "Mochimon": "Motimon",
    "Mugendramon": "Machinedramon",
    "Omega Shoutmon": "OmniShoutmon",
    "Oukuwamon": "Okuwamon",
    "Pegasmon": "Pegasusmon",
    "Petimon": "Petitmon",
    "Pidmon": "Piddomon",
    "Pyocomon": "Yokomon",
    "Ragnamon": "Galacticmon",
    "Ravmon: Burst Mode": "Ravemon: Burst Mode",
    "Ravmon": "Ravemon",
    "SaviorHackmon": "SaviorHuckmon",
    "Stiffilmon": "Stefilmon",
    "Tailmon (Child)": "Gatomon (Child)",
    "Tailmon": "Gatomon",
    "Tesla Jellymon": "TeslaJellymon",
    "Thunderballmon": "Thundermon",
    "Thunderbirmon": "Thunderbirdmon",
    "Tyilinmon": "Chirinmon",
    "Yatagaramon (2006)": "Crowmon (2006)",
    "Anomalocarimon X": "Scorpiomon X",
    "Arachnemon": "Arukenimon",
    "Armadimon": "Armadillomon",
    "Armagemon": "Armageddemon",
    "Atlurkabuterimon (Red)": "MegaKabuterimon (Red)",
    "Babydmon": "Bebydomon",
    "BanchouLilimon": "BanchoLillymon",
    "BaoHackmon": "BaoHuckmon",
    "BelialMyotismon": "MaloMyotismon"
}

def fix_json_file(file_path, file_type):
    """Fix character names in a JSON file."""
    print(f"\n🔧 Processing {file_type}: {file_path}")
    
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track replacements
        replacements_made = {}
        original_content = content
        
        # Replace all incorrect names with correct ones
        for wrong_name, correct_name in NAME_CORRECTIONS.items():
            if wrong_name in content:
                content = content.replace(f'"{wrong_name}"', f'"{correct_name}"')
                count = original_content.count(f'"{wrong_name}"')
                if count > 0:
                    replacements_made[wrong_name] = {
                        'correct_name': correct_name,
                        'count': count
                    }
        
        # Write back the corrected content
        if replacements_made:
            # Create backup
            backup_path = file_path + '.backup'
            shutil.copy2(file_path, backup_path)
            print(f"📋 Backup created: {backup_path}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {file_type} updated successfully!")
            print(f"📊 Replacements made:")
            for wrong, info in replacements_made.items():
                print(f"   • {wrong} → {info['correct_name']} ({info['count']} instances)")
        else:
            print(f"ℹ️  No character name corrections needed in {file_type}")
            
        return replacements_made
        
    except Exception as e:
        print(f"❌ Error processing {file_type}: {e}")
        return {}

def name_to_filename(name):
    """Convert character name to expected filename format."""
    # Replace colons with underscores and add _dmc.zip suffix
    filename = name.replace(":", "_") + "_dmc.zip"
    return filename

def fix_zip_files():
    """Fix ZIP file names in the monsters_hidef folder."""
    print(f"\n🗂️  Processing ZIP files in: {MONSTERS_HIDEF_PATH}")
    
    if not os.path.exists(MONSTERS_HIDEF_PATH):
        print(f"❌ Monsters folder not found: {MONSTERS_HIDEF_PATH}")
        return
    
    monsters_folder = Path(MONSTERS_HIDEF_PATH)
    
    # Track operations
    renamed_files = []
    deleted_files = []
    conflicts_resolved = []
    
    for wrong_name, correct_name in NAME_CORRECTIONS.items():
        wrong_filename = name_to_filename(wrong_name)
        correct_filename = name_to_filename(correct_name)
        
        wrong_file_path = monsters_folder / wrong_filename
        correct_file_path = monsters_folder / correct_filename
        
        if wrong_file_path.exists():
            if correct_file_path.exists():
                # Both files exist - delete the wrong one, keep the correct one
                try:
                    wrong_file_path.unlink()
                    deleted_files.append(wrong_filename)
                    conflicts_resolved.append({
                        'wrong': wrong_filename,
                        'correct': correct_filename,
                        'action': 'deleted_wrong'
                    })
                    print(f"🗑️  Deleted (conflict): {wrong_filename} (kept {correct_filename})")
                except Exception as e:
                    print(f"❌ Error deleting {wrong_filename}: {e}")
            else:
                # Only wrong file exists - rename it to correct name
                try:
                    wrong_file_path.rename(correct_file_path)
                    renamed_files.append({
                        'old': wrong_filename,
                        'new': correct_filename
                    })
                    print(f"📝 Renamed: {wrong_filename} → {correct_filename}")
                except Exception as e:
                    print(f"❌ Error renaming {wrong_filename}: {e}")
    
    # Summary
    print(f"\n📊 ZIP Files Summary:")
    print(f"   • Files renamed: {len(renamed_files)}")
    print(f"   • Files deleted (conflicts): {len(deleted_files)}")
    print(f"   • Conflicts resolved: {len(conflicts_resolved)}")
    
    return {
        'renamed': renamed_files,
        'deleted': deleted_files,
        'conflicts': conflicts_resolved
    }

def save_corrections_report(json_results, zip_results):
    """Save a detailed report of all corrections made."""
    report_file = "character_names_corrections_report.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Character Names Corrections Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total corrections defined: {len(NAME_CORRECTIONS)}\n\n")
            
            # JSON corrections
            f.write("JSON FILE CORRECTIONS:\n")
            f.write("-" * 30 + "\n")
            
            for file_type, results in json_results.items():
                f.write(f"\n{file_type.upper()}:\n")
                if results:
                    for wrong, info in results.items():
                        f.write(f"  {wrong} → {info['correct_name']} ({info['count']} instances)\n")
                else:
                    f.write("  No corrections needed\n")
            
            # ZIP file corrections
            f.write(f"\nZIP FILE CORRECTIONS:\n")
            f.write("-" * 30 + "\n")
            
            if zip_results['renamed']:
                f.write("RENAMED FILES:\n")
                for item in zip_results['renamed']:
                    f.write(f"  {item['old']} → {item['new']}\n")
                f.write("\n")
            
            if zip_results['deleted']:
                f.write("DELETED FILES (conflicts resolved):\n")
                for filename in zip_results['deleted']:
                    f.write(f"  {filename}\n")
                f.write("\n")
            
            if zip_results['conflicts']:
                f.write("CONFLICT RESOLUTIONS:\n")
                for conflict in zip_results['conflicts']:
                    f.write(f"  Kept: {conflict['correct']}, Deleted: {conflict['wrong']}\n")
            
            # All corrections mapping
            f.write(f"\nCOMPLETE CORRECTIONS MAPPING:\n")
            f.write("-" * 30 + "\n")
            for wrong, correct in NAME_CORRECTIONS.items():
                f.write(f"{wrong} → {correct}\n")
        
        print(f"💾 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error saving report: {e}")

def main():
    """Main function to execute all character name corrections."""
    print("Character Names Correction Process")
    print("=" * 50)
    print(f"📊 Total corrections to apply: {len(NAME_CORRECTIONS)}")
    
    # Fix JSON files
    json_results = {}
    json_results['monster.json'] = fix_json_file(MONSTER_JSON_PATH, "monster.json")
    json_results['battle.json'] = fix_json_file(BATTLE_JSON_PATH, "battle.json")
    
    # Fix ZIP files
    zip_results = fix_zip_files()
    
    # Generate report
    save_corrections_report(json_results, zip_results)
    
    print(f"\n✅ Character name correction process completed!")
    print(f"📋 Check the detailed report for all changes made.")

if __name__ == "__main__":
    main()