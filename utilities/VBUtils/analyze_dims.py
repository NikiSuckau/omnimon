#!/usr/bin/env python3
"""
DIM Analysis Script
Analyzes which DIMs we have and identifies which ones still need translation.
"""

import json
from collections import defaultdict, Counter

def analyze_dims(char_names_file):
    """Analyze which DIMs we have and their translation status."""
    
    print("🔍 Loading character names...")
    with open(char_names_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group by folder and count statuses
    folder_stats = defaultdict(lambda: {'total': 0, 'translated': 0, 'extracted': 0, 'untranslated_japanese': 0})
    all_folders = set()
    
    for char in data.get('characters', []):
        folder_name = char.get('folder_name', 'Unknown')
        all_folders.add(folder_name)
        folder_stats[folder_name]['total'] += 1
        
        status = char.get('status', 'unknown')
        manual_name = char.get('manual_name', '')
        
        if status == 'translated':
            folder_stats[folder_name]['translated'] += 1
        elif status == 'extracted':
            folder_stats[folder_name]['extracted'] += 1
            # Check if it's still Japanese
            if contains_japanese(manual_name):
                folder_stats[folder_name]['untranslated_japanese'] += 1
    
    # Define what our translators can handle
    ultraman_folders = {
        "Vol 00 - 6 Ultrabrothers", 
        "Vol 00 - Ultraman Tiga", 
        "Vol 01 - Ultraman Zero",
        "Vol 01 - Zetton", 
        "Vol 02 - Ultraman Trigger",
        "Vol 02 - Alien Baltan",
        "Vol 03 - Ultraman Z",
        "Vol 03 - Sevenger",
        "Vol 04 - Ultraman Dyna and Gaia", 
        "Vol 04 - Gomora"
    }
    
    kamen_rider_folders = {
        "Vol 00 - Masked Rider Kuuga",
        "Vol 00 - Showa 10 Masked Rider",
        "Vol 01 - Kamen Rider Zero One", 
        "Vol 01 - Kamen Rider Horobi", 
        "Vol 02 - Kamen Rider Ex-Aid", 
        "Vol 02 - Kamen Rider Genm",
        "Vol 03 - Kamen Rider Build", 
        "Vol 03 - Kamen Rider Rogue", 
        "Vol 04 - Kamen Rider 000",
        "Vol 04 - Greeed"
    }
    
    dc_folders = {
        "Batman", 
        "DC Heroes", 
        "DC Villains"
    }
    
    print(f"\n📊 DIM Analysis Results")
    print(f"=" * 60)
    print(f"Total DIMs found: {len(all_folders)}")
    print()
    
    # Categorize folders
    print("🦸 DC/Batman DIMs (Pre-translated):")
    dc_total = 0
    for folder in sorted(dc_folders & all_folders):
        stats = folder_stats[folder]
        print(f"   • {folder}: {stats['translated']}/{stats['total']} translated")
        dc_total += stats['total']
    print(f"   Total DC characters: {dc_total}")
    print()
    
    print("🌟 Ultraman DIMs (Translator available):")
    ultraman_total = 0
    ultraman_translated = 0
    for folder in sorted(ultraman_folders & all_folders):
        stats = folder_stats[folder]
        print(f"   • {folder}: {stats['translated']}/{stats['total']} translated")
        ultraman_total += stats['total']
        ultraman_translated += stats['translated']
    print(f"   Total Ultraman characters: {ultraman_translated}/{ultraman_total} translated")
    print()
    
    print("🦗 Kamen Rider DIMs (Translator available):")
    kr_total = 0
    kr_translated = 0
    for folder in sorted(kamen_rider_folders & all_folders):
        stats = folder_stats[folder]
        print(f"   • {folder}: {stats['translated']}/{stats['total']} translated")
        kr_total += stats['total']
        kr_translated += stats['translated']
    print(f"   Total Kamen Rider characters: {kr_translated}/{kr_total} translated")
    print()
    
    # Find DIMs without translators
    covered_folders = dc_folders | ultraman_folders | kamen_rider_folders
    uncovered_folders = all_folders - covered_folders
    
    print("❓ DIMs WITHOUT translators (need manual work):")
    uncovered_total = 0
    untranslated_japanese_total = 0
    
    for folder in sorted(uncovered_folders):
        stats = folder_stats[folder]
        uncovered_total += stats['total']
        untranslated_japanese_total += stats['untranslated_japanese']
        
        status_str = f"{stats['extracted']}/{stats['total']} extracted"
        if stats['untranslated_japanese'] > 0:
            status_str += f" ({stats['untranslated_japanese']} still Japanese)"
        
        print(f"   • {folder}: {status_str}")
    
    print(f"   Total uncovered characters: {uncovered_total}")
    print(f"   Characters with Japanese names: {untranslated_japanese_total}")
    print()
    
    # Summary
    total_chars = sum(stats['total'] for stats in folder_stats.values())
    total_translated = sum(stats['translated'] for stats in folder_stats.values())
    total_japanese = sum(stats['untranslated_japanese'] for stats in folder_stats.values())
    
    print("📈 Overall Summary:")
    print(f"   • Total characters: {total_chars}")
    print(f"   • Fully translated: {total_translated} ({total_translated/total_chars*100:.1f}%)")
    print(f"   • Still in Japanese: {total_japanese} ({total_japanese/total_chars*100:.1f}%)")
    print(f"   • Coverage by translators: {(total_chars-uncovered_total)/total_chars*100:.1f}%")
    print()
    
    # Show which specific DIMs need attention
    if untranslated_japanese_total > 0:
        print("🎯 Priority DIMs needing translation work:")
        for folder in sorted(uncovered_folders):
            stats = folder_stats[folder]
            if stats['untranslated_japanese'] > 0:
                print(f"   • {folder}: {stats['untranslated_japanese']} Japanese names")

def contains_japanese(text):
    """Check if text contains Japanese characters."""
    if not text:
        return False
    import re
    japanese_pattern = r'[ひ-ろゎ-ん゙-゜ァ-ヿ一-龯]'
    return bool(re.search(japanese_pattern, text))

if __name__ == "__main__":
    analyze_dims('character_names.json')