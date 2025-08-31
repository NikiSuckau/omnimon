"""
Sprite loading utilities for pets and enemies with fallback support and zip file compatibility.
"""
import os
import zipfile
import pygame
import io
from typing import Dict, List
from core import runtime_globals


def get_sprite_name(pet_name: str, name_format: str = "$_dmc") -> str:
    """
    Generate standardized sprite folder/zip name using module name_format.
    Default format is $_dmc where $ is replaced with pet name and : with _.
    
    Args:
        pet_name: Name of the pet (e.g., "Agumon")
        name_format: Format string (e.g., "$_dmc") where $ = pet name, : = _
    
    Returns:
        Formatted sprite name (e.g., "Agumon_dmc")
    """
    # Replace $ with pet name and : with _
    sprite_name = name_format.replace("$", pet_name).replace(":", "_")
    return sprite_name


def load_sprites_from_directory(sprite_path: str, size: tuple = None, scale: float = 1.0) -> Dict[str, pygame.Surface]:
    """
    Load all PNG sprites from a directory.
    
    Args:
        sprite_path: Path to directory containing sprites
        size: Target size tuple (width, height) for scaling
        scale: Scale factor if size is not provided
        
    Returns:
        Dictionary mapping filename (without .png) to pygame Surface
    """
    sprites = {}
    if not os.path.exists(sprite_path) or not os.path.isdir(sprite_path):
        return sprites
    
    try:
        for filename in os.listdir(sprite_path):
            if filename.lower().endswith('.png'):
                file_path = os.path.join(sprite_path, filename)
                try:
                    sprite = pygame.image.load(file_path).convert_alpha()
                    
                    # Apply scaling
                    if size:
                        sprite = pygame.transform.scale(sprite, size)
                    elif scale != 1.0:
                        base_size = sprite.get_size()
                        new_size = (int(base_size[0] * scale), int(base_size[1] * scale))
                        sprite = pygame.transform.scale(sprite, new_size)
                    
                    sprite_name = filename[:-4]  # Remove .png extension
                    sprites[sprite_name] = sprite
                except pygame.error as e:
                    runtime_globals.game_console.log(f"Failed to load sprite {file_path}: {e}")
    except OSError as e:
        runtime_globals.game_console.log(f"Failed to read directory {sprite_path}: {e}")
    
    return sprites


def load_sprites_from_zip(zip_path: str, pet_name: str, size: tuple = None, scale: float = 1.0) -> Dict[str, pygame.Surface]:
    """
    Load sprites from a zip file. Supports sprites in root or in a subfolder.
    
    Args:
        zip_path: Path to zip file
        pet_name: Name of pet (used to check for subfolder)
        size: Target size tuple (width, height) for scaling
        scale: Scale factor if size is not provided
        
    Returns:
        Dictionary mapping filename (without .png) to pygame Surface
    """
    sprites = {}
    if not os.path.exists(zip_path):
        return sprites
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Get list of PNG files in the zip
            png_files = [f for f in zip_file.namelist() if f.lower().endswith('.png')]
            
            for zip_entry in png_files:
                try:
                    # Read the file data
                    with zip_file.open(zip_entry) as sprite_file:
                        sprite_data = sprite_file.read()
                    
                    # Create pygame surface from the data
                    sprite = pygame.image.load(io.BytesIO(sprite_data)).convert_alpha()
                    
                    # Apply scaling
                    if size:
                        sprite = pygame.transform.scale(sprite, size)
                    elif scale != 1.0:
                        base_size = sprite.get_size()
                        new_size = (int(base_size[0] * scale), int(base_size[1] * scale))
                        sprite = pygame.transform.scale(sprite, new_size)
                    
                    # Extract just the filename (handle both root and subfolder cases)
                    filename = os.path.basename(zip_entry)
                    sprite_name = filename[:-4]  # Remove .png extension
                    sprites[sprite_name] = sprite
                    
                except Exception as e:
                    runtime_globals.game_console.log(f"Failed to load sprite {zip_entry} from {zip_path}: {e}")
                    
    except zipfile.BadZipFile as e:
        runtime_globals.game_console.log(f"Invalid zip file {zip_path}: {e}")
    except Exception as e:
        runtime_globals.game_console.log(f"Failed to read zip file {zip_path}: {e}")
    
    return sprites


def load_pet_sprites(pet_name: str, module_path: str, name_format: str = "$_dmc", size: tuple = None, scale: float = 1.0) -> Dict[str, pygame.Surface]:
    """
    Load pet sprites with fallback support and zip file compatibility.
    
    Loading order:
    1. Try module_path/monsters/PetName_format/ directory
    2. Try module_path/monsters/PetName_format.zip file
    3. Try assets/monsters/PetName_format/ directory (fallback)
    4. Try assets/monsters/PetName_format.zip file (fallback)
    
    Args:
        pet_name: Name of the pet
        module_path: Path to the module folder
        name_format: Format string for sprite naming (default: "$_dmc")
        size: Target size tuple (width, height) for scaling
        scale: Scale factor if size is not provided
        
    Returns:
        Dictionary mapping sprite frame names to pygame Surfaces
    """
    sprite_name = get_sprite_name(pet_name, name_format)
    sprites = {}
    
    # Path 1: Try module_path/monsters/PetName_format/ directory
    module_sprite_dir = os.path.join(module_path, "monsters", sprite_name)
    sprites = load_sprites_from_directory(module_sprite_dir, size, scale)
    if sprites:
        runtime_globals.game_console.log(f"Loaded {len(sprites)} sprites for {pet_name} from module directory")
        return sprites
    
    # Path 2: Try module_path/monsters/PetName_format.zip file
    module_sprite_zip = os.path.join(module_path, "monsters", f"{sprite_name}.zip")
    sprites = load_sprites_from_zip(module_sprite_zip, sprite_name, size, scale)
    if sprites:
        runtime_globals.game_console.log(f"Loaded {len(sprites)} sprites for {pet_name} from module zip")
        return sprites
    
    # Path 3: Try assets/monsters/PetName_format/ directory (fallback)
    assets_sprite_dir = os.path.join("assets", "monsters", sprite_name)
    sprites = load_sprites_from_directory(assets_sprite_dir, size, scale)
    if sprites:
        runtime_globals.game_console.log(f"Loaded {len(sprites)} sprites for {pet_name} from assets directory")
        return sprites
    
    # Path 4: Try assets/monsters/PetName_format.zip file (fallback)
    assets_sprite_zip = os.path.join("assets", "monsters", f"{sprite_name}.zip")
    sprites = load_sprites_from_zip(assets_sprite_zip, sprite_name, size, scale)
    if sprites:
        runtime_globals.game_console.log(f"Loaded {len(sprites)} sprites for {pet_name} from assets zip")
        return sprites
    
    # No sprites found
    runtime_globals.game_console.log(f"No sprites found for {pet_name} ({sprite_name}) with format {name_format}")
    return sprites


def load_enemy_sprites(enemy_name: str, module_path: str, name_format: str = "$_dmc", size: tuple = None, scale: float = 1.0) -> Dict[str, pygame.Surface]:
    """
    Load enemy sprites using the same fallback system as pets.
    
    Args:
        enemy_name: Name of the enemy
        module_path: Path to the module folder
        name_format: Format string for sprite naming (default: "$_dmc")
        size: Target size tuple (width, height) for scaling
        scale: Scale factor if size is not provided
        
    Returns:
        Dictionary mapping sprite frame names to pygame Surfaces
    """
    # Enemies use the same loading system as pets
    return load_pet_sprites(enemy_name, module_path, name_format, size, scale)


def convert_sprites_to_list(sprites_dict: Dict[str, pygame.Surface], max_frames: int = 20) -> List[pygame.Surface]:
    """
    Convert sprite dictionary to ordered list for compatibility with existing code.
    
    Args:
        sprites_dict: Dictionary mapping sprite names to surfaces
        max_frames: Maximum number of frames to include
        
    Returns:
        List of sprite surfaces ordered by frame number (0.png, 1.png, etc.)
    """
    sprite_list = []
    for i in range(max_frames):
        frame_name = str(i)
        if frame_name in sprites_dict:
            sprite_list.append(sprites_dict[frame_name])
        else:
            break  # Stop at first missing frame
    return sprite_list
