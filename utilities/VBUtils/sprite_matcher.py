#!/usr/bin/env python3
"""
Sprite Matcher for Battle Generator
Compares sprites from adventure sheets with main character sheets using image similarity.
Handles different sizes and scaling while finding matching characters.
"""

import cv2
import numpy as np
import requests
from urllib.parse import urljoin, urlparse
import os
import json
from PIL import Image
import imagehash
from skimage.metrics import structural_similarity as ssim
import hashlib

def download_image(url, cache_dir="sprite_cache"):
    """Download and cache an image from URL."""
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Create filename from URL hash
    url_hash = hashlib.md5(url.encode()).hexdigest()
    filename = f"{url_hash}.png"
    filepath = os.path.join(cache_dir, filename)
    
    # Return cached version if exists
    if os.path.exists(filepath):
        return filepath
    
    try:
        # Download image
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save to cache
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return None

def preprocess_sprite(image_path):
    """Preprocess sprite for comparison - normalize size, remove background, etc."""
    try:
        # Load image
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
        
        # Convert to RGBA if needed
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
        
        # Remove transparent/white background
        # Create mask for non-transparent pixels
        alpha_channel = img[:, :, 3]
        mask = alpha_channel > 50  # Threshold for transparency
        
        # Find bounding box of non-transparent content
        coords = np.column_stack(np.where(mask))
        if len(coords) == 0:
            return None
            
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Crop to content
        cropped = img[y_min:y_max+1, x_min:x_max+1]
        
        # Resize to standard size for comparison (64x64)
        resized = cv2.resize(cropped, (64, 64), interpolation=cv2.INTER_LANCZOS4)
        
        # Convert to grayscale for some comparisons
        gray = cv2.cvtColor(resized, cv2.COLOR_RGBA2GRAY)
        
        return {
            'original': img,
            'cropped': cropped,
            'resized': resized,
            'gray': gray,
            'path': image_path
        }
        
    except Exception as e:
        print(f"❌ Error preprocessing {image_path}: {e}")
        return None

def calculate_image_similarity(sprite1, sprite2):
    """Calculate similarity between two preprocessed sprites using multiple methods."""
    if sprite1 is None or sprite2 is None:
        return 0.0
    
    similarities = []
    
    try:
        # Method 1: Structural Similarity (SSIM)
        ssim_score = ssim(sprite1['gray'], sprite2['gray'])
        similarities.append(('ssim', ssim_score))
        
        # Method 2: Perceptual Hash (using PIL)
        pil1 = Image.fromarray(cv2.cvtColor(sprite1['resized'], cv2.COLOR_RGBA2RGB))
        pil2 = Image.fromarray(cv2.cvtColor(sprite2['resized'], cv2.COLOR_RGBA2RGB))
        
        hash1 = imagehash.phash(pil1)
        hash2 = imagehash.phash(pil2)
        hash_similarity = 1 - (hash1 - hash2) / len(hash1.hash) ** 2
        similarities.append(('phash', hash_similarity))
        
        # Method 3: Template Matching
        result = cv2.matchTemplate(sprite1['gray'], sprite2['gray'], cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        similarities.append(('template', max_val))
        
        # Method 4: Histogram Comparison
        hist1 = cv2.calcHist([sprite1['resized']], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([sprite2['resized']], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        similarities.append(('histogram', hist_similarity))
        
        # Weighted average of similarities
        weights = {
            'ssim': 0.4,      # Structural similarity is most important
            'phash': 0.3,     # Perceptual hash good for scaled images
            'template': 0.2,  # Template matching
            'histogram': 0.1  # Color similarity
        }
        
        weighted_score = sum(weights[method] * score for method, score in similarities)
        
        return weighted_score, dict(similarities)
        
    except Exception as e:
        print(f"❌ Error calculating similarity: {e}")
        return 0.0, {}

def extract_sprite_urls_from_html(soup, base_url=""):
    """Extract all sprite URLs from HTML soup."""
    sprite_urls = {}
    
    # Find all images with unnamed pattern
    images = soup.find_all('img')
    for img in images:
        src = img.get('src', '')
        if 'unnamed(' in src:
            # Extract sprite number
            import re
            match = re.search(r'unnamed\((\d+)\)\.png', src)
            if match:
                sprite_num = int(match.group(1))
                # Convert relative URL to absolute if needed
                if base_url and not src.startswith('http'):
                    full_url = urljoin(base_url, src)
                else:
                    full_url = src
                sprite_urls[sprite_num] = full_url
    
    return sprite_urls

def match_adventure_to_character_sprites(adventure_urls, character_urls, similarity_threshold=0.7):
    """Match adventure sheet sprites to main character sheet sprites."""
    print(f"🔍 Matching {len(adventure_urls)} adventure sprites to {len(character_urls)} character sprites...")
    
    matches = {}
    processed_adventure = {}
    processed_character = {}
    
    # Preprocess all adventure sprites
    print("📥 Preprocessing adventure sprites...")
    for sprite_num, url in adventure_urls.items():
        image_path = download_image(url)
        if image_path:
            processed = preprocess_sprite(image_path)
            if processed:
                processed_adventure[sprite_num] = processed
    
    # Preprocess all character sprites  
    print("📥 Preprocessing character sprites...")
    for sprite_num, url in character_urls.items():
        image_path = download_image(url)
        if image_path:
            processed = preprocess_sprite(image_path)
            if processed:
                processed_character[sprite_num] = processed
    
    print(f"✅ Preprocessed {len(processed_adventure)} adventure and {len(processed_character)} character sprites")
    
    # Compare each adventure sprite against all character sprites
    for adv_num, adv_sprite in processed_adventure.items():
        print(f"🔍 Matching adventure sprite {adv_num}...")
        
        best_match = None
        best_score = 0
        best_details = {}
        
        for char_num, char_sprite in processed_character.items():
            score, details = calculate_image_similarity(adv_sprite, char_sprite)
            
            if score > best_score:
                best_score = score
                best_match = char_num
                best_details = details
        
        # Only accept matches above threshold
        if best_score >= similarity_threshold:
            matches[adv_num] = {
                'character_sprite': best_match,
                'similarity_score': best_score,
                'details': best_details
            }
            print(f"  ✅ Adventure {adv_num} -> Character {best_match} (score: {best_score:.3f})")
        else:
            print(f"  ❌ Adventure {adv_num} -> No match found (best: {best_score:.3f})")
    
    return matches

def save_sprite_matches(matches, filename="sprite_matches.json"):
    """Save sprite matches to JSON file."""
    with open(filename, 'w') as f:
        json.dump(matches, f, indent=2)
    print(f"💾 Saved {len(matches)} sprite matches to {filename}")

def load_sprite_matches(filename="sprite_matches.json"):
    """Load sprite matches from JSON file."""
    try:
        with open(filename, 'r') as f:
            matches = json.load(f)
        print(f"📂 Loaded {len(matches)} sprite matches from {filename}")
        return matches
    except FileNotFoundError:
        print(f"❌ No sprite matches file found: {filename}")
        return {}

def main():
    """Main function to test sprite matching."""
    print("🎯 Sprite Matcher - Testing Image Similarity")
    
    # For testing, we can use the example images you provided
    # This would be expanded to work with the HTML sheets
    
    print("✅ Sprite matching system ready!")
    print("💡 To use: call match_adventure_to_character_sprites() with sprite URLs")

if __name__ == "__main__":
    main()