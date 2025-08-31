import pygame
import random

from core import runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from game.core.combat import combat_constants
import game.core.constants as constants
from core.utils.pygame_utils import blit_with_cache, blit_with_shadow, sprite_load_percent
from core.utils.scene_utils import change_scene

class CountMatchTraining(Training):
    def __init__(self):
        super().__init__()
        self.press_counter = 0
        self.rotation_index = 0
        self.start_time = 0
        self.final_color = 3
        self.correct_color = 0
        self.super_hits = {}
        self.result_text = None
        self.flash_frame = 0
        self.anim_counter = -1
        self.cached_ready_sprites = None
        self.cached_count_sprites = None
        self.cached_mega_hit = None
        self.load_sprites()

    def load_sprites(self):
        """Loads and caches sprites only once."""
        if self.cached_ready_sprites is None:
            self.cached_ready_sprites = {key: sprite_load_percent(path, 100, keep_proportion=True, base_on="width", alpha=False) for key, path in constants.READY_SPRITES_PATHS.items()}
        if self.cached_count_sprites is None:
            self.cached_count_sprites = {key: sprite_load_percent(path, 100, keep_proportion=True, base_on="width", alpha=False) for key, path in constants.COUNT_SPRITES_PATHS.items()}
        if self.cached_mega_hit is None:
            self.cached_mega_hit = sprite_load_percent(constants.MEGA_HIT_PATH, 100, keep_proportion=True, base_on="width", alpha=False)

    @property
    def ready_sprites(self):
        return self.cached_ready_sprites

    @property
    def count_sprites(self):
        return self.cached_count_sprites

    @property
    def mega_hit(self):
        return self.cached_mega_hit

    def update_charge_phase(self):
        if self.frame_counter == 1:
            self.start_count_phase()
        # Use frame-rate independent timing (3 seconds)
        if self.frame_counter > int(3 * constants.FRAME_RATE):
            self.phase = "wait_attack"
            self.calculate_results()
            self.prepare_attack()

    def start_count_phase(self):
        self.phase = "charge"
        self.press_counter = 0
        self.rotation_index = 3

    def handle_event(self, input_action):
        if self.phase == "charge" and input_action in ("Y", "SHAKE"):
            if self.phase == "alert":
                self.phase = "charge"
            elif self.phase == "charge":
                self.press_counter += 1
                if self.press_counter % 2 == 0:
                    self.rotation_index -= 1
                    if self.rotation_index < 1:
                        self.rotation_index = 3
        elif self.phase in ["wait_attack", "attack_move", "impact", "result"] and input_action in ["B", "START"]:
            self.finish_training()
        elif self.phase in ("alert", "charge") and input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")

    def get_first_pet_attribute(self):
        pet = self.pets[0]
        attr = getattr(pet, "attribute", "")
        if attr in ["", "Va"]:
            return 1
        elif attr == "Da":
            return 2
        elif attr == "Vi":
            return 3
        return 1

    def calculate_results(self):
        self.correct_color = self.get_first_pet_attribute()
        self.final_color = self.rotation_index
        pets = self.pets
        if not pets:
            return

        pet = pets[0]
        shakes = self.press_counter
        attr_type = getattr(pet, "attribute", "")

        if shakes < 2:
            hits = 0
        else:
            color = self.final_color
            if attr_type in ("", "Va"):
                hits = 5 if color == 1 else random.choice([3, 4]) if color == 2 else 2 if color == 3 else 1
            elif attr_type == "Da":
                hits = 5 if color == 2 else random.choice([3, 4]) if color == 1 else 2 if color == 3 else 1
            elif attr_type == "Vi":
                hits = 5 if color == 3 else random.choice([3, 4]) if color == 2 else 2 if color == 1 else 1
            else:
                hits = 1

        for p in pets:
            self.super_hits[p] = hits

    def prepare_attack(self):
        self.attack_phase = 0
        self.attack_waves = [[] for _ in range(5)]
        pets = self.pets
        total_pets = len(pets)
        available_height = constants.SCREEN_HEIGHT
        spacing = min(available_height // total_pets, constants.OPTION_ICON_SIZE + (20 * constants.UI_SCALE))
        start_y = (constants.SCREEN_HEIGHT - (spacing * total_pets)) // 2

        for i, pet in enumerate(pets):
            sprite = self.get_attack_sprite(pet, pet.atk_main)
            if not sprite:
                continue
            count = self.super_hits.get(pet, 0)
            pattern = [3] * 5 if count == 5 else [2] * count + [1] * (5 - count)
            pet_y = start_y + i * spacing + constants.OPTION_ICON_SIZE // 2 - sprite.get_height() // 2
            for j, kind in enumerate(pattern):
                x = constants.SCREEN_WIDTH - constants.OPTION_ICON_SIZE - (20 * constants.UI_SCALE)
                y = pet_y
                self.attack_waves[j].append((sprite, kind, x, y))
        self.frame_counter = 0

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
            x -= speed
            if x + (24 * constants.UI_SCALE) > 0:
                all_off_screen = False
                new_wave.append((sprite, kind, x, y))

        self.attack_waves[self.current_wave_index] = new_wave

        # Wait at least 10 frames (at 30fps) before next wave
        if all_off_screen and self.frame_counter >= int(10 * (constants.FRAME_RATE / 30)):
            self.current_wave_index += 1
            self.frame_counter = 0

    def draw_pets(self, surface, frame_enum=PetFrame.IDLE1):
        """Draws pets using appropriate frame based on attack animation phase."""
        if self.phase == "attack_move":
            frame_enum = self.animate_attack(46)
        super().draw_pets(surface, frame_enum)

    def draw_alert(self, surface):
        attr = self.get_first_pet_attribute()
        sprite = self.ready_sprites[attr]
        y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
        blit_with_cache(surface, sprite, (0, y))

    def draw_charge(self, surface):
        sprite = self.count_sprites[4 if self.press_counter == 0 else self.rotation_index]
        y = (constants.SCREEN_HEIGHT - sprite.get_height()) // 2
        blit_with_cache(surface, sprite, (0, y))

    def draw_attack_move(self, surface):
        self.draw_pets(surface)
        for wave in self.attack_waves:
            for sprite, kind, x, y in wave:
                if x < constants.SCREEN_WIDTH - (90 * constants.UI_SCALE):
                    blit_with_shadow(surface, sprite, (x, y))
                    if kind > 1:
                        blit_with_shadow(surface, sprite, (x - (20 * constants.UI_SCALE), y - (10 * constants.UI_SCALE)))
                    if kind == 3:
                        blit_with_shadow(surface, sprite, (x - (40 * constants.UI_SCALE), y + (10 * constants.UI_SCALE)))

    def draw_result(self, screen):
        pets = self.pets
        pet = pets[0]
        hits = self.super_hits.get(pet, 0)
        if hits == 5:
            sprite = self.mega_hit
            x = constants.SCREEN_WIDTH // 2 - sprite.get_width() // 2
            y = constants.SCREEN_HEIGHT // 2 - sprite.get_height() // 2
            blit_with_shadow(screen, sprite, (x, y))
            # Draw trophy notification if maximum score achieved
            self.draw_trophy_notification(screen, quantity=1)
        else:
            font = pygame.font.Font(None, constants.FONT_SIZE_LARGE)
            text = font.render(f"{hits} Super-Hits", True, (255, 255, 255))
            x = constants.SCREEN_WIDTH // 2 - text.get_width() // 2
            y = int(100 * constants.UI_SCALE)
            screen.blit(text, (x, y))

    def check_victory(self):
        """Apply training results and return to game."""
        return self.super_hits.get(self.pets[0], 0) > 1

    def check_and_award_trophies(self):
        """Award trophy if super_hits reaches maximum (5)"""
        if self.super_hits.get(self.pets[0], 0) == 5:
            for pet in self.pets:
                pet.trophies += 1
            runtime_globals.game_console.log(f"[TROPHY] Count training perfect score achieved! Trophy awarded.")

    # ...existing code...
    def get_attack_count(self):
        """
        Determine attack count based on super-hit count:
          5 hits -> 3
          4 hits -> 2
          3 hits -> 1
          <3  -> 0 (defeat)
        Supports reading hits from self.super_hits (dict) or falls back to self.victories.
        """
        hits = self.super_hits.get(self.pets[0], 0)
        if hits >= 5:
            return 3
        if hits == 4:
            return 2
        if hits == 3:
            return 1
        return 0
