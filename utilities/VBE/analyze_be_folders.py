#!/usr/bin/env python3
"""
Analyze BE Folder Translation Status
===================================
Analyzes the translation status of all BE memory folders in the mapping.
"""

import json

def analyze_be_folders():
    """Analyze translation status for all mapped BE folders."""
    
    # Load character data from the translated output
    try:
        with open(r'e:\Omnimon\utilities\VBE\character_names_be_translated.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Using translated output file")
    except FileNotFoundError:
        with open(r'e:\Omnimon\utilities\VBE\character_names.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Using original file (no translations found)")
    
    # Define the folder mappings from be_translator.py
    mapped_folders = [
        "Ghost Game - Angoramon BE",
        "Ghost Game - Gammamon BE", 
        "Ghost Game - Jellymon BE",
        "Loogamon BE",
        "Ryudamon BE", 
        "Dorumon BE",
        "Pulsemon BE",
        "Imperialdramon BE",
        "rampage of the beast",
        "Forest Guardian",
        "draconic blaze",
        "Holy Wings",
        "25th Anniversary BEM"
    ]
    
    print("BE Memory Folder Translation Analysis")
    print("=" * 60)
    
    total_chars = 0
    total_translated = 0
    
    for folder_name in mapped_folders:
        # Find all characters in this folder
        folder_chars = [c for c in data['characters'] if c.get('folder_name') == folder_name]
        
        if not folder_chars:
            print(f"❌ {folder_name}: FOLDER NOT FOUND")
            continue
            
        # Count translated characters
        translated_chars = [c for c in folder_chars if c.get('status') == 'translated']
        
        total_chars += len(folder_chars)
        total_translated += len(translated_chars)
        
        # Calculate percentage
        if len(folder_chars) > 0:
            percentage = (len(translated_chars) / len(folder_chars)) * 100
        else:
            percentage = 0
            
        # Show status
        if len(translated_chars) == len(folder_chars):
            status = "✅ COMPLETE"
        elif len(translated_chars) > 0:
            status = "🔄 PARTIAL"
        else:
            status = "❌ NONE"
            
        print(f"{status} {folder_name}: {len(translated_chars)}/{len(folder_chars)} ({percentage:.1f}%)")
        
        # Show some example untranslated characters
        if len(translated_chars) < len(folder_chars):
            untranslated = [c for c in folder_chars if c.get('status') != 'translated'][:3]
            print(f"      Examples needing translation:")
            for char in untranslated:
                char_name = char.get('character_name', char.get('extracted_name', 'Unknown'))
                print(f"        #{char['character_number']}: {char_name}")
    
    print("\n" + "=" * 60)
    print(f"OVERALL STATUS: {total_translated}/{total_chars} characters translated ({(total_translated/total_chars)*100:.1f}%)")
    
    return mapped_folders, total_chars, total_translated

if __name__ == "__main__":
    analyze_be_folders()