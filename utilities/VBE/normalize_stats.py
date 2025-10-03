#!/usr/bin/env python3
"""
Monster Stats Normalizer
Normalizes hp, star, power, attack, and critical_turn values in VBE module
to match the same range as VB module values.
"""

import os
import json
import random
from statistics import mean

# Configuration
VB_MONSTER_JSON = r'e:\Omnimon\modules\VB\monster.json'
VBE_MONSTER_JSON = r'e:\Omnimon\modules\VBE\monster.json'
OUTPUT_MONSTER_JSON = r'e:\Omnimon\utilities\VBE\monster_normalized.json'

def load_json(path):
    """Load JSON file with error handling."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {path}: {e}")
        return None

def save_json(path, data):
    """Save data to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def analyze_vb_stats(monsters):
    """Analyze VB monster stats to get ranges."""
    hp_values = []
    attack_values = []
    critical_turn_values = []
    effective_power_values = []  # power + 16 * star
    
    for monster in monsters:
        # Skip stage 0 monsters (eggs)
        if monster.get('stage', 0) == 0:
            continue
            
        hp = monster.get('hp', 0)
        attack = monster.get('attack', 0)
        critical_turn = monster.get('critical_turn', 0)
        power = monster.get('power', 0)
        star = monster.get('star', 0)
        
        if hp > 0:
            hp_values.append(hp)
        if attack > 0:
            attack_values.append(attack)
        if critical_turn > 0:
            critical_turn_values.append(critical_turn)
        if power > 0 or star > 0:
            effective_power = power + (16 * star)
            if effective_power > 0:
                effective_power_values.append(effective_power)
    
    return {
        'hp': {'min': min(hp_values) if hp_values else 0, 'max': max(hp_values) if hp_values else 0, 'values': hp_values},
        'attack': {'min': min(attack_values) if attack_values else 0, 'max': max(attack_values) if attack_values else 0, 'values': attack_values},
        'critical_turn': {'min': min(critical_turn_values) if critical_turn_values else 0, 'max': max(critical_turn_values) if critical_turn_values else 0, 'values': critical_turn_values},
        'effective_power': {'min': min(effective_power_values) if effective_power_values else 0, 'max': max(effective_power_values) if effective_power_values else 0, 'values': effective_power_values}
    }

def analyze_vbe_stats(monsters):
    """Analyze VBE monster stats to get ranges."""
    hp_values = []
    attack_values = []
    power_values = []
    
    for monster in monsters:
        # Skip stage 0 monsters (eggs)
        if monster.get('stage', 0) == 0:
            continue
            
        hp = monster.get('hp', 0)
        attack = monster.get('attack', 0)
        power = monster.get('power', 0)
        
        if hp > 0:
            hp_values.append(hp)
        if attack > 0:
            attack_values.append(attack)
        if power > 0:
            power_values.append(power)
    
    return {
        'hp': {'min': min(hp_values) if hp_values else 0, 'max': max(hp_values) if hp_values else 0, 'values': hp_values},
        'attack': {'min': min(attack_values) if attack_values else 0, 'max': max(attack_values) if attack_values else 0, 'values': attack_values},
        'power': {'min': min(power_values) if power_values else 0, 'max': max(power_values) if power_values else 0, 'values': power_values}
    }

def scale_value(value, source_min, source_max, target_min, target_max):
    """Scale a value from source range to target range."""
    if value == 0:
        return 0
    if source_max == source_min:
        return target_min
    
    # Linear scaling
    ratio = (value - source_min) / (source_max - source_min)
    scaled = target_min + (ratio * (target_max - target_min))
    return max(1, round(scaled))  # Ensure minimum of 1 for non-zero values

def normalize_monster_stats(vbe_monsters, vb_stats, vbe_stats):
    """Normalize VBE monster stats based on VB ranges."""
    normalized_count = 0
    
    for monster in vbe_monsters:
        # Skip stage 0 monsters (eggs)
        if monster.get('stage', 0) == 0:
            continue
        
        monster_name = monster.get('name', 'Unknown')
        original_values = {}
        updated_values = {}
        
        # Normalize HP
        original_hp = monster.get('hp', 0)
        if original_hp > 0:
            new_hp = scale_value(original_hp, vbe_stats['hp']['min'], vbe_stats['hp']['max'], 
                               vb_stats['hp']['min'], vb_stats['hp']['max'])
            if new_hp != original_hp:
                original_values['hp'] = original_hp
                updated_values['hp'] = new_hp
                monster['hp'] = new_hp
        
        # Normalize Attack
        original_attack = monster.get('attack', 0)
        if original_attack > 0:
            new_attack = scale_value(original_attack, vbe_stats['attack']['min'], vbe_stats['attack']['max'],
                                   vb_stats['attack']['min'], vb_stats['attack']['max'])
            if new_attack != original_attack:
                original_values['attack'] = original_attack
                updated_values['attack'] = new_attack
                monster['attack'] = new_attack
        
        # Normalize Power (combining star and power into just power)
        original_power = monster.get('power', 0)
        original_star = monster.get('star', 0)
        if original_power > 0:
            new_power = scale_value(original_power, vbe_stats['power']['min'], vbe_stats['power']['max'],
                                  vb_stats['effective_power']['min'], vb_stats['effective_power']['max'])
            if new_power != original_power:
                original_values['power'] = original_power
                updated_values['power'] = new_power
                monster['power'] = new_power
            
            # Set star to 0 since we're putting everything in power
            if original_star > 0:
                original_values['star'] = original_star
                updated_values['star'] = 0
                monster['star'] = 0
        
        # Set Critical Turn (random value in VB range for monsters with power > 0)
        original_critical = monster.get('critical_turn', 0)
        if monster.get('power', 0) > 0 and vb_stats['critical_turn']['min'] > 0:
            # Assign random critical turn value from VB range
            new_critical = random.randint(vb_stats['critical_turn']['min'], vb_stats['critical_turn']['max'])
            if new_critical != original_critical:
                original_values['critical_turn'] = original_critical
                updated_values['critical_turn'] = new_critical
                monster['critical_turn'] = new_critical
        
        # Log changes if any were made
        if updated_values:
            normalized_count += 1
            changes = []
            for key, new_val in updated_values.items():
                old_val = original_values.get(key, 0)
                changes.append(f"{key}: {old_val} → {new_val}")
            print(f"✅ Normalized {monster_name}: {', '.join(changes)}")
    
    return normalized_count

def main():
    """Main function to normalize monster stats."""
    print("Monster Stats Normalizer")
    print("=" * 50)
    
    # Check if files exist
    if not os.path.exists(VB_MONSTER_JSON):
        print(f"❌ VB monster file not found: {VB_MONSTER_JSON}")
        return 1
    
    if not os.path.exists(VBE_MONSTER_JSON):
        print(f"❌ VBE monster file not found: {VBE_MONSTER_JSON}")
        return 1
    
    print(f"📄 VB monster JSON: {VB_MONSTER_JSON}")
    print(f"📄 VBE monster JSON: {VBE_MONSTER_JSON}")
    print(f"📄 Output JSON: {OUTPUT_MONSTER_JSON}")
    print()
    
    # Load data
    print("📥 Loading data files...")
    vb_data = load_json(VB_MONSTER_JSON)
    vbe_data = load_json(VBE_MONSTER_JSON)
    
    if not vb_data or 'monster' not in vb_data:
        print("❌ Failed to load VB monster data")
        return 1
    
    if not vbe_data or 'monster' not in vbe_data:
        print("❌ Failed to load VBE monster data")
        return 1
    
    vb_monsters = vb_data['monster']
    vbe_monsters = vbe_data['monster']
    
    print(f"📊 VB monsters: {len(vb_monsters)}")
    print(f"📊 VBE monsters: {len(vbe_monsters)}")
    print()
    
    # Analyze VB stats to get target ranges
    print("🔍 Analyzing VB monster stats...")
    vb_stats = analyze_vb_stats(vb_monsters)
    
    print(f"📈 VB HP range: {vb_stats['hp']['min']} - {vb_stats['hp']['max']} ({len(vb_stats['hp']['values'])} non-zero values)")
    print(f"📈 VB Attack range: {vb_stats['attack']['min']} - {vb_stats['attack']['max']} ({len(vb_stats['attack']['values'])} non-zero values)")
    print(f"📈 VB Critical Turn range: {vb_stats['critical_turn']['min']} - {vb_stats['critical_turn']['max']} ({len(vb_stats['critical_turn']['values'])} non-zero values)")
    print(f"📈 VB Effective Power range: {vb_stats['effective_power']['min']} - {vb_stats['effective_power']['max']} ({len(vb_stats['effective_power']['values'])} non-zero values)")
    print()
    
    # Analyze VBE stats to get source ranges
    print("🔍 Analyzing VBE monster stats...")
    vbe_stats = analyze_vbe_stats(vbe_monsters)
    
    print(f"📈 VBE HP range: {vbe_stats['hp']['min']} - {vbe_stats['hp']['max']} ({len(vbe_stats['hp']['values'])} non-zero values)")
    print(f"📈 VBE Attack range: {vbe_stats['attack']['min']} - {vbe_stats['attack']['max']} ({len(vbe_stats['attack']['values'])} non-zero values)")
    print(f"📈 VBE Power range: {vbe_stats['power']['min']} - {vbe_stats['power']['max']} ({len(vbe_stats['power']['values'])} non-zero values)")
    print()
    
    # Set random seed for consistent critical_turn assignment
    random.seed(42)
    
    # Normalize VBE stats
    print("🔧 Normalizing VBE monster stats...")
    normalized_count = normalize_monster_stats(vbe_monsters, vb_stats, vbe_stats)
    
    print()
    print("📊 Normalization Summary:")
    print(f"   • Normalized monsters: {normalized_count}")
    print(f"   • Total VBE monsters: {len(vbe_monsters)}")
    
    # Save normalized data
    if normalized_count > 0:
        print(f"\n💾 Saving normalized monster data to: {OUTPUT_MONSTER_JSON}")
        try:
            save_json(OUTPUT_MONSTER_JSON, vbe_data)
            print("✅ Successfully saved normalized monster data!")
            
            # Show final ranges
            print(f"\n📈 Final VBE stat ranges after normalization:")
            final_stats = analyze_vbe_stats(vbe_monsters)
            print(f"   HP: {final_stats['hp']['min']} - {final_stats['hp']['max']}")
            print(f"   Attack: {final_stats['attack']['min']} - {final_stats['attack']['max']}")
            print(f"   Power: {final_stats['power']['min']} - {final_stats['power']['max']}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error saving normalized data: {e}")
            return 1
    else:
        print("\n⚠️  No monsters were normalized, not saving output file")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())