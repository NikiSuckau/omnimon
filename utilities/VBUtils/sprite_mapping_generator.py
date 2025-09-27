#!/usr/bin/env python3
"""
Battle Generator with Sprite Matching Integration
Integrates the sprite matcher to properly map adventure sprites to character sprites.
"""

import json
import re
from bs4 import BeautifulSoup
import os
from sprite_matcher import extract_sprite_urls_from_html, match_adventure_to_character_sprites, save_sprite_matches, load_sprite_matches

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
    """Extract DIM names and their corresponding enemy sprite numbers from HTML."""
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
                # Clean up the DIM name
                dim_text = re.sub(r'<br[^>]*>', ' ', str(cell))
                dim_text = BeautifulSoup(dim_text, 'html.parser').get_text(strip=True)
                dim_text = re.sub(r'\s+', ' ', dim_text)
                dim_positions.append((i, dim_text))
                print(f"Found DIM at row {i}: {dim_text}")
    
    # Second pass: extract enemies for each DIM from preceding rows
    for j, (dim_row, dim_name) in enumerate(dim_positions):
        enemies = []
        
        # Look in rows before this DIM
        start_row = max(0, dim_row - 3)
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
        
        # Take only the first 15 enemies
        if enemies:
            dim_enemies[dim_name] = enemies[:15]
            print(f"  Extracted {len(enemies[:15])} enemies: {enemies[:15]}")
        else:
            print(f"  ⚠️  No enemies found for {dim_name}")
    
    return dim_enemies

def create_sprite_mapping():
    """Create sprite mapping between adventure and character sheets."""
    print("🎯 Creating Sprite Mapping between Adventure and Character Sheets")
    
    # Load HTML sheets
    kamen_rider_adventure_soup = load_html('kamen_rider_adventure_sheet.html')
    ultraman_adventure_soup = load_html('ultraman_adventure_sheet.html')
    kamen_rider_main_soup = load_html('kamen_rider_sheet.html')
    ultraman_main_soup = load_html('ultraman_sheet.html')
    
    if not all([kamen_rider_adventure_soup, ultraman_adventure_soup, kamen_rider_main_soup, ultraman_main_soup]):
        print("❌ Could not load all required HTML sheets")
        return
    
    # Extract sprite URLs from adventure sheets
    print("📊 Extracting adventure sprite URLs...")
    kamen_rider_adventure_urls = extract_sprite_urls_from_html(kamen_rider_adventure_soup)
    ultraman_adventure_urls = extract_sprite_urls_from_html(ultraman_adventure_soup)
    
    # Extract sprite URLs from main character sheets  
    print("📊 Extracting character sprite URLs...")
    kamen_rider_character_urls = extract_sprite_urls_from_html(kamen_rider_main_soup)
    ultraman_character_urls = extract_sprite_urls_from_html(ultraman_main_soup)
    
    print(f"Found {len(kamen_rider_adventure_urls)} Kamen Rider adventure sprites")
    print(f"Found {len(ultraman_adventure_urls)} Ultraman adventure sprites")
    print(f"Found {len(kamen_rider_character_urls)} Kamen Rider character sprites")
    print(f"Found {len(ultraman_character_urls)} Ultraman character sprites")
    
    # Match Kamen Rider sprites
    print("\n🔍 Matching Kamen Rider sprites...")
    kamen_rider_matches = match_adventure_to_character_sprites(
        kamen_rider_adventure_urls, 
        kamen_rider_character_urls,
        similarity_threshold=0.6  # Lower threshold for initial testing
    )
    
    # Match Ultraman sprites
    print("\n🔍 Matching Ultraman sprites...")
    ultraman_matches = match_adventure_to_character_sprites(
        ultraman_adventure_urls,
        ultraman_character_urls,
        similarity_threshold=0.6
    )
    
    # Combine and save matches
    all_matches = {
        'kamen_rider': kamen_rider_matches,
        'ultraman': ultraman_matches,
        'metadata': {
            'kamen_rider_adventure_sprites': len(kamen_rider_adventure_urls),
            'kamen_rider_character_sprites': len(kamen_rider_character_urls), 
            'kamen_rider_matches': len(kamen_rider_matches),
            'ultraman_adventure_sprites': len(ultraman_adventure_urls),
            'ultraman_character_sprites': len(ultraman_character_urls),
            'ultraman_matches': len(ultraman_matches)
        }
    }
    
    save_sprite_matches(all_matches, 'sprite_matches.json')
    
    print(f"\n✅ Sprite matching complete!")
    print(f"   Kamen Rider: {len(kamen_rider_matches)}/{len(kamen_rider_adventure_urls)} matches")
    print(f"   Ultraman: {len(ultraman_matches)}/{len(ultraman_adventure_urls)} matches")
    
    return all_matches

def main():
    """Main function to create sprite mapping."""
    sprite_matches = create_sprite_mapping()
    
    if sprite_matches:
        print("\n💡 Next steps:")
        print("1. Review sprite_matches.json to verify accuracy")
        print("2. Adjust similarity threshold if needed")
        print("3. Integrate with battle_generator.py")
        print("4. Generate battle.json with proper character names")

if __name__ == "__main__":
    main()