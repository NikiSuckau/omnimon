#=====================================================================
# ShakeTraining (Simple Strength Bar Training)
#=====================================================================

import random
import pygame

from core import runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from game.components.ui.ui_manager import UIManager
from game.core.combat import combat_constants
import game.core.constants as constants
from core.game_module import sprite_load
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow
from game.core.utils.scene_utils import change_scene

class ShakeTraining(Training):
    """
    Shake training mode where players build up strength by holding a bar.
    """

    def __init__(self, ui_manager: UIManager) -> None:
        super().__init__(ui_manager)
        self.strength = 0
        self.bar_level = 20
        self.bar_timer = 0

        self.attack_phase = 1
        self.flash_frame = 0

        SPRITE_SETS = [
            (constants.BAG1_PATH, constants.BAG2_PATH),
            (constants.ROCK1_PATH, constants.ROCK2_PATH),
            (constants.TREE1_PATH, constants.TREE2_PATH),
            (constants.BRICK1_PATH, constants.BRICK2_PATH),
        ]

        selected_sprites = random.choice(SPRITE_SETS)

        self.bag1 = sprite_load(selected_sprites[0], size=(60 * constants.UI_SCALE, 120 * constants.UI_SCALE))
        self.bag2 = sprite_load(selected_sprites[1], size=(60 * constants.UI_SCALE, 120 * constants.UI_SCALE))

    def update_charge_phase(self):
        if self.strength == 20 or pygame.time.get_ticks() - self.bar_timer > combat_constants.PUNCH_HOLD_TIME_MS:
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
        return self.strength >= 10

    def check_and_award_trophies(self):
        """Award trophy if strength reaches maximum (20)"""
        if self.strength == 20:
            for pet in self.pets:
                pet.trophies += 2
            runtime_globals.game_console.log(f"[TROPHY] Shake training excellent score achieved! Trophy awarded.")
        elif self.strength >= 15:
            for pet in self.pets:
                pet.trophies += 1
            runtime_globals.game_console.log(f"[TROPHY] Shake training great score achieved! Trophy awarded.")

    def draw_charge(self, surface):
        # --- Cache rectangles for performance ---
        if not hasattr(self, "_charge_rect_cache"):
            self._charge_rect_cache = {}

        # Determine color based on strength
        if self.strength < 10:
            color = (220, 40, 40)      # Red
        elif self.strength < 15:
            color = (255, 140, 0)      # Orange
        elif self.strength < 20:
            color = (255, 220, 0)      # Yellow
        else:
            color = (40, 220, 40)      # Green

        # Use pet width for rectangle width
        if self.pets:
            pet_sprite = self.pets[0].get_sprite(PetFrame.IDLE1.value)
            rect_width = pet_sprite.get_width()
        else:
            rect_width = int(50 * constants.UI_SCALE)
        rect_height = constants.SCREEN_HEIGHT
        screen_w = constants.SCREEN_WIDTH
        screen_h = constants.SCREEN_HEIGHT

        cache_key = (color, rect_width, rect_height, screen_w, screen_h)
        if cache_key not in self._charge_rect_cache:
            left_rect_surf = pygame.Surface((rect_width, rect_height))
            left_rect_surf.fill(color)
            right_rect_surf = pygame.Surface((rect_width, rect_height))
            right_rect_surf.fill(color)
            bg_rect_surf = pygame.Surface((screen_w - 2 * rect_width, rect_height))
            bg_rect_surf.fill((0, 0, 0))
            self._charge_rect_cache[cache_key] = (left_rect_surf, right_rect_surf, bg_rect_surf)
        else:
            left_rect_surf, right_rect_surf, bg_rect_surf = self._charge_rect_cache[cache_key]

        # Draw black background in the center
        surface.blit(bg_rect_surf, (rect_width, 0))
        # Draw colored rectangles on left and right
        surface.blit(left_rect_surf, (0, 0))
        surface.blit(right_rect_surf, (screen_w - rect_width, 0))

        # --- Draw timer above "PUNCH" ---
        max_ms = combat_constants.PUNCH_HOLD_TIME_MS
        elapsed_ms = pygame.time.get_ticks() - self.bar_timer
        remaining_ms = max(0, max_ms - elapsed_ms)
        remaining_sec = int(remaining_ms / 1000) + (1 if remaining_ms % 1000 > 0 else 0)

        timer_font = pygame.font.Font(None, int(32 * constants.UI_SCALE))
        timer_text = timer_font.render(str(remaining_sec), True, (255, 255, 255))
        timer_x = (screen_w - timer_text.get_width()) // 2
        # Place timer above "PUNCH" with a little spacing
        timer_y = screen_h // 2 - int(60 * constants.UI_SCALE) - timer_text.get_height() - int(10 * constants.UI_SCALE)
        blit_with_shadow(surface, timer_text, (timer_x, timer_y))

        # Draw "PUNCH" text centered
        font = pygame.font.Font(None, int(48 * constants.UI_SCALE))
        punch_text = font.render("PUNCH", True, (255, 255, 255))
        punch_x = (screen_w - punch_text.get_width()) // 2
        punch_y = screen_h // 2 - int(60 * constants.UI_SCALE)
        blit_with_shadow(surface, punch_text, (punch_x, punch_y))

        # Draw strength number centered below "PUNCH"
        num_font = pygame.font.Font(None, int(64 * constants.UI_SCALE))
        strength_text = num_font.render(str(self.strength), True, (255, 255, 255))
        strength_x = (screen_w - strength_text.get_width()) // 2
        strength_y = punch_y + punch_text.get_height() + int(10 * constants.UI_SCALE)
        blit_with_shadow(surface, strength_text, (strength_x, strength_y))

        # Draw pets spread on the colored rectangles, no scaling
        total = len(self.pets)
        if total > 0:
            left_count = total // 2
            right_count = total - left_count
            # Vertical spacing for pets
            left_spacing = rect_height // max(left_count, 1)
            right_spacing = rect_height // max(right_count, 1)
            # Draw left side pets
            for i in range(left_count):
                pet = self.pets[i]
                anim_toggle = (self.frame_counter + i * 5) // (15 * constants.FRAME_RATE / 30) % 2
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.ANGRY.value
                sprite = pet.get_sprite(frame_id)
                x = (rect_width - sprite.get_width()) // 2
                y = i * left_spacing + (left_spacing - sprite.get_height()) // 2
                blit_with_cache(surface, sprite, (x, y))
            # Draw right side pets
            for i in range(right_count):
                pet = self.pets[left_count + i]
                anim_toggle = (self.frame_counter + (left_count + i) * 5) // (15 * constants.FRAME_RATE / 30) % 2
                frame_id = PetFrame.IDLE1.value if anim_toggle == 0 else PetFrame.ANGRY.value
                sprite = pet.get_sprite(frame_id)
                x = screen_w - rect_width + (rect_width - sprite.get_width()) // 2
                y = i * right_spacing + (right_spacing - sprite.get_height()) // 2
                blit_with_cache(surface, sprite, (x, y))

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
        # Use cached result sprites
        bad_sprite = self._sprite_cache['bad']
        good_sprite = self._sprite_cache['good']
        great_sprite = self._sprite_cache['great']
        excellent_sprite = self._sprite_cache['excellent']

        result_img = None
        if 15 <= self.strength < 20:
            result_img = self.bag2
        elif self.strength < 10:
            result_img = self.bag1

        if self.frame_counter < 30:
            if result_img:
                x = int(50 * constants.UI_SCALE)
                y = constants.SCREEN_HEIGHT // 2 - result_img.get_height() // 2
                blit_with_shadow(surface, result_img, (x, y))
        else:
            y = constants.SCREEN_HEIGHT // 2 - bad_sprite.get_height() // 2
            if self.strength < 10:
                blit_with_shadow(surface, bad_sprite, (0, y))
            elif self.strength < 15:
                blit_with_shadow(surface, good_sprite, (0, y))
            elif self.strength < 20:
                blit_with_shadow(surface, great_sprite, (0, y))
                self.draw_trophy_notification(surface, quantity=1)
            elif self.strength >= 20:
                blit_with_shadow(surface, excellent_sprite, (0, y))
                # Draw trophy notification if maximum score achieved
                self.draw_trophy_notification(surface, quantity=2)

    def prepare_attacks(self):
        """Prepare multiple attacks from each pet based on strength level."""
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
        if self.strength < 15:
            return 1
        elif self.strength < 20:
            return 2
        else:
            return 3
        
    def handle_event(self, input_action):
        if self.phase == "charge" and input_action in ("Y", "SHAKE"):
            runtime_globals.game_sound.play("menu")
            self.strength = min(getattr(self, "strength", 0) + 1, getattr(self, "bar_level", 20))
        elif self.phase in ["wait_attack", "attack_move", "impact", "result"] and input_action in ["B", "START"]:
            self.finish_training()
        elif self.phase in ["alert", "charge"] and input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")