#=====================================================================
# BattleEncounter
#=====================================================================

import math
import random
import pygame
from components.window_xai import WindowXai
from components.window_xaibar import WindowXaiBar
from core import game_globals, runtime_globals
from core.animation import PetFrame
from core.combat.game_battle import GameBattle
from core.combat.sim.models import Digimon
from core.game_module import sprite_load
from core.utils.module_utils import get_module
from core.utils.pet_utils import distribute_pets_evenly, get_battle_targets
from core.utils.pygame_utils import blit_with_cache, get_font, load_attack_sprites, module_attack_sprites, sprite_load_percent
from core.utils.scene_utils import change_scene
from core.utils.utils_unlocks import unlock_item
from core.utils import inventory_utils
from core.combat.sim.global_battle_simulator import GlobalBattleSimulator
from core import constants
from core.combat import combat_constants
from core.game_quest import QuestType
from core.utils.quest_event_utils import update_quest_progress

#=====================================================================
# BattleEncounter Class
#=====================================================================

BAR_COUNTER = 20  # Number of frames for the bar counter

class BattleEncounter:
    """
    Handles the logic and rendering for a battle encounter.
    """

    #========================
    # Region: Setup & State
    #========================

    def __init__(self, module, area=0, round=0, version=1, pvp_mode=False):
        """
        Initializes the BattleEncounter, loading graphics and setting initial state.
        """
        # Load module-specific attack sprites for pets and enemies
        self.pvp_mode = pvp_mode
        self.module_attack_sprites = {}
        self.module = get_module(module)
        self.set_initial_state(area, round, version)

        # Graphics and assets (keep in __init__)
        self.backgroundIm = sprite_load_percent(constants.BATTLE_BACKGROUND_PATH, percent=100, keep_proportion=True, base_on="width")
        self.battle_sprite = sprite_load_percent(constants.BATTLE_SPRITE_PATH, percent=100, keep_proportion=True, base_on="width")
        self.level_sprite = sprite_load_percent(constants.BATTLE_LEVEL_SPRITE_PATH, percent=100, keep_proportion=True, base_on="width")
        self.bar_piece = sprite_load_percent(constants.BAR_PIECE_PATH, percent=(int(12 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self.bar_back = sprite_load_percent(constants.BAR_BACK_PATH, percent=(int(170 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self.training_max = sprite_load_percent(constants.TRAINING_MAX_PATH, percent=(int(60 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self.ready_sprite = sprite_load_percent(constants.READY_SPRITE_PATH, percent=100, keep_proportion=True, base_on="width")
        self.go_sprite = sprite_load_percent(constants.GO_SPRITE_PATH, percent=100, keep_proportion=True, base_on="width")

        self.font = get_font(constants.FONT_SIZE_LARGE)
        self.font_small = get_font(constants.FONT_SIZE_MEDIUM)
        self.result_sprites = {
            "clear": [
                sprite_load_percent(constants.CLEAR1_PATH, percent=100, keep_proportion=True, base_on="width"),
                sprite_load_percent(constants.CLEAR2_PATH, percent=100, keep_proportion=True, base_on="width")
            ],
            "warning": [
                sprite_load_percent(constants.WARNING1_PATH, percent=100, keep_proportion=True, base_on="width"),
                sprite_load_percent(constants.WARNING2_PATH, percent=100, keep_proportion=True, base_on="width")
            ]
        }
        self.ready_sprites = {
            1: sprite_load_percent(constants.READY_SPRITES_PATHS[1], 100, keep_proportion=True, base_on="width"),
            2: sprite_load_percent(constants.READY_SPRITES_PATHS[2], 100, keep_proportion=True, base_on="width"),
            3: sprite_load_percent(constants.READY_SPRITES_PATHS[3], 100, keep_proportion=True, base_on="width")
        }
        self.count_sprites = {
            4: sprite_load_percent(constants.COUNT_SPRITES_PATHS[4], 100, keep_proportion=True, base_on="width"),
            3: sprite_load_percent(constants.COUNT_SPRITES_PATHS[3], 100, keep_proportion=True, base_on="width"),
            2: sprite_load_percent(constants.COUNT_SPRITES_PATHS[2], 100, keep_proportion=True, base_on="width"),
            1: sprite_load_percent(constants.COUNT_SPRITES_PATHS[1], 100, keep_proportion=True, base_on="width")
        }
        self.mega_hit = sprite_load_percent(constants.MEGA_HIT_PATH, 100, keep_proportion=True, base_on="width")
        self.attack_sprites = load_attack_sprites()
        
        
        self.load_module_attack_sprites()
        
        self.hit_animation_frames = self.load_hit_animation()
        self.hit_animations = []
        self.turn_limit = 12
        self.super_hits = 0
        self.strength = 0
        

    def set_initial_state(self, area=0, round=0, version=1):
        """
        Set all non-graphic variables for (re)initialization.
        """
        # --- Jumper Gate: skip to boss if status_boost is active ---
        if not self.pvp_mode:
            if (
                "skip_to_boss" in game_globals.battle_effects
                and game_globals.battle_effects["skip_to_boss"].get("amount", 0) > 0
            ):
                # Find the next boss round for this area
                current_area = game_globals.battle_area[self.module.name] if area == 0 else area
                round_to_check = game_globals.battle_round[self.module.name] if round == 0 else round
                # Only skip if not already at boss
                while not self.module.is_boss(current_area, round_to_check, version):
                    round_to_check += 1
                # Use local variables for area and round
                area = current_area
                round = round_to_check  # Set round to boss round

        self.phase = "level"
        self.after_attack_phase = None
        self.victory_status = None
        self.bonus_experience = 0
        self.frame_counter = 0
        self.enemies = []

        if self.pvp_mode:
            self.area = 0
            self.round = 0

            self.boss = False
            self.enemy_entry_counter = 0
        else:
            # Use self.area and self.round, not the global values
            self.area = area if area != 0 else game_globals.battle_area[self.module.name]
            self.round = round if round != 0 else game_globals.battle_round[self.module.name]

            self.boss = self.module.is_boss(self.area, self.round, version)
            self.enemy_entry_counter = constants.PET_WIDTH + (2 * constants.UI_SCALE)

            # --- Apply XAI roll boost (Seven Switch) ---
            if "xai_roll" in game_globals.battle_effects:
                xai_val = game_globals.battle_effects["xai_roll"].get("amount", None)
                if xai_val is not None:
                    runtime_globals.game_console.log(f"[BattleEncounter] XAI roll boost applied: {xai_val}")

            # --- Apply EXP multiplier boost (EXP Coat) ---
            if "exp_multiplier" in game_globals.battle_effects:
                exp_val = game_globals.battle_effects["exp_multiplier"].get("amount", None)
                if exp_val is not None:
                    runtime_globals.game_console.log(f"[BattleEncounter] EXP multiplier boost applied: x{exp_val}")

            # --- Apply Jumper Gate boost ---
            if "skip_to_boss" in game_globals.battle_effects:
                skip_val = game_globals.battle_effects["skip_to_boss"].get("amount", None)
                if skip_val:
                    runtime_globals.game_console.log(f"[BattleEncounter] Jumper Gate: Skipping to boss round.")

        self.strength = 0
        self.bar_level = 14
        self.xai_phase = 0
        self.xai_number = 1
        self.window_xai = None
        self.window_xaibar = None

        self.result_timer = 0
        self.press_counter = 0
        self.final_color = 3
        self.correct_color = 0

        if self.pvp_mode:
            self.hp_boost = 0
            self.attack_boost = 0
            self.strength_bonus = 0
        else:
            self.load_enemies()

            # --- Apply HP boost from status_boost items if present ---
            self.hp_boost = 0
            if "hp" in game_globals.battle_effects:
                self.hp_boost = game_globals.battle_effects["hp"].get("amount", 0)
                runtime_globals.game_console.log(f"[BattleEncounter] HP boost applied: +{self.hp_boost}")

            # --- Apply Attack boost from status_boost items (DMX ruleset) ---
            self.attack_boost = 0
            if "attack" in game_globals.battle_effects:
                self.attack_boost = game_globals.battle_effects["attack"].get("amount", 0)
                runtime_globals.game_console.log(f"[BattleEncounter] Attack boost applied: +{self.attack_boost}")

            # --- Apply Strength boost from status_boost items (PW Board) ---
            self.strength_bonus = 0
            if "strength" in game_globals.battle_effects:
                self.strength_bonus = game_globals.battle_effects["strength"].get("amount", 0)
                runtime_globals.game_console.log(f"[BattleEncounter] Strength boost applied: +{self.strength_bonus}")

        self.battle_player = GameBattle(get_battle_targets(), self.enemies, self.hp_boost, self.attack_boost, self.module)
        # PvP ordering flag: when True, enemy actions are processed before pets
        self.enemy_first = False
        
        # For PvP mode, use staggered cooldowns to prevent simultaneous attacks
        if self.pvp_mode:
            self.battle_player.reset_cooldowns_staggered()

        # Debug battle log display (when DEBUG flag is on)
        self.debug_battle_logs = []  # List of log entries per pet position: [{"turn": int, "hit": str, "arrow": str}, ...]
        self.init_debug_battle_logs()

        # Reload module attack sprites for the current battle participants
        self.load_module_attack_sprites()

    def prime_enemy_first(self):
        """Configure this encounter so enemy actions are processed before pets.

        This sets the flag and primes the BattlePlayer shot/phase arrays so
        the enemy (team2) will fire on the first update cycle.
        """
        self.enemy_first = True
        if not hasattr(self, 'battle_player') or self.battle_player is None:
            return
        bp = self.battle_player
        n = max(len(bp.team1), len(bp.team2))
        for i in range(n):
            if i < len(bp.team1_shot):
                bp.team1_shot[i] = False
            if i < len(bp.team2_shot):
                bp.team2_shot[i] = True
            if i < len(bp.phase):
                bp.phase[i] = "enemy_attack"
        
        # For PvP clients, use staggered cooldowns to ensure proper synchronization
        if self.pvp_mode:
            bp.reset_cooldowns_staggered()

    def setup_pvp_teams(self, my_pets, enemy_pet_data):
        """Sets up teams for PvP battle from pet data."""
        from core.game_enemy import GameEnemy
        
        # Create enemy objects from received pet data
        enemy_objects = []
        for i, pet_data in enumerate(enemy_pet_data):
            # Create GameEnemy with the pet data
            enemy = GameEnemy(
                name=pet_data["name"], 
                power=pet_data["power"],
                attribute=pet_data["attribute"], 
                area=0,  # PvP doesn't use area/round
                round=0,
                version=1,  # Default version
                atk_main=pet_data["atk_main"],
                atk_alt=pet_data["atk_alt"],
                handicap=0,  # No handicap in PvP
                id=i,  # Use index as ID
                stage=pet_data["stage"],
                hp=pet_data["hp"],
                unlock="",  # No unlock requirements for PvP
                prize=""  # No prizes in PvP
            )
            
            # Set additional properties that might be needed
            enemy.level = pet_data["level"]
            enemy.sick = 1 if pet_data["sick"] else 0
            enemy.traited = pet_data["traited"]
            enemy.shook = pet_data["shook"]
            enemy.module = pet_data["module"]
            
            # Load sprite for the enemy
            enemy.load_sprite(enemy.module, boss=False)
            
            enemy_objects.append(enemy)
        
        # Update battle_player with PvP teams (my pets vs enemy objects)
        self.battle_player = GameBattle(my_pets, enemy_objects, 0, 0, self.module)
        self.enemies = enemy_objects
        
        # Initialize debug logs for PvP
        if constants.DEBUG_MODE:
            self.init_debug_battle_logs()

    def init_debug_battle_logs(self):
        """Initialize debug battle log entries for each pet position."""
        if not constants.DEBUG_MODE:
            return
        
        num_pets = len(get_battle_targets()) if not self.pvp_mode else len(self.battle_player.team1)
        self.debug_battle_logs = []
        for i in range(num_pets):
            self.debug_battle_logs.append({
                "turn": 1,
                "hit": "",
                "arrow": ""
            })

    def update_debug_battle_logs(self):
        """Update debug battle logs with current phase information and hit results."""
        if not constants.DEBUG_MODE or not hasattr(self, 'debug_battle_logs'):
            return
            
        for i in range(len(self.debug_battle_logs)):
            if i >= len(self.battle_player.phase) or i >= len(self.battle_player.turns):
                continue
                
            phase = self.battle_player.phase[i]
            turn = self.battle_player.turns[i]
            
            # Update turn number
            self.debug_battle_logs[i]["turn"] = turn
            
            # Update arrow and hit info based on phase
            if phase == "pet_charge":
                self.debug_battle_logs[i]["arrow"] = ">"
                # Show last hit result if available
                self.debug_battle_logs[i]["hit"] = self.get_last_hit_result(i, "pet")
            elif phase == "pet_attack":
                self.debug_battle_logs[i]["arrow"] = ">"
                self.debug_battle_logs[i]["hit"] = ""
            elif phase == "enemy_charge":
                self.debug_battle_logs[i]["arrow"] = "<"
                # Show last hit result if available
                self.debug_battle_logs[i]["hit"] = self.get_last_hit_result(i, "enemy")
            elif phase == "enemy_attack":
                self.debug_battle_logs[i]["arrow"] = "<"
                self.debug_battle_logs[i]["hit"] = ""
            else:
                self.debug_battle_logs[i]["arrow"] = ""
                self.debug_battle_logs[i]["hit"] = ""

    def get_last_hit_result(self, pet_index, attacker_type):
        """Get the last hit result for display in debug logs."""
        if not hasattr(self, 'global_battle_log') or not self.global_battle_log:
            return ""
            
        try:
            # Predict the upcoming attack for the current turn (show before it lands)
            turn = self.battle_player.turns[pet_index]
            turn_idx = max(0, int(turn) - 1)  # use current turn (0-based)
            if turn_idx < len(self.global_battle_log.battle_log):
                turn_log = self.global_battle_log.battle_log[turn_idx]

                # Support both dataclass objects and dict shapes
                attacks = None
                if hasattr(turn_log, 'attacks'):
                    attacks = turn_log.attacks
                elif isinstance(turn_log, dict):
                    attacks = turn_log.get('attacks', [])
                else:
                    attacks = []

                for attack in attacks:
                    # extract fields generically
                    if isinstance(attack, dict):
                        dev = attack.get('device')
                        attacker = attack.get('attacker')
                        defender = attack.get('defender')
                        hit = attack.get('hit')
                        damage = attack.get('damage', 0)
                    else:
                        dev = getattr(attack, 'device', None)
                        attacker = getattr(attack, 'attacker', None)
                        defender = getattr(attack, 'defender', None)
                        hit = getattr(attack, 'hit', None)
                        damage = getattr(attack, 'damage', 0)

                    try:
                        attacker = int(attacker) if attacker is not None else None
                    except Exception:
                        attacker = None
                    try:
                        defender = int(defender) if defender is not None else None
                    except Exception:
                        defender = None

                    if attacker_type == 'pet' and dev == 'device1' and attacker == pet_index:
                        if not hit:
                            return 'Miss!'
                        if damage <= 2:
                            return 'Hit!'
                        if damage == 3:
                            return 'SuperHit!'
                        if damage >= 4:
                            return 'MegaHit!'
                        return 'Hit!'

                    if attacker_type == 'enemy' and dev == 'device2' and defender == pet_index:
                        if not hit:
                            return 'Miss!'
                        if damage <= 2:
                            return 'Hit!'
                        if damage == 3:
                            return 'SuperHit!'
                        if damage >= 4:
                            return 'MegaHit!'
                        return 'Hit!'
        except:
            pass
            
        return ""

    def get_hit_text_color(self, hit_text):
        """Get the color for hit text display."""
        if hit_text == "Miss!":
            return constants.FONT_COLOR_RED
        elif hit_text == "Hit!":
            return constants.FONT_COLOR_DEFAULT  # White
        elif hit_text == "SuperHit!":
            return constants.FONT_COLOR_GREEN
        elif hit_text == "MegaHit!":
            return (255, 192, 203)  # Pink
        else:
            return constants.FONT_COLOR_DEFAULT

    def load_enemies(self):
        """
        Loads enemy data for the current area and round, sets up enemy positions and health.
        """
        selected_pets = get_battle_targets()
        version_range = self.module.get_enemy_versions(self.area, self.round)
        versions = []
        for p in selected_pets:
            if not version_range:
                versions.append(p.version)
            elif p.version not in version_range:
                versions.append(random.choice(version_range))
            else:
                versions.append(p.version)

        self.enemies = self.module.get_enemies(self.area, self.round, versions)
        if self.boss:
            # If it's a boss, ensure we have only one enemy
            self.enemies = [self.enemies[0]] if self.enemies else []

        for enemy in self.enemies:
            if enemy:
                enemy.load_sprite(self.module.name, self.boss)

    def load_hit_animation(self):
        """
        Loads the hit animation sprite sheet and splits it into frames.
        """
        sprite_sheet = sprite_load(constants.HIT_ANIMATION_PATH, (constants.PET_WIDTH * 12, constants.PET_HEIGHT))
        frames = []
        for i in range(12):
            frame = sprite_sheet.subsurface(pygame.Rect(i * constants.PET_WIDTH, 0, constants.PET_WIDTH, constants.PET_HEIGHT))
            frames.append(frame)
        return frames

    def load_module_attack_sprites(self):
        """
        Load module-specific attack sprites for all pets and enemies in battle.
        """
        # Get all unique modules from pets and enemies
        modules_to_load = set()
        
        # Add modules from battle targets (pets)
        for pet in get_battle_targets():
            modules_to_load.add(pet.module)
        
        # Add module from enemies (they use the same module as the battle area)
        modules_to_load.add(self.module.name)
        
        # Load sprites for each unique module
        for module_name in modules_to_load:
            self.module_attack_sprites[module_name] = module_attack_sprites(module_name)

    def get_attack_sprite(self, entity, attack_id):
        """
        Get attack sprite for a pet or enemy, preferring module-specific sprites over defaults.
        """
        module_name = getattr(entity, 'module', self.module.name)
        
        # First try module-specific attack sprites
        if module_name in self.module_attack_sprites:
            module_sprite = self.module_attack_sprites[module_name].get(str(attack_id))
            if module_sprite:
                return module_sprite
        
        # Fall back to default attack sprites
        return self.attack_sprites.get(str(attack_id))

    #========================
    # Region: Update Methods
    #========================

    def update(self):
        """
        Main update loop for the battle encounter, calls phase-specific updates.
        """
        self.frame_counter += 1
        self.battle_player.increment_frame_counters()

        if self.phase == "level":
            self.update_level()
        elif self.phase == "entry":
            self.update_entry()
        elif self.phase == "intimidate":
            self.update_intimidate()
        elif self.phase == "set_attribute":
            self.update_set_attribute()
        elif self.phase == "alert":
            self.update_alert()
        elif self.phase == "charge":
            self.update_charge()
        elif self.phase == "battle":
            self.update_battle()
        elif self.phase == "clear":
            self.update_clear()
        elif self.phase == "result":
            self.update_result()

        runtime_globals.game_message.update()

        advance_every = max(1, int( constants.FRAME_RATE // 15))
        if self.frame_counter % advance_every == 0:
            for anim in self.hit_animations:
                anim[0] += 1  # Advance one frame

        self.hit_animations = [a for a in self.hit_animations if a[0] < len(self.hit_animation_frames)]

    def update_level(self):
        """
        Update logic for the level phase, transitions to entry phase after duration.
        """
        if self.frame_counter >= combat_constants.LEVEL_DURATION_FRAMES:
            self.phase = "entry"
            self.frame_counter = 0
            runtime_globals.game_sound.play("battle")

    def update_entry(self):
        """
        Update logic for the enemy entry phase, moves enemies into position.
        """

        self.enemy_entry_counter -= combat_constants.ENEMY_ENTRY_SPEED * (30 / constants.FRAME_RATE)  # Frame-rate independent speed

        if self.enemy_entry_counter <= 0:
            runtime_globals.game_console.log("Entering intimidate phase")
            self.phase = "intimidate"
            self.frame_counter = 0
            self.enemy_entry_counter = 0
            self.battle_player.reset_frame_counters()

    def update_intimidate(self):
        """
        Update logic for the intimidate phase, transitions to set_attribute or alert phase.
        """
        if self.frame_counter >= combat_constants.IDLE_ANIM_DURATION:
            self.phase = "set_attribute" if self.module.ruleset == "penc" else "alert"
            self.frame_counter = 0

    def update_set_attribute(self):
        """
        Update logic for setting pet attributes, transitions to alert phase.
        """
        #self.frame_counter += 1
        if self.frame_counter >= int(combat_constants.READY_FRAME_COUNTER):
            self.phase = "alert"
            self.frame_counter = 0

    def update_alert(self):
        """
        Update logic for the alert phase, prepares for charge phase after duration.
        """
        if self.frame_counter == int(combat_constants.ALERT_DURATION_FRAMES * 0.8):
            runtime_globals.game_sound.play("happy")
        if self.frame_counter > combat_constants.ALERT_DURATION_FRAMES:
            runtime_globals.game_console.log("Entering charge phase")
            self.phase = "charge"
            self.frame_counter = 0
            self.bar_timer = pygame.time.get_ticks()
            self.setup_charge()

    def setup_charge(self):
        """
        Setup logic for the charge phase, varies by ruleset.
        """
        if self.module.ruleset == "dmc":
            self.strength = 0
            self.bar_level = 14
            self.battle_player.reset_frame_counters()
        elif self.module.ruleset == "dmx":
            self.xai_phase = 1  # Start Xai roll
            self.window_xai = WindowXai(
                x=constants.SCREEN_WIDTH // 2 - int(100 * constants.UI_SCALE) // 2,
                y=constants.SCREEN_HEIGHT // 2 - int(100 * constants.UI_SCALE) // 2,
                width=int(100 * constants.UI_SCALE),
                height=int(100 * constants.UI_SCALE),
                xai_number=1
            )
            self.window_xai.roll()
        elif self.module.ruleset == "penc":
            self.press_counter = 0
            self.rotation_index = 3

    def update_charge(self):
        """
        Update logic for the charge phase, handles input and transitions to pet_charge phase.
        """
        if self.module.ruleset == "dmx":
            if self.xai_phase == 1:
                self.window_xai.update()
                if not self.window_xai.rolling and not self.window_xai.stopping:
                    self.xai_phase = 2
                    self.window_xaibar = WindowXaiBar(
                        x=constants.SCREEN_WIDTH // 2 - int(152 * constants.UI_SCALE) // 2,
                        y=constants.SCREEN_HEIGHT // 2 - int(72 * constants.UI_SCALE) // 2 + int(48 * constants.UI_SCALE),
                        xai_number=self.xai_number,
                        pet=self.attacking_pet if hasattr(self, "attacking_pet") and self.attacking_pet else get_battle_targets()[0]
                    )
                    self.window_xaibar.start()
            elif self.xai_phase == 2:
                self.window_xaibar.update()
        if self.module.ruleset != "dmx" or self.xai_phase == 3:
            if pygame.time.get_ticks() - self.bar_timer > combat_constants.BAR_HOLD_TIME_MS:
                runtime_globals.game_console.log("Entering pet_charge phase")
                self.phase = "battle"
                self.frame_counter = 0
                self.battle_player.reset_frame_counters()
                self.battle_player.reset_jump_and_forward()
                if self.module.ruleset == "penc":
                    self.calculate_results()
                self.calculate_combat_for_pairs()

    def calculate_results(self):
        self.correct_color = self.get_first_pet_attribute()
        self.final_color = self.rotation_index
        pets = self.battle_player.team1
        if not pets:
            return

        # Calculate hits for the first pet only
        pet = pets[0]
        shakes = self.press_counter
        attr_type = getattr(pet, "attribute", "")


        if shakes < 2:
            hits = 0
        else:
            # Color mapping: 1=Red, 2=Yellow, 3=Blue
            color = self.final_color
            if attr_type in ("", "Va"):
                if color == 1:      # Red
                    hits = 3
                elif color == 2:    # Yellow
                    hits = 2
                elif color == 3:    # Blue
                    hits = 1
                else:
                    hits = 0
            elif attr_type == "Da":
                if color == 2:      # Yellow
                    hits = 3
                elif color == 1:    # Red
                    hits = 2
                elif color == 3:    # Blue
                    hits = 1
                else:
                    hits = 0
            elif attr_type == "Vi":
                if color == 3:      # Blue
                    hits = 3
                elif color == 2:    # Yellow
                    hits = 2
                elif color == 1:    # Red
                    hits = 1
                else:
                    hits = 0
            else:
                hits = 0

        # Assign the same result to all pets
        self.super_hits = hits

    def get_first_pet_attribute(self):
        """
        Get the attribute of the first pet, used for determining attack color in charge phase.
        """
        pet = get_battle_targets()[0]
        if pet.attribute in ["", "Va"]:
            return 1
        elif pet.attribute == "Da":
            return 2
        elif pet.attribute == "Vi":
            return 3
        return 1
    
    def process_battle_results(self):
        """
        Processes the results of a global protocol battle using the new log structure.
        """
        # Skip experience and level-ups for PvP mode
        if self.pvp_mode:
            runtime_globals.game_console.log("[BattleEncounter] PvP battle completed - no experience awarded")
            return
            
        # If defeat, no XP for anyone
        if self.victory_status == "Defeat":
            self.battle_player.xp = 0
            self.battle_player.bonus = 0
            # Call finish_battle here to update DP, battle number, and win rate for a loss.
            for i, pet in enumerate(self.battle_player.team1):
                pet.finish_battle(self.victory_status == "Victory", self.battle_player.team2[0], self.area, (self.boss or not self.module.battle_sequential_rounds))
            return

        # If victory, calculate XP for winners and bonus
        xp_multiplier = 1
        if "exp_multiplier" in game_globals.battle_effects:
            xp_multiplier = game_globals.battle_effects["exp_multiplier"].get("amount", 1)
        boss = self.boss

        self.battle_player.xp = int((2.83 * self.battle_player.team2[0].stage) + (0.81 * self.battle_player.team2[0].power) + (0.17 * self.round) + ((0.67 * self.area) * (6.39 if boss else 0))) * xp_multiplier
        #total_xp = int(self.battle_player.xp * len(self.battle_player.team1))

        if all(digimonstatus.alive for digimonstatus in self.global_battle_log.device1_final):
            # If all pets are alive, apply bonus XP
            self.battle_player.bonus = int(self.battle_player.xp * 0.1)

        for i, pet in enumerate(self.battle_player.team1):
            prev_level = getattr(pet, "level", 1)
            # Add XP and bonus to pet, check for level up
            if hasattr(pet, "add_experience"):
                pet.add_experience(self.battle_player.xp + self.battle_player.bonus)
                self.battle_player.level_up[i] = getattr(pet, "level", 1) > prev_level
            else:
                self.battle_player.level_up[i] = False

            pet.finish_battle(self.victory_status == "Victory", self.battle_player.team2[0], self.area, (self.boss or not self.module.battle_sequential_rounds))

        # --- Prize logic for Victory ---
        self.prize_item = None
        if self.victory_status == "Victory":
            # Collect all enemies with a prize
            prize_enemies = [e for e in self.battle_player.team2 if hasattr(e, "prize") and e.prize]
            if prize_enemies:
                chosen_enemy = random.choice(prize_enemies)
                prize_name = getattr(chosen_enemy, "prize", None)
                if prize_name and hasattr(self.module, "items") and self.module.items:
                    matching_items = [item for item in self.module.items if item.name == prize_name]
                    if matching_items:
                        self.prize_item = random.choice(matching_items)
                        inventory_utils.add_to_inventory(self.prize_item.id, 1)
                        runtime_globals.game_console.log(f"Received item: {self.prize_item.name}")

        # --- Remove expired boosts if boss or not sequential rounds ---
        if self.boss or not self.module.battle_sequential_rounds:
            to_remove = []
            for status, effect in game_globals.battle_effects.items():
                if "boost_time" in effect:
                    effect["boost_time"] -= 1
                    if effect["boost_time"] <= 0:
                        to_remove.append(status)
            if to_remove:
                runtime_globals.game_console.log(f"[BattleEncounter] Removing expired boosts: {', '.join(to_remove)}")
            for status in to_remove:
                del game_globals.battle_effects[status]

    def update_battle(self):
        self.battle_player.update()

        # Update debug battle logs based on current phases
        if constants.DEBUG_MODE:
            self.update_debug_battle_logs()

        # For PvP, always process attacks in the same order (team1 then team2)
        # The battle log device labels are pre-swapped for clients so the correct attacks are found
        for i in range(len(self.battle_player.team1)):
            if self.battle_player.turns[i] <= self.turn_limit and self.battle_player.team1_shot[i] and self.battle_player.phase[i] == "pet_attack":
                self.setup_pet_attack(self.battle_player.team1[i])
                self.battle_player.team1_shot[i] = False

        for i in range(len(self.battle_player.team2)):
            if self.battle_player.turns[i] <= self.turn_limit and self.battle_player.team2_shot[i] and self.battle_player.phase[i] == "enemy_attack":
                self.setup_enemy_attack(self.battle_player.team2[i])
                self.battle_player.team2_shot[i] = False

        self.update_battle_pet_projectiles()
        self.update_battle_enemy_projectiles()

        # Check for battle termination
        if self.pvp_mode:
            # For PvP, check if simulation is complete or if we've run out of battle log entries
            max_turn = max(self.battle_player.turns)
            battle_log_length = len(self.global_battle_log.battle_log) if hasattr(self.global_battle_log, 'battle_log') else 0
            
            # Check if all pets have finished their turns or reached the end of battle log
            if (all(turn > self.turn_limit for turn in self.battle_player.turns) or 
                max_turn > battle_log_length or
                all(phase == "result" for phase in self.battle_player.phase)):
                self.phase = "result" if not self.boss else "clear"
                self.frame_counter = 0
                runtime_globals.game_console.log(f"PvP battle finished: max_turn={max_turn}, log_length={battle_log_length}")
        else:
            # For PvE, use HP-based termination
            if self.battle_player.team1_total_hp <= 0 or self.battle_player.team2_total_hp <= 0 or all(turn > self.turn_limit for turn in self.battle_player.turns):
                self.phase = "result" if not self.boss else "clear"
                self.frame_counter = 0
                runtime_globals.game_console.log("All pairs finished battle, entering result phase")

    def setup_pet_attack(self, pet):
        """
        Sets up the pet's attack animation and projectiles using the global battle log.
        """
        # Find the index of the pet in team1
        pet_index = self.battle_player.team1.index(pet)

        # Determine the current turn (1-based)
        turn = self.battle_player.turns[pet_index]

        # Get the correct log entry for this turn
        if turn - 1 >= len(self.global_battle_log.battle_log):
            runtime_globals.game_console.log(f"[BattleEncounter] Invalid turn {turn} for pet {pet_index}, log length is {len(self.global_battle_log.battle_log)}")
            return
        turn_log = self.global_battle_log.battle_log[turn - 1]

        # For PvP, determine which device this pet belongs to from the perspective of the battle log
        # Both devices use the same battle log and same visual team arrangement:
        # Team1 (left) = device1 pets, Team2 (right) = device2 pets
        if self.pvp_mode:
            # Both host and client: team1 maps to device1
            device_label = "device1"
        else:
            # PvE: my pets are always device1
            device_label = "device1"

        # Find the attack entry for this pet
        attack_entry = next(
            (a for a in turn_log.attacks if a.device == device_label and a.attacker == pet_index),
            None
        )

        runtime_globals.game_console.log(f"Device {device_label} turn {turn} attack {attack_entry}")

        if not attack_entry:
            runtime_globals.game_console.log(f"[BattleEncounter] No attack entry found for pet {pet_index} in turn {turn} for device {device_label}")
            return

        hits = attack_entry.damage if attack_entry.hit else 0
        defender_idx = attack_entry.defender if attack_entry else 0

        if pet_index != defender_idx:
            runtime_globals.game_console.log(f"[BattleEncounter] Pet {pet_index} attacking defender {defender_idx} with hits: {hits}")

        # Update debug battle log for this pet
        if constants.DEBUG_MODE and pet_index < len(self.debug_battle_logs):
            self.debug_battle_logs[pet_index]["turn"] = turn
            self.debug_battle_logs[pet_index]["arrow"] = ">"
            # Don't show hit info during attack phase, only during charge

        # Choose attack sprite
        if self.module.ruleset == "dmc":
            if hits == 2 and getattr(pet, "atk_alt", 0) > 0:
                atk_id = str(pet.atk_alt)
            else:
                atk_id = str(pet.atk_main)
        else:
            if getattr(pet, "atk_alt", 0) > 0 and hits >= 3:
                atk_id = str(pet.atk_alt)
            else:
                atk_id = str(pet.atk_main)
        atk_sprite = self.get_attack_sprite(pet, atk_id)

        # Start position
        y = self.get_y(pet_index, len(self.battle_player.team1)) + atk_sprite.get_height() // 2
        x = self.get_team1_x(pet_index)

        # Target position
        if defender_idx < len(self.battle_player.team2):
            target_enemy = self.battle_player.team2[defender_idx]
            target_x = self.get_team2_x(defender_idx) + (constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH) // 2
            target_y = self.get_y(defender_idx, len(self.battle_player.team2)) + atk_sprite.get_height() // 2
        else:
            target_x, target_y = x, y

        dx = target_x - x
        dy = target_y - y
        angle = -math.degrees(math.atan2(dy, dx))
        atk_sprite = pygame.transform.flip(atk_sprite, True, True)
        rotated_sprite = pygame.transform.rotate(atk_sprite, angle)

        self.battle_player.team1_projectiles[pet_index] = []
        if self.module.ruleset in ["dmc", "penc"] and self.module.battle_damage_limit < 3:
            if hits == 2:
                rotated_sprite = pygame.transform.scale2x(rotated_sprite.copy())
            self.battle_player.team1_projectiles[pet_index].append([rotated_sprite, [x, y], [target_x, target_y], attack_entry])
        else:
            if hits == 4:
                rotated_sprite = pygame.transform.scale2x(rotated_sprite.copy())
                self.battle_player.team1_projectiles[pet_index].append([rotated_sprite, [x, y], [target_x, target_y], attack_entry])
            else:
                self.battle_player.team1_projectiles[pet_index].append([rotated_sprite.copy(), [x, y], [target_x, target_y], attack_entry])
                if hits > 1:
                    self.battle_player.team1_projectiles[pet_index].append([rotated_sprite.copy(), [x - (20 * constants.UI_SCALE), y - (10 * constants.UI_SCALE)], [target_x - (20 * constants.UI_SCALE), target_y - (10 * constants.UI_SCALE)], attack_entry])
                if hits == 3:
                    self.battle_player.team1_projectiles[pet_index].append([rotated_sprite.copy(), [x - (40 * constants.UI_SCALE), y + (10 * constants.UI_SCALE)], [target_x - (40 * constants.UI_SCALE), target_y + (10 * constants.UI_SCALE)], attack_entry])

    def setup_enemy_attack(self, enemy):
        """
        Sets up the enemy's attack animation and projectiles using the global battle log.
        Handles boss attacks (multiple per turn).
        """
        # Find the index of the enemy in team2
        enemy_index = self.battle_player.team2.index(enemy)

        # Determine the current turn (1-based)
        turn = self.battle_player.turns[enemy_index]

        # Get the correct log entry for this turn
        if turn - 1 >= len(self.global_battle_log.battle_log):
            runtime_globals.game_console.log(f"[BattleEncounter] Invalid turn {turn} for enemy {enemy_index}, log length is {len(self.global_battle_log.battle_log)}")
            return
        turn_log = self.global_battle_log.battle_log[turn - 1]

        # For PvP, determine which device this enemy belongs to from the perspective of the battle log
        # Both devices use the same battle log and same visual team arrangement:
        # Team1 (left) = device1 pets, Team2 (right) = device2 pets
        if self.pvp_mode:
            # Both host and client: team2 maps to device2
            device_label = "device2"
        else:
            # PvE: enemy attacks are always device2
            device_label = "device2"

        # For bosses, collect all attacks by this enemy in this turn
        attack_entries = [
            a for a in turn_log.attacks
            if a.device == device_label and a.attacker == enemy_index
        ]

        runtime_globals.game_console.log(f"Device {device_label} turn {turn} attack {attack_entries}")

        if not attack_entries:
            runtime_globals.game_console.log(f"[BattleEncounter] No attack entries found for enemy {enemy_index} in turn {turn} for device {device_label}")
            return

        # Choose attack sprite
        hits = attack_entries[0].damage if attack_entries and attack_entries[0].hit else 0
        
        # Update debug battle log for enemy attacks (affects the defender pet)
        if constants.DEBUG_MODE and attack_entries:
            for attack_entry in attack_entries:
                defender_idx = attack_entry.defender
                if defender_idx < len(self.debug_battle_logs):
                    self.debug_battle_logs[defender_idx]["turn"] = turn
                    self.debug_battle_logs[defender_idx]["arrow"] = "<"
                    # Don't show hit info during attack phase, only during charge
        if self.module.ruleset == "dmc":
            if hits == 2 and getattr(enemy, "atk_alt", 0) > 0:
                atk_id = str(enemy.atk_alt)
            else:
                atk_id = str(enemy.atk_main)
        else:
            if getattr(enemy, "atk_alt", 0) > 0 and hits >= 3:
                atk_id = str(enemy.atk_alt)
            else:
                atk_id = str(enemy.atk_main)
        base_sprite = self.get_attack_sprite(enemy, atk_id)
        base_sprite = pygame.transform.flip(base_sprite, True, False)

        y = self.get_y(enemy_index, len(self.battle_player.team2)) + base_sprite.get_height() // 2
        x = self.get_team2_x(enemy_index) + (constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH) // 2

        # For each attack entry (boss may attack multiple pets in one turn)
        for attack_entry in attack_entries:
            defender_idx = attack_entry.defender if attack_entry else 0
            self.battle_player.team2_projectiles[defender_idx] = []
            # Target position
            if defender_idx < len(self.battle_player.team1):
                target_pet_x = self.get_team1_x(defender_idx) - (constants.PET_WIDTH // 2)
                target_pet_y = self.get_y(defender_idx, len(self.battle_player.team1)) + base_sprite.get_height() // 2
            else:
                target_pet_x, target_pet_y = x, y

            dx = target_pet_x - x
            dy = target_pet_y - y
            angle = -math.degrees(math.atan2(dy, dx))
            rotated_sprite = pygame.transform.rotate(base_sprite, angle)

            # Add projectile for this attack
            
            if self.module.battle_damage_limit < 3:
                if hits == 2:
                    rotated_sprite = pygame.transform.scale2x(rotated_sprite)
                self.battle_player.team2_projectiles[defender_idx].append([rotated_sprite, [x, y], [target_pet_x, target_pet_y], attack_entry])
            else:
                if hits == 4:
                    rotated_sprite = pygame.transform.scale2x(rotated_sprite)
                    self.battle_player.team2_projectiles[defender_idx].append([rotated_sprite, [x, y], [target_pet_x, target_pet_y], attack_entry])
                else:
                    self.battle_player.team2_projectiles[defender_idx].append([rotated_sprite, [x, y], [target_pet_x, target_pet_y], attack_entry])
                    if hits > 1:
                        self.battle_player.team2_projectiles[defender_idx].append([rotated_sprite, [x + (20 * constants.UI_SCALE), y + (10 * constants.UI_SCALE)], [target_pet_x + (20 * constants.UI_SCALE), target_pet_y + (10 * constants.UI_SCALE)], attack_entry])
                    if hits == 3:
                        self.battle_player.team2_projectiles[defender_idx].append([rotated_sprite, [x + (40 * constants.UI_SCALE), y - (10 * constants.UI_SCALE)], [target_pet_x + (40 * constants.UI_SCALE), target_pet_y - (10 * constants.UI_SCALE)], attack_entry])

    def move_towards(self, pos, target, speed):
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return pos
        step = min(speed, dist)
        return [pos[0] + dx / dist * step, pos[1] + dy / dist * step]


    def update_battle_pet_projectiles(self):
        if len(self.battle_player.team1_projectiles) == 0:
            return

        for i, main_data in enumerate(self.battle_player.team1_projectiles):
            if len(main_data) == 0:
                continue

            # Move projectiles
            done = True
            for sprite_data in main_data:
                sprite, pos, target, attack_entry = sprite_data
                new_pos = self.move_towards(pos, target, combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE))
                sprite_data[1][0], sprite_data[1][1] = new_pos
                if math.hypot(new_pos[0] - target[0], new_pos[1] - target[1]) > 2:
                    done = False

            # When all projectiles are done for this attack
            if done:
                defender_idx = attack_entry.defender
                hit = attack_entry.hit
                damage = attack_entry.damage

                # Play hit or miss sound and animation
                self.battle_player.shot_wait[i] = True
                if hit:
                    enemy = self.battle_player.team2[defender_idx]
                    enemy_y = self.get_y(defender_idx, len(self.battle_player.team2))
                    enemy_x = self.get_team2_x(defender_idx) + (constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH) // 2
                    self.hit_animations.append([0, [enemy_x, enemy_y + (16 * constants.UI_SCALE)]])
                    runtime_globals.game_sound.play("attack_hit")

                    # Apply damage
                    self.battle_player.team2_hp[defender_idx] = max(0, self.battle_player.team2_hp[defender_idx] - damage)
                    self.battle_player.team2_total_hp = sum(self.battle_player.team2_hp)
                    self.battle_player.team2_bar_counters[defender_idx] = BAR_COUNTER
                else:
                    runtime_globals.game_sound.play("attack_fail")
                    if defender_idx >= 0 and defender_idx < len(self.battle_player.team2):
                        enemy = self.battle_player.team2[defender_idx]
                        enemy_y = self.get_y(defender_idx, len(self.battle_player.team2))
                        enemy_x = self.get_team2_x(defender_idx)
                        runtime_globals.game_message.add("MISS", (enemy_x + (16 * constants.UI_SCALE), enemy_y - (10 * constants.UI_SCALE)), (255, 0, 0))

                self.battle_player.team1_projectiles[i] = []

        # Check if all pets/enemies are in result phase
        if all(phase == "result" for phase in self.battle_player.phase):
            self.phase = "result" if not self.boss else "clear"
            self.frame_counter = 0

    def update_battle_enemy_projectiles(self):
        if len(self.battle_player.team2_projectiles) == 0:
            return

        for i, main_data in enumerate(self.battle_player.team2_projectiles):
            if len(main_data) == 0:
                continue

            # Move projectiles
            done = True
            for sprite_data in main_data:
                sprite, pos, target, attack_entry = sprite_data
                new_pos = self.move_towards(pos, target, combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE))
                sprite_data[1][0], sprite_data[1][1] = new_pos
                if math.hypot(new_pos[0] - target[0], new_pos[1] - target[1]) > 2:
                    done = False

            # When all projectiles are done for this attack
            if done:
                index = i
                if self.boss:
                    index = 0
                defender_idx = attack_entry.defender
                hit = attack_entry.hit
                damage = attack_entry.damage
                self.battle_player.shot_wait[index] = True
                if hit:
                    pet_y = self.get_y(defender_idx, len(self.battle_player.team1))
                    pet_x = self.get_team1_x(defender_idx) + (constants.PET_WIDTH // 2)
                    self.hit_animations.append([0, [pet_x, pet_y + (24 * constants.UI_SCALE)]])
                    runtime_globals.game_sound.play("attack_hit")
                    self.battle_player.team1_hp[defender_idx] = max(0, self.battle_player.team1_hp[defender_idx] - damage)
                    self.battle_player.team1_total_hp = sum(self.battle_player.team1_hp)
                    self.battle_player.team1_bar_counters[defender_idx] = BAR_COUNTER
                else:
                    runtime_globals.game_sound.play("attack_fail")
                    if defender_idx >= 0 and defender_idx < len(self.battle_player.team1):
                        pet_y = self.get_y(defender_idx, len(self.battle_player.team1))
                        pet_x = self.get_team1_x(defender_idx)
                        runtime_globals.game_message.add("MISS", (pet_x + (16 * constants.UI_SCALE), pet_y - (10 * constants.UI_SCALE)), (255, 0, 0))
                self.battle_player.team2_projectiles[i] = []

        # Check if all pets/enemies are in result phase
        if all(phase == "result" for phase in self.battle_player.phase):
            self.phase = "result" if not self.boss else "clear"
            self.frame_counter = 0

    def update_clear(self):
        """
        Update logic for the update_clear phase,
        """

        if not self.boss or self.frame_counter > int(30 * ( constants.FRAME_RATE / 30)):
            self.frame_counter = 0
            self.phase = "result"

    def update_result(self):
        """
        Update logic for the result phase, handles victory or defeat actions.
        """
        # Result timer, frame-rate independent
        self.result_timer += 1

        if self.result_timer < int(120 * ( constants.FRAME_RATE / 30)):
            # pisca aviso clear
            return

        # For PvP battles, update per-pet PvP counters, run unlock checks, then
        # return to game after showing results. We maintain per-pet counters so
        # unlocks that rely on PvP wins/participation can reference them.
        if self.pvp_mode:
            # Play appropriate sound
            runtime_globals.game_sound.play("happy" if self.victory_status == "Victory" else "fail")

            # Update each local pet's PvP counters. Pets on team1 are the local
            # owner's pets in PvP mode.
            for i, pet in enumerate(self.battle_player.team1):
                try:
                    pet.pvp_battles += 1
                    # Determine if this pet won its pairing
                    if hasattr(self.battle_player, 'winners') and i < len(self.battle_player.winners):
                        winner = self.battle_player.winners[i]
                        local_won = (winner == 'team1') or (self.victory_status == 'Victory')
                    else:
                        # Fallback: use global victory_status when per-pair winners
                        # are not available
                        local_won = (self.victory_status == 'Victory')

                    if local_won:
                        pet.pvp_wins += 1

                    # Persist these counters to global save state via runtime globals
                    # so they'll be picked up on next autosave
                    runtime_globals.game_console.log(f"[PvP] Pet {getattr(pet,'name',i)} pvp_battles={pet.pvp_battles} pvp_wins={pet.pvp_wins}")
                except Exception as e:
                    runtime_globals.game_console.log(f"[PvP] Error updating pet PvP counters: {e}")

            # Unlock logic for PvP: scan module unlock entries of type 'pvp' and
            # compare their "amount" to the pet owner's pvp_wins count.
            try:
                module_unlocks = getattr(self.module, 'unlocks', []) or []
                for unlock in module_unlocks:
                    if unlock.get('type') == 'pvp':
                        req = unlock.get('amount', None)
                        name = unlock.get('name')
                        if req is None or not name:
                            continue
                        # If any local pet has pvp_wins >= req, unlock for module
                        for pet in self.battle_player.team1:
                            if getattr(pet, 'pvp_wins', 0) >= int(req):
                                unlock_item(self.module.name, 'pvp', name)
                                break
            except Exception as e:
                runtime_globals.game_console.log(f"[PvP] Error processing PvP unlocks: {e}")

            # Return to main scene after PvP
            self.return_to_main_scene()
            return

        if self.victory_status == "Victory":
            runtime_globals.game_sound.play("happy")
            if not self.boss:
                self.round += 1
                if self.round > game_globals.battle_round[self.module.name]:
                    game_globals.battle_round[self.module.name] = self.round
                self.victory_status = None
                if self.module.battle_sequential_rounds:
                    self.set_initial_state(round=self.round, area=self.area)
                    return
            else:
                # --- Unlock adventure items of the area just won ---
                unlocks = getattr(self.module, "unlocks", None)
                if isinstance(unlocks, list):
                    for unlock in unlocks:
                        unlocked = False
                        
                        # Check for area-based unlocks
                        if unlock.get("type") == "adventure" and unlock.get("area") == self.area:
                            unlocked = True
                        
                        # Check for boss-specific unlock keys
                        elif unlock.get("type") == "adventure" and "name" in unlock:
                            unlock_name = unlock["name"]
                            # Check if any defeated enemy has this unlock key
                            for enemy in self.battle_player.team2:
                                if hasattr(enemy, 'unlock') and enemy.unlock == unlock_name:
                                    unlocked = True
                                    runtime_globals.game_console.log(f"[Adventure] Boss {enemy.name} dropped unlock key: {unlock_name}")
                                    break
                        
                        if unlocked:
                            unlock_item(self.module.name, "adventure", unlock["name"])
                            runtime_globals.game_console.log(f"[Adventure] Unlocked: {unlock['name']}")

                self.area += 1
                self.round = 1

                if self.module.area_exists(self.area):
                    game_globals.battle_round[self.module.name] = self.round
                    game_globals.battle_area[self.module.name] = max(self.area, game_globals.battle_area[self.module.name])
        else:
            runtime_globals.game_sound.play("fail")
            # perdeu
            game_globals.battle_round[self.module.name] = 1

        self.return_to_main_scene()

    def load_next_round(self):
        """
        Prepares the next round by resetting health and loading new enemies.
        """
        self.phase = "level"
        self.result_timer  = 0
        self.press_counter = 0
        self.final_color = 3
        self.correct_color = 0
        self.super_hits = 0
        self.frame_counter = 0
        self.enemies = []
        self.enemy_positions = []
        self.load_enemies()

    def draw(self, surface: pygame.Surface):
        """
        Main draw loop for the battle encounter, calls phase-specific draws.
        """
        self.draw_health_bars(surface)
        surface.blit(self.backgroundIm, (0, 0))

        # Draw by phase
        if self.phase == "level":
            self.draw_level(surface)
        elif self.phase == "entry":
            self.draw_entry(surface)
        elif self.phase == "intimidate":
            self.draw_intimidate(surface)
        elif self.phase == "set_attribute":
            self.draw_set_attribute(surface)
        elif self.phase == "alert":
            self.draw_alert(surface)
        elif self.phase == "charge":
            self.draw_charge(surface)
        elif self.phase == "battle":
            self.draw_battle(surface)
        elif self.phase == "clear":
            self.draw_clear(surface)
        elif self.phase == "result":
            self.draw_result(surface)

        # Draw debug battle logs if DEBUG_MODE and DEBUG_BATTLE_INFO flags are enabled
        if constants.DEBUG_MODE and constants.DEBUG_BATTLE_INFO and self.phase in ["battle"]:
            self.draw_debug_battle_logs(surface)

    def draw_level(self, surface):
        """
        Draws the level information on the screen.
        """
        surface.blit(self.level_sprite, (0, constants.SCREEN_HEIGHT // 2 - self.level_sprite.get_height() // 2))
        level_text = self.font.render(f"Round {self.round}", True, constants.FONT_COLOR_GREEN).convert_alpha()
        blit_with_cache(surface, level_text, (6 * constants.UI_SCALE, 116 * constants.UI_SCALE))

    def draw_entry(self, surface):
        """
        Draws the entry phase, showing enemies and pets in their starting positions.
        """
        self.draw_enemies(surface)
        self.draw_pets(surface)
        runtime_globals.game_message.draw(surface)
        self.draw_hit_animations(surface)

    def draw_intimidate(self, surface):
        """
        Draws the intimidate phase, showing warning or battle sprites.
        """
        if self.frame_counter >= combat_constants.IDLE_ANIM_DURATION // 2:
            if self.boss:
                sprite = self.result_sprites["warning"][(self.frame_counter // int(10 * constants.FRAME_RATE / 30)) % 2]
                surface.blit(sprite, (0, constants.SCREEN_HEIGHT // 2 - sprite.get_height() // 2))
            else:
                surface.blit(self.battle_sprite, (0, constants.SCREEN_HEIGHT // 2 - self.battle_sprite.get_height() // 2))
        else:
            self.draw_enemies(surface)
            self.draw_pets(surface)
            runtime_globals.game_message.draw(surface)
            self.draw_hit_animations(surface)

    def draw_set_attribute(self, surface):
        """
        Draws the attribute selection for the pet, indicating readiness to attack.
        """
        attr = self.get_first_pet_attribute()
        sprite = self.ready_sprites[attr]
        y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
        surface.blit(sprite, (0, y))

    def draw_alert(self, surface):
        """
        Draws the alert phase, showing readiness sprites or count down.
        """
        if self.module.ruleset == "penc":
            sprite = self.count_sprites[4]
            y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
            surface.blit(sprite, (0, y))
        else:
            center_y = constants.SCREEN_HEIGHT // 2 - self.ready_sprite.get_height() // 2
            surface.blit(self.ready_sprite, (0, center_y))

    def draw_charge(self, surface):
        """
        Draws the charge phase, showing strength bar or Xai roll.
        """
        self.draw_enemies(surface)
        self.draw_pets(surface)
        if self.module.ruleset == "dmc":
            self.draw_strength_bar(surface)
        elif self.module.ruleset == "penc":
            sprite = self.count_sprites[self.rotation_index]
            y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
            surface.blit(sprite, (0, y))
        elif self.module.ruleset == "dmx":
            if self.xai_phase == 1:
                self.window_xai.draw(surface)
            elif self.xai_phase >= 2:
                self.window_xaibar.draw(surface)

    def draw_battle(self, surface):
        """
        Draws the battle phase, showing pets and enemies in combat.
        """
        self.draw_enemies(surface)
        self.draw_pets(surface)
        runtime_globals.game_message.draw(surface)
        self.draw_hit_animations(surface)
        self.draw_projectiles(surface)
        self.draw_enemy_projectiles(surface)
        self.draw_health_bars_for_battlers(surface)

    def draw_clear(self, surface):
        """
        Draws the clear of the battle, showing clear sprites.
        """
        if self.boss:
            sprites = self.result_sprites["clear"]
            sprite = sprites[(self.result_timer // (10 * int(constants.FRAME_RATE / 30))) % 2]
            surface.blit(sprite, (0, constants.SCREEN_HEIGHT // 2 - sprite.get_height() // 2))

    def draw_result(self, surface):
        """
        Improved result screen: victory/defeat, battle damage, pet stats, and prize.
        Uses new global battle structures.
        """
        # Draw header
        header = self.font.render(
            f"{self.victory_status}!",
            True,
            constants.FONT_COLOR_GREEN if self.victory_status == "Victory" else constants.FONT_COLOR_RED
        ).convert_alpha()
        blit_with_cache(surface, header, (20 * constants.UI_SCALE, 30 * constants.UI_SCALE))

        # Draw pet sprites horizontally (half size)
        # For PvP, client should show their own pets (team2), not team1
        if self.pvp_mode and hasattr(self, 'show_team2_in_result') and self.show_team2_in_result:
            pets = [enemy for enemy in self.battle_player.team2 if hasattr(enemy, 'get_sprite')]
            # Use team2 indices for frame counters and winners
            team1_count = len(self.battle_player.team1)
            pet_frame_counters = []
            pet_winners = []
            for i in range(len(pets)):
                frame_counter_idx = team1_count + i
                if frame_counter_idx < len(self.battle_player.frame_counters):
                    pet_frame_counters.append(self.battle_player.frame_counters[frame_counter_idx])
                else:
                    pet_frame_counters.append(0)  # Default frame counter
                
                winner_idx = team1_count + i  
                if winner_idx < len(self.battle_player.winners):
                    pet_winners.append(self.battle_player.winners[winner_idx])
                else:
                    pet_winners.append("team1")  # Default winner
        else:
            pets = self.battle_player.team1
            pet_frame_counters = self.battle_player.frame_counters[:len(self.battle_player.team1)]
            pet_winners = self.battle_player.winners[:len(self.battle_player.team1)]
            
        total = len(pets)
        sprite_width = constants.PET_WIDTH // 2
        sprite_height = constants.PET_HEIGHT // 2
        spacing = min((constants.SCREEN_WIDTH - int(30 * constants.UI_SCALE)) // total, sprite_width + int(16 * constants.UI_SCALE))
        total_width = spacing * total
        offset_x = 30 +(constants.SCREEN_WIDTH - total_width) // 2
        y = int(86 * constants.UI_SCALE)
        for i, pet in enumerate(pets):
            # Safety check for frame counters
            if i < len(pet_frame_counters):
                anim_toggle = (pet_frame_counters[i] + i * 5) // (15 * constants.FRAME_RATE / 30) % 2
            else:
                anim_toggle = 0
                
            # Safety check for winners
            if (i < len(pet_winners) and pet_winners[i] == "team2") or self.victory_status == "Defeat":
                frame_id = PetFrame.LOSE.value
            else:
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.HAPPY.value
            sprite = pet.get_sprite(frame_id)
            sprite = pygame.transform.scale(sprite, (sprite_width, sprite_height))
            x = offset_x + i * spacing
            blit_with_cache(surface, sprite, (x, y))

        # Draw Level, Exp, Bonus headers and values (adjusted for new sprite size)
        label_y = y + sprite_height + int(10 * constants.UI_SCALE)
        col_xs = [offset_x + i * spacing + sprite_width // 2 for i in range(total)]

        any_dmx_pets = False
        for i, pet in enumerate(pets):
            if pet.module == "DMX":
                any_dmx_pets = True

        if any_dmx_pets:            
            # Draw headers
            for idx, label in enumerate(["Lv", "Xp", "+"]):
                text = self.font_small.render(label, True, constants.FONT_COLOR_GREEN).convert_alpha()
                blit_with_cache(surface, text, (20 * constants.UI_SCALE, label_y + idx * 24 * constants.UI_SCALE))
            # Draw values for each pet
            for i, pet in enumerate(pets):
                if pet.module == "DMX":
                    # Level
                    level = getattr(pet, "level", "-")
                    # For PvP, no level ups occur
                    level_up_indicator = ""
                    if not self.pvp_mode and i < len(self.battle_player.level_up):
                        level_up_indicator = '+' if self.battle_player.level_up[i] else ''
                    
                    level_text = self.font_small.render(
                        f"{level}{level_up_indicator}", True,
                        constants.FONT_COLOR_YELLOW if level_up_indicator else constants.FONT_COLOR_DEFAULT
                    ).convert_alpha()
                    level_text_width = level_text.get_width()
                    blit_with_cache(surface, level_text, (col_xs[i] - level_text_width // 2, label_y))

                    # Exp (show XP gained this battle)
                    exp = self.battle_player.xp if self.victory_status == "Victory" else 0
                    xp_color = constants.FONT_COLOR_DEFAULT
                    
                    # For PvP client showing team2 pets, check team2 max level
                    if (self.pvp_mode and hasattr(self, 'show_team2_in_result') and self.show_team2_in_result):
                        max_level_check = pet.level == constants.MAX_LEVEL.get(pet.stage, 99)
                        level_up_check = False  # No level ups in PvP
                    else:
                        # Safety check for team1 access
                        if i < len(self.battle_player.team1):
                            max_level_check = self.battle_player.team1[i].level == constants.MAX_LEVEL[self.battle_player.team1[i].stage]
                        else:
                            max_level_check = False
                        level_up_check = self.battle_player.level_up[i] if i < len(self.battle_player.level_up) else False
                    
                    if not level_up_check and max_level_check:
                        exp = 0
                        xp_color = constants.FONT_COLOR_RED
                    exp_text = self.font_small.render(str(exp), True, xp_color).convert_alpha()
                    exp_text_width = exp_text.get_width()
                    blit_with_cache(surface, exp_text, (col_xs[i] - exp_text_width // 2, label_y + 24 * constants.UI_SCALE))

                    # Bonus
                    bonus = self.battle_player.bonus if self.victory_status == "Victory" else 0
                    bonus_text = self.font_small.render(str(bonus), True, constants.FONT_COLOR_DEFAULT).convert_alpha()
                    bonus_text_width = bonus_text.get_width()
                    blit_with_cache(surface, bonus_text, (col_xs[i] - bonus_text_width // 2, label_y + 48 * constants.UI_SCALE))

        # Draw Prize
        if self.victory_status == "Victory" and getattr(self, "prize_item", None):
            prize_text = self.prize_item.name
        else:
            prize_text = "None"
        prize_label = self.font_small.render(f"Prize: {prize_text}", True, constants.FONT_COLOR_YELLOW).convert_alpha()
        blit_with_cache(surface, prize_label, (20 * constants.UI_SCALE, constants.SCREEN_HEIGHT - 40 * constants.UI_SCALE))

    def draw_hit_animations(self, surface):
        """
        Draws the hit animations at the impact points of attacks.
        """
        for frame_index, (x, y) in self.hit_animations:
            if 0 <= frame_index < len(self.hit_animation_frames):
                sprite = self.hit_animation_frames[frame_index]
                blit_with_cache(surface, sprite, (x - sprite.get_width() // 2, y - 32))

    def draw_enemies(self, surface: pygame.Surface):
        """
        Draws the enemy sprites on the screen, with animations based on the battle phase.
        """
        total = len(self.battle_player.team2)
        anim_frames = 10 * ( constants.FRAME_RATE / 30)

        for i, enemy in enumerate(self.battle_player.team2):
            y = self.get_y(i, total)
            x = self.get_team2_x(i) - self.enemy_entry_counter
            anim_toggle = (self.battle_player.frame_counters[i] + i * 5) // (15 * constants.FRAME_RATE / 30) % 2

            attack_entry = None
            if self.phase in ["battle"]:
                # Check the global battle log for an attack entry
                turn = self.battle_player.turns[i]
                if turn <= self.turn_limit and self.global_battle_log and len(self.global_battle_log.battle_log) >= turn:
                    turn_log = self.global_battle_log.battle_log[turn - 1]
                    attack_entry = next(
                        (a for a in turn_log.attacks if a.device == "device2" and a.attacker == i),
                        None
                    )

            if self.phase in ["intimidate", "entry"]:
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.ANGRY.value
            elif self.phase in ["alert", "charge"]:
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.IDLE2.value
            elif self.battle_player.team2_hp[i] <= 0:
                frame_id = PetFrame.LOSE.value
            elif attack_entry and self.battle_player.phase[i] == "enemy_attack":
                frame_id = PetFrame.ATK1.value
            elif attack_entry and self.battle_player.phase[i] == "enemy_charge":
                if self.battle_player.cooldowns[i] < anim_frames:
                    frame_id = PetFrame.ATK2.value
                else:
                    frame_id = PetFrame.ATK1.value
            elif self.battle_player.phase[i] == "result":
                if self.battle_player.winners[i] == "team1":
                    frame_id = PetFrame.LOSE.value
                else:
                    frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.HAPPY.value
            else:
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.IDLE2.value

            sprite = enemy.get_sprite(frame_id)

            if attack_entry and self.battle_player.phase[i] == "enemy_charge" and self.battle_player.team2_hp[i] > 0:
                y -= int(self.battle_player.attack_jump[i] * constants.UI_SCALE)
                x -= int(self.battle_player.attack_forward[i] * constants.UI_SCALE)

            if sprite:
                sprite = pygame.transform.flip(sprite, True, False)
                blit_with_cache(surface, sprite, (x + (2 * constants.UI_SCALE), y))

    def draw_pets(self, surface: pygame.Surface):
        """
        Draws the player pets on the screen, with animations based on the battle phase.
        In the result phase, pets are drawn horizontally and centered vertically.
        """
        total = len(self.battle_player.team1)
        anim_frames = 10 * ( constants.FRAME_RATE / 30)

        if self.phase == "result":
            # Horizontal layout
            spacing = min((constants.SCREEN_WIDTH - int(30 * constants.UI_SCALE)) // total, int(constants.PET_WIDTH * constants.UI_SCALE) + int(16 * constants.UI_SCALE))
            total_width = spacing * total
            offset_x = (constants.SCREEN_WIDTH - total_width) // 2
            y = (constants.SCREEN_HEIGHT - constants.PET_HEIGHT) // 2
            for i, pet in enumerate(self.battle_player.team1):
                x = self.get_team1_x(i)
                anim_toggle = (self.battle_player.frame_counters[i] + i * 5) // (15 * constants.FRAME_RATE / 30) % 2
                if self.victory_status == "Defeat":
                    frame_id = PetFrame.LOSE.value
                else:
                    frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.HAPPY.value
                sprite = pet.get_sprite(frame_id)
                sprite = pygame.transform.scale(sprite, (constants.PET_WIDTH, constants.PET_HEIGHT))
                x = offset_x + i * spacing
                blit_with_cache(surface, sprite, (x, y))
        else:
            # Original vertical layout
            for i, pet in enumerate(self.battle_player.team1):
                anim_toggle = (self.battle_player.frame_counters[i] + i * 5) // (15 * constants.FRAME_RATE / 30) % 2
                x = self.get_team1_x(i)
                attack_entry = None
                if self.phase in ["battle"]:
                    # Check the global battle log for an attack entry
                    turn = self.battle_player.turns[i]
                    if turn <= self.turn_limit and self.global_battle_log and len(self.global_battle_log.battle_log) >= turn:
                        turn_log = self.global_battle_log.battle_log[turn - 1]
                        attack_entry = next(
                            (a for a in turn_log.attacks if a.device == "device1" and a.attacker == i),
                            None
                        )

                if self.phase in ["alert", "charge"]:
                    frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.ANGRY.value
                elif self.phase in ["intimidate", "entry"]:
                    frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.IDLE2.value
                elif self.battle_player.team1_hp[i] <= 0:
                    frame_id = PetFrame.LOSE.value
                elif attack_entry and self.battle_player.phase[i] == "pet_attack":
                    frame_id = PetFrame.ATK1.value
                elif attack_entry and self.battle_player.phase[i] == "pet_charge":
                    if self.battle_player.cooldowns[i] < anim_frames:
                        frame_id = PetFrame.ATK2.value
                    else:
                        frame_id = PetFrame.ATK1.value
                elif self.battle_player.phase[i] == "result":
                    if self.battle_player.winners[i] == "team2":
                        frame_id = PetFrame.LOSE.value
                    else:
                        frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.HAPPY.value
                else:
                    frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.IDLE2.value

                sprite = pet.get_sprite(frame_id)
                sprite = pygame.transform.scale(sprite, (constants.PET_WIDTH, constants.PET_HEIGHT))
                y = self.get_y(i, total)
                if attack_entry and self.battle_player.phase[i] == "pet_charge" and self.battle_player.team1_hp[i] > 0:
                    y -= int(self.battle_player.attack_jump[i] * constants.UI_SCALE)
                    x += int(self.battle_player.attack_forward[i] * constants.UI_SCALE)
                blit_with_cache(surface, sprite, (x, y))

    def draw_projectiles(self, surface):
        """
        Draws the projectiles fired by the player's pets during their attack.
        """
        for data in self.battle_player.team1_projectiles:
            for sprite, pos, target, dt in data:
                blit_with_cache(surface, sprite, (pos[0], pos[1])) 

    def draw_enemy_projectiles(self, surface):
        """
        Draws the projectiles fired by the enemies during their attack.
        """
        for data in self.battle_player.team2_projectiles:
            for sprite, pos, target, dt in data:
                blit_with_cache(surface, sprite, (pos[0], pos[1]))

    def draw_strength_bar(self, surface):
        """
        Draws the strength training bar for the DMC ruleset.
        """
        bar_x = (constants.SCREEN_WIDTH // 2) - (self.bar_back.get_width() // 2)
        bar_bottom_y = constants.SCREEN_HEIGHT - int(2 * constants.UI_SCALE)

        if self.strength == 14:
            surface.blit(self.training_max, (bar_x - int(18 * constants.UI_SCALE), bar_bottom_y - int(209 * constants.UI_SCALE)))

        blit_with_cache(surface, self.bar_back, (bar_x - int(3 * constants.UI_SCALE), bar_bottom_y - int(169 * constants.UI_SCALE)))

        for i in range(self.strength):
            y = bar_bottom_y - (i + 1) * self.bar_piece.get_height()
            surface.blit(self.bar_piece, (bar_x, y))

    def draw_health_bars(self, surface):
        """
        Draws the health bars for the player and enemy, showing current and max health.
        """
        max_player_health = self.battle_player.team1_max_total_hp 
        max_enemy_health = self.battle_player.team2_max_total_hp

        width_scale = constants.SCREEN_WIDTH / 240
        bar_width = int(67 * width_scale)
        bar_height = int(18 * width_scale)

        # Cores
        red = (181, 41, 41)
        green = (0, 255, 108)

        # Player bar (right side)
        start_x_player = constants.SCREEN_WIDTH - int(96 * width_scale)
        y = int(6 * width_scale)
        # Draw red background
        pygame.draw.rect(surface, red, (start_x_player, y, bar_width, bar_height))
        # Draw green foreground (current health)
        if max_player_health > 0:
            green_width = int(bar_width * (self.battle_player.team1_total_hp / self.battle_player.team1_max_total_hp))
            pygame.draw.rect(surface, green, (start_x_player + (bar_width - green_width), y, green_width, bar_height))

        # Enemy bar (left side)
        start_x_enemy = int(96 * width_scale)
        # Draw red background
        pygame.draw.rect(surface, red, (start_x_enemy - bar_width, y, bar_width, bar_height))
        # Draw green foreground (current health)
        if max_enemy_health > 0:
            green_width = int(bar_width * (self.battle_player.team2_total_hp / max_enemy_health))
            pygame.draw.rect(surface, green, (start_x_enemy - bar_width, y, green_width, bar_height))

    def draw_health_bars_for_battlers(self, surface):
        """
        Draws individual health bars under each pet and enemy using the new team structure.
        """
        bar_height = int(8 * constants.UI_SCALE)
        bar_offset_y = constants.PET_HEIGHT - int(6 * constants.UI_SCALE)
        green = (0, 255, 108)
        red = (181, 41, 41)
        x_color = (255, 0, 0)
        x_thickness = max(2, int(2 * constants.UI_SCALE))

        # Draw pet health bars
        total_pets = len(self.battle_player.team1)
        for i, pet in enumerate(self.battle_player.team1):
            pet_x = self.get_team1_x(i)
            pet_y = self.get_y(i, total_pets) + bar_offset_y
            current_hp = self.battle_player.team1_hp[i]
            max_hp = self.battle_player.team1_max_hp[i]
            if current_hp > 0:
                if self.battle_player.team1_bar_counters[i] > 0:
                    pet_hp_ratio = current_hp / max_hp if max_hp else 0
                    pet_bar_width = int(constants.PET_WIDTH * pet_hp_ratio)
                    pygame.draw.rect(surface, red, (pet_x, pet_y, constants.PET_WIDTH, bar_height))
                    pygame.draw.rect(surface, green, (pet_x, pet_y, pet_bar_width, bar_height))
            else:
                pet_y = self.get_y(i, total_pets)
                # Draw red X over where the bar would be
                start1 = (pet_x, pet_y)
                end1 = (pet_x + constants.PET_WIDTH, pet_y + constants.PET_HEIGHT)
                start2 = (pet_x + constants.PET_WIDTH, pet_y)
                end2 = (pet_x, pet_y + constants.PET_HEIGHT)
                pygame.draw.line(surface, x_color, start1, end1, x_thickness)
                pygame.draw.line(surface, x_color, start2, end2, x_thickness)

        # Draw enemy health bars
        total_enemies = len(self.battle_player.team2)
        if self.boss:
            bar_offset_y = int(constants.PET_HEIGHT * constants.BOSS_MULTIPLIER) - int(6 * constants.UI_SCALE)
        for i, enemy in enumerate(self.battle_player.team2):
            enemy_x = self.get_team2_x(i)
            enemy_y = self.get_y(i, total_enemies) + bar_offset_y
            current_hp = self.battle_player.team2_hp[i]
            max_hp = self.battle_player.team2_max_hp[i]
            width = constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH
            heigh = constants.PET_HEIGHT * constants.BOSS_MULTIPLIER if self.boss else constants.PET_HEIGHT
            if current_hp > 0:
                if self.battle_player.team2_bar_counters[i] > 0:
                    enemy_hp_ratio = current_hp / max_hp if max_hp else 0
                    enemy_bar_width = int(width * enemy_hp_ratio)
                    pygame.draw.rect(surface, red, (enemy_x, enemy_y, width, bar_height))
                    pygame.draw.rect(surface, green, (enemy_x, enemy_y, enemy_bar_width, bar_height))
            else:
                enemy_y = self.get_y(i, total_enemies)
                # Draw red X over the entire enemy sprite
                start1 = (enemy_x, enemy_y)
                end1 = (enemy_x + width, enemy_y + heigh)
                start2 = (enemy_x + width, enemy_y)
                end2 = (enemy_x, enemy_y + heigh)
                pygame.draw.line(surface, x_color, start1, end1, x_thickness)
                pygame.draw.line(surface, x_color, start2, end2, x_thickness)

    def get_y(self, index, total):
        """
        Calculates the vertical position for drawing based on index and total number of sprites.
        Centers sprites dynamically and spreads them evenly, accounting for sprite height.
        """
        margin_top = int(40 * constants.UI_SCALE)
        margin_bottom = int(10 * constants.UI_SCALE)
        available_height = constants.SCREEN_HEIGHT - margin_top - margin_bottom

        sprite_height = constants.PET_HEIGHT

        if total == 1:
            # Center single sprite vertically
            return (constants.SCREEN_HEIGHT - sprite_height) // 2
        else:
            # Spread sprites evenly, center each sprite in its slot
            slot_height = available_height / total
            return int(margin_top + slot_height * index + (slot_height - sprite_height) / 2)

    def get_team1_x(self, index):
        """
        Returns the x position for the player's team based on index.
        """
        return constants.SCREEN_WIDTH - constants.PET_WIDTH - (4 * constants.UI_SCALE)
    
    def get_team2_x(self, index):
        """
        Returns the x position for the enemy team based on index.
        If it's a boss, it returns the enemy's x position.
        """
        return (3 * constants.UI_SCALE)
    #========================
    # Region: Event Handling
    #========================

    def handle_event(self, input_action):
        """
        Handles input events for the battle encounter, phase and ruleset specific.
        """
        if input_action == "B":
            if self.phase == "battle":
                runtime_globals.game_sound.play("cancel")
                self.phase = "result"
                self.frame_counter = 0
            else:
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
        elif self.module.ruleset == 'dmc':
            if self.phase == "charge":
                if input_action == "A":
                    runtime_globals.game_sound.play("menu")
                    self.strength = min(self.strength + 1, self.bar_level)
        elif self.module.ruleset == 'dmx':
            if self.phase == "charge":
                if self.xai_phase == 1 and input_action == "A" and not self.window_xai.stopping:
                    # --- Seven Switch: force XAI roll to 7 if status_boost is active ---
                    if (
                        "xai_roll" in game_globals.battle_effects
                        and game_globals.battle_effects["xai_roll"].get("amount", 0) == 7
                    ):
                        self.window_xai.stop()
                        self.xai_number = 7
                        self.window_xai.current_frame = 6  # 0-based index for 7
                    else:
                        self.window_xai.stop()
                        self.xai_number = self.window_xai.current_frame + 1
                elif self.xai_phase == 2 and input_action == "A":
                    self.window_xaibar.stop()
                    self.strength = self.window_xaibar.selected_strength or 1
                    self.xai_phase = 3
                    self.bar_timer = pygame.time.get_ticks()
        elif self.module.ruleset == 'penc':
            if input_action == "Y" or input_action == "SHAKE":
                if self.phase == "alert":
                    self.frame_counter = combat_constants.ALERT_DURATION_FRAMES
                elif self.phase == "charge":
                    self.press_counter += 1
                    if self.press_counter % 2 == 0:
                        self.rotation_index -= 1
                        if self.rotation_index < 1:
                            self.rotation_index = 3

    #========================
    # Region: Utility Methods
    #========================

    def return_to_main_scene(self):
        """
        Ends the battle and returns to the main game scene.
        """

        runtime_globals.game_console.log(f"[Scene_Battle] exiting to main game")
        distribute_pets_evenly()
        change_scene("game")

    def calculate_combat_for_pairs(self):
        self.simulate_global_combat()

        self.process_battle_results()

    def get_minigame_strength(self):
        """
        Returns the selected strength for the mini-game, defaulting to 1 if not set.
        """
        if self.module.ruleset == "dmc":
            if self.strength < 5:
                return 0
            elif self.strength < 10:
                return 1
            elif self.strength < 14:
                return 2
            else:
                return 3
        elif self.module.ruleset == "dmx":
            return self.strength
        elif self.module.ruleset == "penc":
            return self.super_hits
        return 1

    def simulate_global_combat(self):
        # Use the BattlePlayer's teams for simulation
        team1 = []
        team2 = []
        
        # Prepare team1 (player's Digimon)
        for i, pet in enumerate(self.battle_player.team1):
            team1.append(Digimon(
                name=pet.name,
                order=i,
                traited=1 if pet.traited else 0,
                egg_shake=1 if pet.shook else 0,
                index=i,
                hp=self.battle_player.team1_hp[i],
                attribute=pet.attribute,
                power=pet.get_power(),
                handicap=0,
                buff=self.attack_boost,
                mini_game=self.get_minigame_strength(),
                level=pet.level,
                stage=pet.stage,
                sick=1 if pet.sick > 0 else 0,
                shot1=pet.atk_main,
                shot2=pet.atk_alt,
                tag_meter=0
            ))

        # Prepare team2 (enemy Digimon)
        for i, enemy in enumerate(self.battle_player.team2):
            enemy_stage_index = max(1, enemy.stage - 1)
            enemy_level = constants.MAX_LEVEL.get(enemy_stage_index, 1)
            
            # Get enemy power - handle PvP pets with custom power values
            if hasattr(enemy, '_pvp_power'):
                enemy_power = enemy._pvp_power
            elif hasattr(enemy, 'get_power') and callable(enemy.get_power):
                enemy_power = enemy.get_power()
            else:
                enemy_power = getattr(enemy, 'power', 1)
            
            team2.append(Digimon(
                name=enemy.name,
                order=i,
                traited=getattr(enemy, 'traited', 0),
                egg_shake=getattr(enemy, 'shook', 0),
                index=i,
                hp=self.battle_player.team2_hp[i],
                attribute=enemy.attribute,
                power=enemy_power,
                handicap=getattr(enemy, "handicap", 0),
                buff=0,
                mini_game=1,
                level=getattr(enemy, 'level', enemy_level),
                stage=enemy.stage,
                sick=1 if getattr(enemy, 'sick', 0) > 0 else 0,
                shot1=enemy.atk_main,
                shot2=enemy.atk_alt,
                tag_meter=0
            ))

        # Simulate the battle using the GlobalBattleSimulator
        sim = GlobalBattleSimulator(
            attribute_advantage=self.module.battle_atribute_advantage,
            damage_limit=self.module.battle_damage_limit
        )
        result = sim.simulate(team1, team2)

        # Store the result for animation/processing
        self.global_battle_log = result
        self.victory_status = "Victory" if result.winner == "device1" else "Defeat"
        
        # Update quest progress if battle was won (skip for PvP)
        if not self.pvp_mode and self.victory_status == "Victory":
            if self.boss:
                # Update BOSS quest progress
                update_quest_progress(QuestType.BOSS, 1, self.module.name)
            # Update BATTLE quest progress
            update_quest_progress(QuestType.BATTLE, 1, self.module.name)

        # Process battle results for animations and rewards
        #Remove because it is called by calling function calculate_combat_for_pairs() directly,
        #otherwise it is called twice, and DP and battles are updated twice, not once.
        #self.process_battle_results()

    def draw_debug_battle_logs(self, surface):
        """
        Draws debug battle log information between enemies and pets when DEBUG_MODE flag is enabled.
        Shows turn number, hit results, and attack direction arrows.
        """
        if not constants.DEBUG_MODE or not hasattr(self, 'debug_battle_logs'):
            return
            
        font_small = get_font(constants.FONT_SIZE_SMALL)
        
        for i, log_entry in enumerate(self.debug_battle_logs):
            if i >= len(self.battle_player.team1):
                continue
                
            # Calculate position between enemy and pet
            pet_y = self.get_y(i, len(self.battle_player.team1))
            pet_x = self.get_team1_x(i)
            
            if i < len(self.battle_player.team2):
                enemy_x = self.get_team2_x(i) + (constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH)
            else:
                # For cases where there are fewer enemies than pets (boss battle)
                enemy_x = self.get_team2_x(0) + (constants.PET_WIDTH * constants.BOSS_MULTIPLIER if self.boss else constants.PET_WIDTH)
            
            # Position debug log in the middle between enemy and pet
            log_x = (enemy_x + pet_x) // 2
            log_y = pet_y + constants.PET_HEIGHT // 2
            
            # Draw turn information
            turn_text = f"Turn {log_entry['turn']}"
            arrow = log_entry['arrow']
            hit_text = log_entry['hit']
            
            # Combine arrow and turn text
            if arrow == ">":
                display_text = f"{turn_text} >"
            elif arrow == "<":
                display_text = f"< {turn_text}"
            else:
                display_text = turn_text
                
            # Draw turn text
            turn_surface = font_small.render(display_text, True, constants.FONT_COLOR_DEFAULT)
            text_rect = turn_surface.get_rect(center=(log_x, log_y - int(10 * constants.UI_SCALE)))
            surface.blit(turn_surface, text_rect)
            
            # Draw hit result if available
            if hit_text:
                hit_color = self.get_hit_text_color(hit_text)
                hit_surface = font_small.render(hit_text, True, hit_color)
                hit_rect = hit_surface.get_rect(center=(log_x, log_y + int(10 * constants.UI_SCALE)))
                surface.blit(hit_surface, hit_rect)
