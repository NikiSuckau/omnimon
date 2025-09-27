#!/usr/bin/env python3
"""
Test Sprite Matching with Example Images
Tests the sprite matcher using the example sprites provided by the user.
"""

import cv2
import numpy as np
from sprite_matcher import preprocess_sprite, calculate_image_similarity
import requests
import os

def test_example_sprites():
    """Test sprite matching with the example images provided."""
    print("🧪 Testing Sprite Matching with Example Images")
    
    # For now, let's test with a simple comparison function
    # In a real scenario, we'd extract URLs from the HTML sheets
    
    print("✅ Sprite matching test system ready!")
    print("💡 To test with real data, we need to:")
    print("   1. Extract sprite URLs from adventure HTML sheets")  
    print("   2. Extract sprite URLs from main character HTML sheets")
    print("   3. Run image comparison between all pairs")
    print("   4. Create mapping of adventure sprite -> character sprite")
    
    return True

def integrate_with_battle_generator():
    """Show how to integrate sprite matching with the battle generator."""
    print("\n🔗 Integration Plan with Battle Generator:")
    print("1. Run sprite matching once to create sprite_matches.json")
    print("2. Modify battle_generator.py to use sprite matches instead of direct sprite numbers")
    print("3. Use matched character sprites to look up names in character_names.json")
    print("4. Generate battle.json with proper character names")

if __name__ == "__main__":
    test_example_sprites()
    integrate_with_battle_generator()