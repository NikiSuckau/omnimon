#!/usr/bin/env python3
"""
Validate character_name fields
==============================
Checks if all entries in the JSON file have a `character_name` and ensures no duplicate `character_name` values exist within the same `folder_name`.

Default input:  e:\\Omnimon\\utilities\\VBE\\character_names.json

Usage:
  python validate_character_names.py                # uses default input
  python validate_character_names.py <input_file>  # specify input file
"""

import json
import sys
from collections import defaultdict

def validate_character_names(data: dict):
    characters = data.get("characters", [])

    missing_names = []
    duplicates = defaultdict(list)  # folder_name -> list of duplicate names

    # Track seen names per folder
    seen_names = defaultdict(set)

    for entry in characters:
        folder = entry.get("folder_name", "")
        name = entry.get("character_name")

        if not name:
            missing_names.append(entry)
        elif name in seen_names[folder]:
            duplicates[folder].append(name)
        else:
            seen_names[folder].add(name)

    return missing_names, duplicates

def main():
    default_input = r"e:\\Omnimon\\utilities\\VBE\\character_names.json"
    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing_names, duplicates = validate_character_names(data)

    if missing_names:
        print(f"Entries missing character_name: {len(missing_names)}")
        for entry in missing_names:
            print(f"  Folder: {entry.get('folder_name', 'Unknown')}, Character Number: {entry.get('character_number', 'Unknown')}")
    else:
        print("All entries have a character_name.")

    if duplicates:
        print("\nDuplicate character_name entries found:")
        for folder, names in duplicates.items():
            print(f"  Folder: {folder}")
            for name in set(names):
                print(f"    {name}")
    else:
        print("No duplicate character_name entries found.")

if __name__ == "__main__":
    main()