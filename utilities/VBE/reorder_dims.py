#!/usr/bin/env python3
"""
Reorder DIM blocks in the characters JSON
=========================================
Moves all entries of each DIM (folder_name) as a block into a desired order,
while preserving the current order of entries inside each DIM.

Default input:  e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.json
Default output: e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.reordered.json

Usage:
  python reorder_dims.py                # uses defaults above
  python reorder_dims.py <in> <out>
"""

import json
import sys
from collections import OrderedDict

# Desired folder (DIM) order as specified
DESIRED_ORDER = [
    "25th Anniversary BEM",
    "Ghost Game - Gammamon BE",
    "Imperialdramon BE",
    "Ghost Game - Angoramon BE",
    "Ghost Game - Jellymon BE",
    "draconic blaze",
    "rampage of the beast",
    "Loogamon BE",
    "Holy Wings",
    "Forest Guardian",
    "Ryudamon BE",
    "Dorumon BE",
    "D-3 White & Yellow",
    "D-3 White & Red",
    "Pulsemon BE",
    "MHA 01",
    "MHA 02",
    "Tokyo Revengers 01",
    "Demon Slayer 01",
    "Demon Slayer 02",
    "JJK 01",
    "Tousouchuu Great Mission 01",
]


def reorder_characters(data: dict) -> dict:
    chars = data.get("characters", [])

    # Group by folder_name, preserving the first-seen folder order and within-folder order
    folder_to_entries: "OrderedDict[str, list]" = OrderedDict()
    for entry in chars:
        folder = entry.get("folder_name", "")
        if folder not in folder_to_entries:
            folder_to_entries[folder] = []
        folder_to_entries[folder].append(entry)

    # Build the new ordered list
    new_chars = []
    seen = set()

    # 1) Add folders in the desired order (if present)
    for folder in DESIRED_ORDER:
        if folder in folder_to_entries:
            new_chars.extend(folder_to_entries[folder])
            seen.add(folder)

    # 2) Append any remaining folders in their original relative order
    for folder, entries in folder_to_entries.items():
        if folder not in seen:
            new_chars.extend(entries)

    out = dict(data)
    out["characters"] = new_chars
    return out


def main():
    # Default paths
    default_in = r"e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.json"
    default_out = r"e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.reordered.json"

    in_path = sys.argv[1] if len(sys.argv) > 1 else default_in
    out_path = sys.argv[2] if len(sys.argv) > 2 else default_out

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = len(data.get("characters", []))
    out = reorder_characters(data)
    new_count = len(out.get("characters", []))

    # Basic integrity checks
    if original_count != new_count:
        print(f"Warning: character count changed from {original_count} to {new_count}")

    # Write output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # Print ordered folder summary (first occurrence only)
    ordered_folders = []
    seen = set()
    for entry in out["characters"]:
        folder = entry.get("folder_name", "")
        if folder not in seen:
            ordered_folders.append(folder)
            seen.add(folder)

    print("Reordering complete.")
    print(f"Characters: {new_count}")
    print("Folder order:")
    for i, folder in enumerate(ordered_folders, 1):
        print(f"  {i:2d}. {folder}")


if __name__ == "__main__":
    sys.exit(main())
