#!/usr/bin/env python3
"""
VB Complete Importer - Summary and Setup Guide
"""

import os
import sys

def check_dependencies():
    """Check which dependencies are available."""
    print("Checking dependencies...\n")
    
    # Core dependencies
    try:
        from PIL import Image
        print("✅ Pillow (PIL) - Available")
    except ImportError:
        print("❌ Pillow (PIL) - REQUIRED - Install with: pip install Pillow")
        return False
    
    # Optional OCR dependencies
    ocr_available = True
    try:
        import cv2
        print("✅ OpenCV (cv2) - Available")
    except ImportError:
        print("⚠️  OpenCV (cv2) - Optional - Install with: pip install opencv-python")
        ocr_available = False
    
    try:
        import numpy as np
        print("✅ NumPy - Available") 
    except ImportError:
        print("⚠️  NumPy - Optional - Install with: pip install numpy")
        ocr_available = False
    
    try:
        import pytesseract
        print("✅ PyTesseract - Available")
    except ImportError:
        print("⚠️  PyTesseract - Optional - Install with: pip install pytesseract")
        ocr_available = False
    
    if ocr_available:
        print("\n🎯 OCR capabilities: FULL (automatic character name extraction)")
    else:
        print("\n⚠️  OCR capabilities: LIMITED (will use fallback character names)")
    
    return True

def show_file_structure():
    """Show the expected file structure."""
    print("\nExpected Data Structure:")
    print("=" * 50)
    print("""
ROOT_FOLDER/
├── DIM_Card_1/
│   ├── data/
│   │   ├── character_00.json  ← Character stats and evolution data
│   │   ├── character_01.json
│   │   └── ...
│   └── sprites/
│       ├── characters/
│       │   ├── character_00/
│       │   │   ├── sprite_00.png  ← Contains character name (OCR)
│       │   │   ├── sprite_01.png  ← Used for character sprites
│       │   │   ├── sprite_03.png  ← Mapped to ZIP index 0
│       │   │   ├── sprite_04.png  ← Mapped to ZIP index 1
│       │   │   └── ...
│       │   └── character_01/
│       └── system/
│           └── other/
│               ├── egg_00.png  ← Egg sprite frame 0
│               ├── egg_01.png  ← Egg sprite frame 1
│               └── egg_07.png  ← Egg sprite frame 2
├── DIM_Card_2/
└── ...
    """)

def show_conversion_rules():
    """Show the data conversion rules."""
    print("Data Conversion Rules:")
    print("=" * 50)
    print("""
VB JSON → Monster JSON Mapping:

• hp → hp (normalized: 65535 → 0)
• stars/star → star (normalized: 65535 → 0)  
• bp/BP/power → power (normalized: 65535 → 0)
• attribute → attribute (1=Vi, 2=Da, 3=Va, other=Free)
• smallAttack → atk_main (65535→0, else value+1)
• bigAttack → atk_alt (65535→0, else value+41)
• ap/AP/attack → attack (normalized: 65535 → 0)

Evolution Data:
• transformations → normal evolutions with requirements
• attributeFusions → Jogress evolutions with attribute matching

Stage Detection (based on HP):
• HP = 0: Stage 1 (Baby/Fresh)
• HP ≤ 10: Stage 2 (In-Training)
• HP ≤ 15: Stage 3 (Rookie) 
• HP ≤ 20: Stage 4 (Champion)
• HP ≤ 25: Stage 5 (Ultimate)
• HP > 25: Stage 6 (Mega)
    """)

def show_sprite_mapping():
    """Show the sprite file mapping."""
    print("Character Sprite Mapping:")
    print("=" * 50)
    print("""
ZIP File Index → Source Sprite File
0  → sprite_03.png
1  → sprite_04.png
2  → sprite_09.png
3  → sprite_11.png
4  → sprite_01.png
5  → sprite_11.png
6  → sprite_01.png
7  → sprite_11.png
8  → sprite_01.png
9  → sprite_09.png
10 → sprite_01.png
11 → sprite_10.png
12 → sprite_10.png
13 → sprite_10.png
14 → sprite_10.png

Egg Sprites: egg_00.png, egg_01.png, egg_07.png → 0.png, 1.png, 2.png
All sprites get green background removed and fit to proper canvas size.
    """)

def show_usage_instructions():
    """Show usage instructions."""
    print("Usage Instructions:")
    print("=" * 50)
    print("""
1. Setup:
   • Ensure Pillow is installed: pip install Pillow
   • (Optional) Install OCR: pip install opencv-python numpy pytesseract
   • For Tesseract OCR: Install from https://github.com/UB-Mannheim/tesseract/wiki

2. Configuration:
   • Edit vb_complete_importer.py
   • Update ROOT_FOLDER = r'YOUR_PATH_HERE'
   • Default: ROOT_FOLDER = r'D:\\Digimon\\DIMS\\SpriteB'

3. Run:
   • python vb_complete_importer.py
   
4. Output:
   • monster.json - Complete monster database
   • monsters/ - Folder with all sprite ZIP files

5. Testing:
   • python test_vb_complete_importer.py - Run unit tests
   • python demo_vb_complete_importer.py - See sample output
    """)

def main():
    """Main function to show complete setup guide."""
    print("VB Complete Importer - Setup Guide")
    print("=" * 60)
    print()
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n❌ Please install required dependencies before proceeding.")
        return 1
    
    show_file_structure()
    show_conversion_rules()
    show_sprite_mapping()
    show_usage_instructions()
    
    print("\nFiles in this package:")
    print("=" * 50)
    
    files = [
        ("vb_complete_importer.py", "Main script - processes VB dump files"),
        ("test_vb_complete_importer.py", "Unit tests for validation"),
        ("demo_vb_complete_importer.py", "Demo showing expected output"),
        ("requirements.txt", "Dependency list"),
        ("README_VB_Complete_Importer.md", "Detailed documentation"),
        ("vb_complete_importer_setup.py", "This setup guide")
    ]
    
    for filename, description in files:
        if os.path.exists(filename):
            print(f"✅ {filename:30} - {description}")
        else:
            print(f"❌ {filename:30} - {description}")
    
    print(f"\n🎯 Ready to process VB dump files!")
    print(f"📁 Update ROOT_FOLDER in vb_complete_importer.py to your data path")
    print(f"▶️  Run: python vb_complete_importer.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())