"""
Scene Battle PvP
A scene for network battles against other Omnimon devices.
"""
import pygame
from components.window_background import WindowBackground
from core import game_globals, runtime_globals
from core.combat.battle_encounter import BattleEncounter
from core.combat.sim import models as sim_models
from core.utils.scene_utils import change_scene
import game.core.constants as constants

class SceneBattlePvP:
    """
    Scene for PvP network battles using simulation data.
    """

    def __init__(self) -> None:
        """
        Initializes the PvP battle scene.
        """
        self.background = WindowBackground()
        self.battle_encounter = None
        
        runtime_globals.game_console.log("[SceneBattlePvP] Initializing PvP battle scene...")
        
        # Get PvP battle data from runtime globals
        if hasattr(runtime_globals, 'pvp_battle_data') and runtime_globals.pvp_battle_data:
            try:
                pvp_data = runtime_globals.pvp_battle_data
                self.is_host = pvp_data.get('is_host', False)
                self.my_pets = pvp_data.get('my_pets', [])
                self.my_team_data = pvp_data.get('my_team_data', [])
                self.enemy_team_data = pvp_data.get('enemy_team_data', [])
                self.simulation_data = pvp_data.get('simulation_data', {})
                self.module_name = pvp_data.get('module', 'DMC')
                
                # Validate required data
                if not self.my_pets:
                    runtime_globals.game_console.log("[SceneBattlePvP] No my_pets data found")
                    change_scene("game")
                    return
                    
                if not self.enemy_team_data:
                    runtime_globals.game_console.log("[SceneBattlePvP] No enemy_team_data found")
                    change_scene("game")
                    return
                    
                if not self.simulation_data:
                    runtime_globals.game_console.log("[SceneBattlePvP] No simulation_data found")
                    change_scene("game")
                    return
                
                runtime_globals.game_console.log(f"[SceneBattlePvP] PvP data loaded:")
                runtime_globals.game_console.log(f"  - Is Host: {self.is_host}")
                runtime_globals.game_console.log(f"  - My pets: {len(self.my_pets)}")
                runtime_globals.game_console.log(f"  - Enemy team data: {len(self.enemy_team_data)}")
                runtime_globals.game_console.log(f"  - Module: {self.module_name}")
                
                # Create battle encounter for PvP
                self.setup_pvp_battle()
                
                runtime_globals.game_console.log(f"[SceneBattlePvP] PvP battle scene initialized successfully")
                
            except Exception as e:
                runtime_globals.game_console.log(f"[SceneBattlePvP] Error initializing PvP data: {e}")
                import traceback
                runtime_globals.game_console.log(f"[SceneBattlePvP] Traceback: {traceback.format_exc()}")
                change_scene("game")
        else:
            runtime_globals.game_console.log("[SceneBattlePvP] No PvP battle data found, returning to game")
            change_scene("game")

    def setup_pvp_battle(self) -> None:
        """Sets up the PvP battle encounter with simulation data."""
        try:
            runtime_globals.game_console.log("[SceneBattlePvP] Setting up PvP battle encounter...")
            # Create battle encounter in PvP mode
            self.battle_encounter = BattleEncounter(
                self.module_name, 
                area=0, 
                round=0, 
                version=1, 
                pvp_mode=True
            )
            
            runtime_globals.game_console.log(f"[SceneBattlePvP] Battle encounter created for module: {self.module_name}")
            
            # Both devices should show the same visual arrangement:
            # Team1 (left) = device1 pets, Team2 (right) = device2 pets
            # Determine which pets belong to device1 and device2 from the battle log
            
            if self.is_host:
                # Host created the battle log: device1 = host pets, device2 = client pets
                team1_pets = self.my_pets  # Host pets (GamePet objects)
                team2_pet_data = self.enemy_team_data  # Client pets (pet data dicts)
            else:
                # Client: device1 = host pets, device2 = client pets (same as host perspective)
                # For client, we need to convert host's pet data to GamePet objects for team1
                # and convert client's GamePet objects to pet data dicts for team2
                
                # Convert host pet data dicts to GamePet objects for team1
                from core.game_pet import GamePet
                team1_pets = []
                for pet_data in self.enemy_team_data:  # Host pets (pet data dicts)
                    # Add missing keys that GamePet constructor expects
                    complete_pet_data = pet_data.copy()
                    complete_pet_data.setdefault("version", 1)  # Default version
                    complete_pet_data.setdefault("special", False)  # Default special
                    complete_pet_data.setdefault("evolve", [])  # Default evolve list
                    complete_pet_data.setdefault("sleeps", None)  # Default sleep time
                    complete_pet_data.setdefault("wakes", None)  # Default wake time
                    complete_pet_data.setdefault("time", 0)  # Default time
                    complete_pet_data.setdefault("poop_timer", 60)  # Default poop timer
                    complete_pet_data.setdefault("min_weight", 10)  # Default min weight
                    complete_pet_data.setdefault("evol_weight", 0)  # Default evol weight
                    complete_pet_data.setdefault("stomach", 4)  # Default stomach
                    complete_pet_data.setdefault("hunger_loss", 60)  # Default hunger loss
                    complete_pet_data.setdefault("strength_loss", 60)  # Default strength loss
                    complete_pet_data.setdefault("energy", 100)  # Default energy
                    complete_pet_data.setdefault("heal_doses", 1)  # Default heal doses
                    complete_pet_data.setdefault("condition_hearts", 0)  # Default condition hearts
                    complete_pet_data.setdefault("jogress_avaliable", 0)  # Default jogress
                    
                    # Create GamePet object using complete pet_data
                    temp_pet = GamePet(complete_pet_data)
                    team1_pets.append(temp_pet)
                
                # Convert client GamePet objects to pet data dicts for team2
                team2_data = []
                for pet in self.my_pets:  # Client pets (GamePet objects)
                    pet_data = {
                        "name": pet.name,
                        "stage": pet.stage,
                        "level": pet.level,
                        "hp": pet.get_hp() if hasattr(pet, "get_hp") else getattr(pet, "hp", 100),
                        "power": pet.get_power() if hasattr(pet, "get_power") else getattr(pet, "power", 1),
                        "attribute": pet.attribute,
                        "atk_main": pet.atk_main,
                        "atk_alt": pet.atk_alt,
                        "module": pet.module,
                        "sick": getattr(pet, "sick", 0) > 0,
                        "traited": getattr(pet, "traited", False),
                        "shook": getattr(pet, "shook", False)
                    }
                    team2_data.append(pet_data)
                team2_pet_data = team2_data
            
            runtime_globals.game_console.log(f"[SceneBattlePvP] Setting up teams: team1_pets={len(team1_pets)}, team2_pet_data={len(team2_pet_data)}")
            self.battle_encounter.setup_pvp_teams(team1_pets, team2_pet_data)
            
            # Set flag for which team to show in result phase
            # Host should show team1 (their pets), client should show team2 (their pets)
            self.battle_encounter.show_team2_in_result = not self.is_host
            
            # Set the simulation data
            # Try to use original battle log object first (for host)
            original_battle_log = runtime_globals.pvp_battle_data.get('original_battle_log', None)
            if original_battle_log is not None:
                runtime_globals.game_console.log("[SceneBattlePvP] Using original battle log object")
                self.battle_encounter.global_battle_log = original_battle_log
                # Log the winner from the battle log
                if hasattr(original_battle_log, 'winner'):
                    runtime_globals.game_console.log(f"[SceneBattlePvP] Battle log winner: {original_battle_log.winner}")
            else:
                # Fallback to serialized data (for non-host)
                battle_log = self.simulation_data.get('battle_log', {})
                runtime_globals.game_console.log("[SceneBattlePvP] Using serialized battle log data")
                # Log the winner from serialized data
                if isinstance(battle_log, dict) and 'winner' in battle_log:
                    runtime_globals.game_console.log(f"[SceneBattlePvP] Serialized battle log winner: {battle_log['winner']}")

                # Deserialize the battle log data
                try:
                    from core.combat.sim.models import battle_result_from_serialized
                    self.battle_encounter.global_battle_log = battle_result_from_serialized(battle_log)
                except Exception as e:
                    runtime_globals.game_console.log(f"[SceneBattlePvP] Failed to deserialize battle log: {e}")
                    self.battle_encounter.global_battle_log = battle_log
                
            # The simulation payload's victory_status represents the canonical result:
            # "Victory" = device1 won, "Defeat" = device2 won
            # Since both devices now show device1 pets on left, device2 pets on right:
            # - Host sees their pets (device1) on left, so "Victory" = their victory
            # - Client sees host pets (device1) on left, so "Victory" = host victory = client defeat
            original_victory_status = self.simulation_data.get('victory_status', 'Victory')
            runtime_globals.game_console.log(f"[SceneBattlePvP] Original victory status from simulation: {original_victory_status}")
            
            self.battle_encounter.victory_status = original_victory_status

            if not self.is_host:
                # Client: since they see host pets (device1) on left side:
                # The victory_status represents: "Victory" = device1 won, "Defeat" = device2 won
                # Client sees device1 pets on left, device2 pets (theirs) on right
                # So if device1 won ("Victory"), client lost and should see "Defeat"
                # If device2 won ("Defeat"), client won and should see "Victory"
                vs = self.battle_encounter.victory_status
                if vs == "Victory":  # device1 (host) won
                    self.battle_encounter.victory_status = "Defeat"  # client lost
                elif vs == "Defeat":  # device2 (client) won
                    self.battle_encounter.victory_status = "Victory"  # client won
                # Handle legacy device labels
                elif vs == "device1":
                    self.battle_encounter.victory_status = "Defeat" 
                elif vs == "device2":
                    self.battle_encounter.victory_status = "Victory"
                runtime_globals.game_console.log(f"[SceneBattlePvP] Client flipped victory status from {vs} to {self.battle_encounter.victory_status}")
            else:
                runtime_globals.game_console.log(f"[SceneBattlePvP] Host perspective. Victory status: {self.battle_encounter.victory_status}")
            
            # Log battle data info
            if hasattr(self.battle_encounter.global_battle_log, 'battle_log'):
                log_length = len(self.battle_encounter.global_battle_log.battle_log)
            elif isinstance(self.battle_encounter.global_battle_log, list):
                log_length = len(self.battle_encounter.global_battle_log)
            elif isinstance(self.battle_encounter.global_battle_log, dict) and 'battle_log' in self.battle_encounter.global_battle_log:
                log_length = len(self.battle_encounter.global_battle_log['battle_log'])
            else:
                log_length = 0
                
            runtime_globals.game_console.log(f"[SceneBattlePvP] Loaded {log_length} battle log entries")
            runtime_globals.game_console.log(f"[SceneBattlePvP] Victory status: {self.battle_encounter.victory_status}")
            
            # Process results for animations (but skip XP/level ups in PvP mode)
            if hasattr(self.battle_encounter, 'process_battle_results'):
                self.battle_encounter.process_battle_results()
            
            # Skip to battle phase
            self.battle_encounter.phase = "battle"
            self.battle_encounter.frame_counter = 0
            
            runtime_globals.game_console.log("[SceneBattlePvP] Battle setup completed successfully")
                
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattlePvP] Error setting up PvP battle: {e}")
            import traceback
            runtime_globals.game_console.log(f"[SceneBattlePvP] Traceback: {traceback.format_exc()}")
            change_scene("game")

    def swap_battle_log_devices(self, battle_log_dict):
        """Swaps device1/device2 in battle log for client perspective."""
        try:
            swapped_log = battle_log_dict.copy()
            
            # Swap winner
            if swapped_log.get('winner') == 'device1':
                swapped_log['winner'] = 'device2'
            elif swapped_log.get('winner') == 'device2':
                swapped_log['winner'] = 'device1'
            
            # Swap final device states
            if 'device1_final' in swapped_log and 'device2_final' in swapped_log:
                temp = swapped_log['device1_final']
                swapped_log['device1_final'] = swapped_log['device2_final']
                swapped_log['device2_final'] = temp
            
            # Swap battle log entries
            if 'battle_log' in swapped_log:
                for turn_log in swapped_log['battle_log']:
                    # Swap device status
                    if 'device1_status' in turn_log and 'device2_status' in turn_log:
                        temp = turn_log['device1_status']
                        turn_log['device1_status'] = turn_log['device2_status']
                        turn_log['device2_status'] = temp
                    
                    # Swap attack device references
                    if 'attacks' in turn_log:
                        for attack in turn_log['attacks']:
                            if attack.get('device') == 'device1':
                                attack['device'] = 'device2'
                            elif attack.get('device') == 'device2':
                                attack['device'] = 'device1'
            
            return swapped_log
        except Exception as e:
            runtime_globals.game_console.log(f"[SceneBattlePvP] Error swapping battle log: {e}")
            return battle_log_dict  # Return original on error

    def deserialize_battle_result(self, serialized: dict) -> sim_models.BattleResult:
        """Convert a serialized battle result dict into sim_models.BattleResult dataclass.

        This reconstructs DigimonStatus, AttackLog, TurnLog and BattleResult instances.
        Packet hex strings will be converted back to bytes when possible.
        """
        # Helper to restore DigimonStatus
        def make_status(d):
            return sim_models.DigimonStatus(name=d.get('name', ''), hp=int(d.get('hp', 0)), alive=bool(d.get('alive', False)))

        # Helper to restore AttackLog
        def make_attack(d):
            return sim_models.AttackLog(
                turn=int(d.get('turn', 0)),
                device=d.get('device', ''),
                attacker=int(d.get('attacker', -1)),
                defender=int(d.get('defender', -1)),
                hit=bool(d.get('hit', False)),
                damage=int(d.get('damage', 0))
            )

        # Helper to restore TurnLog
        def make_turn(t):
            device1 = [make_status(s) for s in t.get('device1_status', [])]
            device2 = [make_status(s) for s in t.get('device2_status', [])]
            attacks = [make_attack(a) for a in t.get('attacks', [])]
            return sim_models.TurnLog(turn=int(t.get('turn', 0)), device1_status=device1, device2_status=device2, attacks=attacks)

        # Reconstruct packets: convert hex strings back to bytes where applicable
        def restore_packets(packet_lists):
            restored = []
            for pkt_list in packet_lists or []:
                new_list = []
                for pkt in pkt_list:
                    if isinstance(pkt, str):
                        try:
                            new_list.append(bytes.fromhex(pkt))
                        except Exception:
                            new_list.append(pkt)
                    else:
                        new_list.append(pkt)
                restored.append(new_list)
            return restored

        winner = serialized.get('winner', 'draw')
        device1_final = [make_status(s) for s in serialized.get('device1_final', [])]
        device2_final = [make_status(s) for s in serialized.get('device2_final', [])]
        battle_log = [make_turn(t) for t in serialized.get('battle_log', [])]
        device1_packets = restore_packets(serialized.get('device1_packets', []))
        device2_packets = restore_packets(serialized.get('device2_packets', []))

        return sim_models.BattleResult(
            winner=winner,
            device1_final=device1_final,
            device2_final=device2_final,
            battle_log=battle_log,
            device1_packets=device1_packets,
            device2_packets=device2_packets
        )

    def update(self) -> None:
        """
        Updates the PvP battle scene.
        """
        if self.battle_encounter:
            self.battle_encounter.update()
            
            # Check if battle is complete
            if self.battle_encounter.phase == "result" or self.battle_encounter.phase == "clear":
                # Battle completed, check for return to game
                pass

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the PvP battle scene.
        """
        self.background.draw(surface)
        if self.battle_encounter:
            self.battle_encounter.draw(surface)

    def handle_event(self, input_action) -> None:
        """
        Handles keyboard and GPIO button inputs for the PvP battle scene.
        """
        if self.battle_encounter:
            self.battle_encounter.handle_event(input_action)
            
            # Check for battle completion and return to game
            if self.battle_encounter.phase in ["result", "clear", "finished"]:
                if input_action == "A" or input_action == "B" or input_action == "START":
                    runtime_globals.game_console.log("[SceneBattlePvP] PvP battle completed, returning to game")
                    # Clear PvP data
                    if hasattr(runtime_globals, 'pvp_battle_data'):
                        delattr(runtime_globals, 'pvp_battle_data')
                    change_scene("game")
        else:
            # If no battle encounter, return to game on any input
            if input_action:
                runtime_globals.game_console.log("[SceneBattlePvP] No battle encounter, returning to game")
                if hasattr(runtime_globals, 'pvp_battle_data'):
                    delattr(runtime_globals, 'pvp_battle_data')
                change_scene("game")
