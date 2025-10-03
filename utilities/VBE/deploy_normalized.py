#!/usr/bin/env python3
"""
Deploy Normalized Monster Data
Copies the normalized monster data to the VBE module.
"""

import os
import json
import shutil

# Configuration
NORMALIZED_JSON = r'e:\Omnimon\utilities\VBE\monster_normalized.json'
VBE_MONSTER_JSON = r'e:\Omnimon\modules\VBE\monster.json'
BACKUP_JSON = r'e:\Omnimon\modules\VBE\monster_backup.json'

def main():
    """Deploy normalized monster data to VBE module."""
    print("Deploy Normalized Monster Data")
    print("=" * 40)
    
    # Check if normalized file exists
    if not os.path.exists(NORMALIZED_JSON):
        print(f"❌ Normalized file not found: {NORMALIZED_JSON}")
        return 1
    
    # Check if VBE file exists
    if not os.path.exists(VBE_MONSTER_JSON):
        print(f"❌ VBE monster file not found: {VBE_MONSTER_JSON}")
        return 1
    
    try:
        # Create backup
        print(f"📋 Creating backup: {BACKUP_JSON}")
        shutil.copy2(VBE_MONSTER_JSON, BACKUP_JSON)
        
        # Deploy normalized data
        print(f"🚀 Deploying normalized data to: {VBE_MONSTER_JSON}")
        shutil.copy2(NORMALIZED_JSON, VBE_MONSTER_JSON)
        
        print("✅ Successfully deployed normalized monster data!")
        print("📋 Original data backed up to monster_backup.json")
        return 0
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())