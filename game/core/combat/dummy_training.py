#=====================================================================
# DummyTraining (Simple Strength Bar Training)
#=====================================================================

import random
import pygame

from core import runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from components.ui.ui_manager import UIManager
from core.combat import combat_constants
import core.constants as constants
from core.game_module import sprite_load
from core.utils.pygame_utils import blit_with_shadow
from components.minigames.dummy_charge import DummyCharge
from core.utils.scene_utils import change_scene

class DummyTraining(Training):
    """
    Dummy training mode where players build up strength by holding a bar.
    """

    def __init__(self, ui_manager: UIManager) -> None:
        super().__init__(ui_manager)
        # Delegate charge/attack logic to the DummyCharge minigame
        self.minigame = DummyCharge(ui_manager)
        # expose commonly accessed fields for compatibility
        self.strength = self.minigame.strength
        self.bar_level = self.minigame.bar_level
        self.bar_timer = 0
        self.attack_phase = 1
        self.flash_frame = 0

        # Restore attack/result assets/positions (training-specific)
        SPRITE_SETS = [
            (constants.BAG1_PATH, constants.BAG2_PATH),
            (constants.ROCK1_PATH, constants.ROCK2_PATH),
            (constants.TREE1_PATH, constants.TREE2_PATH),
            (constants.BRICK1_PATH, constants.BRICK2_PATH),
        ]

        selected_sprites = random.choice(SPRITE_SETS)
        self.bag1 = sprite_load(selected_sprites[0], size=(60 * constants.UI_SCALE, 120 * constants.UI_SCALE))
        self.bag2 = sprite_load(selected_sprites[1], size=(60 * constants.UI_SCALE, 120 * constants.UI_SCALE))
        self.attack_positions = []

    def update_charge_phase(self):
        # Ensure minigame is updated and synced before checking phase
        self.minigame.update()
        self.strength = self.minigame.strength

        # Transition to wait_attack if hold time exceeded
        if pygame.time.get_ticks() - self.bar_timer > combat_constants.BAR_HOLD_TIME_MS:
            self.phase = "wait_attack"
            self.frame_counter = 0
            self.prepare_attacks()

    def move_attacks(self):
        """Handles the attack movement towards the bag."""
        finished = False
        new_positions = []

        if self.attack_phase == 1:
            for sprite, (x, y) in self.attack_positions:
                x -= combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE)  # Frame-rate independent speed
                if x <= 0:
                    finished = True
                new_positions.append((sprite, (x, y)))

            if finished:
                new_positions = []
                self.attack_phase = 2
                for sprite, (x, y) in self.attack_positions:
                    x += constants.SCREEN_WIDTH
                    new_positions.append((sprite, (x, y)))

            self.attack_positions = new_positions

        elif self.attack_phase == 2:
            bag_x = 50 * constants.UI_SCALE
            for sprite, (x, y) in self.attack_positions:
                x -= combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE)  # Frame-rate independent speed

                if x <= bag_x + (48 * constants.UI_SCALE):
                    finished = True
                new_positions.append((sprite, (x, y)))

            if finished:
                runtime_globals.game_sound.play("attack_hit")
                self.phase = "impact"
                self.flash_frame = 0

            self.attack_positions = new_positions

    def check_victory(self):
        """Apply training results and return to game."""
        # sync strength from minigame
        self.strength = self.minigame.strength
        return self.strength > 10

    def check_and_award_trophies(self):
        """Award trophy if strength reaches maximum (14)"""
        self.strength = self.minigame.strength

        if self.strength == 14:
            for pet in self.pets:
                pet.trophies += 1
            runtime_globals.game_console.log(f"[TROPHY] Dummy training perfect score achieved! Trophy awarded.")

    def draw_charge(self, surface):
        
        self.minigame.draw(surface)
        self.draw_pets(surface)

    def handle_event(self, event):
        """Forward input events to the bar component."""
        if self.minigame.handle_event(event):
            return
        
        if isinstance(event, str):
            if event in ("START", "B") and self.phase in ("charge", "alert"):
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
            elif event in ("A", "B") and self.phase != "result":
                runtime_globals.game_sound.play("cancel")
                self.phase = "result"

    def draw_attack_move(self, surface):
        if self.attack_phase == 1:
            if self.frame_counter < int(10 * (constants.FRAME_RATE / 30)):
                self.draw_pets(surface, PetFrame.ATK2)
            else:
                self.draw_pets(surface, PetFrame.ATK1)
        else:
            blit_with_shadow(surface, self.bag1, (int(50 * constants.UI_SCALE), constants.SCREEN_HEIGHT // 2 - self.bag1.get_height() // 2))

        for sprite, (x, y) in self.attack_positions:
            blit_with_shadow(surface, sprite, (int(x), int(y)))

    def draw_result(self, surface):
        self.strength = self.minigame.strength

        # Use cached result sprites
        bad_sprite = self._sprite_cache['bad']
        great_sprite = self._sprite_cache['great']
        excellent_sprite = self._sprite_cache['excellent']

        result_img = None
        if 10 <= self.strength < 14:
            result_img = self.bag2
        elif self.strength < 10:
            result_img = self.bag1

        
        if self.frame_counter < 30:
            if result_img:
                x = int(50 * constants.UI_SCALE)
                y = constants.SCREEN_HEIGHT // 2 - result_img.get_height() // 2
                blit_with_shadow(surface, result_img, (x, y))
        else:
            # Composition for result screen:
            # 1) black background
            surface.fill((0, 0, 0))

            # Choose which result sprite to display
            if self.strength < 10:
                selected_sprite = bad_sprite
                cache_key = 'result_bad'
            elif self.strength < 14:
                selected_sprite = great_sprite
                cache_key = 'result_great'
            else:
                selected_sprite = excellent_sprite
                cache_key = 'result_excellent'

            # 2) semi-transparent full-screen proportional overlay when ui scale >= 2
            self._draw_overlay_background(surface, selected_sprite, cache_key)

            # 3) integer-scaled sprite centered
            sx, sy = selected_sprite.get_width(), selected_sprite.get_height()
            center_x = constants.SCREEN_WIDTH // 2 - sx // 2
            center_y = constants.SCREEN_HEIGHT // 2 - sy // 2
            blit_with_shadow(surface, selected_sprite, (center_x, center_y))

            # Trophy notification on max
            if self.strength >= 14:
                self.draw_trophy_notification(surface)

    def prepare_attacks(self):
        attack_count = self.get_attack_count()
        targets = self.pets
        total_pets = len(targets)
        if total_pets == 0:
            return

        available_height = constants.SCREEN_HEIGHT
        spacing = min(available_height // total_pets, int(48 * constants.UI_SCALE) + int(20 * constants.UI_SCALE))
        start_y = (constants.SCREEN_HEIGHT - (spacing * total_pets)) // 2

        for i, pet in enumerate(targets):
            atk_sprite = self.get_attack_sprite(pet, pet.atk_main)
            x = constants.SCREEN_WIDTH - int(48 * constants.UI_SCALE) - int(70 * constants.UI_SCALE)
            y = start_y + i * spacing

            if attack_count == 1:
                self.attack_positions.append((atk_sprite, (x, y)))
            elif attack_count == 2:
                self.attack_positions.append((atk_sprite, (x, y)))
                self.attack_positions.append((atk_sprite, (x + int(20 * constants.UI_SCALE), y + int(10 * constants.UI_SCALE))))
            elif attack_count == 3:
                scaled_sprite = pygame.transform.scale2x(atk_sprite)
                self.attack_positions.append((scaled_sprite, (x, y)))
                # Optionally, add more positions for extra visual feedback:
                #self.attack_positions.append((atk_sprite, (x + int(20 * constants.UI_SCALE), y + int(10 * constants.UI_SCALE))))
                #self.attack_positions.append((atk_sprite, (x - int(20 * constants.UI_SCALE), y - int(10 * constants.UI_SCALE))))

    def get_attack_count(self):
        """Returns the number of attacks based on strength."""
        self.strength = self.minigame.strength
        if self.strength < 10:
            return 1
        elif self.strength < 14:
            return 2
        else:
            return 3