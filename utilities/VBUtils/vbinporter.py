import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# Base URLs
BASE_URL = "https://humulos.com/digimon/vbbe/all/"
DETAILS_URL = "https://humulos.com/digimon/php/details.php"

# Stage mapping
STAGE_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VI+": 7
}

# Default values by stage (from PetTemplates.cs)
DEFAULT_VALUES_BY_STAGE = {
    0: {
        "time": 1, "poop_timer": 0, "energy": 0, "min_weight": 0, "evol_weight": 0,
        "stomach": 0, "hunger_loss": 0, "strength_loss": 0, "heal_doses": 0,
        "condition_hearts": 0, "jogress_avaliable": False, "hp": 0
    },
    1: {
        "time": 10, "poop_timer": 3, "energy": 0, "min_weight": 5, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 3, "strength_loss": 3, "heal_doses": 1,
        "condition_hearts": 1, "jogress_avaliable": False, "hp": 0
    },
    2: {
        "time": 720, "poop_timer": 60, "energy": 0, "min_weight": 10, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 30, "strength_loss": 30, "heal_doses": 1,
        "condition_hearts": 2, "jogress_avaliable": False, "hp": 0
    },
    3: {
        "time": 1440, "poop_timer": 120, "energy": 20, "min_weight": 20, "evol_weight": 0,
        "stomach": 4, "hunger_loss": 48, "strength_loss": 48, "heal_doses": 1,
        "condition_hearts": 3, "jogress_avaliable": False, "hp": 10
    },
    4: {
        "time": 2160, "poop_timer": 120, "energy": 30, "min_weight": 30, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 12
    },
    5: {
        "time": 2400, "poop_timer": 120, "energy": 40, "min_weight": 40, "evol_weight": 0,
        "stomach": 6, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": True, "hp": 15
    },
    6: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 18
    },
    7: {
        "time": 2880, "poop_timer": 120, "energy": 50, "min_weight": 40, "evol_weight": 0,
        "stomach": 8, "hunger_loss": 59, "strength_loss": 59, "heal_doses": 1,
        "condition_hearts": 4, "jogress_avaliable": False, "hp": 20
    }
}

def load_html_from_file(file_path):
    """Load HTML content from a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_soup_from_url(url):
    """Get BeautifulSoup object from URL."""
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_stage_number(stage_str):
    """Convert stage string to number."""
    # Extract Roman numeral from stage string like "Stage IV (Adult)"
    match = re.search(r"Stage\s+([IVX]+)", stage_str)
    if match:
        return STAGE_MAP.get(match.group(1).strip(), 0)
    return 0

def normalize_attribute(attribute_str):
    """Convert attribute string to standard format."""
    attribute_map = {
        "vaccine": "Va",
        "data": "Da", 
        "virus": "Vi",
        "free": ""
    }
    return attribute_map.get(attribute_str.lower(), "")

def normalize_time_string(time_str):
    """Convert time string to HH:MM format."""
    try:
        # Handle formats like "08:00-20:00"
        if "-" in time_str:
            times = time_str.split("-")
            return times[0].strip(), times[1].strip()
        return time_str.strip(), None
    except:
        return "08:00", None

def parse_evolution_conditions(conditions_text):
    """Parse evolution conditions from text."""
    conditions = {}
    
    # Trophies
    if match := re.search(r"(\d+)\+?\s*Trophies", conditions_text, re.I):
        conditions["trophies"] = [int(match.group(1)), 999999]
    
    # Vital Values
    if match := re.search(r"([\d,]+)\+?\s*Vital Values", conditions_text, re.I):
        vital_value = int(match.group(1).replace(',', ''))
        conditions["vital_values"] = [vital_value, 999999]
    
    # Battles
    if match := re.search(r"(\d+)\+?\s*Battles", conditions_text, re.I):
        conditions["battles"] = [int(match.group(1)), 999999]
    
    # Win Ratio
    if match := re.search(r"(\d+)%\+?\s*Win Ratio", conditions_text, re.I):
        conditions["win_ratio"] = [int(match.group(1)), 100]
    
    # Jogress
    # Jogress: prefer a required pet name when present (e.g. "Jogress with Darkdramon");
    # set jogress to the required pet name (string) and include a unresolved version = -1.
    if m := re.search(r"Jogress with ([^,\.]+)", conditions_text, re.I):
        candidate = m.group(1).strip()
        # Remove trailing 'Adult' and 'from the <Line> Dim' parts
        candidate = re.sub(r"\s*Adult\s*$", "", candidate, flags=re.I).strip()
        candidate = re.sub(r"\s*from the .*Dim$", "", candidate, flags=re.I).strip()

        # If candidate refers to attributes (Data/Virus/Vaccine/Free or combinations), treat as attribute-based
        attrs = []
        for attr in ("Data", "Virus", "Vaccine", "Free"):
            if re.search(rf"\b{attr}\b", candidate, re.I):
                attrs.append(attr)

        mapping = {"Data": "Da", "Virus": "Vi", "Vaccine": "Va", "Free": ""}
        if attrs:
            # attribute-based jogress: record attribute(s) instead of pet name
            if len(attrs) == 1:
                conditions["jogress_attribute"] = mapping.get(attrs[0], "")
            else:
                conditions["jogress_attribute"] = [mapping.get(a, "") for a in attrs]
        else:
            # assume candidate is a pet name required for jogress
            conditions["jogress"] = candidate
            # version is unknown here; user can fill later
            conditions["version"] = -1
    elif re.search(r"\bJogress\b", conditions_text, re.I):
        # Jogress mentioned but no 'with' clause; set empty string and unresolved version
        conditions["jogress"] = ""
        conditions["version"] = -1
    
    return conditions

def extract_digimon_code(onclick_str):
    """Extract digimon code from onclick attribute."""
    # Extract from onclick="digimonDetailsUnified('pulse','13','')"
    match = re.search(r"digimonDetailsUnified\(['\"]([^'\"]+)['\"]", onclick_str)
    return match.group(1) if match else None

def get_digimon_details(code, device="13"):
    """Fetch digimon details from the details page."""
    params = {
        "digimon": code,
        "device": device,
        "version": ""
    }
    
    try:
        response = requests.get(DETAILS_URL, params=params)
        response.raise_for_status()
        
        # Save HTML for debugging
        os.makedirs("debug_html", exist_ok=True)
        with open(f"debug_html/{code}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching details for {code}: {e}")
        return None

def extract_digimon_info(details_soup):
    """Extract digimon information from details page."""
    info = {}
    
    # Extract name (prefer dub over sub)
    name_section = details_soup.find("div", class_="diginame")
    if name_section:
        dub_name = name_section.find("p", class_="dub")
        sub_name = name_section.find("p", class_="sub")
        info["name"] = (dub_name or sub_name).get_text(strip=True) if (dub_name or sub_name) else "Unknown"
    
    # Extract stage
    stage_div = details_soup.find("div", string=re.compile(r"Stage\s+[IVX]+"))
    if stage_div:
        info["stage"] = get_stage_number(stage_div.get_text())
    
    # Extract attribute
    attribute_div = details_soup.find("div", class_="attribute")
    if attribute_div:
        info["attribute"] = normalize_attribute(attribute_div.get_text())
    
    # Extract stats from bj divs
    bj_divs = details_soup.find_all("div", class_="bj")
    for bj_div in bj_divs:
        text = bj_div.get_text()
        
        # DP (Power) and Star
        if match := re.search(r"DP:\s*(\d+)\s*\[★(\d+)\]", text):
            info["power"] = int(match.group(1))
            info["star"] = int(match.group(2))
        
        # HP
        if match := re.search(r"HP:\s*(\d+)", text):
            info["hp"] = int(match.group(1))
        
        # AP (Attack)
        if match := re.search(r"AP:\s*(\d+)", text):
            info["attack"] = int(match.group(1))
        
        # Sleep/Wake times
        if match := re.search(r"Awake from:\s*(\d{2}:\d{2})-(\d{2}:\d{2})", text):
            info["wakes"] = match.group(1)
            info["sleeps"] = match.group(2)
        
        # Critical Hit
        if match := re.search(r"Critical Hit:\s*Turn\s*(\d+)", text):
            info["critical_turn"] = int(match.group(1))
    
    # Extract evolutions
    info["evolve"] = []
    evo_section = details_soup.find("div", class_="evo")
    if evo_section:
        evolutions = evo_section.find_all("div", class_="evolutions")
        for evo in evolutions:
            name_elem = evo.find("h3", class_="names")
            if name_elem:
                evo_name = name_elem.get_text(strip=True)
                
                # Find the conditions in the next p.deets element
                next_p = evo.find_next_sibling("p", class_="deets")
                conditions = {}
                if next_p:
                    conditions = parse_evolution_conditions(next_p.get_text())
                
                evolution = {
                    "to": evo_name,
                    **conditions
                }
                info["evolve"].append(evolution)
    
    return info

def extract_egg_lines(soup):
    """Extract egg line information from the main page."""
    egg_lines = []
    
    # Find all anchor divs that start egg lines
    anchors = soup.find_all("div", class_="anchor")
    
    for i, anchor in enumerate(anchors):
        # Extract egg line name from emblem title
        emblem = anchor.find("img", class_="emblem")
        if emblem and emblem.get("title"):
            egg_name = emblem.get("title")
            
            # Find the family div containing the digimon
            family_div = anchor.find_next("div", class_="family")
            if family_div:
                egg_lines.append({
                    "name": egg_name,
                    "version": i + 1,  # Version based on order
                    "family_div": family_div
                })
    
    return egg_lines

def parse_digimon_from_family(family_div, version):
    """Parse all digimon from a family div."""
    digimons = []
    
    # Find all profile divs with onclick events
    profiles = family_div.find_all("div", class_="profile")
    
    for profile in profiles:
        onclick = profile.get("onclick", "")
        code = extract_digimon_code(onclick)
        
        if code:
            print(f"Processing {code}...")
            details_soup = get_digimon_details(code)
            
            if details_soup:
                info = extract_digimon_info(details_soup)
                
                if info.get("name"):
                    # Get default values for this stage
                    stage = info.get("stage", 0)
                    defaults = DEFAULT_VALUES_BY_STAGE.get(stage, DEFAULT_VALUES_BY_STAGE[0])
                    
                    # Build digimon JSON
                    digimon = {
                        "name": info["name"],
                        "stage": stage,
                        "version": version,
                        "special": False,
                        "special_key": "",
                        "sleeps": info.get("sleeps", "21:00"),
                        "wakes": info.get("wakes", "08:00"),
                        "atk_main": info.get("attack", 0),
                        "atk_alt": info.get("attack", 0),
                        "time": defaults["time"],
                        "poop_timer": defaults["poop_timer"],
                        "energy": defaults["energy"],
                        "min_weight": defaults["min_weight"],
                        "evol_weight": defaults["evol_weight"],
                        "stomach": defaults["stomach"],
                        "hunger_loss": defaults["hunger_loss"],
                        "strength_loss": defaults["strength_loss"],
                        "heal_doses": defaults["heal_doses"],
                        "power": info.get("power", 0),
                        "attribute": info.get("attribute", ""),
                        "condition_hearts": defaults["condition_hearts"],
                        "jogress_avaliable": defaults["jogress_avaliable"],
                        "hp": info.get("hp", defaults["hp"]),
                        "evolve": info.get("evolve", [])
                    }
                    
                    # Add new VB-specific attributes
                    if "star" in info:
                        digimon["star"] = info["star"]
                    if "critical_turn" in info:
                        digimon["critical_turn"] = info["critical_turn"]
                    
                    digimons.append(digimon)
    
    return digimons

def create_egg_digimon(egg_name, version):
    """Create the egg digimon for an egg line."""
    defaults = DEFAULT_VALUES_BY_STAGE[0]
    
    return {
        "name": egg_name,
        "stage": 0,
        "version": version,
        "special": False,
        "special_key": "",
        "atk_main": 10,
        "atk_alt": 10,
        "time": defaults["time"],
        "poop_timer": defaults["poop_timer"],
        "energy": defaults["energy"],
        "min_weight": 99,
        "evol_weight": defaults["evol_weight"],
        "stomach": defaults["stomach"],
        "hunger_loss": 65535,
        "strength_loss": 65535,
        "heal_doses": 100,
        "power": defaults["hp"],
        "attribute": "",
        "condition_hearts": defaults["condition_hearts"],
        "jogress_avaliable": defaults["jogress_avaliable"],
        "hp": defaults["hp"],
        "evolve": []
    }

def import_vb_data(html_file_path=None):
    """Main function to import VB data."""
    all_digimons = []
    
    if html_file_path:
        # Load from local file
        html_content = load_html_from_file(html_file_path)
        soup = BeautifulSoup(html_content, "html.parser")
    else:
        # Load from URL
        soup = get_soup_from_url(BASE_URL)
    
    # Extract egg lines
    egg_lines = extract_egg_lines(soup)
    
    for egg_line in egg_lines:
        print(f"Processing egg line: {egg_line['name']} (Version {egg_line['version']})")
        
        # Add the egg itself
        egg_digimon = create_egg_digimon(egg_line["name"], egg_line["version"])
        all_digimons.append(egg_digimon)
        
        # Process all digimon in this family
        family_digimons = parse_digimon_from_family(egg_line["family_div"], egg_line["version"])
        all_digimons.extend(family_digimons)
    
    # Save to JSON
    output_data = {"monster": all_digimons}
    
    with open("vb_digimons.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Imported {len(all_digimons)} digimons to vb_digimons.json")
    return output_data

if __name__ == "__main__":
    # Use local HTML file if provided, otherwise fetch from URL
    html_file = "Bundled.html"  # Change this path as needed
    
    if os.path.exists(html_file):
        print(f"Using local HTML file: {html_file}")
        import_vb_data(html_file)
    else:
        print("Fetching data from URL...")
        import_vb_data()