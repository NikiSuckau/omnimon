#!/usr/bin/env python3
"""
Character Names Reorderer
Reorders the character_names.json file according to the specified folder order.
"""

import json
import re

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

def analyze_folders(characters):
    """Analyze all unique folder names in the data."""
    folders = set()
    for char in characters:
        folders.add(char['folder_name'])
    return sorted(folders)

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'character_names.json')
    
    # Load the data
    data = load_json(input_file)
    if not data:
        return 1
    
    characters = data.get('characters', [])
    
    # Analyze current folders
    print("Current folders found:")
    folders = analyze_folders(characters)
    for i, folder in enumerate(folders, 1):
        print(f"{i:2d}. {folder}")
    
    print(f"\nTotal folders: {len(folders)}")
    print(f"Total characters: {len(characters)}")
    
    # Define the desired order
    desired_order = [
        # DC Series
        "Batman",
        "DC Heroes", 
        "DC Villains",
        
        # Kamen Rider Series (using actual folder names)
        "Vol 00 - Masked Rider Kuuga",
        "Vol 00 - Showa 10 Masked Rider", 
        "Vol 01 - Kamen Rider Zero One",
        "Vol 01 - Kamen Rider Horobi",
        "Vol 02 - Kamen Rider Ex-Aid",
        "Vol 02 - Kamen Rider Genm",
        "Vol 03 - Kamen Rider Build",
        "Vol 03 - Kamen Rider Rogue",
        "Vol 04 - Kamen Rider 000",
        "Vol 04 - Greeed"
    ]
    
    # Find which folders exist and which don't match exactly
    existing_folders = set(folders)
    matched_folders = []
    missing_folders = []
    
    for folder in desired_order:
        if folder in existing_folders:
            matched_folders.append(folder)
        else:
            missing_folders.append(folder)
    
    # Find folders that are in the data but not in our desired order
    remaining_folders = []
    for folder in folders:
        if folder not in desired_order:
            remaining_folders.append(folder)
    
    print(f"\n✅ Matched folders ({len(matched_folders)}):")
    for folder in matched_folders:
        print(f"   • {folder}")
    
    if missing_folders:
        print(f"\n❌ Missing folders ({len(missing_folders)}):")
        for folder in missing_folders:
            print(f"   • {folder}")
            # Try to find similar names
            for existing in existing_folders:
                if any(word in existing.lower() for word in folder.lower().split()):
                    print(f"     → Similar: {existing}")
    
    if remaining_folders:
        print(f"\n🔍 Remaining folders ({len(remaining_folders)}):")
        for folder in remaining_folders:
            print(f"   • {folder}")
    
    # Create the final order
    final_order = matched_folders + sorted(remaining_folders)
    
    print(f"\n📋 Final order ({len(final_order)}):")
    for i, folder in enumerate(final_order, 1):
        print(f"{i:2d}. {folder}")
    
    # Group characters by folder
    characters_by_folder = {}
    for char in characters:
        folder = char['folder_name']
        if folder not in characters_by_folder:
            characters_by_folder[folder] = []
        characters_by_folder[folder].append(char)
    
    # Sort characters within each folder by character_number
    for folder in characters_by_folder:
        characters_by_folder[folder].sort(key=lambda x: x['character_number'])
    
    # Reorder characters according to final_order
    reordered_characters = []
    for folder in final_order:
        if folder in characters_by_folder:
            reordered_characters.extend(characters_by_folder[folder])
    
    # Update the data
    data['characters'] = reordered_characters
    
    # Save the reordered file
    output_file = os.path.join(script_dir, 'character_names_reordered.json')
    save_json(output_file, data)
    
    print(f"\n✅ Reordered file saved as: {output_file}")
    print(f"   • Total characters: {len(reordered_characters)}")
    
    # Show breakdown by folder
    print(f"\n📊 Character count by folder:")
    for folder in final_order:
        if folder in characters_by_folder:
            count = len(characters_by_folder[folder])
            print(f"   • {folder}: {count} characters")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())