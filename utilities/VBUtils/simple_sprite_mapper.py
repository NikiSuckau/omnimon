#!/usr/bin/env python3
"""
Simple Sprite Mapping for Battle Generator
Creates a mapping between adventure sheet sprites and character sheet sprites
by analyzing their context and position in the sheets.
"""

import json
import re
from bs4 import BeautifulSoup

def load_html(file_path):
    """Load and parse HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def create_simple_sprite_mapping():
    """Create a simple mapping assuming sprites with same numbers might be the same character."""
    print("🎯 Creating Simple Sprite Mapping")
    
    # For now, let's assume a direct mapping and see what happens
    # This is a hypothesis that we can test
    
    # Create a 1:1 mapping for testing
    kamen_rider_mapping = {}
    ultraman_mapping = {}
    
    # Map adventure sprites 1-154 to character sprites 1-154 (if they exist)
    for i in range(1, 155):
        kamen_rider_mapping[i] = i
        
    for i in range(1, 155):
        ultraman_mapping[i] = i
    
    mapping = {
        'kamen_rider': kamen_rider_mapping,
        'ultraman': ultraman_mapping,
        'method': 'direct_number_mapping',
        'note': 'Testing hypothesis that adventure sprite X maps to character sprite X'
    }
    
    # Save the mapping
    with open('simple_sprite_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✅ Created simple mapping with {len(kamen_rider_mapping)} Kamen Rider and {len(ultraman_mapping)} Ultraman mappings")
    return mapping

def test_mapping_with_battle_generator():
    """Test the mapping by integrating with battle generator."""
    print("🧪 Testing mapping integration...")
    
    # Load the mapping
    try:
        with open('simple_sprite_mapping.json', 'r') as f:
            mapping = json.load(f)
        print("📂 Loaded sprite mapping")
        return mapping
    except FileNotFoundError:
        print("❌ No mapping file found, creating one...")
        return create_simple_sprite_mapping()

def main():
    """Main function."""
    mapping = create_simple_sprite_mapping()
    
    print("\n💡 Next steps:")
    print("1. Modify battle_generator.py to use this mapping")
    print("2. Test if sprite X from adventure sheet corresponds to sprite X from character sheet")
    print("3. If not, we'll need to implement proper image comparison")
    
    return mapping

if __name__ == "__main__":
    main()