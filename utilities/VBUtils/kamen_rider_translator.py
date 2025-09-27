#!/usr/bin/env python3
"""
Kamen Rider Name Translator
============================
Parses the Kamen Rider HTML sheet to extract English character names
and updates the character names JSON file with proper translations.

Usage: python kamen_rider_translator.py
"""

import json
import re
from bs4 import BeautifulSoup

def parse_kamen_rider_html(html_file):
    """Parse the Kamen Rider HTML sheet to extract character names."""
    print("📖 Parsing Kamen Rider HTML sheet...")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    kamen_rider_names = {}

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
            
            # Column A: DIM name (like "KAMEN RIDER ZERO-ONE SIDE: ZEA")
            if i == 1 and any(keyword.upper() in text.upper() for keyword in ['KAMEN RIDER', 'MASKED RIDER', 'SHOWA', 'ZERO-ONE', 'EX-AID', 'BUILD', 'ROGUE', 'HOROBI', 'GENM', '000', 'OOO', 'KUUGA']):
                dim_name = text
            
            # Column B: Index code (like "D086_01")
            elif i == 2 and re.match(r'D\d+_\d+', text):
                index_code = text
            
            # Column D: Japanese name
            elif i == 4 and text and not text.startswith('D') and len(text) > 1:
                japanese_name = text.replace('\n', '').replace('<br>', '')
            
            # Column E: English name  
            elif i == 5 and text and len(text) > 1 and not re.match(r'D\d+_\d+', text):
                english_name = text.strip().upper()
                # Special handling for cases where English name is same as DIM name
                if english_name == dim_name and japanese_name:
                    # Keep the name but mark it as found
                    pass
        
        # If we found all required data, store it
        if dim_name and index_code:
            # Extract character number from index (D086_01 -> character_number = 0)
            match = re.search(r'D(\d+)_(\d+)', index_code)
            if match:
                char_num = int(match.group(2)) - 1  # Convert to 0-based indexing
                if char_num >= 0:
                    # For english_name, use the found name or fall back to a processed japanese name
                    final_english_name = english_name
                    
                    if not final_english_name and japanese_name:
                        # Fallback: clean up Japanese name if no English found
                        final_english_name = japanese_name.replace('<br>', ' ').replace('\n', ' ').strip()
                    
                    if final_english_name:
                        char_key = f"{dim_name} #{char_num}"
                        kamen_rider_names[char_key] = final_english_name
                        print(f"📝 Found: {char_key} -> {final_english_name}")
    
    print(f"✅ Extracted {len(kamen_rider_names)} Kamen Rider character names")
    return kamen_rider_names

def map_folder_names():
    """Map DIM names from HTML to actual folder names in our data."""
    return {
        # Correct mappings for all Kamen Rider DIMs
        "MASKED RIDER KUUGA": "Vol 00 - Masked Rider Kuuga",
        "SHOWA 10 MASKED RIDERS": "Vol 00 - Showa 10 Masked Rider",
        "KAMEN RIDER ZERO-ONESIDE: ZEA": "Vol 01 - Kamen Rider Zero One",
        "KAMEN RIDER HOROBISIDE: ARK": "Vol 01 - Kamen Rider Horobi",
        "KAMEN RIDER EX-AIDSIDE: EX-AID": "Vol 02 - Kamen Rider Ex-Aid",
        "KAMEN RIDER GENMSIDE: GENM": "Vol 02 - Kamen Rider Genm", 
        "KAMEN RIDER BUILDSIDE: BUILD": "Vol 03 - Kamen Rider Build",
        "KAMEN RIDER BUILDSIDE: ROGUE": "Vol 03 - Kamen Rider Rogue",
        "KAMEN RIDER OOOSIDE: OOO": "Vol 04 - Kamen Rider 000",
        "KAMEN RIDER OOOSIDE: GREEED": "Vol 04 - Greeed"
    }

def update_character_names(names_data, kamen_rider_names):
    """Update character names with Kamen Rider translations."""
    folder_mapping = map_folder_names()
    
    updated_count = 0
    
    for char_key, english_name in kamen_rider_names.items():
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
    """Main function to run the Kamen Rider name translator."""
    try:
        print("Kamen Rider Name Translator")
        print("=" * 50)
        
        # File paths
        html_file = r'e:\Omnimon\utilities\VBUtils\kamen_rider_sheet.html'
        names_file = r'e:\Omnimon\utilities\VBUtils\character_names.json'
        output_file = r'e:\Omnimon\utilities\VBUtils\character_names_kamen_rider.json'
        
        print(f"📄 HTML Source: {html_file}")
        print(f"📄 Names Source: {names_file}")
        print(f"📄 Output: {output_file}")
        print()
        
        # Parse Kamen Rider HTML
        kamen_rider_names = parse_kamen_rider_html(html_file)
        
        # Load existing character names
        print("\n🔄 Updating character names...")
        with open(names_file, 'r', encoding='utf-8') as f:
            names_data = json.load(f)
        
        # Update character names
        updated_count = update_character_names(names_data, kamen_rider_names)
        
        # Save updated data  
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(names_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Translation complete!")
        print(f"📊 Summary:")
        print(f"   • Updated characters: {updated_count}")
        print(f"   • Total characters: {len(names_data['characters'])}")
        print(f"   • Output file: {output_file}")
        
        # Show breakdown by folder for Kamen Rider series
        kamen_rider_folders = ["Vol 00 - Masked Rider Kuuga", "Vol 00 - Showa 10 Masked Rider",
                              "Vol 01 - Kamen Rider Zero One", "Vol 01 - Kamen Rider Horobi", 
                              "Vol 02 - Kamen Rider Ex-Aid", "Vol 02 - Kamen Rider Genm",
                              "Vol 03 - Kamen Rider Build", "Vol 03 - Kamen Rider Rogue", 
                              "Vol 04 - Kamen Rider 000", "Vol 04 - Greeed"]
        
        print(f"\n📈 Kamen Rider translations by folder:")
        for folder in kamen_rider_folders:
            folder_chars = [c for c in names_data['characters'] if c['folder_name'] == folder]
            translated_chars = [c for c in folder_chars if c.get('status') == 'translated']
            if folder_chars:
                print(f"   • {folder}: {len(translated_chars)}/{len(folder_chars)} translated")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())