#!/usr/bin/env python3
"""
Normalize character_name fields to title case
=============================================
Reads a JSON file, updates all character_name fields to be capitalized (e.g., 'KOROMON' → 'Koromon'), and writes the result.

Default input:  e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.reordered.json
Default output: e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.normalized.json

Usage:
  python normalize_character_names.py                # uses defaults above
  python normalize_character_names.py <in> <out>
"""

import json
import sys

def normalize_name(name: str) -> str:
    # Only normalize if all uppercase or all lowercase
    if not name:
        return name
    # If name is all uppercase or all lowercase, use title case
    if name.isupper() or name.islower():
        return name.capitalize()
    # If name contains spaces, apply title case to each word
    return ' '.join(w.capitalize() if w.isupper() or w.islower() else w for w in name.split(' '))

def main():
    default_in = r"e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.reordered.json"
    default_out = r"e:\\Omnimon\\utilities\\VBE\\character_names_be_translated_v1.normalized.json"

    in_path = sys.argv[1] if len(sys.argv) > 1 else default_in
    out_path = sys.argv[2] if len(sys.argv) > 2 else default_out

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chars = data.get("characters", [])
    changed = 0
    for entry in chars:
        name = entry.get("character_name")
        if name:
            norm = normalize_name(name)
            if norm != name:
                entry["character_name"] = norm
                changed += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Normalized {changed} character_name fields.")
    print(f"Output: {out_path}")

if __name__ == "__main__":
    main()