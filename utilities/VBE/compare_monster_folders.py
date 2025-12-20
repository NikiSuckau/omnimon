#!/usr/bin/env python3
"""
Monster Folders Comparison and Update Script
Compares files between two monster folders and replaces newer files from Mons to hidef folder.
For files newer than September 5, 2025, replaces hidef version with Mons version if available.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
FOLDER_A = r'e:\Omnimon\assets\monsters_hidef'  # Target folder (will be updated)
FOLDER_B = r'C:\Users\Ander\Downloads\Mons'     # Source folder (newer files)
CUTOFF_DATE = datetime(2025, 9, 5)  # September 5, 2025

def get_files_with_dates(folder_path):
    """Get files with their modification dates."""
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"❌ Folder does not exist: {folder_path}")
            return {}
        
        files_info = {}
        for file_path in folder.iterdir():
            if file_path.is_file():
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                files_info[file_path.name] = {
                    'path': file_path,
                    'mod_time': mod_time
                }
        
        return files_info
    except Exception as e:
        print(f"❌ Error reading folder {folder_path}: {e}")
        return {}

def normalize_filename(filename):
    """Normalize filename for comparison (remove extensions, handle variations)."""
    # Remove file extension
    name = Path(filename).stem
    
    # Common normalizations
    name = name.replace('_dmc', '')  # Remove _dmc suffix
    name = name.replace('_', ' ')    # Replace underscores with spaces
    name = name.strip()              # Remove leading/trailing spaces
    
    return name.lower()

def update_newer_files(hidef_folder, mons_folder, cutoff_date):
    """Update hidef folder with newer files from mons folder."""
    print(f"Monster Files Update Process")
    print("=" * 50)
    print(f"🎯 Target folder (hidef): {hidef_folder}")
    print(f"📦 Source folder (mons): {mons_folder}")
    print(f"📅 Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
    print()
    
    # Get files with dates from both folders
    hidef_files = get_files_with_dates(hidef_folder)
    mons_files = get_files_with_dates(mons_folder)
    
    if not hidef_files and not mons_files:
        print("❌ Both folders are empty or inaccessible")
        return
    
    print(f"📊 Target folder: {len(hidef_files)} files")
    print(f"📊 Source folder: {len(mons_files)} files")
    print()
    
    # Create normalized name mappings for comparison
    hidef_normalized = {}
    mons_normalized = {}
    
    for filename, info in hidef_files.items():
        norm_name = normalize_filename(filename)
        hidef_normalized[norm_name] = {
            'original_name': filename,
            'info': info
        }
    
    for filename, info in mons_files.items():
        norm_name = normalize_filename(filename)
        mons_normalized[norm_name] = {
            'original_name': filename,
            'info': info
        }
    
    # Find files in hidef that are newer than cutoff date
    newer_hidef_files = []
    for norm_name, data in hidef_normalized.items():
        if data['info']['mod_time'] > cutoff_date:
            newer_hidef_files.append(norm_name)
    
    print(f"🔍 Files in target folder newer than {cutoff_date.strftime('%Y-%m-%d')}: {len(newer_hidef_files)}")
    
    # Process updates
    updated_files = []
    skipped_files = []
    backup_folder = Path(hidef_folder) / "backup_before_update"
    
    if newer_hidef_files:
        # Create backup folder
        backup_folder.mkdir(exist_ok=True)
        print(f"📋 Created backup folder: {backup_folder}")
        print()
    
    for norm_name in newer_hidef_files:
        hidef_data = hidef_normalized[norm_name]
        hidef_filename = hidef_data['original_name']
        hidef_path = hidef_data['info']['path']
        hidef_mod_time = hidef_data['info']['mod_time']
        
        if norm_name in mons_normalized:
            # File exists in mons folder - replace it
            mons_data = mons_normalized[norm_name]
            mons_filename = mons_data['original_name']
            mons_path = mons_data['info']['path']
            mons_mod_time = mons_data['info']['mod_time']
            
            try:
                # Create backup
                backup_path = backup_folder / hidef_filename
                shutil.copy2(hidef_path, backup_path)
                
                # Replace with mons version
                shutil.copy2(mons_path, hidef_path)
                
                updated_files.append({
                    'filename': hidef_filename,
                    'hidef_date': hidef_mod_time,
                    'mons_date': mons_mod_time,
                    'mons_source': mons_filename
                })
                
                print(f"✅ Updated: {hidef_filename}")
                print(f"   Source: {mons_filename} ({mons_mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
                print(f"   Backup: {backup_path.name}")
                
            except Exception as e:
                print(f"❌ Error updating {hidef_filename}: {e}")
                skipped_files.append({
                    'filename': hidef_filename,
                    'reason': f"Update error: {e}"
                })
        else:
            # File not found in mons folder
            skipped_files.append({
                'filename': hidef_filename,
                'reason': "Not found in source folder",
                'date': hidef_mod_time
            })
    
    # Report results
    print()
    print("📊 Update Summary:")
    print(f"   • Files updated: {len(updated_files)}")
    print(f"   • Files skipped: {len(skipped_files)}")
    print()
    
    if updated_files:
        print("✅ Successfully Updated Files:")
        for file_info in updated_files:
            print(f"   • {file_info['filename']} ← {file_info['mons_source']}")
        print()
    
    if skipped_files:
        print("⚠️  Skipped Files (newer than cutoff but not in source):")
        for file_info in skipped_files:
            reason = file_info['reason']
            if 'date' in file_info:
                date_str = file_info['date'].strftime('%Y-%m-%d')
                print(f"   • {file_info['filename']} ({date_str}) - {reason}")
            else:
                print(f"   • {file_info['filename']} - {reason}")
        print()
    
    return updated_files, skipped_files

def save_update_report(hidef_folder, mons_folder, cutoff_date, updated_files, skipped_files, output_file):
    """Save detailed update report to file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Monster Files Update Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Target folder: {hidef_folder}\n")
        f.write(f"Source folder: {mons_folder}\n")
        f.write(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}\n")
        f.write(f"Update timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files updated: {len(updated_files)}\n")
        f.write(f"Files skipped: {len(skipped_files)}\n")
        f.write("\n")
        
        if updated_files:
            f.write("SUCCESSFULLY UPDATED FILES:\n")
            f.write("-" * 30 + "\n")
            for file_info in updated_files:
                f.write(f"{file_info['filename']}\n")
                f.write(f"  Source: {file_info['mons_source']}\n")
                f.write(f"  Source date: {file_info['mons_date'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Original date: {file_info['hidef_date'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
        
        if skipped_files:
            f.write("SKIPPED FILES:\n")
            f.write("-" * 30 + "\n")
            for file_info in skipped_files:
                f.write(f"{file_info['filename']}\n")
                f.write(f"  Reason: {file_info['reason']}\n")
                if 'date' in file_info:
                    f.write(f"  Date: {file_info['date'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")

def main():
    """Main function to update monster files."""
    # Update files newer than cutoff date
    updated_files, skipped_files = update_newer_files(FOLDER_A, FOLDER_B, CUTOFF_DATE)
    
    # Save detailed report
    output_file = "monster_files_update_report.txt"
    try:
        save_update_report(FOLDER_A, FOLDER_B, CUTOFF_DATE, updated_files, skipped_files, output_file)
        print(f"💾 Detailed report saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving report: {e}")

if __name__ == "__main__":
    main()