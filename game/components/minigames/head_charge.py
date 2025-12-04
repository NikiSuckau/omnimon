import random
import pygame
from components.ui.ui_manager import UIManager
from components.ui.button import Button
from core import runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_shadow
from core.animation import PetFrame
from core.combat import combat_constants


class HeadCharge:
    """
    Head-to-Head charge minigame - extracted from head training for cleaner separation.
    Handles pattern matching, pet attacks, and strikes counter.
    """
    
    PATTERNS = [
        "ABABB", "BBAAB", "BAABB",
        "ABBAA", "BABAB", "ABABA"
    ]

    def __init__(self, ui_manager: UIManager, left_pet=None, right_pet=None, left_attack_sprite=None, right_attack_sprite=None):
        """Initialize the head charge minigame."""
        self.ui_manager = ui_manager
        if self.ui_manager is None:
            raise ValueError("UIManager cannot be None")
            
        self.left_pet = left_pet
        self.right_pet = right_pet
        self.left_attack_sprite = left_attack_sprite
        self.right_attack_sprite = right_attack_sprite

        self.pattern = ""
        self.current_index = 0
        self.victories = 0
        self.failures = 0
        self.player_input = None
        self.is_collision = False
        self.attack_positions = []
        
        # Calculate proper sprite scale - UI scale is based on 240x240, but sprites are 2x size
        sprite_scale_factor = constants.UI_SCALE / 2
        
        # Cached sprites using UI manager - use new HeadTraining specific sprites
        self._sprite_cache = {}
        self._sprite_cache['head_training_img'] = self.ui_manager.load_sprite_non_integer_scaling(constants.HEADTRAINING_PATH, constants.UI_SCALE * 1.5)
        self._sprite_cache['vs_img'] = self.ui_manager.load_sprite_non_integer_scaling(constants.VS_PATH, constants.UI_SCALE * 1.5)
        self._sprite_cache['strikes'] = self.ui_manager.load_sprite_non_integer_scaling(constants.HEADTRAINING_STRIKE_PATH, sprite_scale_factor)
        self._sprite_cache['strikes_back'] = self.ui_manager.load_sprite_non_integer_scaling(constants.HEADTRAINING_BACK_PATH, sprite_scale_factor)
        
        # Cache pet sprites scaled at +50%
        if self.left_pet and self.right_pet:
            pet_scale_factor = 1.50  # Direct scaling factor, not based on sprite_scale_factor
            left_atk1 = runtime_globals.pet_sprites[self.left_pet][PetFrame.ATK1.value]
            left_atk2 = runtime_globals.pet_sprites[self.left_pet][PetFrame.ATK2.value]
            right_atk1 = runtime_globals.pet_sprites[self.right_pet][PetFrame.ATK1.value]
            right_atk2 = runtime_globals.pet_sprites[self.right_pet][PetFrame.ATK2.value]
            
            scaled_width = int(left_atk1.get_width() * pet_scale_factor)
            scaled_height = int(left_atk1.get_height() * pet_scale_factor)
            
            self._sprite_cache['left_pet_atk1'] = pygame.transform.scale(left_atk1, (scaled_width, scaled_height))
            self._sprite_cache['left_pet_atk2'] = pygame.transform.scale(left_atk2, (scaled_width, scaled_height))
            self._sprite_cache['right_pet_atk1'] = pygame.transform.scale(right_atk1, (scaled_width, scaled_height))
            self._sprite_cache['right_pet_atk2'] = pygame.transform.scale(right_atk2, (scaled_width, scaled_height))
        
        # Create UP/DOWN UI buttons using UI manager's base coordinate system (240x240)
        ui_base = 240  # UI manager's base resolution
        button_size = 30  # Base size in UI coordinates
        
        # Centered X position in UI coordinates
        center_x = (ui_base - button_size) // 2

        # UP button at middle top with ArrowUp decorator
        up_y = 40  # UI coordinates
        runtime_globals.game_console.log(f"[HeadCharge] Creating UP button: UI pos=({center_x}, {up_y}), size={button_size}x{button_size}")
        self.up_button = Button(center_x, up_y, button_size, button_size, "", 
                               callback=lambda: self.handle_button_press("UP"),
                               decorators=["ArrowUp"], shadow_mode="full")
        runtime_globals.game_console.log(f"[HeadCharge] UP button created: rect={self.up_button.rect}")
        self.ui_manager.add_component(self.up_button)

        # DOWN button at middle bottom with ArrowDown decorator
        down_y = ui_base - button_size - 40  # UI coordinates
        runtime_globals.game_console.log(f"[HeadCharge] Creating DOWN button: UI pos=({center_x}, {down_y}), size={button_size}x{button_size}")
        self.down_button = Button(center_x, down_y, button_size, button_size, "", 
                                 callback=lambda: self.handle_button_press("DOWN"),
                                 decorators=["ArrowDown"], shadow_mode="full")
        runtime_globals.game_console.log(f"[HeadCharge] DOWN button created: rect={self.down_button.rect}")
        self.ui_manager.add_component(self.down_button)
            
        # Internal state
        self.phase = "charge"  # charge, attack_move, alert, result
        self.frame_counter = 0

        self.select_pattern()

    def select_pattern(self):
        """Select a new pattern for the training sequence"""
        last = runtime_globals.last_headtohead_pattern
        runtime_globals.last_headtohead_pattern = (last + 1) % 6
        self.pattern = self.PATTERNS[runtime_globals.last_headtohead_pattern]
        self.current_index = 0

    def update(self):
        """Update minigame state"""
        if self.phase == "attack_move":
            self.move_attacks()
        elif self.phase == "alert":
            self.frame_counter += 1
            if self.frame_counter > 30:  # Alert duration
                self.phase = "charge"
                self.frame_counter = 0

        mouse_enabled = runtime_globals.game_input.is_mouse_enabled()
        if self.phase != "result" and mouse_enabled:
            self.up_button.update()
            self.down_button.update()

    def handle_button_press(self, direction):
        """Handle button press from UI buttons"""
        if self.phase == "charge":
            if direction == "UP":
                self.player_input = "B"
                self.start_attack()
            elif direction == "DOWN":
                self.player_input = "A"
                self.start_attack()

    def handle_event(self, input_action):
        """Handle input events for the head charge minigame"""
        # Handle pygame events (like mouse clicks) for buttons
        if hasattr(input_action, 'type'):
            if input_action.type == pygame.MOUSEBUTTONDOWN and input_action.button == 1:
                mouse_pos = input_action.pos
                # Check if click is on UP button using rect
                if (mouse_pos[0] >= self.up_button.rect.x and mouse_pos[0] <= self.up_button.rect.x + self.up_button.rect.width and
                    mouse_pos[1] >= self.up_button.rect.y and mouse_pos[1] <= self.up_button.rect.y + self.up_button.rect.height):
                    self.handle_button_press("UP")
                    return True
                # Check if click is on DOWN button using rect
                elif (mouse_pos[0] >= self.down_button.rect.x and mouse_pos[0] <= self.down_button.rect.x + self.down_button.rect.width and
                      mouse_pos[1] >= self.down_button.rect.y and mouse_pos[1] <= self.down_button.rect.y + self.down_button.rect.height):
                    self.handle_button_press("DOWN")
                    return True
            return False
        
        # Handle string action events (keyboard/controller/mouse abstractions)
        if isinstance(input_action, str):
            if input_action == "LCLICK" and runtime_globals.game_input.is_mouse_enabled():
                mouse_pos = pygame.mouse.get_pos()
                if self.up_button.rect.collidepoint(mouse_pos):
                    self.handle_button_press("UP")
                    return True
                elif self.down_button.rect.collidepoint(mouse_pos):
                    self.handle_button_press("DOWN")
                    return True

            if self.phase == "charge":
                if input_action == "UP":
                    self.player_input = "B"
                    self.start_attack()
                    return True
                elif input_action == "DOWN":
                    self.player_input = "A"
                    self.start_attack()
                    return True
        return False

    def start_attack(self):
        """Start the attack animation sequence"""
        self.phase = "attack_move"
        self.attack_positions.clear()

        left_dir = self.pattern[self.current_index]
        right_dir = self.player_input

        # Calculate attack positions
        y_up = self.left_y
        y_down = y_up + int(32 * constants.UI_SCALE)

        left_x = constants.PET_WIDTH + (5 * constants.UI_SCALE)
        right_x = constants.SCREEN_WIDTH - constants.PET_WIDTH - (5 * constants.UI_SCALE)

        left_sprite = self.left_attack_sprite
        right_sprite = self.right_attack_sprite
        left_sprite = pygame.transform.flip(left_sprite, True, False)
        self.attack_positions.append([left_sprite, [left_x, y_up if left_dir == "A" else y_down]])
        self.attack_positions.append([right_sprite, [right_x, y_up if right_dir == "A" else y_down]])

        self.is_collision = (left_dir == right_dir)

    def move_attacks(self):
        """Update attack positions and check for completion"""
        finished = False
        if self.is_collision:
            finished = self.update_collision()
        else:
            finished = self.update_cross_attack()
        if finished:
            self.process_attack_result()

    def update_collision(self):
        """Update attacks for a collision (meet in center)"""
        target_x = constants.SCREEN_WIDTH // 2 - int(12 * constants.UI_SCALE)
        for atk in self.attack_positions:
            sprite, (x, y) = atk
            if x < target_x:
                x += combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE)
            elif x > target_x:
                x -= combat_constants.ATTACK_SPEED * (30 / constants.FRAME_RATE)
            atk[1] = (x, y)
        left_x = self.attack_positions[0][1][0]
        right_x = self.attack_positions[1][1][0]
        return (
            abs(left_x - target_x) <= int(10 * constants.UI_SCALE)
            and abs(right_x - target_x) <= int(10 * constants.UI_SCALE)
        )

    def update_cross_attack(self):
        """Update attacks for cross fire (no collision)"""
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

    def process_attack_result(self):
        """Process the result of an attack and advance to next pattern"""
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

    def draw(self, surface):
        """Draw the head charge minigame components"""
        if self.phase == "result":
            self.draw_result(surface)
        else:
            self.draw_strikes_counter(surface)
            self.draw_pets(surface)
            if self.phase == "attack_move":
                self.draw_attacks(surface)

            # Draw UI buttons only if mouse is available (and not on result screen)
            mouse_enabled = runtime_globals.game_input.is_mouse_enabled()
            if self.phase != "result" and mouse_enabled:
                self.up_button.draw(surface)
                self.down_button.draw(surface)

    def draw_strikes_counter(self, surface):
        """Draw the strikes counter using HeadTraining_Back (208x48) and HeadTraining_Strike (32x32)"""
        strikes_back = self._sprite_cache['strikes_back']
        strikes = self._sprite_cache['strikes']
        
        # Position at bottom right (not touching the border)
        margin = int(10 * constants.UI_SCALE)
        starting_x = constants.SCREEN_WIDTH - strikes_back.get_width() - margin
        starting_y = constants.SCREEN_HEIGHT - strikes_back.get_height() - margin
        
        blit_with_shadow(surface, strikes_back, (starting_x, starting_y))

        # Calculate sprite scale factor for positioning
        sprite_scale_factor = constants.UI_SCALE / 2
        
        # Strike positioning: first at 12,8, last at 156,8 with 4px distance between them
        # Strikes are 32px wide, so: first=12, second=48, third=84, fourth=120, fifth=156
        first_strike_x = int(12 * sprite_scale_factor)
        strike_y = int(8 * sprite_scale_factor)
        strike_width = int(32 * sprite_scale_factor)  # Strike sprite width scaled
        strike_spacing = int(4 * sprite_scale_factor)  # 4px spacing scaled
        
        # Draw remaining strikes (5 - current_index), removed from right to left
        strikes_remaining = 5 - self.current_index
        for i in range(strikes_remaining):
            # Calculate x position for each strike from right to left
            strike_index = strikes_remaining - 1 - i  # Strike index from right to left
            x = starting_x + first_strike_x + (strike_index * (strike_width + strike_spacing))
            y = starting_y + strike_y
            blit_with_shadow(surface, strikes, (x, y))

    def draw_pets(self, surface):
        """Draw the two pets in attack poses using cached scaled sprites"""
        # Use cached scaled pet sprites
        if self.phase == "attack_move":
            left_sprite = self._sprite_cache['left_pet_atk2']
            right_sprite = self._sprite_cache['right_pet_atk2']
        else:
            left_sprite = self._sprite_cache['left_pet_atk1']
            right_sprite = self._sprite_cache['right_pet_atk1']
        
        # Flip left sprite and draw
        left_sprite = pygame.transform.flip(left_sprite, True, False)

        # Calculate positions to center the scaled sprites
        left_x = 0 + (5 * constants.UI_SCALE)
        self.left_y = constants.SCREEN_HEIGHT // 2 - left_sprite.get_height() // 2
        right_x = constants.SCREEN_WIDTH - right_sprite.get_width() - (5 * constants.UI_SCALE)
        self.right_y = constants.SCREEN_HEIGHT // 2 - right_sprite.get_height() // 2

        blit_with_shadow(surface, left_sprite, (left_x, self.left_y))
        blit_with_shadow(surface, right_sprite, (right_x, self.right_y))

    def draw_attacks(self, surface):
        """Draw the attack sprites moving across screen"""
        for sprite, (x, y) in self.attack_positions:
            blit_with_shadow(surface, sprite, (int(x), int(y)))

    def draw_result(self, surface):
        """Draw the final result screen with scores"""
        center_x = constants.SCREEN_WIDTH // 2
        center_y = constants.SCREEN_HEIGHT // 2
        head_training_img = self._sprite_cache['head_training_img']
        vs_img = self._sprite_cache['vs_img']

        # Draw header image
        blit_with_shadow(
            surface,
            head_training_img,
            (center_x - head_training_img.get_width() // 2, center_y - head_training_img.get_height() - int(20 * constants.UI_SCALE))
        )

        font = self.up_button.get_font(custom_size=int(48 * constants.UI_SCALE))
        
        wins_text = font.render(str(self.victories), True, constants.FONT_COLOR_DEFAULT)
        losses_text = font.render(str(self.failures), True, constants.FONT_COLOR_DEFAULT)

        # Layout: wins + VS + losses
        total_width = wins_text.get_width() + vs_img.get_width() + losses_text.get_width() + int(20 * constants.UI_SCALE)
        start_x = center_x - total_width // 2
        y = center_y + int(15 * constants.UI_SCALE)

        blit_with_shadow(surface, wins_text, (start_x, y))
        blit_with_shadow(surface, vs_img, (start_x + wins_text.get_width() + int(10 * constants.UI_SCALE), y - (4 * constants.UI_SCALE)))
        blit_with_shadow(surface, losses_text, (start_x + wins_text.get_width() + vs_img.get_width() + int(20 * constants.UI_SCALE), y))

    def is_complete(self):
        """Check if the minigame is complete"""
        return self.phase == "result"

    def check_victory(self):
        """Check if player won the minigame"""
        return self.victories > self.failures

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