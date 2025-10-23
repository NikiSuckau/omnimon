#=====================================================================
# ExciteTraining (Simple Strength Bar Training)
#=====================================================================

import pygame
from core import game_globals, runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from game.components.ui.ui_manager import UIManager
from game.core.combat import combat_constants
import game.core.constants as constants
from components.window_xaibar import WindowXaiBar
from core.utils.pygame_utils import blit_with_shadow
from core.utils.scene_utils import change_scene

class ExciteTraining(Training):
    """
    Excite training mode where players build up strength by holding a bar.
    """

    def __init__(self, ui_manager: UIManager) -> None:
        super().__init__(ui_manager)
        self.xaibar = WindowXaiBar(10 * constants.UI_SCALE, constants.SCREEN_HEIGHT // 2 - (18 * constants.UI_SCALE), game_globals.xai, self.pets[0])
        self.xaibar.start()
        # Remove separate sprite assignments; use self._sprite_cache from base class

    def update_charge_phase(self):
        self.xaibar.update()
        # End phase after a certain time or on input (like bar phase)
        if self.frame_counter > int(30 * 3 * (constants.FRAME_RATE / 30)):
            self.xaibar.stop()
            runtime_globals.game_console.log(f"XaiBar phase ended strength {self.xaibar.selected_strength}.")
            self.phase = "wait_attack"
            self.frame_counter = 0
            self.prepare_attacks()

    def move_attacks(self):
        """Handles the attack movement towards the bag, all in one phase."""
        if self.current_wave_index >= len(self.attack_waves):
            self.phase = "result"
            self.frame_counter = 0
            return

        wave = self.attack_waves[self.current_wave_index]
        new_wave = []
        all_off_screen = True

        if self.frame_counter <= 1:
            runtime_globals.game_sound.play("attack")

        speed = combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE)

        for sprite, kind, x, y in wave:
            x -= speed  # Frame-rate independent speed
            if x + (24 * constants.UI_SCALE) > 0:
                all_off_screen = False
                new_wave.append((sprite, kind, x, y))

        self.attack_waves[self.current_wave_index] = new_wave

        # Wait at least 10 frames (at 30fps) before next wave
        if all_off_screen and self.frame_counter >= int(10 * (constants.FRAME_RATE / 30)):
            self.current_wave_index += 1
            self.frame_counter = 0

    def check_victory(self):
        """Apply training results and return to game."""
        return self.xaibar.selected_strength > 0

    def check_and_award_trophies(self):
        """Award trophy if strength reaches maximum (3)"""
        if self.xaibar.selected_strength == 3:
            for pet in self.pets:
                pet.trophies += 1
            runtime_globals.game_console.log(f"[TROPHY] Excite training perfect score achieved! Trophy awarded.")

    def draw_charge(self, surface):
        self.xaibar.draw(surface)
        self.draw_pets(surface, PetFrame.IDLE1)

    def draw_pets(self, surface, frame_enum=PetFrame.IDLE1):
        """
        Draws pets using appropriate frame based on attack animation phase.
        """
        if self.phase == "attack_move":
            frame_enum = self.animate_attack(46)
        super().draw_pets(surface, frame_enum)

    def draw_attack_move(self, surface):
        self.draw_pets(surface)
        for wave in self.attack_waves:
            for sprite, kind, x, y in wave:
                if x < constants.SCREEN_WIDTH - (90 * constants.UI_SCALE):
                    blit_with_shadow(surface, sprite, (x, y))
                    if kind in [2, 3]:
                        blit_with_shadow(surface, sprite, (x - (20 * constants.UI_SCALE), y - (10 * constants.UI_SCALE)))
                    if kind == 3:
                        blit_with_shadow(surface, sprite, (x - (40 * constants.UI_SCALE), y + (10 * constants.UI_SCALE)))

    def draw_result(self, surface):
        # Composition for result screen:
        # 1) black background
        surface.fill(self.background_color)

        # Use cached result sprites from base class
        bad_sprite = self._sprite_cache['bad']
        good_sprite = self._sprite_cache['good']
        great_sprite = self._sprite_cache['great']
        excellent_sprite = self._sprite_cache['excellent']

        strength = self.xaibar.selected_strength
        
        # Choose which result sprite to display
        if strength == 0:
            selected_sprite = bad_sprite
            cache_key = 'excite_result_bad'
        elif strength == 1:
            selected_sprite = good_sprite
            cache_key = 'excite_result_good'
        elif strength == 2:
            selected_sprite = great_sprite
            cache_key = 'excite_result_great'
        else:
            selected_sprite = excellent_sprite
            cache_key = 'excite_result_excellent'

        # 2) semi-transparent full-screen proportional overlay when ui scale >= 2
        self._draw_overlay_background(surface, selected_sprite, cache_key)

        # 3) integer-scaled sprite centered
        sx, sy = selected_sprite.get_width(), selected_sprite.get_height()
        center_x = constants.SCREEN_WIDTH // 2 - sx // 2
        center_y = constants.SCREEN_HEIGHT // 2 - sy // 2
        blit_with_shadow(surface, selected_sprite, (center_x, center_y))

        # Trophy notification on max
        if strength == 3:
            self.draw_trophy_notification(surface)

    def prepare_attacks(self):
        """Prepare 5 attacks from each pet based on selected_strength."""
        self.attack_phase = 0
        self.attack_waves = [[] for _ in range(5)]
        pets = self.pets
        total_pets = len(pets)

        available_height = constants.SCREEN_HEIGHT
        spacing = min(available_height // total_pets, constants.OPTION_ICON_SIZE + (20 * constants.UI_SCALE))
        start_y = (constants.SCREEN_HEIGHT - (spacing * total_pets)) // 2

        # Determine super-hit pattern based on selected_strength
        strength = self.xaibar.selected_strength
        if strength == 3:
            pattern = [4, 3, 3, 3, 3]  # 5 super-hits (megahit)
        elif strength == 2:
            pattern = [3, 3, 3, 2, 2]  # 3 super-hits, 2 normal
        elif strength == 1:
            pattern = [3, 2, 1, 1, 1]  # 1 super-hit, 4 normal
        else:
            pattern = [1] * 5  # all normal, fail

        for i, pet in enumerate(pets):
            sprite = self.get_attack_sprite(pet, pet.atk_main)
            if not sprite:
                continue
            pet_y = start_y + i * spacing + constants.OPTION_ICON_SIZE // 2 - sprite.get_height() // 2
            for j, kind in enumerate(pattern):
                x = constants.SCREEN_WIDTH - constants.OPTION_ICON_SIZE - (20 * constants.UI_SCALE)
                y = pet_y
                if kind == 4:
                    sprite2 = pygame.transform.scale2x(sprite)
                    self.attack_waves[j].append((sprite2, kind, x, y))
                else:
                    self.attack_waves[j].append((sprite, kind, x, y))

    def get_attack_count(self):
        strength = self.xaibar.selected_strength
        if strength < 1:
            return 1
        elif strength < 3:
            return 2
        else:
            return 3

    def handle_event(self, input_action):
        if self.phase == "charge" and input_action in ["A", "LCLICK"]:
            runtime_globals.game_sound.play("menu")
            self.xaibar.stop()
            runtime_globals.game_console.log(f"XaiBar phase ended strength {self.xaibar.selected_strength}.")
            self.phase = "wait_attack"
            self.frame_counter = 0
            self.prepare_attacks()
        elif self.phase in ["wait_attack", "attack_move", "impact", "result"] and input_action in ["B", "START"]:
            self.finish_training()
        elif self.phase in ["alert", "charge"] and input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")