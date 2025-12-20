#!/usr/bin/env python3
"""
Battle.json Generator for Omnimon VB Utils
Extracts enemy information from HTML sheets and creates battle configurations.
"""

import json
import re
from bs4 import BeautifulSoup
import os

def load_json(file_path):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def load_html(file_path):
    """Load and parse HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def extract_dim_names_and_enemies(soup, sheet_type):
    """
    Extract DIM names and their corresponding enemy sprite numbers from HTML.
    Returns a dictionary mapping DIM names to lists of 15 enemy sprite numbers.
    """
    dim_enemies = {}
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    # First pass: find all DIM names and their row indices
    dim_positions = []
    for i, row in enumerate(rows):
        dim_cells = row.find_all('td', class_='s2')
        for cell in dim_cells:
            dim_text = cell.get_text(strip=True)
            if dim_text and len(dim_text) > 5:
                # Clean up the DIM name - remove HTML breaks and extra whitespace  
                dim_text = re.sub(r'<br[^>]*>', ' ', str(cell))
                dim_text = BeautifulSoup(dim_text, 'html.parser').get_text(strip=True)
                dim_text = re.sub(r'\s+', ' ', dim_text)  # Normalize whitespace
                dim_positions.append((i, dim_text))
                print(f"Found DIM at row {i}: {dim_text}")
    
    # Second pass: extract enemies for each DIM from preceding rows
    for j, (dim_row, dim_name) in enumerate(dim_positions):
        enemies = []
        
        # Look in rows before this DIM (typically the 2 rows immediately before)
        start_row = max(0, dim_row - 3)  # Look 3 rows back
        end_row = dim_row
        
        for row_idx in range(start_row, end_row):
            if row_idx < len(rows):
                row = rows[row_idx]
                images = row.find_all('img')
                for img in images:
                    src = img.get('src', '')
                    # Look for unnamed(X).png pattern
                    match = re.search(r'unnamed\((\d+)\)\.png', src)
                    if match:
                        sprite_num = int(match.group(1))
                        enemies.append(sprite_num)
        
        # Take only the first 15 enemies (there should be exactly 15)
        if enemies:
            dim_enemies[dim_name] = enemies[:15]
            print(f"  Extracted {len(enemies[:15])} enemies: {enemies[:15]}")
        else:
            print(f"  ⚠️  No enemies found for {dim_name}")
    
    return dim_enemies

def map_dim_names_to_folders(dim_enemies, character_names):
    """
    Map DIM names from HTML to folder names in character_names.json
    """
    folder_mapping = {}
    
    # Get all folder names from character_names
    folder_names = set()
    for char in character_names.get('characters', []):
        folder_names.add(char['folder_name'])
    
    # Special mapping rules for known mismatches
    special_mappings = {
        'KAMEN RIDER ZERO-ONE SIDE: ZEA': 'Vol 01 - Kamen Rider Zero One',
        'KAMEN RIDER HOROBI SIDE: ARK': 'Vol 01 - Kamen Rider Horobi',
        'KAMEN RIDER BUILD SIDE: ROGUE': 'Vol 03 - Kamen Rider Rogue',
        'KAMEN RIDER OOO SIDE: OOO': 'Vol 04 - Kamen Rider 000',
        'KAMEN RIDER OOO SIDE: GREEED': 'Vol 04 - Greeed',
        '6 Ultra Brothers': 'Vol 00 - 6 Ultrabrothers'
    }
    
    # Try to match DIM names to folder names
    for dim_name in dim_enemies.keys():
        # First check special mappings
        if dim_name in special_mappings:
            target_folder = special_mappings[dim_name]
            if target_folder in folder_names:
                folder_mapping[dim_name] = target_folder
                print(f"Mapped (special): '{dim_name}' -> '{target_folder}'")
                continue
        
        best_match = None
        best_score = 0
        
        for folder_name in folder_names:
            # Skip DC/Batman folders
            if any(dc in folder_name.upper() for dc in ['BATMAN', 'DC HEROES', 'DC VILLAINS']):
                continue
                
            # Simple matching logic - count common words
            dim_words = set(dim_name.upper().split())
            folder_words = set(folder_name.upper().split())
            
            # Remove common words that don't help matching
            common_stopwords = {'VOL', 'THE', 'AND', 'OF', '-', '0', '00', '01', '02', '03', '04', 'SIDE:', 'RIDER', 'KAMEN', 'ULTRA', 'ULTRAMAN'}
            dim_words -= common_stopwords
            folder_words -= common_stopwords
            
            # Calculate match score
            if dim_words and folder_words:
                intersection = dim_words & folder_words
                score = len(intersection) / max(len(dim_words), len(folder_words))
                
                if score > best_score and score > 0.3:  # Minimum 30% match
                    best_score = score
                    best_match = folder_name
        
        if best_match:
            # Check if folder is already mapped to prevent overwriting
            if best_match not in folder_mapping.values():
                folder_mapping[dim_name] = best_match
                print(f"Mapped: '{dim_name}' -> '{best_match}' (score: {best_score:.2f})")
            else:
                print(f"⚠️  Folder '{best_match}' already mapped, skipping '{dim_name}'")
        else:
            print(f"⚠️  No mapping found for: '{dim_name}'")
    
    return folder_mapping

def extract_character_data_from_main_sheet(soup, sheet_type):
    """
    Extract character data from the main character sheets.
    Maps unnamed(X).png sprite numbers to actual character names and data.
    """
    character_data = {}
    
    # Find all table rows
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 6:
            continue
        
        # Look for rows with character data
        sprite_number = None
        character_name = None
        japanese_name = None
        index_code = None
        
        for i, cell in enumerate(cells):
            # Look for images with unnamed(X).png pattern
            img_tags = cell.find_all('img')
            for img in img_tags:
                src = img.get('src', '')
                if 'unnamed(' in src:
                    # Extract the number from unnamed(X).png
                    match = re.search(r'unnamed\((\d+)\)\.png', src)
                    if match:
                        sprite_number = int(match.group(1))
            
            # Get text content for names and codes
            text = cell.get_text(strip=True)
            softmerge_div = cell.find('div', class_='softmerge-inner')
            if softmerge_div:
                text = softmerge_div.get_text(strip=True)
            
            # Column B: Index code (like "D086_01")
            if i == 2 and re.match(r'D\d+_\d+', text):
                index_code = text
            
            # Column D: Japanese name
            elif i == 4 and text and not text.startswith('D') and len(text) > 1:
                japanese_name = text.replace('\n', '').replace('<br>', '')
            
            # Column E: English name
            elif i == 5 and text and len(text) > 1 and not re.match(r'D\d+_\d+', text):
                character_name = text.strip()
        
        # If we found a sprite number and character data, store it
        if sprite_number and character_name and index_code:
            character_data[sprite_number] = {
                'name': character_name,
                'japanese_name': japanese_name or '',
                'index_code': index_code,
                'sheet_type': sheet_type
            }
    
    return character_data

def cross_reference_enemies_with_characters(battle_enemies_data, kamen_rider_soup, ultraman_soup):
    """
    Cross-reference enemy sprite numbers with actual character data from main sheets.
    """
    print("\n🔍 Cross-referencing enemy sprites with character data...")
    
    # Extract character data from main sheets
    print("📊 Extracting Kamen Rider character data...")
    kamen_rider_chars = extract_character_data_from_main_sheet(kamen_rider_soup, 'kamen_rider')
    print(f"Found {len(kamen_rider_chars)} Kamen Rider characters")
    
    print("📊 Extracting Ultraman character data...")
    ultraman_chars = extract_character_data_from_main_sheet(ultraman_soup, 'ultraman')
    print(f"Found {len(ultraman_chars)} Ultraman characters")
    
    # Combine character data
    all_character_data = {**kamen_rider_chars, **ultraman_chars}
    
    # Update battle enemies with actual character data
    updated_count = 0
    for folder_name, data in battle_enemies_data.items():
        enemy_sprites = data['enemy_sprites']
        sheet_type = data['sheet_type']
        
        # Update each enemy with character data
        updated_enemies = []
        for sprite_num in enemy_sprites:
            if sprite_num in all_character_data:
                char_data = all_character_data[sprite_num]
                # Only use characters from the same sheet type
                if char_data['sheet_type'] == sheet_type:
                    updated_enemies.append({
                        'sprite_number': sprite_num,
                        'name': char_data['name'],
                        'japanese_name': char_data['japanese_name'],
                        'index_code': char_data['index_code']
                    })
                    updated_count += 1
                else:
                    # Keep as generic enemy if no matching character found
                    updated_enemies.append({
                        'sprite_number': sprite_num,
                        'name': f"Enemy_{sprite_num}",
                        'japanese_name': '',
                        'index_code': ''
                    })
            else:
                # Keep as generic enemy if no character data found
                updated_enemies.append({
                    'sprite_number': sprite_num,
                    'name': f"Enemy_{sprite_num}",
                    'japanese_name': '',
                    'index_code': ''
                })
        
        # Update the battle data
        data['enemy_characters'] = updated_enemies
        
        print(f"✅ {folder_name}: {len([e for e in updated_enemies if not e['name'].startswith('Enemy_')])}/{len(updated_enemies)} enemies matched")
    
    print(f"\n🎉 Cross-reference complete! Matched {updated_count} enemy characters")
    return battle_enemies_data

def find_character_by_index_code(index_code, folder_name, character_names_data):
    """
    Find character name from character_names.json using index code (like D093_07) and folder name.
    """
    if not index_code or not folder_name:
        return None
        
    for char in character_names_data.get('characters', []):
        # Only consider characters from the same folder
        if char.get('folder_name') != folder_name:
            continue
            
        # Get the final name - use character_name if available, otherwise manual_name or extracted_name
        final_name = char.get('character_name') or char.get('manual_name') or char.get('extracted_name', '')
        
        # Match based on character number from index code
        if index_code:
            # Extract character number from index code (D093_07 -> 6, since it's 0-based)
            match = re.search(r'D\d+_(\d+)', index_code)
            if match:
                char_num_from_code = int(match.group(1)) - 1  # Convert to 0-based
                
                # Check if this character matches the index code pattern
                if char.get('character_number') == char_num_from_code:
                    return final_name
    
    return None

def find_monster_stats(character_name, folder_name, monster_data):
    """
    Find monster stats from monster.json using character name and folder (version).
    """
    # Map folder names to version numbers
    folder_to_version = {
        'Vol 00 - Showa 10 Masked Rider': 5,
        'Vol 00 - Masked Rider Kuuga': 6,
        'Vol 01 - Kamen Rider Zero One': 7,
        'Vol 01 - Kamen Rider Horobi': 8,
        'Vol 02 - Kamen Rider Ex-Aid': 9,
        'Vol 02 - Kamen Rider Genm': 10,
        'Vol 03 - Kamen Rider Build': 11,
        'Vol 03 - Kamen Rider Rogue': 12,
        'Vol 04 - Kamen Rider 000': 13,
        'Vol 04 - Greeed': 14,
        'Vol 00 - 6 Ultrabrothers': 15,
        'Vol 00 - Ultraman Tiga': 16,
        'Vol 01 - Ultraman Zero': 17,
        'Vol 01 - Zetton': 18,
        'Vol 02 - Ultraman Trigger': 19,
        'Vol 02 - Alien Baltan': 20,
        'Vol 03 - Ultraman Z': 21,
        'Vol 03 - Sevenger': 22,
        'Vol 04 - Ultraman Dyna and Gaia': 23,
        'Vol 04 - Gomora': 24
    }
    
    version_num = folder_to_version.get(folder_name)
    if not version_num:
        return None
    
    # Search for matching monster
    for monster in monster_data.get('monster', []):
        if (monster.get('name', '').upper() == character_name.upper() and 
            monster.get('version') == version_num):
            return monster
    
    return None

def generate_battle_json(battle_enemies_data, character_names_data, monster_data, kamen_rider_soup, ultraman_soup):
    """
    Generate the complete battle.json configuration following the correct 5-step process.
    """
    battle_entries = []
    
    # Map folder names to version numbers
    folder_to_version = {
        'Vol 00 - Showa 10 Masked Rider': 5,
        'Vol 00 - Masked Rider Kuuga': 6,
        'Vol 01 - Kamen Rider Zero One': 7,
        'Vol 01 - Kamen Rider Horobi': 8,
        'Vol 02 - Kamen Rider Ex-Aid': 9,
        'Vol 02 - Kamen Rider Genm': 10,
        'Vol 03 - Kamen Rider Build': 11,
        'Vol 03 - Kamen Rider Rogue': 12,
        'Vol 04 - Kamen Rider 000': 13,
        'Vol 04 - Greeed': 14,
        'Vol 00 - 6 Ultrabrothers': 15,
        'Vol 00 - Ultraman Tiga': 16,
        'Vol 01 - Ultraman Zero': 17,
        'Vol 01 - Zetton': 18,
        'Vol 02 - Ultraman Trigger': 19,
        'Vol 02 - Alien Baltan': 20,
        'Vol 03 - Ultraman Z': 21,
        'Vol 03 - Sevenger': 22,
        'Vol 04 - Ultraman Dyna and Gaia': 23,
        'Vol 04 - Gomora': 24
    }
    
    # Extract character data from main sheets for index code lookup
    print("🔍 Extracting character data from main sheets...")
    kamen_rider_chars = extract_character_data_from_main_sheet(kamen_rider_soup, 'kamen_rider')
    ultraman_chars = extract_character_data_from_main_sheet(ultraman_soup, 'ultraman')
    
    print(f"📊 Kamen Rider sprites found: {sorted(list(kamen_rider_chars.keys())[:10])}...")
    print(f"📊 Ultraman sprites found: {sorted(list(ultraman_chars.keys())[:10])}...")
    
    # Process each mapped folder (following 5-step process)
    for folder_name, data in battle_enemies_data.items():
        version_num = folder_to_version.get(folder_name)
        if not version_num:
            print(f"⚠️  No version number found for {folder_name}")
            continue
            
        enemy_sprites = data.get('enemy_sprites', [])
        sheet_type = data.get('sheet_type', '')
        
        if not enemy_sprites:
            print(f"⚠️  No enemy sprites found for {folder_name}")
            continue
        
        # Select appropriate character data based on sheet type
        character_lookup = kamen_rider_chars if sheet_type == 'kamen_rider' else ultraman_chars
        
        # Process each of the 15 areas
        for area_num in range(1, 16):
            sprite_index = (area_num - 1) % len(enemy_sprites)
            sprite_number = enemy_sprites[sprite_index]
            
            # Step 1: Get the unnamed number (sprite_number) - already done
            
            # Step 2: Map adventure sprite to character sprite using sprite mapping
            # Load sprite mapping if not already loaded
            if not hasattr(generate_battle_json, 'sprite_mapping'):
                try:
                    import simple_sprite_mapper
                    generate_battle_json.sprite_mapping = simple_sprite_mapper.test_mapping_with_battle_generator()
                except:
                    generate_battle_json.sprite_mapping = {'kamen_rider': {}, 'ultraman': {}}
            
            # Get the corresponding character sprite number
            mapping_key = 'kamen_rider' if sheet_type == 'kamen_rider' else 'ultraman'
            mapped_sprite = generate_battle_json.sprite_mapping.get(mapping_key, {}).get(sprite_number)
            
            index_code = None
            character_name_from_sheet = None
            
            if mapped_sprite and mapped_sprite in character_lookup:
                char_data = character_lookup[mapped_sprite]
                index_code = char_data.get('index_code', '')
                character_name_from_sheet = char_data.get('name', '')
                print(f"  🎯 Adventure sprite {sprite_number} -> Character sprite {mapped_sprite} -> {character_name_from_sheet}")
            
            # Step 3: Look into character_names.json to get the real translated name
            final_character_name = None
            if index_code:
                final_character_name = find_character_by_index_code(index_code, folder_name, character_names_data)
            
            # If no translated name found, use the name from sheet
            if not final_character_name and character_name_from_sheet:
                final_character_name = character_name_from_sheet
            
            # Error if we still don't have a proper character name
            if not final_character_name:
                error_msg = f"❌ ERROR: No character name found for sprite {sprite_number} in {folder_name}"
                error_msg += f"\n   - Index code: {index_code}"
                error_msg += f"\n   - Character from sheet: {character_name_from_sheet}"
                error_msg += f"\n   - Area: {area_num}"
                error_msg += f"\n   - Version: {version_num}"
                print(error_msg)
                print(f"\n💡 Need to fix character data mapping for this entry!")
                raise ValueError(f"Missing character name for sprite {sprite_number} in {folder_name}")
            
            # Step 4: Look at monster.json to find the correct record
            monster_stats = find_monster_stats(final_character_name, folder_name, monster_data)
            
            # Step 5: Build the battle.json entry
            if monster_stats:
                battle_entry = {
                    "name": final_character_name,
                    "power": monster_stats.get('attack', 0),
                    "attribute": monster_stats.get('attribute', ''),
                    "hp": monster_stats.get('hp', 3),
                    "area": area_num,
                    "round": 1,
                    "version": version_num,
                    "handicap": 0,
                    "atk_main": monster_stats.get('atk_main', 4),
                    "atk_alt": monster_stats.get('atk_alt', 52),
                    "stage": monster_stats.get('stage', 3)
                }
            else:
                # Default entry if no stats found
                battle_entry = {
                    "name": final_character_name,
                    "power": 0,
                    "attribute": "",
                    "hp": 3,
                    "area": area_num,
                    "round": 1,
                    "version": version_num,
                    "handicap": 0,
                    "atk_main": 4,
                    "atk_alt": 52,
                    "stage": 3
                }
            
            battle_entries.append(battle_entry)
        
        print(f"✅ Generated battle entries for {folder_name} (version {version_num})")
    
    return battle_entries

def main():
    """Main function to extract battle enemy data."""
    print("🔍 Battle Generator - Extracting enemy data from HTML sheets...")
    
    # Load required files
    character_names = load_json('character_names.json')
    if not character_names:
        return
    
    # Load HTML sheets (both adventure and main character sheets)
    kamen_rider_adventure_soup = load_html('kamen_rider_adventure_sheet.html')
    ultraman_adventure_soup = load_html('ultraman_adventure_sheet.html')
    kamen_rider_main_soup = load_html('kamen_rider_sheet.html')
    ultraman_main_soup = load_html('ultraman_sheet.html')
    
    if not kamen_rider_adventure_soup or not ultraman_adventure_soup:
        print("❌ Could not load adventure sheets")
        return
    
    if not kamen_rider_main_soup or not ultraman_main_soup:
        print("❌ Could not load main character sheets")
        return
    
    # Extract enemy data from both adventure sheets
    print("\n📊 Extracting Kamen Rider enemy data...")
    kamen_rider_enemies = extract_dim_names_and_enemies(kamen_rider_adventure_soup, 'kamen_rider')
    
    print(f"Found {len(kamen_rider_enemies)} Kamen Rider DIMs")
    for dim_name, enemies in kamen_rider_enemies.items():
        print(f"  {dim_name}: {len(enemies)} enemies -> {enemies[:5]}...")
    
    print("\n📊 Extracting Ultraman enemy data...")
    ultraman_enemies = extract_dim_names_and_enemies(ultraman_adventure_soup, 'ultraman')
    
    print(f"Found {len(ultraman_enemies)} Ultraman DIMs")
    for dim_name, enemies in ultraman_enemies.items():
        print(f"  {dim_name}: {len(enemies)} enemies -> {enemies[:5]}...")
    
    # Map DIM names to folder names
    print("\n🔗 Mapping DIM names to folder names...")
    
    all_dim_enemies = {**kamen_rider_enemies, **ultraman_enemies}
    folder_mapping = map_dim_names_to_folders(all_dim_enemies, character_names)
    
    # Create final enemy mapping with folder names
    battle_enemies_data = {}
    for dim_name, folder_name in folder_mapping.items():
        if dim_name in all_dim_enemies:
            battle_enemies_data[folder_name] = {
                'dim_name': dim_name,
                'enemy_sprites': all_dim_enemies[dim_name],
                'sheet_type': 'kamen_rider' if dim_name in kamen_rider_enemies else 'ultraman'
            }
    
    print(f"\n✅ Successfully mapped {len(battle_enemies_data)} DIMs to battle enemies")
    print("\nMapped folders:")
    for folder_name, data in battle_enemies_data.items():
        print(f"  📁 {folder_name}")
        print(f"     DIM: {data['dim_name']}")
        print(f"     Type: {data['sheet_type']}")
        print(f"     Enemies: {data['enemy_sprites']}")
        print()
    
    # Load monster data for stats
    print("📊 Loading monster data for battle stats...")
    monster_data = load_json('monster.json')
    if not monster_data:
        print("⚠️  Could not load monster.json, using default stats")
        monster_data = {}
    
    # Generate battle.json following the correct 5-step process
    print("\n🎮 Generating battle.json configuration...")
    battle_entries = generate_battle_json(battle_enemies_data, character_names, monster_data, 
                                         kamen_rider_main_soup, ultraman_main_soup)
    
    # Save to file
    try:
        with open('battle.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(battle_entries, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Successfully generated battle.json!")
        print(f"   Total battle entries: {len(battle_entries)}")
        print(f"   Unique versions: {len(set(entry['version'] for entry in battle_entries))}")
        print(f"   Areas per version: 15")
    except Exception as e:
        print(f"❌ Error saving battle.json: {e}")
    
    return battle_entries

if __name__ == "__main__":
    result = main()