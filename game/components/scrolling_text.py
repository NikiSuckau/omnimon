import pygame
from core.utils.pygame_utils import blit_with_shadow
from core import constants

class ScrollingText:
    def __init__(self, text_surface, max_width, speed=1):
        """Initializes scrolling text with optimized behavior."""
        self.text_surface = text_surface
        self.max_width = max_width
        self.speed = speed  # Pixels per 30fps frame
        self.offset = 0
        self.direction = 1  # 1: left, -1: right
        self.should_scroll = self.text_surface.get_width() > self.max_width  # Scroll only if necessary

    def update(self):
        """Updates text scrolling only if required, frame-rate independent."""
        if self.should_scroll:
            # Move at the same speed per second regardless of frame rate
            increment = self.speed * (30 / constants.FRAME_RATE)  # Adjust for 30 FPS
            self.offset += increment * self.direction
            # Clamp and reverse direction if needed
            if self.offset + self.max_width >= self.text_surface.get_width():
                self.offset = self.text_surface.get_width() - self.max_width
                self.direction = -1
            elif self.offset <= 0:
                self.offset = 0
                self.direction = 1

    def draw(self, surface, position):
        """Draws scrolling text or static text if it fits."""
        if not self.should_scroll:
            # If text fits, render normally
            blit_with_shadow(surface, self.text_surface, position)
        else:
            # Scroll text using clamped rect
            rect = pygame.Rect(int(self.offset), 0, self.max_width, self.text_surface.get_height())
            if rect.right > self.text_surface.get_width():
                rect.width = self.text_surface.get_width() - rect.left

            visible_surface = pygame.Surface((self.max_width, self.text_surface.get_height()), pygame.SRCALPHA)
            visible_surface.blit(self.text_surface, (0, 0), rect)

            # Draw the visible surface with shadow
            blit_with_shadow(surface, visible_surface, position)