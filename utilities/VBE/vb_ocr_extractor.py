#!/usr/bin/env python3
"""
VB OCR Name Extractor - Part 1 of 2
Extracts character names from all sprite files using OCR and saves to JSON for review/editing.
"""

import os
import json
import re
from glob import glob
from PIL import Image

# Required OCR imports for character name extraction
try:
    import cv2
    import numpy as np
    import pytesseract
    
    # Configure tesseract path for Windows
    import platform
    if platform.system() == "Windows":
        # Common Windows installation paths
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.environ.get('USERNAME', 'User'))
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ Found tesseract at: {path}")
                break
        else:
            print("❌ Warning: tesseract.exe not found in common Windows locations")
    
    OCR_AVAILABLE = True
except ImportError:
    print("ERROR: OCR libraries (cv2, numpy, pytesseract) are required for character name extraction.")
    print("Please install them with: pip install opencv-python numpy pytesseract")
    print("Also ensure tesseract-ocr is installed on your system.")
    OCR_AVAILABLE = False

# Configuration
ROOT_FOLDER = r'D:\Digimon\DIMS\Sprites2'
OUTPUT_NAMES_JSON = 'character_names.json'

def extract_name_from_sprite(sprite_path):
    """Extract character name from sprite image using OCR with enhanced Japanese support."""
    if not OCR_AVAILABLE:
        return None
    
    if not os.path.exists(sprite_path):
        return None
    
    try:
        # Load image with PIL
        img = Image.open(sprite_path).convert('RGB')
        img_array = np.array(img)
        
        # Enhance image for better OCR results
        def preprocess_image_for_ocr(img_array):
            """Apply image preprocessing to improve OCR accuracy."""
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Scale up the image for better OCR (3x scaling)
            height, width = gray.shape
            scaled = cv2.resize(gray, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
            
            # Apply Gaussian blur to smooth out pixelation
            blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
            
            # Apply threshold to get clear black text on white background
            # Try different threshold methods
            threshold_methods = [
                cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)[1],
                cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            ]
            
            return threshold_methods
        
        # Try multiple preprocessing approaches
        processed_images = preprocess_image_for_ocr(img_array)
        
        # Also try the original color-based approach for white text
        lower_white = np.array([180, 180, 180])
        upper_white = np.array([255, 255, 255])
        mask = cv2.inRange(img_array, lower_white, upper_white)
        white_text = cv2.bitwise_and(img_array, img_array, mask=mask)
        processed_images.append(cv2.cvtColor(white_text, cv2.COLOR_RGB2GRAY))
        
        # OCR configurations for both English and Japanese
        ocr_configs = [
            # English configurations
            '--psm 8 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
            '--psm 7 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
            '--psm 6 -l eng -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
            
            # Japanese configurations (requires Japanese language pack)
            '--psm 8 -l jpn',
            '--psm 7 -l jpn',
            '--psm 6 -l jpn',
            
            # Mixed language configurations
            '--psm 8 -l eng+jpn',
            '--psm 7 -l eng+jpn',
            
            # Fallback configurations
            '--psm 8',
            '--psm 7',
            '--psm 6'
        ]
        
        best_result = None
        best_confidence = 0
        
        # Try each processed image with each OCR configuration
        for img_processed in processed_images:
            pil_img = Image.fromarray(img_processed)
            
            for config in ocr_configs:
                try:
                    # Try to get OCR data with confidence scores
                    try:
                        ocr_data = pytesseract.image_to_data(pil_img, config=config, output_type=pytesseract.Output.DICT)
                        # Calculate average confidence for words with text
                        confidences = [int(conf) for conf, text in zip(ocr_data['conf'], ocr_data['text']) if text.strip() and int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        
                        # Get the actual text
                        text = pytesseract.image_to_string(pil_img, config=config).strip()
                    except:
                        # Fallback to simple string extraction
                        text = pytesseract.image_to_string(pil_img, config=config).strip()
                        avg_confidence = 50  # Assume medium confidence if we can't get confidence scores
                    
                    if not text:
                        continue
                    
                    # Clean up the text based on detected language
                    if 'jpn' in config:
                        # For Japanese, keep more characters
                        cleaned_text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', text).strip()
                    else:
                        # For English, strict filtering
                        cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
                    
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace
                    
                    # Check if this result is better than previous ones
                    if (cleaned_text and len(cleaned_text) >= 2 and 
                        (avg_confidence > best_confidence or 
                         (avg_confidence == best_confidence and len(cleaned_text) > len(best_result or '')))):
                        best_result = cleaned_text
                        best_confidence = avg_confidence
                        
                except Exception:
                    # Continue trying other configurations
                    continue
        
        return best_result, best_confidence if best_result else (None, 0)
        
    except Exception as e:
        print(f"Error processing sprite {sprite_path}: {e}")
        return None, 0

def find_character_sprites(sprites_folder):
    """Find all character sprite files in the sprites folder."""
    character_sprites = []
    characters_folder = os.path.join(sprites_folder, 'characters')
    
    if not os.path.exists(characters_folder):
        return character_sprites
    
    # Find all character_XX folders
    for char_folder in os.listdir(characters_folder):
        if char_folder.startswith('character_'):
            # Extract character number
            match = re.search(r'character_(\d+)$', char_folder)
            if match:
                char_number = int(match.group(1))
                sprite_path = os.path.join(characters_folder, char_folder, 'sprite_00.png')
                if os.path.exists(sprite_path):
                    character_sprites.append({
                        'character_number': char_number,
                        'sprite_path': sprite_path
                    })
    
    # Sort by character number
    return sorted(character_sprites, key=lambda x: x['character_number'])

def process_folder_ocr(folder_path):
    """Process OCR for a single folder and return character names."""
    folder_name = os.path.basename(folder_path)
    sprites_folder = os.path.join(folder_path, 'sprites')
    
    print(f"Processing OCR for folder: {folder_name}")
    
    if not os.path.exists(sprites_folder):
        print(f"  ⚠️  Sprites folder not found: {sprites_folder}")
        return []
    
    character_sprites = find_character_sprites(sprites_folder)
    if not character_sprites:
        print(f"  ⚠️  No character sprites found in {folder_name}")
        return []
    
    results = []
    for sprite_info in character_sprites:
        char_number = sprite_info['character_number']
        sprite_path = sprite_info['sprite_path']
        
        print(f"  🔍 Processing character {char_number:02d}...", end=' ')
        
        name, confidence = extract_name_from_sprite(sprite_path)
        
        if name:
            print(f"✅ '{name}' (confidence: {confidence:.1f})")
        else:
            print(f"❌ No name extracted")
        
        results.append({
            'character_number': char_number,
            'extracted_name': name,
            'confidence': confidence,
            'sprite_path': sprite_path
        })
    
    return results

def main():
    """Main function to extract all character names using OCR."""
    print("VB OCR Name Extractor - Part 1 of 2")
    print("=" * 50)
    
    # Check OCR availability first
    if not OCR_AVAILABLE:
        print("❌ OCR libraries are not available. Character name extraction requires:")
        print("   • pip install opencv-python numpy pytesseract")
        print("   • tesseract-ocr system installation")
        return 1
    
    print("✅ OCR libraries available for character name extraction")
    print()
    
    if not os.path.exists(ROOT_FOLDER):
        print(f"❌ Root folder not found: {ROOT_FOLDER}")
        print(f"Please update ROOT_FOLDER in the script to point to your data directory.")
        return 1
    
    # Get script directory for output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_json_path = os.path.join(script_dir, OUTPUT_NAMES_JSON)
    
    print(f"📁 Source: {ROOT_FOLDER}")
    print(f"📄 Output Names JSON: {output_json_path}")
    print()
    
    all_character_data = []
    
    try:
        # Get all subfolders
        folders = [f for f in os.listdir(ROOT_FOLDER) if os.path.isdir(os.path.join(ROOT_FOLDER, f))]
        folders.sort()
        
        if not folders:
            print("❌ No subfolders found in ROOT_FOLDER")
            return 1
        
        print(f"Found {len(folders)} folders to process:")
        for i, folder in enumerate(folders, 1):
            print(f"  {i}. {folder}")
        print()
        
        total_characters = 0
        successful_extractions = 0
        
        for folder in folders:
            try:
                folder_path = os.path.join(ROOT_FOLDER, folder)
                character_results = process_folder_ocr(folder_path)
                
                for result in character_results:
                    character_data = {
                        'folder_name': folder,
                        'character_number': result['character_number'],
                        'extracted_name': result['extracted_name'],
                        'confidence': result['confidence'],
                        'sprite_path': result['sprite_path'],
                        'manual_name': result['extracted_name'],  # This field can be manually edited
                        'status': 'extracted' if result['extracted_name'] else 'failed'
                    }
                    all_character_data.append(character_data)
                    total_characters += 1
                    if result['extracted_name']:
                        successful_extractions += 1
                
                print(f"✅ {folder}: Processed {len(character_results)} characters")
                
            except Exception as e:
                print(f"❌ Error processing {folder}: {e}")
                continue
        
        if not all_character_data:
            print("❌ No character data was extracted.")
            return 1
        
        # Save results to JSON
        output_data = {
            'extraction_info': {
                'total_folders': len(folders),
                'total_characters': total_characters,
                'successful_extractions': successful_extractions,
                'failed_extractions': total_characters - successful_extractions,
                'success_rate': f"{(successful_extractions/total_characters*100):.1f}%" if total_characters > 0 else "0%"
            },
            'characters': all_character_data
        }
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ OCR extraction complete!")
        print(f"📊 Summary:")
        print(f"   • Total folders processed: {len(folders)}")
        print(f"   • Total characters found: {total_characters}")
        print(f"   • Successful extractions: {successful_extractions}")
        print(f"   • Failed extractions: {total_characters - successful_extractions}")
        print(f"   • Success rate: {(successful_extractions/total_characters*100):.1f}%")
        print(f"   • Character names JSON: {output_json_path}")
        print()
        print("📝 Next steps:")
        print(f"   1. Review and edit the character names in: {output_json_path}")
        print(f"   2. Fix any failed extractions by editing the 'manual_name' field")
        print(f"   3. Run vb_sprite_builder.py to generate sprites and monster.json")
        
        return 0
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())