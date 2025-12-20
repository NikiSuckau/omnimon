#!/usr/bin/env python3
"""
VB BE Memory Name Translator
============================
Parses the VB BE HTML sheet to extract English character names
and updates the character names JSON file with proper translations.

Usage: python be_translator.py
"""

import json
import re
from bs4 import BeautifulSoup

def parse_be_html(html_file):
    """Parse the VB BE HTML sheet to extract character names."""
    print("📖 Parsing VB BE HTML sheet...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    be_names = {}

    # Helper to decide if a cell text looks like an English Digimon name
    def is_likely_english_name(text: str) -> bool:
        if not text:
            return False
        t = text.strip()
        if len(t) < 2 or len(t) > 60:
            return False
        u = t.upper()
        # Exclude obvious non-name labels and noise
        bad_tokens = {
            'NORMAL', 'ACTIVE', 'STOIC', 'LAZY', 'INDOOR', 'FRESH', 'ROOKIE', 'CHAMPION',
            'ULTIMATE', 'MEGA', 'NA', 'VACCINE', 'DATA', 'VIRUS', 'FREE', 'NA ', 'NA\t'
        }
        if any(bt in u for bt in bad_tokens):
            return False
        if 'BE ' in u or u.startswith('BE:'):
            return False
        # Exclude time-like cells such as "24 h", "12h", "3 h"
        if re.match(r'^\d+\s*h$', t, flags=re.IGNORECASE) or re.match(r'^\d+h$', t, flags=re.IGNORECASE):
            return False
        # Skip cells that are just numbers, percentages or arrows
        simple = t.replace(' ', '').replace('↑', '').replace('%', '').replace(':', '')
        if simple.isdigit():
            return False
        # Exclude D-codes
        if re.match(r'^D\d+_\d+$', u):
            return False
        # Must contain at least one ASCII letter
        if not re.search(r'[A-Za-z]', t):
            return False
        return True

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 5:
            continue
        
        # Look for rows with the expected pattern
        dim_name = None
        index_code = None
        japanese_name = None
        english_name = None

        for i, cell in enumerate(cells):
            # Get text, checking both direct text and softmerge-inner divs
            text = cell.get_text(strip=True)
            softmerge_div = cell.find('div', class_='softmerge-inner')
            if softmerge_div:
                text = softmerge_div.get_text(strip=True)
            
            # Look for DIM name - BE memories have specific patterns
            if (
                i in (0, 1) and text and text.strip().upper().startswith('BE ') and
                any(keyword in text.upper() for keyword in [
                    'SEEKERS', 'GAMMAMON', 'ANGORAMON', 'JELLYMON', 'JELLYMOM', 'AGUMON', 'GABUMON',
                    'PULSEMON', 'VOLCDRAMON', 'HERMITMON', 'FANGMON', 'TERRIERMON',
                    'RENAMON', 'VEEMON', 'WORMMON', 'GUILMON', 'IMPMON', 'PALMON',
                    'GOMAMON', 'PATAMON', 'SALAMON', 'BIYOMON', 'TENTOMON', 'RYUDAMON', 'DORUMON',
                    'RAMPAGE OF THE BEAST', 'FOREST GUARDIANS', 'IMPERIALDRAMON', 'IMPERIA',
                    'DRAGONIC BLAZE', 'HOLY WINGS', '25TH ANNIVERSARY', 'ANNIVERSARY'
                ])
            ):
                dim_name = text.strip()
            
            # Look for memory ID (D###_##) - only take the primary ID column (index 2)
            elif i == 2 and re.match(r'D\d+_\d+', text):
                index_code = text
            
            # Look for character names in the expected positions
            # Based on HTML structure: column 4 = JP name, column 5 = EN name
            elif i == 4 and text and any(ord(char) > 127 for char in text) and len(text) > 1:
                # This is likely a Japanese name in column 4
                japanese_name = text.replace('<br>', '').replace('\n', '').strip()
            elif i == 5 and text and len(text) > 1 and not text.startswith('D'):
                # This is likely an English name in column 5
                if is_likely_english_name(text):
                    english_name = text.replace('<br>', '').replace('\n', '').strip()

        # Fallbacks: if we have a DIM and D-code but missing an English name, try to infer it
        if dim_name and index_code and not english_name:
            for j, cell in enumerate(cells[4:], start=4):
                text = cell.get_text(strip=True)
                softmerge_div = cell.find('div', class_='softmerge-inner')
                if softmerge_div:
                    text = softmerge_div.get_text(strip=True)
                if is_likely_english_name(text):
                    english_name = text.replace('<br>', '').replace('\n', '').strip()
                    break
        
        # Store the mapping if we have all the data
        # Store the mapping if we have the core data (DIM, D-code, and an English name)
        if dim_name and index_code and english_name:
            # Extract character number from index (D136_01 -> character_number = 0)
            match = re.search(r'D(\d+)_(\d+)', index_code)
            if match:
                dim_num = match.group(1)
                char_num = int(match.group(2)) - 1  # Convert to 0-based indexing
                if char_num >= 0:
                    char_key = f"{dim_name} #{char_num}"
                    be_names[char_key] = english_name
                    if japanese_name:
                        print(f"📝 Found: {char_key} -> {english_name} (JP: {japanese_name})")
                    else:
                        print(f"📝 Found: {char_key} -> {english_name}")
    
    # Post-process: route Pulsemon line found under 25th Anniversary to Pulsemon BE
    remapped = {}
    for key, val in be_names.items():
        # If the dim name contains 25TH ANNIVERSARY and the Digimon is part of Pulsemon line, route to Pulsemon BE
        if key.startswith("BE 25TH ANNIVERSARY ") and any(
            pulse in val.upper() for pulse in [
                "PULSEMON", "BULKMON", "BOUTMON", "KAZUCHIMON"
            ]
        ):
            dim, suffix = key.split(" #", 1)
            new_key = f"BE PULSEMON #{suffix}"
            # Keep both original and remapped to preserve 25th Anniversary coverage
            remapped[key] = val
            remapped[new_key] = val
        else:
            remapped[key] = val

    # Manual overrides for rows where the sheet lacks an English name
    manual_overrides = {
        # 25th Anniversary
        "BE 25TH ANNIVERSARY #11": "MetalGreymon (Virus)",
        # Seekers - Dorumon
        "BE SEEKERS DORUMON #11": "Megadramon",
        # Seekers - Loogamon
        "BE SEEKERS LOOGAMON #20": "Snatchmon",
        "BE SEEKERS LOOGAMON #22": "Ragnamon",
        # Draconic Blaze
        "BE DRAGONIC BLAZE #22": "MagnaKidmon",
        # Rampage of the Beast
        "BE RAMPAGE OF THE BEAST #3": "Coronamon",
        "BE RAMPAGE OF THE BEAST #4": "Lunamon",
        "BE RAMPAGE OF THE BEAST #15": "Dianamon",
    }
    for k, v in manual_overrides.items():
        remapped.setdefault(k, v)

    print(f"✅ Extracted {len(remapped)} VB BE character names")
    return remapped

def map_folder_names():
    """Map DIM names from HTML to actual folder names in our data."""
    return {
        # BE Memory cards - map HTML names to actual JSON folder names
        "BE ANGORAMON": "Ghost Game - Angoramon BE",
        "BE GAMMAMON": "Ghost Game - Gammamon BE", 
        "BE JELLYMOM": "Ghost Game - Jellymon BE",
        "BE SEEKERS LOOGAMON": "Loogamon BE",
        "BE SEEKERS RYUDAMON": "Ryudamon BE", 
        "BE SEEKERS DORUMON": "Dorumon BE",
        "BE iMPERIALDRAMON": "Imperialdramon BE",  # HTML has lowercase 'i'
        "BE IMPERIALDRAMON": "Imperialdramon BE",   # Backup for uppercase
        "BE RAMPAGE OF THE BEAST": "rampage of the beast",
        "BE FOREST GUARDIANS": "Forest Guardian",
        "BE DRAGONIC BLAZE": "draconic blaze",
        "BE HOLY WINGS": "Holy Wings",
        "BE 25TH ANNIVERSARY": "25th Anniversary BEM",
        # Pulsemon
        "BE PULSEMON": "Pulsemon BE"
    }

def update_character_names(names_data, be_names):
    """Update character names with VB BE translations."""
    folder_mapping = map_folder_names()
    
    updated_count = 0
    
    for char_key, english_name in be_names.items():
        # Parse character key: "DIM_NAME #0" -> ("DIM_NAME", 0)
        if ' #' in char_key:
            dim_name, char_num_str = char_key.rsplit(' #', 1)
            try:
                char_num = int(char_num_str)
            except ValueError:
                continue
            
            # Map DIM name to folder name
            folder_name = folder_mapping.get(dim_name)
            if not folder_name:
                # Try fuzzy matching for folder names
                for mapped_dim, mapped_folder in folder_mapping.items():
                    if dim_name.upper() in mapped_dim.upper() or mapped_dim.upper() in dim_name.upper():
                        folder_name = mapped_folder
                        break
                
                if not folder_name:
                    continue
            
            # Find matching character in our data
            for char in names_data['characters']:
                if (char.get('folder_name') == folder_name and 
                    char.get('character_number') == char_num):
                    
                    # Update the character name and mark as translated
                    char['character_name'] = english_name
                    char['status'] = 'translated'
                    updated_count += 1
                    print(f"🔄 Updated: {folder_name} #{char_num} -> {english_name}")
                    break
    
    return updated_count

def main():
    """Main function to run the VB BE name translator."""
    try:
        print("VB BE Memory Name Translator")
        print("=" * 50)
        
        # File paths
        html_file = r'e:\Omnimon\utilities\VBE\sheet.html'
        names_file = r'e:\Omnimon\utilities\VBE\character_names.json'
        output_file = r'e:\Omnimon\utilities\VBE\character_names_be_translated.json'
        
        print(f"📄 HTML Source: {html_file}")
        print(f"📄 Names Source: {names_file}")
        print(f"📄 Output: {output_file}")
        print()
        
        # Parse VB BE HTML
        be_names = parse_be_html(html_file)
        
        # Load existing character names
        print("\n🔄 Updating character names...")
        with open(names_file, 'r', encoding='utf-8') as f:
            names_data = json.load(f)
        
        # Update character names
        updated_count = update_character_names(names_data, be_names)
        
        # Save updated data  
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(names_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Translation complete!")
        print(f"📊 Summary:")
        print(f"   • Updated characters: {updated_count}")
        print(f"   • Total characters: {len(names_data['characters'])}")
        print(f"   • Output file: {output_file}")
        
        # Show breakdown by folder for VB BE series
        be_folders = [
            "Vol 01 - Impulse City", "Vol 02 - Gammamon", "Vol 03 - Angoramon", 
            "Vol 04 - Jellymon", "Vol 05 - Agumon -25th COLOR EVOLUTION-", 
            "Vol 06 - Gabumon -25th COLOR EVOLUTION-", "Vol 07 - Pulsemon",
            "Vol 08 - Volcdramon", "Vol 09 - Hermitmon", "Vol 10 - Fangmon",
            "Vol 11 - Terriermon", "Vol 12 - Renamon", "Vol 13 - Veemon",
            "Vol 14 - Wormmon", "Vol 15 - Guilmon", "Vol 16 - Impmon",
            "Vol 17 - Palmon", "Vol 18 - Gomamon", "Vol 19 - Patamon",
            "Vol 20 - Salamon", "Vol 21 - Biyomon", "Vol 22 - Tentomon"
        ]
        
        print(f"\n📈 VB BE translations by folder:")
        for folder in be_folders:
            folder_chars = [c for c in names_data['characters'] if c['folder_name'] == folder]
            translated_chars = [c for c in folder_chars if c.get('status') == 'translated']
            if folder_chars:
                print(f"   • {folder}: {len(translated_chars)}/{len(folder_chars)} translated")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())