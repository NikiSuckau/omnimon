def build_evolutions(monsters, version, entries, entry_to_char, char_objs):
    # Create a mapping from character file index to monster name
    # We need to map from the actual character file indices to monster names
    file_idx_to_name = {}
    for idx, entry in enumerate(entries):
        ci = entry_to_char.get(idx)
        if ci is not None:
            # Extract the file number from the character file path
            char_path = char_objs[ci]['path']
            import re
            match = re.search(r'character_(\d+)\.json$', char_path)
            if match:
                file_idx = int(match.group(1))
                file_idx_to_name[file_idx] = entry.get('name')
    
    # Attribute mapping
    attr_map = {1: 'Vi', 2: 'Da', 3: 'Va', 4: 'Free'}
    fusion_keys = ['type1', 'type2', 'type3', 'type4']

    # Only update entries in monsters with the specified version
    for idx, entry in enumerate(entries):
        ci = entry_to_char.get(idx)
        if ci is None:
            continue
        char_data = char_objs[ci]['data']
        evolutions = []

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
                "stage": entry.get('stage'),
                "attribute": attr_map.get(i+1),
                "jogress": "PenC"
            }
            evolutions.append(evo)

        # Find the corresponding monster.json entry and update only if version matches
        for m in monsters:
            if m.get('version') == version and m.get('name') == entry.get('name'):
                m['evolve'] = evolutions
                break
import os
import json
import argparse
from glob import glob
import re

jsonfile = 'E:/Omnimon/modules/VBE/monster.json'
version = 1
dataFolder = 'D:/Digimon/DIMS/Sprites2/Ghost Game - Gammamon BE/data/'

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_character_files(folder):
    pattern = os.path.join(folder, 'character_*.json')
    files = glob(pattern)
    # sort by the numeric suffix if available
    def keyfn(p):
        m = re.search(r'character_(\d+)\.json$', p)
        return int(m.group(1)) if m else p
    return sorted(files, key=keyfn)


def extract_int(d, keys):
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


def name_normalize(s):
    if not s:
        return ''
    s = str(s).lower()
    # keep only alphanumeric
    return re.sub(r'[^a-z0-9]', '', s)


def char_data_has_name(char_data, target_name):
    """Return True if any string field in char_data matches target_name (normalized)."""
    if not char_data or not target_name:
        return False
    tn = name_normalize(target_name)
    # check common name keys first
    for key in ('name', 'Name', 'displayName', 'display_name'):
        v = char_data.get(key) if isinstance(char_data, dict) else None
        if isinstance(v, str) and name_normalize(v) == tn:
            return True
    # fallback: scan all values for matching string
    if isinstance(char_data, dict):
        for v in char_data.values():
            if isinstance(v, str) and name_normalize(v) == tn:
                return True
            # lists of strings
            if isinstance(v, (list, tuple)):
                for item in v:
                    if isinstance(item, str) and name_normalize(item) == tn:
                        return True
    return False


def exact_match_character(monster_entry, char_data):
    """Return (True, '') if all comparable fields (hp, star, power, attribute) match exactly after normalization.
    Returns (False, reason) otherwise.
    """
    reasons = []

    m_hp = monster_entry.get('hp')
    c_hp_raw = extract_int(char_data, ['hp', 'HP'])
    c_hp = normalize_value(c_hp_raw) if c_hp_raw is not None else None
    if m_hp is not None:
        if c_hp is None or int(m_hp) != int(c_hp):
            reasons.append(f"hp mismatch (monster:{m_hp} vs char:{c_hp_raw})")

    m_star = monster_entry.get('star')
    c_star_raw = extract_int(char_data, ['stars', 'star', 'Stars'])
    c_star = normalize_value(c_star_raw) if c_star_raw is not None else None
    if m_star is not None:
        if c_star is None or int(m_star) != int(c_star):
            reasons.append(f"star mismatch (monster:{m_star} vs char:{c_star_raw})")

    m_power = monster_entry.get('power')
    c_bp_raw = extract_int(char_data, ['bp', 'BP', 'power'])
    c_bp = normalize_value(c_bp_raw) if c_bp_raw is not None else None
    if m_power is not None:
        if c_bp is None or int(m_power) != int(c_bp):
            reasons.append(f"power/bp mismatch (monster:{m_power} vs char:{c_bp_raw})")

    # Check attribute matching
    m_attr = monster_entry.get('attribute', '')
    c_attr_raw = extract_int(char_data, ['attribute', 'Attribute'])
    # Convert char attribute: 1=Vi, 2=Da, 3=Va, anything else=Free (empty string)
    if c_attr_raw == 1:
        c_attr = 'Vi'
    elif c_attr_raw == 2:
        c_attr = 'Da'
    elif c_attr_raw == 3:
        c_attr = 'Va'
    else:
        c_attr = ''  # Free attribute
    
    if m_attr != c_attr:
        reasons.append(f"attribute mismatch (monster:'{m_attr}' vs char:{c_attr_raw}->'{c_attr}')")

    if reasons:
        return False, ' / '.join(reasons)
    return True, ''


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


def match_character(monster_entry, char_data):
    """Compare hp, star(s), power/bp, and attribute and return (matched:bool, reason:str)."""
    reasons = []
    matched = 0
    total = 0

    m_hp = monster_entry.get('hp')
    c_hp_raw = extract_int(char_data, ['hp', 'HP'])
    c_hp = normalize_value(c_hp_raw) if c_hp_raw is not None else None
    if m_hp is not None and c_hp is not None:
        total += 1
        if int(m_hp) == int(c_hp):
            matched += 1
        else:
            reasons.append(f"hp mismatch (monster:{m_hp} vs char:{c_hp_raw})")

    m_star = monster_entry.get('star')
    c_star_raw = extract_int(char_data, ['stars', 'star', 'Stars'])
    c_star = normalize_value(c_star_raw) if c_star_raw is not None else None
    if m_star is not None and c_star is not None:
        total += 1
        if int(m_star) == int(c_star):
            matched += 1
        else:
            reasons.append(f"star mismatch (monster:{m_star} vs char:{c_star_raw})")

    m_power = monster_entry.get('power')
    c_bp_raw = extract_int(char_data, ['bp', 'BP', 'power'])
    c_bp = normalize_value(c_bp_raw) if c_bp_raw is not None else None
    if m_power is not None and c_bp is not None:
        total += 1
        if int(m_power) == int(c_bp):
            matched += 1
        else:
            reasons.append(f"power/bp mismatch (monster:{m_power} vs char:{c_bp_raw})")

    # Check attribute matching
    m_attr = monster_entry.get('attribute', '')
    c_attr_raw = extract_int(char_data, ['attribute', 'Attribute'])
    if c_attr_raw is not None:
        total += 1
        # Convert char attribute: 1=Vi, 2=Da, 3=Va, anything else=Free (empty string)
        if c_attr_raw == 1:
            c_attr = 'Vi'
        elif c_attr_raw == 2:
            c_attr = 'Da'
        elif c_attr_raw == 3:
            c_attr = 'Va'
        else:
            c_attr = ''  # Free attribute
        
        if m_attr == c_attr:
            matched += 1
        else:
            reasons.append(f"attribute mismatch (monster:'{m_attr}' vs char:{c_attr_raw}->'{c_attr}')")

    if total == 0:
        return False, 'no comparable fields'

    ok = matched >= max(1, total // 2 + (0 if total == 1 else 1))
    reason = ' / '.join(reasons) if reasons else 'matched'
    return ok, reason


def update_attacks(monster_json_path, version, data_folder, backup=True, force=False):
    data = load_json(monster_json_path)
    monsters = data.get('monster', [])

    # select entries for the version, ignoring stage 0
    entries = [m for m in monsters if m.get('version') == version and m.get('stage') != 0]

    # load character files into objects with 'used' flag
    char_paths = find_character_files(data_folder)
    char_objs = []
    warnings = []
    for p in char_paths:
        try:
            d = load_json(p)
            char_objs.append({'path': p, 'data': d, 'used': False})
        except Exception as e:
            warnings.append(f"Failed to load {p}: {e}")
            char_objs.append({'path': p, 'data': None, 'used': False})

    missing = []
    updated = []

    # Map each entry: prefer expected file, otherwise search unused files for exact match
    entry_to_char = {}
    for idx, entry in enumerate(entries):
        expected_path = os.path.join(data_folder, f'character_{idx:02d}.json')
        chosen_ci = None

        # 1) try expected file if present
        for ci, co in enumerate(char_objs):
            if co['path'] == expected_path:
                if co['data'] is not None:
                    ok, reason = exact_match_character(entry, co['data'])
                    if ok:
                        chosen_ci = ci
                        co['used'] = True
                break

        # 2) if expected didn't match, scan all unused files for an exact match of comparable fields
        if chosen_ci is None:
            for ci, co in enumerate(char_objs):
                if co['used'] or co['data'] is None:
                    continue
                ok, reason = exact_match_character(entry, co['data'])
                if ok:
                    chosen_ci = ci
                    co['used'] = True
                    break

        if chosen_ci is None:
            missing.append(entry.get('name'))
            continue

        entry_to_char[idx] = chosen_ci

    # Now process mapped pairs
    for idx, entry in enumerate(entries):
        ci = entry_to_char.get(idx)
        if ci is None:
            # already added to missing
            continue
        co = char_objs[ci]
        char_path = co['path']
        char_data = co['data']

        # Check for non-empty specificFusions and print for manual review
        specific_fusions = char_data.get('specificFusions', {}) if char_data else {}
        if specific_fusions and isinstance(specific_fusions, dict) and len(specific_fusions) > 0:
            print(f"[specificFusions] Found in {char_path}:")
            print(json.dumps(specific_fusions, indent=2, ensure_ascii=False))

        if char_data is None:
            warnings.append(f"Failed to load {char_path}")
            missing.append(entry.get('name'))
            continue

        is_match, reason = match_character(entry, char_data)
        if not is_match and not force:
            warnings.append(f"Validation failed for '{entry.get('name')}' vs {os.path.basename(char_path)}: {reason}")
            missing.append(entry.get('name'))
            continue

        # map fields: smallAttack -> atk_main, bigAttack -> atk_alt, ap -> attack
        raw_small = extract_int(char_data, ['smallAttack', 'small_attack', 'smallAtk', 'small'])
        raw_big = extract_int(char_data, ['bigAttack', 'big_attack', 'bigAtk', 'big'])
        ap = extract_int(char_data, ['ap', 'AP', 'attack'])

        small = convert_small_attack(raw_small)
        big = convert_big_attack(raw_big)

        if small is not None:
            entry['atk_main'] = small
        if big is not None:
            entry['atk_alt'] = big
        if ap is not None:
            # normalize ap: 65535 in source means 0 in our system
            nap = normalize_value(ap)
            entry['attack'] = nap

        updated.append((entry.get('name'), os.path.basename(char_path)))

    # backup original
    if backup:
        bak = monster_json_path + '.bak'
        try:
            with open(bak, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            warnings.append(f"Failed to create backup {bak}: {e}")

    # save updated json (override)
    save_json(monster_json_path, data)

    return {
        'updated_count': len(updated),
        'updated': updated,
        'missing': missing,
        'warnings': warnings,
        'total_entries': len(entries),
        'entry_to_char': entry_to_char,
        'entries': entries,
        'char_objs': char_objs
    }


if __name__ == '__main__':
    # Run using module-level defaults so no CLI args are required
    result = update_attacks(jsonfile, version, dataFolder, backup=True, force=False)
    # Rebuild evolutions using the same mapped character files from update_attacks
    data = load_json(jsonfile)
    monsters = data.get('monster', [])
    
    # Use the mapping from update_attacks to ensure consistency
    entries = result['entries']
    entry_to_char = result['entry_to_char']
    char_objs = result['char_objs']
    
    # Build evolutions
    build_evolutions(monsters, version, entries, entry_to_char, char_objs)
    # Save updated monster.json
    save_json(jsonfile, data)

    print(f"Processed {result['total_entries']} entries for version {version}")
    print(f"Updated: {result['updated_count']}")
    if result['updated']:
        print("Updated mappings:")
        for name, file in result['updated']:
            print(f"  {name} <- {file}")
    if result['missing']:
        print("Missing or skipped entries:")
        for name in result['missing']:
            print(f"  {name}")
    if result['warnings']:
        print("Warnings:")
        for w in result['warnings']:
            print(f"  {w}")
