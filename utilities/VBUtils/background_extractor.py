#!/usr/bin/env python3
"""
Background Extractor for VB Utils
Extracts background images from DIM folders and renames them consistently.
"""

import os
import shutil
import json
from pathlib import Path

def load_character_names():
    """Load character names JSON to get all DIM folder names."""
    try:
        with open('character_names.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract unique folder names
        folder_names = set()
        for char in data.get('characters', []):
            folder_name = char.get('folder_name')
            if folder_name:
                folder_names.add(folder_name)
        
        return sorted(list(folder_names))
    except Exception as e:
        print(f"❌ Error loading character_names.json: {e}")
        return []

def find_background_images(base_path, folder_names):
    """Find background images in each DIM folder."""
    print(f"🔍 Searching for background images in {len(folder_names)} folders...")
    
    backgrounds = {}
    missing_folders = []
    
    for folder_name in folder_names:
        # Construct path to background folder
        background_path = Path(base_path) / folder_name / "sprites" / "system" / "backgrounds"
        
        if background_path.exists():
            # Look for image files in the background folder
            image_files = []
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']:
                image_files.extend(background_path.glob(ext))
            
            if image_files:
                backgrounds[folder_name] = image_files
                print(f"  ✅ {folder_name}: Found {len(image_files)} background image(s)")
                for img in image_files:
                    print(f"    📄 {img.name}")
            else:
                print(f"  ⚠️  {folder_name}: Background folder exists but no images found")
        else:
            missing_folders.append(folder_name)
            print(f"  ❌ {folder_name}: Background path not found")
    
    if missing_folders:
        print(f"\n⚠️  Missing background folders ({len(missing_folders)}):")
        for folder in missing_folders[:10]:  # Show first 10
            print(f"    - {folder}")
        if len(missing_folders) > 10:
            print(f"    ... and {len(missing_folders) - 10} more")
    
    return backgrounds

def create_output_folder():
    """Create the backgrounds output folder."""
    output_path = Path("backgrounds")
    output_path.mkdir(exist_ok=True)
    print(f"📁 Created output folder: {output_path.absolute()}")
    return output_path

def copy_and_rename_backgrounds(backgrounds, output_path):
    """Copy background images to output folder with standardized names."""
    print(f"\n📋 Copying and renaming background images...")
    
    copied_count = 0
    
    for folder_name, image_files in backgrounds.items():
        # Clean folder name for filename (remove invalid characters)
        clean_name = folder_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        clean_name = clean_name.replace('<', '_').replace('>', '_').replace('|', '_')
        clean_name = clean_name.replace('"', '_').replace('?', '_').replace('*', '_')
        
        for i, image_file in enumerate(image_files):
            # Determine output filename
            if len(image_files) == 1:
                output_filename = f"bg_{clean_name}.png"
            else:
                output_filename = f"bg_{clean_name}_{i+1}.png"
            
            output_file_path = output_path / output_filename
            
            try:
                # Copy and rename the file
                shutil.copy2(image_file, output_file_path)
                print(f"  ✅ {folder_name} -> {output_filename}")
                copied_count += 1
            except Exception as e:
                print(f"  ❌ Error copying {image_file}: {e}")
    
    print(f"\n🎉 Successfully copied {copied_count} background images!")
    return copied_count

def main():
    """Main function to extract all DIM backgrounds."""
    print("🖼️  VB Background Extractor")
    print("=" * 50)
    
    # Load folder names from character_names.json
    folder_names = load_character_names()
    if not folder_names:
        print("❌ No folder names found. Make sure character_names.json exists.")
        return
    
    print(f"📊 Found {len(folder_names)} DIM folders to process")
    
    # Ask for base path where DIM folders are located
    print("\n📁 Please specify the base path where DIM folders are located:")
    print("   Example: D:\\Digimon\\DIMS\\SpriteB")
    
    # For now, let's use a common path structure
    base_paths_to_try = [
        "D:\\Digimon\\DIMS\\SpriteB",
        "D:\\DIMS\\SpriteB", 
        "C:\\DIMS\\SpriteB",
        "../../../DIMS/SpriteB",
        "../../DIMS/SpriteB"
    ]
    
    base_path = None
    for path in base_paths_to_try:
        if Path(path).exists():
            base_path = path
            print(f"✅ Found DIM base path: {base_path}")
            break
    
    if not base_path:
        print("❌ Could not find DIM base path. Please specify manually:")
        base_path = input("Enter base path: ").strip()
        if not Path(base_path).exists():
            print(f"❌ Path does not exist: {base_path}")
            return
    
    # Find background images
    backgrounds = find_background_images(base_path, folder_names)
    
    if not backgrounds:
        print("❌ No background images found!")
        return
    
    # Create output folder
    output_path = create_output_folder()
    
    # Copy and rename backgrounds
    copied_count = copy_and_rename_backgrounds(backgrounds, output_path)
    
    print(f"\n✅ Background extraction complete!")
    print(f"   📊 Processed: {len(backgrounds)} folders")
    print(f"   📄 Copied: {copied_count} background images")
    print(f"   📁 Output: {output_path.absolute()}")

if __name__ == "__main__":
    main()