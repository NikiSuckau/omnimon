#!/usr/bin/env python3
"""
Monster ZIP Creator Script

This script takes a path to a monsters folder (like modules/DMC/monsters),
goes through each monster folder, creates a ZIP file of the folder contents,
and moves the ZIP files to the global assets/monsters folder without replacing existing files.

Usage:
    python create_monster_zips.py <monsters_folder_path>
    
Example:
    python create_monster_zips.py "modules/DMH/monsters"
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path


def create_zip_from_folder(folder_path: str, zip_path: str) -> bool:
    """
    Create a ZIP file from a folder containing sprites.
    
    Args:
        folder_path: Path to the folder to zip
        zip_path: Path where the ZIP file should be created
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            folder = Path(folder_path)
            for file_path in folder.rglob('*'):
                if file_path.is_file():
                    # Add file to zip with relative path from folder
                    arcname = file_path.relative_to(folder)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"Error creating ZIP {zip_path}: {e}")
        return False


def process_monsters_folder(monsters_path: str) -> int:
    """
    Process a monsters folder and create ZIP files for each monster.
    
    Args:
        monsters_path: Path to the monsters folder
        
    Returns:
        Number of ZIP files created
    """
    monsters_path = Path(monsters_path)
    
    if not monsters_path.exists():
        print(f"Error: Monsters folder '{monsters_path}' does not exist")
        return 0
    
    if not monsters_path.is_dir():
        print(f"Error: '{monsters_path}' is not a directory")
        return 0
    
    # Ensure assets/monsters directory exists
    assets_monsters = Path("assets/monsters")
    assets_monsters.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    
    # Process each monster folder
    for monster_folder in monsters_path.iterdir():
        if not monster_folder.is_dir():
            continue
        
        monster_name = monster_folder.name
        zip_filename = f"{monster_name}.zip"
        temp_zip_path = Path("temp_monster.zip")
        final_zip_path = assets_monsters / zip_filename
        module_zip_path = monster_folder / zip_filename
        
        print(f"Processing {monster_name}...")
        
        # Check if folder contains PNG files
        png_files = list(monster_folder.glob("*.png"))
        if not png_files:
            print(f"  Skipping {monster_name} - no PNG files found")
            continue
        
        # Create temporary ZIP file
        if create_zip_from_folder(str(monster_folder), str(temp_zip_path)):
            continue
            # If target ZIP already exists, leave new ZIP in module's monsters folder
            #if final_zip_path.exists():
            #    try:
            #        shutil.move(str(temp_zip_path), str(module_zip_path))
            #        print(f"  ZIP already exists in assets/monsters/. New ZIP left in module folder as {zip_filename}")
            #    except Exception as e:
            #        print(f"  Error moving ZIP for {monster_name} to module folder: {e}")
            #        if temp_zip_path.exists():
            #            temp_zip_path.unlink()
            #else:
            #    try:
            #        shutil.move(str(temp_zip_path), str(final_zip_path))
            #        print(f"  Created {zip_filename} with {len(png_files)} sprites")
            #        created_count += 1
            #    except Exception as e:
            #        print(f"  Error moving ZIP for {monster_name}: {e}")
            #        if temp_zip_path.exists():
            #            temp_zip_path.unlink()
        else:
            print(f"  Failed to create ZIP for {monster_name}")
    
    return created_count


def main():
    """Main function to handle command line arguments and process folders."""
    if len(sys.argv) != 2:
        print("Usage: python create_monster_zips.py <monsters_folder_path>")
        print("Example: python create_monster_zips.py 'modules/DMC/monsters'")
        sys.exit(1)
    
    monsters_folder = sys.argv[1]
    
    print(f"Creating monster ZIP files from: {monsters_folder}")
    print(f"Target directory: assets/monsters/")
    print("-" * 50)
    
    created_count = process_monsters_folder(monsters_folder)
    
    print("-" * 50)
    print(f"Processing complete!")
    print(f"Created {created_count} ZIP files")
    
    if created_count > 0:
        print("\nZIP files created in assets/monsters/:")
        assets_monsters = Path("assets/monsters")
        for zip_file in sorted(assets_monsters.glob("*.zip")):
            print(f"  {zip_file.name}")


if __name__ == "__main__":
    main()
