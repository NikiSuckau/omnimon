#!/usr/bin/env python3
"""
Ultraman Name Translator
Extracts English names for Ultraman characters from the HTML sheet and updates character_names.json
"""

import json
import re
from bs4 import BeautifulSoup

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

def parse_ultraman_html(html_path):
    """Parse the Ultraman HTML sheet and extract name mappings."""
    print("📖 Parsing Ultraman HTML sheet...")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    ultraman_names = {}

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
            
            # Column A: DIM name (like "6 Ultra Brothers")
            if i == 1 and any(keyword.upper() in text.upper() for keyword in ['Ultra', 'Ultraman', 'Tiga', 'Zero', 'Trigger', 'Dyna', 'Gaia', 'Z', 'GOMORA', 'ZETTON', 'BALTAN', 'SEVENGER']):
                dim_name = text
            
            # Column B: Index code (like "D064_01")
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
            # Extract character number from index (D064_01 -> character_number = 0)
            match = re.search(r'D(\d+)_(\d+)', index_code)
            if match:
                char_num = int(match.group(2)) - 1  # Convert to 0-based indexing
                if char_num >= 0:
                    # For english_name, use the found name or fall back to a processed japanese name
                    final_english_name = english_name
                    
                    # If no proper English name found, try to process Japanese name or use a fallback
                    if not final_english_name or final_english_name == dim_name:
                        if japanese_name and japanese_name.strip():
                            # Try to extract meaningful part from Japanese name
                            jp_clean = japanese_name.replace('ウルトラマン', 'ULTRAMAN').replace('ティガ', 'TIGA')
                            final_english_name = jp_clean.strip().upper()
                        else:
                            # Use dim_name with character index as fallback
                            final_english_name = f"{dim_name} #{char_num+1}"
                    
                    key = (dim_name, char_num)
                    ultraman_names[key] = {
                        'english_name': final_english_name,
                        'japanese_name': japanese_name or '',
                        'index_code': index_code
                    }
                    print(f"📝 Found: {dim_name} #{char_num} -> {final_english_name}")
                    if not english_name:
                        print(f"   ℹ️  (Generated from JP: '{japanese_name}')")
    
    print(f"✅ Extracted {len(ultraman_names)} Ultraman character names")
    return ultraman_names

def map_folder_names():
    """Map DIM names from HTML to actual folder names in our data."""
    return {
        "6 Ultra Brothers": "Vol 00 - 6 Ultrabrothers",
        "ULTRAMAN TIGA": "Vol 00 - Ultraman Tiga", 
        "ULTRAMAN ZERO": "Vol 01 - Ultraman Zero",
        "ULTRA MONSTER ZETTON": "Vol 01 - Zetton",
        "ULTRAMAN TRIGGER": "Vol 02 - Ultraman Trigger",
        "ALIEN BALTAN": "Vol 02 - Alien Baltan",
        "ULTRAMAN Z": "Vol 03 - Ultraman Z",
        "SEVENGER": "Vol 03 - Sevenger",
        "ULTRAMAN DYNA & GAIA": "Vol 04 - Ultraman Dyna and Gaia",
        "GOMORA": "Vol 04 - Gomora"
    }

def update_character_names(names_data, ultraman_names):
    """Update character names with Ultraman translations."""
    folder_mapping = map_folder_names()
    updated_count = 0
    
    for character in names_data['characters']:
        folder_name = character['folder_name']
        char_number = character['character_number']
        
        # Check if this is an Ultraman folder we can translate
        dim_name = None
        for dim, folder in folder_mapping.items():
            if folder == folder_name:
                dim_name = dim
                break
        
        if dim_name:
            # Look for translation
            key = (dim_name, char_number)
            if key in ultraman_names:
                translation = ultraman_names[key]
                old_name = character.get('manual_name', character.get('extracted_name', ''))
                new_name = translation['english_name']
                
                # Update the manual_name with English translation
                character['manual_name'] = new_name
                character['status'] = 'translated'
                
                # Add translation info
                character['translation_info'] = {
                    'source': 'ultraman_sheet',
                    'index_code': translation['index_code'],
                    'japanese_name': translation['japanese_name'],
                    'previous_name': old_name
                }
                
                updated_count += 1
                print(f"🔄 Updated: {folder_name} #{char_number} -> {new_name}")
    
    return updated_count

def main():
    """Main function to translate Ultraman character names."""
    print("Ultraman Name Translator")
    print("=" * 50)
    
    # Get script directory for file paths
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    html_path = os.path.join(script_dir, 'ultraman_sheet.html')
    names_path = os.path.join(script_dir, 'character_names.json')
    output_path = os.path.join(script_dir, 'character_names_ultraman.json')
    
    # Check if files exist
    if not os.path.exists(html_path):
        print(f"❌ HTML file not found: {html_path}")
        return 1
    
    if not os.path.exists(names_path):
        print(f"❌ Character names file not found: {names_path}")
        return 1
    
    print(f"📄 HTML Source: {html_path}")
    print(f"📄 Names Source: {names_path}")
    print(f"📄 Output: {output_path}")
    print()
    
    try:
        # Parse the HTML sheet
        ultraman_names = parse_ultraman_html(html_path)
        
        if not ultraman_names:
            print("❌ No Ultraman names found in HTML sheet")
            return 1
        
        # Load character names data
        names_data = load_json(names_path)
        if not names_data:
            return 1
        
        print(f"\n🔄 Updating character names...")
        updated_count = update_character_names(names_data, ultraman_names)
        
        # Save updated data
        save_json(output_path, names_data)
        
        print(f"\n✅ Translation complete!")
        print(f"📊 Summary:")
        print(f"   • Updated characters: {updated_count}")
        print(f"   • Total characters: {len(names_data['characters'])}")
        print(f"   • Output file: {output_path}")
        
        # Show breakdown by folder for Ultraman series
        ultraman_folders = ["Vol 00 - 6 Ultrabrothers", "Vol 00 - Ultraman Tiga", "Vol 01 - Ultraman Zero", 
                           "Vol 01 - Zetton", "Vol 02 - Ultraman Trigger", "Vol 02 - Alien Baltan",
                           "Vol 03 - Ultraman Z", "Vol 03 - Sevenger", "Vol 04 - Ultraman Dyna and Gaia", "Vol 04 - Gomora"]
        
        print(f"\n📈 Ultraman translations by folder:")
        for folder in ultraman_folders:
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