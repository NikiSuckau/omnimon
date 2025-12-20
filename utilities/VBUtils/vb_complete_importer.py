import os
import json
import re
import zipfile
from PIL import Image
from glob import glob

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
ROOT_FOLDER = r'D:\Digimon\DIMS\SpriteB'
OUTPUT_MONSTER_JSON = 'monster.json'
OUTPUT_SPRITES_FOLDER = 'monsters'

# Default values by stage (from PetTemplates.cs and existing monster.json)
DEFAULT_VALUES_BY_STAGE = {
    0: {
        "time": 1, "poop_timer": 0, "energy": 0, "min_weight": 99, "evol_weight": 0,
        "stomach": 0, "hunger_loss": 0, "strength_loss": 0, "heal_doses": 100,
        "condition_hearts": 0, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": None, "wakes": None
    },
    1: {
        "time": 10, "poop_timer": 3, "energy": 0, "min_weight": 5, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 3, "strength_loss": 3, "heal_doses": 1,
        "condition_hearts": 1, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    2: {
        "time": 720, "poop_timer": 60, "energy": 0, "min_weight": 10, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 30, "strength_loss": 30, "heal_doses": 1,
        "condition_hearts": 2, "jogress_avaliable": False, "hp": 0, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    3: {
        "time": 1440, "poop_timer": 120, "energy": 20, "min_weight": 20, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 48, "strength_loss": 48, "heal_doses": 1,
        "condition_hearts": 3, "jogress_avaliable": False, "hp": 10, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    4: {
        "time": 2160, "poop_timer": 120, "energy": 30, "min_weight": 30, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 12, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    5: {
        "time": 2400, "poop_timer": 120, "energy": 40, "min_weight": 40, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": True, "hp": 15, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    6: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 18, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    },
    7: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 20, "star": 0,
        "attack": 0, "critical_turn": 0, "sleeps": "21:00", "wakes": "09:00"
    }
}

# Character sprite mapping (zip_file_index -> sprite_file_number)
CHARACTER_SPRITE_MAPPING = {
    0: 3, 1: 4, 2: 9, 3: 11, 4: 1, 5: 11, 6: 1, 7: 11, 8: 1, 9: 9, 10: 1, 11: 10, 12: 10, 13: 10, 14: 10
}

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

def extract_int(d, keys):
    """Extract integer value from dictionary using multiple possible keys."""
    for k in keys:
        if k in d:
            try:
                return int(d[k])
            except Exception:
                try:
                    return int(float(d[k]))
                except Exception:
                    pass
    return None

def normalize_value(v):
    """Normalize values coming from character files: 65535 means 0 in our system."""
    if v is None:
        return None
    try:
        iv = int(v)
    except Exception:
        return None
    return 0 if iv == 65535 else iv

def convert_small_attack(v):
    """Convert smallAttack to atk_main: 65535 -> 0, else value+1"""
    nv = normalize_value(v)
    if nv is None:
        return None
    return 0 if nv == 0 else nv + 1

def convert_big_attack(v):
    """Convert bigAttack to atk_alt: 65535 -> 0, else value+1+40 (i.e. +41)"""
    nv = normalize_value(v)
    if nv is None:
        return None
    return 0 if nv == 0 else nv + 41

def get_attribute_string(attr_num):
    """Convert attribute number to string."""
    attr_map = {1: 'Vi', 2: 'Da', 3: 'Va'}
    return attr_map.get(attr_num, '')

def find_character_files(data_folder):
    """Find all character_*.json files in the data folder."""
    pattern = os.path.join(data_folder, 'character_*.json')
    files = glob(pattern)
    # Sort by the numeric suffix
    def keyfn(p):
        m = re.search(r'character_(\d+)\.json$', p)
        return int(m.group(1)) if m else 999
    return sorted(files, key=keyfn)

def extract_name_from_sprite(sprite_path):
    """Extract character name from sprite image using OCR with enhanced Japanese support. Returns None if OCR fails."""
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR libraries are required but not available. Please install opencv-python, numpy, and pytesseract.")
    
    if not os.path.exists(sprite_path):
        print(f"Sprite file not found: {sprite_path}")
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
                        
                except Exception as ocr_error:
                    # Continue trying other configurations
                    continue
        
        if best_result:
            print(f"OCR extracted name: '{best_result}' (confidence: {best_confidence:.1f}) from {sprite_path}")
            return best_result
        
        print(f"OCR could not extract name from {sprite_path}")
        return None
        
    except Exception as e:
        print(f"Error processing sprite {sprite_path}: {e}")
        return None

def create_egg_monster(folder_name, version):
    """Create egg monster entry."""
    defaults = DEFAULT_VALUES_BY_STAGE[0]
    
    return {
        "name": folder_name,
        "stage": 0,
        "version": version,
        "special": False,
        "special_key": "",
        "atk_main": 10,
        "atk_alt": 10,
        **defaults,
        "evolve": []
    }

def process_egg_sprites(folder_name, sprites_folder, output_folder):
    """Process egg sprites similar to vb_egg_maker."""
    sprite_dir = os.path.join(sprites_folder, 'system', 'other')
    egg_files = ['egg_00.png', 'egg_01.png', 'egg_07.png']
    output_images = []
    
    for idx, egg_file in enumerate(egg_files):
        egg_path = os.path.join(sprite_dir, egg_file)
        if not os.path.exists(egg_path):
            output_images.append(None)
            continue
            
        try:
            img = Image.open(egg_path).convert('RGBA')
            datas = img.getdata()
            newData = []
            
            # Remove green background (0,255,0)
            for item in datas:
                if item[0] == 0 and item[1] == 255 and item[2] == 0:
                    newData.append((0, 0, 0, 0))
                else:
                    newData.append(item)
            
            img.putdata(newData)
            
            # Create new 54x48 canvas
            canvas = Image.new('RGBA', (54, 48), (0, 0, 0, 0))
            
            # Center horizontally, bottom align
            x = (54 - img.width) // 2
            y = 48 - img.height
            canvas.paste(img, (x, y), img)
            
            output_images.append(canvas)
            
        except Exception as e:
            print(f"Error processing egg sprite {egg_file}: {e}")
            output_images.append(None)
    
    # Save images as 0.png, 1.png, 2.png in a zip
    zip_name = f"{folder_name}_dmc.zip"
    zip_path = os.path.join(output_folder, zip_name)
    
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for idx, img in enumerate(output_images):
                if img:
                    temp_path = os.path.join(output_folder, f"temp_{folder_name}_{idx}.png")
                    img.save(temp_path)
                    zipf.write(temp_path, arcname=f"{idx}.png")
                    os.remove(temp_path)
        print(f"Created egg sprite: {zip_name}")
    except Exception as e:
        print(f"Error creating egg sprite zip {zip_name}: {e}")

def process_character_sprites(char_name, char_number, sprites_folder, output_folder):
    """Process character sprites using the mapping with background removal."""
    char_sprite_dir = os.path.join(sprites_folder, 'characters', f'character_{char_number:02d}')
    
    if not os.path.exists(char_sprite_dir):
        print(f"Character sprite directory not found: {char_sprite_dir}")
        return
    
    zip_name = f"{char_name}_dmc.zip"
    zip_path = os.path.join(output_folder, zip_name)
    
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for zip_idx, sprite_num in CHARACTER_SPRITE_MAPPING.items():
                sprite_file = f"sprite_{sprite_num:02d}.png"
                sprite_path = os.path.join(char_sprite_dir, sprite_file)
                
                if os.path.exists(sprite_path):
                    try:
                        # Load and process the sprite (remove green background)
                        img = Image.open(sprite_path).convert('RGBA')
                        datas = img.getdata()
                        newData = []
                        
                        # Remove green background (0,255,0)
                        for item in datas:
                            if item[0] == 0 and item[1] == 255 and item[2] == 0:
                                newData.append((0, 0, 0, 0))
                            else:
                                newData.append(item)
                        
                        img.putdata(newData)
                        
                        # Save processed sprite to temp file, then add to zip
                        temp_path = os.path.join(output_folder, f"temp_{char_name}_{zip_idx}.png")
                        img.save(temp_path)
                        zipf.write(temp_path, arcname=f"{zip_idx}.png")
                        os.remove(temp_path)
                        
                    except Exception as e:
                        print(f"Error processing sprite {sprite_path}: {e}")
                        # Fallback: use original file
                        zipf.write(sprite_path, arcname=f"{zip_idx}.png")
                else:
                    print(f"Warning: Sprite file not found: {sprite_path}")
        
        print(f"Created character sprite: {zip_name}")
    except Exception as e:
        print(f"Error creating character sprite zip {zip_name}: {e}")

def build_evolutions(char_data, file_idx_to_name, current_stage=3):
    """Build evolution data from character JSON."""
    evolutions = []
    
    # Attribute mapping
    attr_map = {1: 'Vi', 2: 'Da', 3: 'Va', 4: 'Free'}
    fusion_keys = ['type1', 'type2', 'type3', 'type4']
    
    # Transformations
    for t in char_data.get('transformations', []):
        tgt_idx = t.get('evolveTo')
        tgt_name = file_idx_to_name.get(tgt_idx)
        if not tgt_name:
            continue
            
        battles = t.get('battlesRequirement', 0)
        win_ratio = t.get('winRatioRequirement', 0)
        trophies = t.get('ppRequirement', 0)
        vital_values = t.get('vitalityRequirement', 0)
        
        evo = {"to": tgt_name}
        
        # Only include conditions with nonzero minimums
        if battles != 0:
            evo["battles"] = [battles, 999999]
        if win_ratio != 0:
            evo["win_ratio"] = [win_ratio, 100]
        if trophies != 0:
            evo["trophies"] = [trophies, 999999]
        if vital_values != 0:
            evo["vital_values"] = [vital_values, 999999]
            
        evolutions.append(evo)
    
    # AttributeFusions (Jogress)
    fusions = char_data.get('attributeFusions', {})
    for i, k in enumerate(fusion_keys):
        tgt_idx = fusions.get(k)
        if tgt_idx is None or tgt_idx == 0:
            continue
            
        tgt_name = file_idx_to_name.get(tgt_idx)
        if not tgt_name:
            continue
            
        evo = {
            "to": tgt_name,
            "stage": current_stage,
            "attribute": attr_map.get(i+1),
            "jogress": "PenC"
        }
        evolutions.append(evo)
    
    return evolutions

def create_monster_from_character(char_data, char_number, char_name, version, file_idx_to_name, monsters):
    """Create monster entry from character JSON data."""
    # Extract basic stats
    hp = extract_int(char_data, ['hp', 'HP'])
    star = extract_int(char_data, ['stars', 'star', 'Stars'])
    power = extract_int(char_data, ['bp', 'BP', 'power'])
    attribute_num = extract_int(char_data, ['attribute', 'Attribute'])
    
    # Convert attacks
    raw_small = extract_int(char_data, ['smallAttack', 'small_attack', 'smallAtk', 'small'])
    raw_big = extract_int(char_data, ['bigAttack', 'big_attack', 'bigAtk', 'big'])
    ap = extract_int(char_data, ['ap', 'AP', 'attack'])
    
    # Normalize values
    hp = normalize_value(hp) if hp is not None else 0
    star = normalize_value(star) if star is not None else 0
    power = normalize_value(power) if power is not None else 0
    atk_main = convert_small_attack(raw_small) if raw_small is not None else 0
    atk_alt = convert_big_attack(raw_big) if raw_big is not None else 0
    attack = normalize_value(ap) if ap is not None else 0
    
    # Determine stage based on stats (rough estimation)
    if hp == 0 and power == 0:
        stage = 1  # Baby/Fresh
    elif hp <= 10:
        stage = 2  # In-Training
    elif hp <= 15:
        stage = 3  # Rookie
    elif hp <= 20:
        stage = 4  # Champion
    elif hp <= 25:
        stage = 5  # Ultimate
    else:
        stage = 6  # Mega
    
    # Get defaults for the stage
    defaults = DEFAULT_VALUES_BY_STAGE.get(stage, DEFAULT_VALUES_BY_STAGE[3])
    
    # Build evolutions
    evolutions = build_evolutions(char_data, file_idx_to_name, stage)
    
    monster = {
        "name": char_name,
        "stage": stage,
        "version": version,
        "special": False,
        "special_key": "",
        "atk_main": atk_main,
        "atk_alt": atk_alt,
        "hp": hp,
        "star": star,
        "power": power,
        "attack": attack,
        "attribute": get_attribute_string(attribute_num),
        "evolve": evolutions,
        **{k: v for k, v in defaults.items() if k not in ['hp', 'star', 'attack']}
    }
    
    return monster

def process_folder(folder_path, version, output_sprites_folder):
    """Process a single folder (DIM card)."""
    folder_name = os.path.basename(folder_path)
    data_folder = os.path.join(folder_path, 'data')
    sprites_folder = os.path.join(folder_path, 'sprites')
    
    print(f"Processing folder: {folder_name} (Version {version})")
    
    monsters = []
    
    # 2.1 Create egg monster
    egg_monster = create_egg_monster(folder_name, version)
    monsters.append(egg_monster)
    
    # 2.2 Create egg sprite
    process_egg_sprites(folder_name, sprites_folder, output_sprites_folder)
    
    # 2.3 Process character files
    if not os.path.exists(data_folder):
        print(f"Data folder not found: {data_folder}")
        return monsters
    
    char_files = find_character_files(data_folder)
    file_idx_to_name = {}
    
    # First pass: extract names and build mapping
    for char_file in char_files:
        match = re.search(r'character_(\d+)\.json$', char_file)
        if not match:
            continue
            
        char_number = int(match.group(1))
        char_data = load_json(char_file)
        
        if char_data is None:
            continue
        
        # 2.4 Extract character name from sprite using OCR (required)
        sprite_path = os.path.join(sprites_folder, 'characters', f'character_{char_number:02d}', 'sprite_00.png')
        char_name = extract_name_from_sprite(sprite_path)
        
        if not char_name:
            print(f"❌ CRITICAL: Could not extract character name from sprite {sprite_path}")
            print(f"   Character names are required for proper monster.json generation.")
            print(f"   Skipping character {char_number:02d} in folder {folder_name}")
            continue
        
        # Clean the name for file system compatibility (preserve Japanese characters)
        char_name = re.sub(r'[<>:"/\\|?*]', '_', char_name)
        char_name = char_name.strip()
        
        # Ensure the name is valid for file systems but preserve Unicode characters
        if not char_name or len(char_name) < 1:
            print(f"⚠️  Warning: Empty name after cleaning for character {char_number:02d}, using fallback")
            char_name = f"Character_{char_number:02d}"
        
        file_idx_to_name[char_number] = char_name
    
    # Second pass: create monsters with proper evolution links
    for char_file in char_files:
        match = re.search(r'character_(\d+)\.json$', char_file)
        if not match:
            continue
            
        char_number = int(match.group(1))
        char_data = load_json(char_file)
        
        if char_data is None:
            continue
        
        char_name = file_idx_to_name.get(char_number)
        if not char_name:
            continue
        
        # Create monster entry
        monster = create_monster_from_character(char_data, char_number, char_name, version, file_idx_to_name, monsters)
        monsters.append(monster)
        
        # 2.5 Create character sprite
        process_character_sprites(char_name, char_number, sprites_folder, output_sprites_folder)
    
    return monsters

def main():
    """Main function to process all folders and create monster.json."""
    print("VB Complete Importer")
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
    output_json_path = os.path.join(script_dir, OUTPUT_MONSTER_JSON)
    output_sprites_folder = os.path.join(script_dir, OUTPUT_SPRITES_FOLDER)
    
    print(f"📁 Source: {ROOT_FOLDER}")
    print(f"📄 Output JSON: {output_json_path}")
    print(f"🎨 Output Sprites: {output_sprites_folder}")
    print()
    
    all_monsters = []
    version = 1
    processed_folders = 0
    
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
        
        for folder in folders:
            try:
                print(f"Processing {folder}...")
                folder_path = os.path.join(ROOT_FOLDER, folder)
                monsters = process_folder(folder_path, version, output_sprites_folder)
                all_monsters.extend(monsters)
                processed_folders += 1
                print(f"✅ {folder}: Created {len(monsters)} entries")
                version += 1
            except Exception as e:
                print(f"❌ Error processing {folder}: {e}")
                continue
        
        if not all_monsters:
            print("❌ No monsters were created. Check your data structure and file formats.")
            return 1
        
        # Create final monster.json
        monster_data = {"monster": all_monsters}
        
        try:
            save_json(output_json_path, monster_data)
            print(f"\n✅ Processing complete!")
            print(f"📊 Summary:")
            print(f"   • Processed folders: {processed_folders}/{len(folders)}")
            print(f"   • Total monsters: {len(all_monsters)}")
            print(f"   • Monster data: {output_json_path}")
            print(f"   • Sprites folder: {output_sprites_folder}")
            
            # Show breakdown by version
            version_counts = {}
            for monster in all_monsters:
                v = monster.get('version', 1)
                version_counts[v] = version_counts.get(v, 0) + 1
            
            print(f"\n📈 Breakdown by version:")
            for v in sorted(version_counts.keys()):
                print(f"   Version {v}: {version_counts[v]} monsters")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error saving monster.json: {e}")
            return 1
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())