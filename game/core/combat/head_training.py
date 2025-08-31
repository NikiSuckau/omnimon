#=====================================================================
# HeadToHeadTraining (Reaction Timing and Coordination)
#=====================================================================

import os
import random
import pygame

from core import runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from game.core.combat import combat_constants
import game.core.constants as constants
from core.utils.pet_utils import get_training_targets
from core.utils.pygame_utils import blit_with_shadow, get_font, sprite_load_percent
from core.utils.scene_utils import change_scene

class HeadToHeadTraining(Training):
    """
    Head-to-Head training mode where two pets face off based on player's timing.
    """

    PATTERNS = [
        "ABABB", "BBAAB", "BAABB",
        "ABBAA", "BABAB", "ABABA"
    ]

    def __init__(self) -> None:
        super().__init__()
        self.left_pet = None
        self.right_pet = None
        self.pattern = ""
        self.current_index = 0
        self.victories = 0
        self.failures = 0
        self.player_input = None
        self.is_collision = False
        self.attack_positions = []

        # Sprite caching
        self._sprite_cache['head_training_img'] = sprite_load_percent(constants.HEADTRAINING_PATH, percent=60, keep_proportion=True, base_on="width")
        self._sprite_cache['vs_img'] = sprite_load_percent(constants.VS_PATH, percent=17, keep_proportion=True, base_on="width")
        self._sprite_cache['strikes'] = sprite_load_percent(constants.STRIKE_PATH, percent=7, keep_proportion=True, base_on="width")
        self._sprite_cache['strikes_back'] = sprite_load_percent(constants.STRIKES_BACK_PATH, percent=40, keep_proportion=True, base_on="width")

        self.select_pets()
        self.select_pattern()

    def select_pets(self):
        candidates = get_training_targets()
        if len(candidates) >= 2:
            self.left_pet, self.right_pet = random.sample(candidates, 2)

    def select_pattern(self):
        last = getattr(runtime_globals, "last_headtohead_pattern", random.randint(0, 5))
        runtime_globals.last_headtohead_pattern = (last + 1) % 6
        self.pattern = self.PATTERNS[runtime_globals.last_headtohead_pattern]
        self.current_index = 0

    def draw(self, surface: pygame.Surface):

        if not (self.left_pet and self.right_pet):
            return

        if self.phase != "result":
            strikes_back = self._sprite_cache['strikes_back']
            strikes = self._sprite_cache['strikes']
            starting_x = constants.SCREEN_WIDTH - strikes_back.get_width() - int(5 * constants.UI_SCALE)
            starting_y = constants.SCREEN_HEIGHT - strikes_back.get_height() - int(5 * constants.UI_SCALE)
            blit_with_shadow(surface, strikes_back, (starting_x, starting_y))

            for i in range(5 - self.current_index):
                x = starting_x + 7 + (4 - i) * strikes.get_width()
                y = starting_y + (6 * constants.UI_SCALE)
                blit_with_shadow(surface, strikes, (x, y))

            self.draw_pets(surface)
            if self.phase == "attack_move":
                self.draw_attacks(surface)
            elif self.phase == "alert":
                self.draw_alert(surface)
        else:
            self.draw_result(surface)

    def draw_pets(self, surface):
        left_frame = PetFrame.ATK2.value if self.phase == "attack_move" else PetFrame.ATK1.value
        right_frame = PetFrame.ATK2.value if self.phase == "attack_move" else PetFrame.ATK1.value

        left_sprite = runtime_globals.pet_sprites[self.left_pet][left_frame]
        right_sprite = runtime_globals.pet_sprites[self.right_pet][right_frame]
        left_sprite = pygame.transform.flip(left_sprite, True, False)

        blit_with_shadow(surface, left_sprite, (0 + (5 * constants.UI_SCALE), constants.SCREEN_HEIGHT // 2 - int(constants.PET_HEIGHT) // 2))
        blit_with_shadow(surface, right_sprite, (constants.SCREEN_WIDTH - constants.PET_WIDTH - (5 * constants.UI_SCALE), constants.SCREEN_HEIGHT // 2 - int(constants.PET_HEIGHT) // 2))

    def draw_attacks(self, surface):
        for sprite, (x, y) in self.attack_positions:
            blit_with_shadow(surface, sprite, (int(x), int(y)))

    def draw_result(self, surface):
        center_x = constants.SCREEN_WIDTH // 2
        center_y = constants.SCREEN_HEIGHT // 2
        head_training_img = self._sprite_cache['head_training_img']
        vs_img = self._sprite_cache['vs_img']

        blit_with_shadow(
            surface,
            head_training_img,
            (center_x - head_training_img.get_width() // 2, center_y - head_training_img.get_height() - int(20 * constants.UI_SCALE))
        )

        font = get_font(int(55 * constants.UI_SCALE))
        wins_text = font.render(str(self.victories), True, constants.FONT_COLOR_DEFAULT)
        losses_text = font.render(str(self.failures), True, constants.FONT_COLOR_DEFAULT)

        total_width = wins_text.get_width() + vs_img.get_width() + losses_text.get_width() + int(20 * constants.UI_SCALE)
        start_x = center_x - total_width // 2
        y = center_y + int(20 * constants.UI_SCALE)

        blit_with_shadow(surface, wins_text, (start_x, y))
        blit_with_shadow(surface, vs_img, (start_x + wins_text.get_width() + int(10 * constants.UI_SCALE), y))
        blit_with_shadow(surface, losses_text, (start_x + wins_text.get_width() + vs_img.get_width() + int(20 * constants.UI_SCALE), y))
        
        # Draw trophy notification if won
        if self.victories > self.failures:
            self.draw_trophy_notification(surface)

    def move_attacks(self):
        finished = False
        if self.is_collision:
            finished = self.update_collision()
        else:
            finished = self.update_cross_attack()
        if finished:
            self.process_attack_result()

    def update_collision(self):
        """Update attacks for a collision (meet in center), frame-rate independent."""
        target_x = constants.SCREEN_WIDTH // 2 - int(12 * constants.UI_SCALE)
        for atk in self.attack_positions:
            sprite, (x, y) = atk
            if x < target_x:
                x += combat_constants.ATTACK_SPEED
            elif x > target_x:
                x -= combat_constants.ATTACK_SPEED
            atk[1] = (x, y)
        left_x = self.attack_positions[0][1][0]
        right_x = self.attack_positions[1][1][0]
        return (
            abs(left_x - target_x) <= int(10 * constants.UI_SCALE)
            and abs(right_x - target_x) <= int(10 * constants.UI_SCALE)
        )

    def update_cross_attack(self):
        """Update attacks for cross fire (no collision), frame-rate independent."""
        self.attack_positions[0][1] = (
            self.attack_positions[0][1][0] + combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE),
            self.attack_positions[0][1][1]
        )
        self.attack_positions[1][1] = (
            self.attack_positions[1][1][0] - combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE),
            self.attack_positions[1][1][1]
        )
        return (
            self.attack_positions[0][1][0] >= constants.SCREEN_WIDTH - constants.PET_WIDTH - (5 * constants.UI_SCALE)
            or self.attack_positions[1][1][0] <= constants.PET_WIDTH + (5 * constants.UI_SCALE)
        )

    def handle_event(self, input_action):
        if self.phase == "charge" and input_action:
            if input_action == "UP":
                self.player_input = "B"
                self.start_attack()
            elif input_action == "DOWN":
                self.player_input = "A"
                self.start_attack()
            elif input_action in ("START", "B"):
                runtime_globals.game_sound.play("cancel")
                change_scene("game")
        elif input_action in ("A", "B"):
            runtime_globals.game_sound.play("cancel")
            change_scene("game")

    def start_attack(self):
        self.phase = "attack_move"
        self.attack_positions.clear()

        left_dir = self.pattern[self.current_index]
        right_dir = self.player_input

        left_sprite = self.get_attack_sprite(self.left_pet, self.left_pet.atk_main)
        left_sprite = pygame.transform.flip(left_sprite, True, False)
        right_sprite = self.get_attack_sprite(self.right_pet, self.right_pet.atk_main)

        y_base = constants.SCREEN_WIDTH // 2 - constants.PET_WIDTH // 2
        y_up = constants.SCREEN_HEIGHT // 2 - constants.PET_WIDTH // 2
        y_down = y_up + int(48 * constants.UI_SCALE)

        left_x = constants.PET_WIDTH + (5 * constants.UI_SCALE)
        right_x = constants.SCREEN_WIDTH - constants.PET_WIDTH - (5 * constants.UI_SCALE)

        self.attack_positions.append([left_sprite, [left_x, y_up if left_dir == "A" else y_down]])
        self.attack_positions.append([right_sprite, [right_x, y_up if right_dir == "A" else y_down]])

        self.is_collision = (left_dir == right_dir)

    def process_attack_result(self):
        correct = self.pattern[self.current_index] != self.player_input
        if correct:
            runtime_globals.game_sound.play("attack_hit")
            self.victories += 1
        else:
            runtime_globals.game_sound.play("attack_fail")
            self.failures += 1
        self.current_index += 1
        if self.current_index >= len(self.pattern):
            self.phase = "result"
            self.frame_counter = 0
            runtime_globals.game_console.log(f"Head-to-Head training done: {self.victories} wins, {self.failures} fails")
        else:
            self.phase = "charge"
            self.attack_positions.clear()

    def check_victory(self):
        return self.victories > self.failures

    def check_and_award_trophies(self):
        """Award trophy on winning head-to-head training"""
        if self.victories > self.failures:
            for pet in self.pets:
                pet.trophies += 1
            runtime_globals.game_console.log(f"[TROPHY] Head-to-head training won! Trophy awarded.")

    def get_attack_count(self):
        """
        Map victories (out of 5 hits) to attack count:
          5 wins -> 3
          4 wins -> 2
          3 wins -> 1
          <3 wins -> 0 (defeat)
        """
        wins = max(0, min(self.victories, 5))
        if wins >= 5:
            return 3
        if wins == 4:
            return 2
        if wins == 3:
            return 1
        return 0
