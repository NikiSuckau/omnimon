import json
import os

from core.utils.asset_utils import open_json


DMX_PATTERN_TABLE = None
DM20_PATTERN_TABLE = None

def get_attack_pattern(level, mini_game, protocol="DMX"):
    if protocol == "DMX":
        global DMX_PATTERN_TABLE
        if DMX_PATTERN_TABLE is None:
            pattern_path = os.path.join(os.path.dirname(__file__), "DMX_pattern.json")
            with open_json(pattern_path) as f:
                DMX_PATTERN_TABLE = json.load(f)
        # Find the pattern_id for this level and mini_game
        for assign in DMX_PATTERN_TABLE["assignments"]:
            if assign["level"] == level and assign["mini-game"] == mini_game:
                pattern_id = assign["pattern_id"]
                break
        else:
            pattern_id = 1  # fallback
        # Find the pattern itself
        for pat in DMX_PATTERN_TABLE["patterns"]:
            if pat["id"] == pattern_id:
                return pat["pattern"]
        return [1, 1, 1, 1, 1]  # fallback
    elif protocol == "DMC_WINNER":
        # DMC uses a fixed pattern for now
        return [1, 1, 1, 1, 2]
    elif protocol == "DMC_LOOSER":
        # DMC uses a fixed pattern for now
        return [1, 1, 1, 1, 1]
    elif protocol == "PEN20":
        return [1, 2, 1, 1, 1]  # PEN20 uses a fixed pattern

def get_dm20_attack_pattern(tag_meter, taps):
    """
    Retrieves the correct attack pattern for the DM20 protocol based on bar1, bar2, and taps.
    :param bar1: The first bar value (int).
    :param bar2: The second bar value (int).
    :param taps: The number of taps (int).
    :return: A list representing the attack pattern.
    """
    global DM20_PATTERN_TABLE
    if DM20_PATTERN_TABLE is None:
        # Load the DM20 pattern table from the JSON file
        pattern_path = os.path.join(os.path.dirname(__file__), "DM20_pattern.json")
        with open_json(pattern_path) as f:
            DM20_PATTERN_TABLE = json.load(f)

    # Search for the matching pattern in the table
    for entry in DM20_PATTERN_TABLE:
        if entry["bar1"] == tag_meter and taps in entry["taps"]:
            return entry["pattern"]

    # Fallback pattern if no match is found
    return [1, 1, 1, 1, 1]