#=====================================================================
# ShakeTraining (Simple Strength Bar Training)
#=====================================================================

import random
import pygame

from core import runtime_globals
from core.animation import PetFrame
from core.combat.training import Training
from game.components.ui.ui_manager import UIManager
from game.components.minigames.shake_punch import ShakePunch
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
        self.attack_phase = 1
        self.flash_frame = 0

        # Initialize the shake punch minigame early so it's available during alert phase
        self.shake_punch = None
        if self.pets:
            self.shake_punch = ShakePunch(self.ui_manager, self.pets)
        
        # Keep references to bag sprites for attack/result phases
        self.bag1 = None
        self.bag2 = None
        if self.shake_punch:
            self.bag1 = self.shake_punch.bag1
            self.bag2 = self.shake_punch.bag2

    def update_charge_phase(self):
        if self.frame_counter == 1:
            self.start_punch_phase()
        
        # Check if punch phase is complete
        if self.shake_punch:
            strength = self.shake_punch.get_strength()
            if strength == 20 or self.shake_punch.is_time_up():
                self.strength = strength  # Store final strength
                self.phase = "wait_attack"
                self.frame_counter = 0
                self.prepare_attacks()
    
    def start_punch_phase(self):
        """Start the punch minigame phase."""
        self.phase = "charge"
        if self.shake_punch:
            self.shake_punch.reset_strength()
            self.shake_punch.set_phase("punch")

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

    def update(self):
        """Override base update to include minigame updates."""
        # Call parent update
        super().update()
        
        # Update minigame
        if self.shake_punch:
            self.shake_punch.update()

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
        # Fill the screen with black background
        surface.fill(self.background_color)

        # Use the shake punch minigame to handle punch interface drawing
        if self.shake_punch:
            self.shake_punch.draw(surface)

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
            # Composition for result screen:
            # 1) black background
            surface.fill(self.background_color)

            # Choose which result sprite to display
            if self.strength < 10:
                selected_sprite = bad_sprite
                cache_key = 'shake_result_bad'
                trophy_qty = 0
            elif self.strength < 15:
                selected_sprite = good_sprite
                cache_key = 'shake_result_good'
                trophy_qty = 0
            elif self.strength < 20:
                selected_sprite = great_sprite
                cache_key = 'shake_result_great'
                trophy_qty = 1
            else:
                selected_sprite = excellent_sprite
                cache_key = 'shake_result_excellent'
                trophy_qty = 2

            # 2) semi-transparent full-screen proportional overlay when ui scale >= 2
            self._draw_overlay_background(surface, selected_sprite, cache_key)

            # 3) integer-scaled sprite centered
            sx, sy = selected_sprite.get_width(), selected_sprite.get_height()
            center_x = constants.SCREEN_WIDTH // 2 - sx // 2
            center_y = constants.SCREEN_HEIGHT // 2 - sy // 2
            blit_with_shadow(surface, selected_sprite, (center_x, center_y))

            # Trophy notification
            if trophy_qty > 0:
                self.draw_trophy_notification(surface, quantity=trophy_qty)

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
            # Let the minigame handle the input
            if self.shake_punch and self.shake_punch.handle_event(input_action):
                pass  # Minigame handled the input
        elif self.phase in ["wait_attack", "attack_move", "impact", "result"] and input_action in ["B", "START"]:
            self.finish_training()
        elif self.phase in ["alert", "charge"] and input_action == "B":
            runtime_globals.game_sound.play("cancel")
            change_scene("game")
            
    def handle_pygame_event(self, event):
        """Handle pygame events for shake detection during punch phase."""
        if self.shake_punch:
            # The minigame now handles shake detection and directly calls handle_event
            return self.shake_punch.handle_pygame_event(event)
        return False