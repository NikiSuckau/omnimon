BLACK = (31,32,38)
GREY = (162, 173, 193)

PURPLE_DARK = (76, 46, 77)
PURPLE_DARK_LINE = (30, 17, 30)
PURPLE = (204, 82, 133)
PURPLE_LIGHT = (255, 238, 217)

GREEN_DARK = (46, 77, 69)
GREEN = (102, 204, 82)
GREEN_LIGHT = (217, 255, 218)

BLUE_DARK = (46, 62, 77)
BLUE = (82, 163, 204)
BLUE_LIGHT = (217, 255, 248)

YELLOW_DARK = (153, 89, 46)
YELLOW = (179, 145, 45)
YELLOW_LIGHT = (255, 255, 217)

RED_DARK = (77, 39, 46)
RED = (204, 82, 82) 
RED_LIGHT = (255, 217, 217)

# Base sizes for 240x240 resolution (1x scale)
BASE_RESOLUTION = 240
TITLE_FONT = "assets/DigimonBasic.ttf"
TEXT_FONT = "assets/ProggySmall.ttf"

# Font sizes per scale level (to avoid blurry text)
TITLE_FONT_SIZES = {1: 24, 2: 48, 3: 72, 4: 96}
TEXT_FONT_SIZES = {1: 16, 2: 32, 3: 48, 4: 64}

# Border sizes per scale level
BORDER_SIZES = {1: 2, 2: 4, 3: 6, 4: 8}

# Spacing values per scale level
SPACING_VALUES = {1: 1, 2: 2, 3: 3, 4: 4}

# Sprite scale mapping: UI scale -> sprite scale
# 1x UI = 1x sprites, 2x UI = 2x sprites, 3x UI = 2x sprites, 4x UI = 3x sprites
SPRITE_SCALE_MAP = {1: 1, 2: 2, 3: 2, 4: 3}

# List sizing constants for different component types
# Fixed list components (like inventory) maintain fixed slot counts at different scales
FIXED_LIST_SLOTS = {1: 4, 2: 6, 3: 8, 4: 10}

# Adaptive list components (like pet selector) scale content to fit available space
ADAPTIVE_LIST_MIN_SLOTS = {1: 1, 2: 1, 3: 1, 4: 1}
ADAPTIVE_LIST_MAX_SLOTS = {1: 4, 2: 6, 3: 8, 4: 10}

# Standardized size constraints for different component types
HEXAGON_SIZE_LIMITS = {
    "min_base": 24,  # Minimum size at 1x scale 
    "max_base": 64,  # Maximum size at 1x scale
    "scaling_type": "adaptive"  # adaptive = scales to fit content, fixed = uses scale multiplier
}

BUTTON_SIZE_CONSTRAINTS = {
    "min_base": 32,
    "max_base": 128,
    "scaling_type": "fixed"
}

# ===============================
# Unified Scaling Utility Functions
# ===============================

def get_sprite_scale_factor(ui_scale):
    """Get the scaling factor needed to scale sprites to match UI scale"""
    sprite_scale = SPRITE_SCALE_MAP.get(ui_scale, 1)
    return ui_scale / sprite_scale

def get_font_size(font_type, ui_scale):
    """Get font size for given type and UI scale"""
    if font_type == "title":
        return TITLE_FONT_SIZES.get(ui_scale, 24)
    elif font_type == "text":
        return TEXT_FONT_SIZES.get(ui_scale, 16)
    else:
        return 16

def get_border_size(ui_scale):
    """Get border size for UI scale"""
    return BORDER_SIZES.get(ui_scale, 2)

def get_spacing_value(ui_scale):
    """Get spacing value for UI scale"""
    return SPACING_VALUES.get(ui_scale, 1)

def scale_component_size(base_size, ui_scale, scaling_type="fixed"):
    """
    Scale a component size based on UI scale and scaling type.
    
    Args:
        base_size: Base size at 1x scale
        ui_scale: Current UI scale factor  
        scaling_type: "fixed" (multiplies by ui_scale) or "adaptive" (uses constraints)
    """
    if scaling_type == "fixed":
        return base_size * ui_scale
    elif scaling_type == "adaptive":
        # For adaptive scaling, use size constraints
        return base_size  # Base size is used as-is for adaptive components
    else:
        return base_size

def get_list_capacity(list_type, ui_scale):
    """
    Get the number of items a list should display at the given UI scale.
    
    Args:
        list_type: "fixed" for inventory-style lists, "adaptive" for pet selectors
        ui_scale: Current UI scale
    """
    if list_type == "fixed":
        return FIXED_LIST_SLOTS.get(ui_scale, 4)
    elif list_type == "adaptive":
        return ADAPTIVE_LIST_MAX_SLOTS.get(ui_scale, 4)
    else:
        return 4

def apply_size_constraints(calculated_size, constraints, ui_scale):
    """
    Apply size constraints to a calculated size.
    
    Args:
        calculated_size: The size calculated by layout algorithms
        constraints: Dictionary with min_base, max_base, scaling_type
        ui_scale: Current UI scale
    """
    min_size = constraints["min_base"]
    max_size = constraints["max_base"] 
    
    if constraints["scaling_type"] == "fixed":
        # For fixed scaling, scale the limits by UI scale
        min_size *= ui_scale
        max_size *= ui_scale
    
    return max(min_size, min(calculated_size, max_size))