import json
from collections import defaultdict

VALIDATE_FILE = 'e:/Omnimon/modules/VBE/monster.json'

def load_json(path):
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)

def validate_evolutions(monster_data):
	# Group entries by version
	versions = defaultdict(list)
	for entry in monster_data:
		versions[entry.get('version')].append(entry)

	for version, entries in versions.items():
		print(f"\n--- Version {version} ---")
		name_to_entry = {e.get('name'): e for e in entries}
		valid_names = set(name_to_entry.keys())
		# Exclude stage 0 from required targets, but allow them to point to others
		non_stage0_names = set(e.get('name') for e in entries if e.get('stage') != 0)
		pointed_to = set()
		errors = []

		for entry in entries:
			# All entries (including stage 0) can point to others
			for evo in entry.get('evolve', []):
				tgt = evo.get('to')
				if tgt:
					if tgt not in valid_names:
						errors.append(f"Invalid evolution target: '{tgt}' from '{entry.get('name')}' (version {version})")
					else:
						pointed_to.add(tgt)

		# Only require non-stage-0 entries to be pointed to by an evolution
		missing = non_stage0_names - pointed_to
		if errors:
			print("Errors:")
			for err in errors:
				print("  ", err)
		else:
			print("All evolution targets are valid.")
		if missing:
			print("Entries not pointed to by any evolution:")
			for name in missing:
				print("  ", name)
		else:
			print("All entries are pointed to by at least one evolution.")

if __name__ == "__main__":
	data = load_json(VALIDATE_FILE)
	monster = data.get('monster', [])
	validate_evolutions(monster)