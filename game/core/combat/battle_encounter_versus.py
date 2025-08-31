# core/combat/battle_encounter_versus.py

import pygame
from core.combat.battle_encounter import BattleEncounter, GameBattle
from core.combat.sim.battle_simulator import BattleSimulator, BattleProtocol
from core.animation import PetFrame
from core.combat.sim.models import Digimon
import game.core.constants as constants
from core.utils.pygame_utils import blit_with_shadow
from core.utils.scene_utils import change_scene
from core import runtime_globals
from core.utils.utils_unlocks import unlock_item


class BattleEncounterVersus(BattleEncounter):
    def __init__(self, pet1, pet2, protocol: BattleProtocol):
        """
        Initializes the Versus encounter for PvP battles.
        """
        self.pet1 = pet1
        self.pet2 = pet2
        self.pet2.x = 2 * (constants.SCREEN_WIDTH / 240)
        self.protocol = protocol
        # Call the base class initializer
        module = "DMC"

        super().__init__(module, 0, 0)
        self.enemy_entry_counter = 0

        # Initialize the BattlePlayer with the two pets
        self.battle_player = GameBattle([pet1], [pet2], 0, 0, self.module)
        fixed_hp = None
        if protocol in [BattleProtocol.DMC_BS]:
            fixed_hp = 6
            self.turn_limit = 5
        elif protocol in [BattleProtocol.DM20_BS]:
            fixed_hp = 4
            self.turn_limit = 6
        elif protocol in [BattleProtocol.PEN20_BS]:
            fixed_hp = 3
            self.turn_limit = 6
        elif protocol in [BattleProtocol.DMX_BS]:
            self.turn_limit = 5

        if fixed_hp is not None:
            self.battle_player.team1_hp[0] = fixed_hp
            self.battle_player.team2_hp[0] = fixed_hp
            self.battle_player.team1_max_hp[0] = fixed_hp
            self.battle_player.team2_max_hp[0] = fixed_hp
            self.battle_player.team1_total_hp = fixed_hp
            self.battle_player.team2_total_hp = fixed_hp
            self.battle_player.team1_max_total_hp = fixed_hp
            self.battle_player.team2_max_total_hp = fixed_hp
        else:
            team1hp = pet1.get_hp()
            team2hp = pet2.get_hp()
            self.battle_player.team1_hp[0] = team1hp
            self.battle_player.team2_hp[0] = team2hp
            self.battle_player.team1_max_hp[0] = team1hp
            self.battle_player.team2_max_hp[0] = team2hp
            self.battle_player.team1_total_hp = team1hp
            self.battle_player.team2_total_hp = team2hp
            self.battle_player.team1_max_total_hp = team1hp
            self.battle_player.team2_max_total_hp = team2hp

        # Initialize the BattleSimulator with the given protocol
        self.simulator = BattleSimulator(protocol)

        # Set initial state
        self.phase = "alert"

    def calculate_combat_for_pairs(self):
        self.simulate_combat()

        self.process_battle_results()
        runtime_globals.game_sound.play("battle_online")

    def simulate_combat(self):
        strength_bonus = 3

        # Attribute mapping
        attribute_mapping = {
            "Va": 0,  # Vaccine
            "Da": 1,  # Data
            "Vi": 2,  # Virus
            "Free": 3  # Free
        }

        # Create Digimon instance for the attacker
        attacker = Digimon(
            name=self.battle_player.team1[0].name,
            order=0,
            traited=1 if self.battle_player.team1[0].traited else 0,
            egg_shake=1 if self.battle_player.team1[0].shook else 0,
            index=0,
            hp=self.battle_player.team1_hp[0],
            attribute=attribute_mapping.get(self.battle_player.team1[0].attribute, 3),  # Default to Free if not found
            power=self.battle_player.team1[0].get_power(),
            handicap=0,
            buff=0,
            mini_game=strength_bonus,
            level=self.battle_player.team1[0].level,
            stage=self.battle_player.team1[0].stage,
            sick=1 if self.battle_player.team1[0].sick else 0,
            shot1=self.battle_player.team1[0].atk_main,
            shot2=self.battle_player.team1[0].atk_alt,
            tag_meter=2
        )

        # Create Digimon instance for the defender
        defender = Digimon(
            name=self.battle_player.team2[0].name,
            order=1,
            traited=1 if self.battle_player.team2[0].traited else 0,
            egg_shake=1 if self.battle_player.team2[0].shook else 0,
            index=1,
            hp=self.battle_player.team2_hp[0],
            attribute=attribute_mapping.get(self.battle_player.team2[0].attribute, 3),  # Default to Free if not found
            power=self.battle_player.team2[0].get_power(),
            handicap=0,
            buff=0,
            mini_game=strength_bonus,
            level=self.battle_player.team2[0].level,
            stage=self.battle_player.team2[0].stage,
            sick=1 if self.battle_player.team2[0].sick else 0,
            shot1=self.battle_player.team2[0].atk_main,
            shot2=self.battle_player.team2[0].atk_alt,
            tag_meter=2
        )

        # Run simulation
        self.global_battle_log = self.simulator.simulate(attacker, defender)

        # Store the attacker's turns as the combat log for animation
        self.victory_status = "Victory" if self.global_battle_log.winner == "device1" else "Defeat"

    def update_alert(self):
        """
        Handles the alert phase, transitioning to the battle phase.
        """
        if self.frame_counter > 60:  # Wait for 1 second (assuming 60 FPS)
            self.frame_counter = 0
            self.phase = "battle"
            self.calculate_combat_for_pairs()

    def update_result(self):
        """
        Handles the result phase, displaying the winner and transitioning back to the main scene.
        """
        self.result_timer += 1
        if self.result_timer > 90:  # Wait for 1.5 seconds (assuming 60 FPS)
            # Process the result
            winner = self.pet1 if self.global_battle_log.winner == "device1" else self.pet2
            loser = self.pet2 if winner == self.pet1 else self.pet1

            runtime_globals.game_sound.play("happy")

            winner.finish_versus(True)
            loser.finish_versus(False)

            # Versus unlock logic: modules may declare unlocks of type 'versus'
            # with conditions such as making two pets of the same module battle
            # where one has version >= specified version.
            try:
                module_unlocks = getattr(self.module, 'unlocks', []) or []
                for unlock in module_unlocks:
                    if unlock.get('type') == 'versus':
                        # Requirement: two participants of same module and
                        # one of them meets the version requirement.
                        ver_req = unlock.get('version', None)
                        # If ver_req is specified and one of the two pets has
                        # at least that version, award to both participants
                        if ver_req is not None:
                            if (getattr(self.pet1, 'module', None) == getattr(self.pet2, 'module', None)):
                                if getattr(self.pet1, 'version', 0) >= ver_req or getattr(self.pet2, 'version', 0) >= ver_req:
                                    unlock_item(self.module.name, 'versus', unlock.get('name'))
            except Exception as e:
                runtime_globals.game_console.log(f"[Versus] Error processing versus unlocks: {e}")
            # Return to the main scene
            change_scene("game")

    def draw_result(self, surface: pygame.Surface):
        """
        Draws the result phase, showing the winner or indicating a draw.
        """
        # Determine winner and loser
        if self.global_battle_log.winner == "device1":
            result_text = f"Winner: {self.pet1.name}"
            color = constants.FONT_COLOR_GREEN
        elif self.global_battle_log.winner == "device2":
            result_text = f"Winner: {self.pet2.name}"
            color = constants.FONT_COLOR_GREEN
        else:
            result_text = "Draw"
            color = constants.FONT_COLOR_YELLOW

        # Render the result text
        result_render = self.font.render(result_text, True, color).convert_alpha()
        blit_with_shadow(surface, result_render, (constants.SCREEN_WIDTH // 2 - result_render.get_width() // 2, int(30 * constants.UI_SCALE)))

        # Draw sprites for both battlers
        sprite_width = constants.PET_WIDTH // 2
        sprite_height = constants.PET_HEIGHT // 2
        spacing = int(20 * constants.UI_SCALE)

        # Position for pet1 (left side)
        pet1_x = constants.SCREEN_WIDTH // 4 - sprite_width // 2
        pet1_y = constants.SCREEN_HEIGHT // 2 - sprite_height // 2

        # Position for pet2 (right side)
        pet2_x = 3 * constants.SCREEN_WIDTH // 4 - sprite_width // 2
        pet2_y = constants.SCREEN_HEIGHT // 2 - sprite_height // 2

        # Animate pet1
        anim_toggle = (self.frame_counter // (15 * constants.FRAME_RATE // 30)) % 2
        if self.global_battle_log.winner == "device1":
            frame_id = PetFrame.HAPPY.value if anim_toggle == 0 else PetFrame.IDLE1.value
        else:
            frame_id = PetFrame.LOSE.value
        pet1_sprite = self.pet1.get_sprite(frame_id)
        pet1_sprite = pygame.transform.scale(pet1_sprite, (sprite_width, sprite_height))
        blit_with_shadow(surface, pet1_sprite, (pet1_x, pet1_y))

        # Animate pet2
        if self.global_battle_log.winner == "device2":
            frame_id = PetFrame.HAPPY.value if anim_toggle == 0 else PetFrame.IDLE1.value
        else:
            frame_id = PetFrame.LOSE.value
        pet2_sprite = self.pet2.get_sprite(frame_id)
        pet2_sprite = pygame.transform.scale(pet2_sprite, (sprite_width, sprite_height))
        blit_with_shadow(surface, pet2_sprite, (pet2_x, pet2_y))