from PIL import Image
import zipfile

import os
import json

DATA_FILE = 'e:/Omnimon/modules/VB/monster.json'
SPRITE_DB = 'D:/Digimon/DIMS/Sprites/'
EGG_SPRITE_PATH = 'E:/Omnimon/modules/VB/monsters_hidef/'

def load_json(path):
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)

def clean_name(name):
	if not name:
		return ''
	return name.replace('Egg', '').strip()

def find_folders(base, names):
	folders = [f for f in os.listdir(base) if os.path.isdir(os.path.join(base, f))]
	pairs = []
	for raw_name in names:
		name = clean_name(raw_name)
		match = None
		# First try full cleaned name
		for folder in folders:
			if name.lower() in folder.lower():
				match = folder
				break
		# If not found and name contains 'EX', try without 'EX'
		if not match and 'ex' in name.lower():
			name_no_ex = name.lower().replace(' ex', '').replace('ex', '').strip()
			for folder in folders:
				if name_no_ex in folder.lower():
					match = folder
					break
		# If still not found and name contains 'GP', try without 'GP'
		if not match and 'gp' in name.lower():
			name_no_gp = name.lower().replace(' gp', '').replace('gp', '').strip()
			for folder in folders:
				if name_no_gp in folder.lower():
					match = folder
					break
		pairs.append((raw_name, match))
	return pairs

if __name__ == "__main__":
	def process_egg_sprites(entry_name, folder_path):
		sprite_dir = os.path.join(folder_path, 'sprites', 'system', 'other')
		egg_files = ['egg_00.png', 'egg_01.png', 'egg_07.png']
		output_images = []
		for idx, egg_file in enumerate(egg_files):
			egg_path = os.path.join(sprite_dir, egg_file)
			if not os.path.exists(egg_path):
				output_images.append(None)
				continue
			img = Image.open(egg_path).convert('RGBA')
			datas = img.getdata()
			newData = []
			for item in datas:
				# Remove green background (0,255,0)
				if item[0] == 0 and item[1] == 255 and item[2] == 0:
					newData.append((0, 0, 0, 0))
				else:
					newData.append(item)
			img.putdata(newData)
			# Create new 54x48 canvas
			canvas = Image.new('RGBA', (54, 48), (0, 0, 0, 0))
			# Center horizontally, bottom align
			x = (54 - img.width) // 2
			y = 48 - img.height
			canvas.paste(img, (x, y), img)
			output_images.append(canvas)
		# Save images as 0.png, 1.png, 2.png in a zip
		zip_name = f"{entry_name}_dmc.zip"
		zip_path = os.path.join(EGG_SPRITE_PATH, zip_name)
		with zipfile.ZipFile(zip_path, 'w') as zipf:
			for idx, img in enumerate(output_images):
				if img:
					temp_path = os.path.join(EGG_SPRITE_PATH, f"{entry_name}_{idx}.png")
					img.save(temp_path)
					zipf.write(temp_path, arcname=f"{idx}.png")
					os.remove(temp_path)
	data = load_json(DATA_FILE)
	monster = data.get('monster', [])
	stage0_names = [e.get('name') for e in monster if e.get('stage') == 0]
	pairs = find_folders(SPRITE_DB, stage0_names)
	print("Egg name -> Folder pairings:")
	for egg, folder in pairs:
		print(f"  {egg} -> {folder}")
		if folder:
			process_egg_sprites(egg, os.path.join(SPRITE_DB, folder))