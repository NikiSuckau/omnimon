#=====================================================================
# Training (Base Class for All Training Modes)
#=====================================================================
import pygame

from core import runtime_globals
from core.animation import PetFrame
from game.core.combat import combat_constants
import game.core.constants as constants
from core.utils.pet_utils import distribute_pets_evenly, get_training_targets
from core.utils.pygame_utils import blit_with_shadow, load_attack_sprites, module_attack_sprites, sprite_load_percent
from core.utils.scene_utils import change_scene
from game.core.game_quest import QuestType
from game.core.utils.quest_event_utils import update_quest_progress

class Training:
    """
    Training mode where players build up strength by holding a bar.
    """

    def __init__(self) -> None:
        self.phase = "alert"
        self.frame_counter = 0

        self.attack_positions = []
        self.attack_phase = 1
        self.attack_waves = []
        self.current_wave_index = 0
        self.flash_frame = 0
        self.impact_counter = 0
        self.attacks_prepared = False

        # Sprite caching
        self._sprite_cache = {}
        self._pet_sprite_cache = {}
        self.pet_state = None

        # Load and cache all sprites once
        self._sprite_cache['ready'] = sprite_load_percent(constants.READY_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['go'] = sprite_load_percent(constants.GO_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['bar_piece'] = sprite_load_percent(constants.BAR_PIECE_PATH, percent=(int(12 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self._sprite_cache['training_max'] = sprite_load_percent(constants.TRAINING_MAX_PATH, percent=(int(60 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self._sprite_cache['bar_back'] = sprite_load_percent(constants.BAR_BACK_PATH, percent=(int(170 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")
        self._sprite_cache['battle1'] = sprite_load_percent(constants.BATTLE1_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['battle2'] = sprite_load_percent(constants.BATTLE2_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['bad'] = sprite_load_percent(constants.BAD_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['good'] = sprite_load_percent(constants.GOOD_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['great'] = sprite_load_percent(constants.GREAT_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['excellent'] = sprite_load_percent(constants.EXCELLENT_SPRITE_PATH, 100, keep_proportion=True, base_on="width", alpha=False)
        self._sprite_cache['trophy'] = sprite_load_percent(constants.TROPHIES_ICON_PATH, percent=(int(24 * constants.UI_SCALE) / constants.SCREEN_HEIGHT) * 100, keep_proportion=True, base_on="height")

        self.attack_jump = 0
        self.attack_forward = 0
        self.attack_frame = None
        self.attack_sprites = load_attack_sprites()
        
        self.pets = get_training_targets()
        self.module_attack_sprites = {}
        for pet in self.pets:
             self.module_attack_sprites[pet.module] = module_attack_sprites(pet.module)

    def get_sprite(self, key):
        return self._sprite_cache[key]

    def get_attack_sprite(self, pet, attack_id):
        """
        Get attack sprite for a pet, preferring module-specific sprites over defaults.
        """
        # First try module-specific attack sprites
        if pet.module in self.module_attack_sprites:
            module_sprite = self.module_attack_sprites[pet.module].get(str(attack_id))
            if module_sprite:
                return module_sprite
        
        # Fall back to default attack sprites
        return self.attack_sprites.get(str(attack_id))

    def update(self):
        if self.phase == "alert":
            self.update_alert_phase()
        elif self.phase == "charge":
            self.update_charge_phase()
        elif self.phase == "wait_attack":
            self.update_wait_attack_phase()
        elif self.phase == "attack_move":
            self.move_attacks()
        elif self.phase == "impact":
            self.update_impact_phase()
        elif self.phase == "result":
            self.update_result_phase()
        self.frame_counter += 1

    def update_alert_phase(self):
        if self.frame_counter == int(30 * (constants.FRAME_RATE / 30)):
            runtime_globals.game_sound.play("happy")
        if self.frame_counter >= combat_constants.ALERT_DURATION_FRAMES:
            self.phase = "charge"
            self.frame_counter = 0
            self.bar_timer = pygame.time.get_ticks()

    def update_charge_phase(self):
        pass

    def update_wait_attack_phase(self):
        self.attack_frame = self.animate_attack(20)
        if self.frame_counter >= combat_constants.WAIT_ATTACK_READY_FRAMES:
            self.attack_frame = None
            self.phase = "attack_move"
            self.frame_counter = 0
            runtime_globals.game_sound.play("attack")

    def animate_attack(self, delay=0):
        appear_frame = int(delay * (constants.FRAME_RATE / 30))
        anim_window = int(20 * (constants.FRAME_RATE / 30))
        anim_start = appear_frame - anim_window
        anim_end = appear_frame

        progress = 0
        if anim_start <= self.frame_counter < anim_end:
            progress = (self.frame_counter - anim_start) / max(1, (anim_end - anim_start))
            if progress < 0.5:
                self.attack_forward += 1 * (30 / constants.FRAME_RATE)
                if progress < 0.25:
                    self.attack_jump += 1 * (30 / constants.FRAME_RATE)
                else:
                    self.attack_jump -= 1 * (30 / constants.FRAME_RATE)
            else:
                self.attack_forward -= 1 * (30 / constants.FRAME_RATE)
        else:
            self.attack_forward = 0
            self.attack_jump = 0

        train2_frames = int(6 * (constants.FRAME_RATE / 30))
        if delay == 20:
            if self.frame_counter > anim_end - train2_frames:
                frame_enum = PetFrame.TRAIN2
            else:
                frame_enum = PetFrame.TRAIN1
        else:
            if (self.frame_counter > anim_end - train2_frames) or (self.frame_counter < train2_frames):
                frame_enum = PetFrame.TRAIN2
            else:
                frame_enum = PetFrame.TRAIN1
        return frame_enum

    def update_impact_phase(self):
        self.flash_frame += 1
        if self.flash_frame >= combat_constants.IMPACT_DURATION_FRAMES:
            self.phase = "result"
            self.frame_counter = 0

    def update_result_phase(self):
        if self.frame_counter >= combat_constants.RESULT_SCREEN_FRAMES:
            self.finish_training()

    def move_attacks(self):
        pass

    def finish_training(self):
        won = self.check_victory()
        if won:
            runtime_globals.game_sound.play("attack_fail")
            
            # Update TRAINING quest progress when training is won
            update_quest_progress(QuestType.TRAINING, 1)
        else:
            runtime_globals.game_sound.play("fail")

        # Check for trophy conditions and award trophies
        self.check_and_award_trophies()

        for pet in self.pets:
            pet.finish_training(won, grade=self.get_attack_count())

        distribute_pets_evenly()
        change_scene("game")

    def draw_trophy_notification(self, surface, quantity=1):
        if quantity > 0:
            """Draw a small trophy icon with +1 in the bottom right corner"""
            trophy_size = int(24 * constants.UI_SCALE)
            font = pygame.font.Font(None, int(24 * constants.UI_SCALE))
            plus_text = font.render(f"+{quantity}", True, constants.FONT_COLOR_YELLOW)

            # Draw trophy icon in bottom right
            trophy_x = constants.SCREEN_WIDTH - trophy_size - plus_text.get_width() - int(4 * constants.UI_SCALE)
            trophy_y = constants.SCREEN_HEIGHT - trophy_size
            blit_with_shadow(surface, self._sprite_cache['trophy'], (trophy_x, trophy_y))
            # Draw +1 text next to trophy
            
            text_x = trophy_x + trophy_size + int(2 * constants.UI_SCALE)
            text_y = trophy_y + int(4 * constants.UI_SCALE)
            blit_with_shadow(surface, plus_text, (text_x, text_y))

    def draw(self, screen: pygame.Surface):
        if self.phase == "alert":
            self.draw_alert(screen)
        elif self.phase == "charge":
            self.draw_charge(screen)
        elif self.phase == "wait_attack":
            self.draw_attack_ready(screen)
        elif self.phase == "attack_move":
            self.draw_attack_move(screen)
        elif self.phase == "impact":
            self.draw_impact(screen)
        elif self.phase == "result":
            self.draw_result(screen)

    def _init_pet_sprite_cache(self):
        """
        Pre-scales all pet sprites for each frame_enum and caches them.
        """
        self._pet_sprite_cache = {}
        for pet in self.pets:
            self._pet_sprite_cache[pet] = {}
            for frame_enum in PetFrame:
                sprite = runtime_globals.pet_sprites[pet][frame_enum.value]
                scaled_sprite = pygame.transform.scale(sprite, (constants.OPTION_ICON_SIZE, constants.OPTION_ICON_SIZE))
                self._pet_sprite_cache[pet][frame_enum] = scaled_sprite

    def draw_pets(self, surface, frame_enum=PetFrame.IDLE1):
        # Initialize cache if not present or pets changed
        if not hasattr(self, '_pet_sprite_cache') or set(self._pet_sprite_cache.keys()) != set(self.pets):
            self._init_pet_sprite_cache()

        # Use the correct frame_enum for animation
        if self.attack_frame:
            frame_enum = self.attack_frame
        self.pet_state = frame_enum

        total_pets = len(self.pets)
        available_height = constants.SCREEN_HEIGHT
        spacing = min(available_height // total_pets, constants.OPTION_ICON_SIZE + int(20 * constants.UI_SCALE))
        start_y = (constants.SCREEN_HEIGHT - (spacing * total_pets)) // 2

        for i, pet in enumerate(self.pets):
            pet_sprite = self._pet_sprite_cache[pet][frame_enum]
            x = constants.SCREEN_WIDTH - constants.OPTION_ICON_SIZE - int(16 * constants.UI_SCALE) + int(self.attack_forward * constants.UI_SCALE)
            y = start_y + i * spacing - int(self.attack_jump * constants.UI_SCALE)
            blit_with_shadow(surface, pet_sprite, (x, y))

    def draw_alert(self, screen):
        center_y = constants.SCREEN_HEIGHT // 2 - self.get_sprite('ready').get_height() // 2
        blit_with_shadow(screen, self.get_sprite('ready'), (0, center_y))

    def draw_attack_ready(self, surface):
        self.draw_pets(surface, PetFrame.ATK1)

    def draw_charge(self, surface):
        pass

    def draw_attack_move(self, surface):
        pass

    def draw_impact(self, screen):
        flash = self.get_sprite('battle1') if (self.flash_frame // int(2 * (constants.FRAME_RATE / 30))) % 2 == 0 else self.get_sprite('battle2')
        flash = pygame.transform.scale(flash, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        screen.blit(flash, (0, 0))

    def draw_result(self, surface):
        pass

    def handle_event(self, input_action):
        if self.phase == "charge" and input_action == "A":
            runtime_globals.game_sound.play("menu")
            self.strength = min(getattr(self, "strength", 0) + 1, getattr(self, "bar_level", 14))
        elif self.phase in ["wait_attack", "attack_move", "impact", "result"] and input_action in ["B", "START"]:
            self.finish_training()
        elif self.phase in ["alert", "charge"] and input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")