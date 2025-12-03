import pygame
from core import runtime_globals
import core.constants as constants
from core.utils.pygame_utils import blit_with_cache, sprite_load

class XaiRoll:
    """XAI rolling minigame for DMX ruleset"""
    FRAME_COUNT = 7

    def __init__(self, x, y, width, height, xai_number):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.xai_number = max(1, min(self.FRAME_COUNT, xai_number))
        # Load the sprite sheet at its original size (no scaling)
        self.sprite_sheet = sprite_load(constants.XAI_ICON_PATH)
        self.current_frame = self.xai_number - 1
        self.rolling = False
        self.roll_timer = 0
        self.roll_speed = int(5 * (constants.FRAME_RATE / 30)) # frames per sprite change

        # Animation state for stop effect
        self.stopping = False
        self.stop_target_frame = None
        self.rect_anim_progress = 0
        self.rect_anim_speed = 2 * (30 / constants.FRAME_RATE)  # pixels per frame
        self.rect_anim_max = self.height // 2
        self.rect_anim_phase = 0  # 0: expanding, 1: shrinking

        # Cache scaled sprites
        self.scaled_sprites = []
        sheet_width, sheet_height = self.sprite_sheet.get_size()
        frame_width = sheet_width // self.FRAME_COUNT
        frame_height = sheet_height
        for i in range(self.FRAME_COUNT):
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            icon = self.sprite_sheet.subsurface(frame_rect)
            icon = pygame.transform.scale(icon, (self.width, self.height))
            self.scaled_sprites.append(icon)

    def roll(self):
        self.rolling = True
        self.stopping = False
        self.roll_timer = 0

    def stop(self, xai_number=None):
        # Begin stop animation
        self.stopping = True
        self.rolling = True  # keep rolling during animation
        self.rect_anim_progress = 0
        self.rect_anim_phase = 0
        if xai_number is not None:
            self.stop_target_frame = max(1, min(self.FRAME_COUNT, xai_number)) - 1
        else:
            self.stop_target_frame = self.current_frame

    def update(self):
        if self.rolling:
            self.roll_timer += 1
            if self.roll_timer >= self.roll_speed:
                self.roll_timer = 0
                self.current_frame = (self.current_frame + 1) % self.FRAME_COUNT

        if self.stopping:
            if self.rect_anim_phase == 0:
                # Expand rectangles
                self.rect_anim_progress += self.rect_anim_speed
                if self.rect_anim_progress >= self.rect_anim_max:
                    self.rect_anim_progress = self.rect_anim_max
                    # Switch to stopped frame and start shrinking
                    self.current_frame = self.stop_target_frame
                    self.rolling = False
                    self.rect_anim_phase = 1
            elif self.rect_anim_phase == 1:
                # Shrink rectangles
                self.rect_anim_progress -= self.rect_anim_speed
                if self.rect_anim_progress <= 0:
                    self.rect_anim_progress = 0
                    self.stopping = False  # Animation done

        # Play sound every half second while rolling
        if self.rolling:
            if not hasattr(self, "_last_sound_tick"):
                self._last_sound_tick = pygame.time.get_ticks()
            now = pygame.time.get_ticks()
            if now - self._last_sound_tick >= 500:
                runtime_globals.game_sound.play("cancel")
                self._last_sound_tick = now
        else:
            if hasattr(self, "_last_sound_tick"):
                del self._last_sound_tick

    def draw(self, surface):
        icon = self.scaled_sprites[self.current_frame]
        #surface.blit(icon, (self.x, self.y))
        blit_with_cache(surface, icon, (self.x, self.y))

        if self.stopping and self.rect_anim_progress > 0:
            # Draw expanding/shrinking rectangles from top and bottom
            rect_height = self.rect_anim_progress
            top_rect = pygame.Rect(self.x, self.y, self.width, rect_height)
            bottom_rect = pygame.Rect(self.x, self.y + self.height - rect_height, self.width, rect_height)
            color = (0, 0, 0)  # Black, or choose another color for the effect
            pygame.draw.rect(surface, color, top_rect)
            pygame.draw.rect(surface, color, bottom_rect)

    def get_result(self):
        """Get the current XAI number result (1-7)"""
        return self.current_frame + 1

    def handle_event(self, event):
        """Handle input events for the XAI roll minigame"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a or event.key == pygame.K_SPACE:
                if not self.rolling:
                    self.roll()
                elif not self.stopping:
                    self.stop()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if not self.rolling:
                    self.roll()
                elif not self.stopping:
                    self.stop()
                return True
        return False