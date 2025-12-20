# VB Complete Importer

A robust script that creates a complete `monster.json` file from raw VB/DIM dump files, extracting all monster data, evolutions, and sprites automatically.

## Features

- ✅ Creates complete `monster.json` from raw dump files
- ✅ Extracts monster data from character JSON files  
- ✅ Builds evolution trees with proper requirements
- ✅ Generates egg and character sprites automatically
- ✅ OCR character name extraction (optional)
- ✅ Fallback naming when OCR unavailable
- ✅ Proper sprite background removal and formatting

## Requirements

### Core Dependencies (Required)
```bash
pip install Pillow
```

### OCR Dependencies (Optional - for automatic name extraction)
```bash
pip install opencv-python numpy pytesseract
```

**Note**: For pytesseract to work, you need Tesseract OCR installed:
- **Windows**: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **Ubuntu**: `sudo apt install tesseract-ocr`
- **macOS**: `brew install tesseract`

## Directory Structure Expected

The script expects the following folder structure:

```
ROOT_FOLDER (e.g., D:\Digimon\DIMS\SpriteB)
├── DIM_Card_1/
│   ├── data/
│   │   ├── character_00.json
│   │   ├── character_01.json
│   │   └── ...
│   └── sprites/
│       ├── characters/
│       │   ├── character_00/
│       │   │   ├── sprite_00.png (contains character name)
│       │   │   ├── sprite_01.png
│       │   │   └── ...
│       │   └── character_01/
│       └── system/
│           └── other/
│               ├── egg_00.png
│               ├── egg_01.png
│               └── egg_07.png
├── DIM_Card_2/
└── ...
```

## Usage

1. **Configure the script**:
   ```python
   # Edit vb_complete_importer.py
   ROOT_FOLDER = r'D:\Digimon\DIMS\SpriteB'  # Update this path
   ```

2. **Run the script**:
   ```bash
   python vb_complete_importer.py
   ```

3. **Output**:
   - `monster.json` - Complete monster database
   - `monsters/` folder - All generated sprites as ZIP files

## How It Works

### 1. Egg Creation
- Creates stage 0 egg entry for each DIM folder
- Generates egg sprites from `egg_00.png`, `egg_01.png`, `egg_07.png`
- Removes green background and fits to 54x48 canvas

### 2. Character Processing
- Reads all `character_*.json` files in each DIM's data folder
- Extracts character name from `sprite_00.png` using OCR
- Converts character stats from JSON format to monster.json format
- Builds evolution requirements from transformation data

### 3. Sprite Generation
- Creates character sprite ZIP files with mapped sprites:
  ```
  ZIP Index → Sprite File
  0 → sprite_03.png
  1 → sprite_04.png  
  2 → sprite_09.png
  3 → sprite_11.png
  4 → sprite_01.png
  ... (see CHARACTER_SPRITE_MAPPING in code)
  ```

### 4. Evolution Building
- Processes `transformations` for normal evolutions
- Handles `attributeFusions` for Jogress evolutions
- Sets proper requirement ranges and conditions

## Value Conversion

The script handles VB-specific value conversions:

- **65535 → 0**: VB uses 65535 to represent "no value" or 0
- **Small Attack**: `value + 1` (0 if original was 0)
- **Big Attack**: `value + 41` (0 if original was 0)  
- **Attributes**: `1=Vi, 2=Da, 3=Va, other=Free`

## Stage Detection

Stages are auto-detected based on HP values:
- HP = 0: Stage 1 (Baby/Fresh)
- HP ≤ 10: Stage 2 (In-Training)  
- HP ≤ 15: Stage 3 (Rookie)
- HP ≤ 20: Stage 4 (Champion)
- HP ≤ 25: Stage 5 (Ultimate)
- HP > 25: Stage 6 (Mega)

## Testing

Run the test suite to verify everything works:

```bash
python test_vb_complete_importer.py
```

## Troubleshooting

### OCR Issues
- If character names aren't extracted properly, install OCR dependencies
- Check that Tesseract is in your system PATH
- Script will use fallback names (`Character_XX`) if OCR fails

### Missing Files
- Ensure all expected sprite files exist
- Check console output for warnings about missing files
- Script continues processing even if some sprites are missing

### Memory Issues
- Processing many large sprites may use significant memory
- Process folders in batches if needed

## Output Format

The generated `monster.json` follows the same format as existing Omnimon monster files:

```json
{
  "monster": [
    {
      "name": "Example Egg",
      "stage": 0,
      "version": 1,
      "special": false,
      "atk_main": 10,
      "atk_alt": 10,
      "hp": 0,
      "evolve": [...]
    },
    {
      "name": "Character Name",
      "stage": 3,
      "version": 1,
      "hp": 15,
      "star": 3,
      "power": 200,
      "attribute": "Vi",
      "evolve": [
        {
          "to": "Evolution Target",
          "battles": [5, 999999],
          "win_ratio": [60, 100]
        }
      ]
    }
  ]
}
```

## Customization

You can customize the script by modifying:

- `DEFAULT_VALUES_BY_STAGE`: Stage-specific default values
- `CHARACTER_SPRITE_MAPPING`: Sprite file mapping
- Stage detection logic in `create_monster_from_character()`
- OCR configuration in `extract_name_from_sprite()`