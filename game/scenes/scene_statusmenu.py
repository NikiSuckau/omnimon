import pygame
from components.window_background import WindowBackground
from components.window_petselector import WindowPetSelector
from components.window_status import WindowStatus
from core import runtime_globals
from core.utils.pygame_utils import blit_with_cache, sprite_load_percent
from core.utils.scene_utils import change_scene
from core import constants


class SceneStatusMenu:
    def __init__(self) -> None:
        self.background = WindowBackground(False)
        self.overlay_image = sprite_load_percent(
            constants.MENU_BACKGROUND_PATH,
            percent=100,
            keep_proportion=True,
            base_on="width"
        )
        self.selector = WindowPetSelector()
        self.selecting_pet = True
        self.page = 1
        self.window_status = None
        self._cache_surface = None  # Cached scene surface
        self._cache_key = None  # Tuple to track what state is cached
        runtime_globals.game_console.log("[SceneStatusMenu] Initialized.")

    def update(self) -> None:
        pass

    def draw(self, surface):
        # Update window components for mouse hover
        if self.selecting_pet:
            self.selector.update()
        
        # Determine current state key that affects drawing
        cache_key = (
            self.selecting_pet,
            self.selector.selected_index,
            self.page,
        )

        if cache_key != self._cache_key or self._cache_surface is None:
            # Cache is invalid or doesn't exist - redraw entire scene once
            cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)

            self.background.draw(cache_surface)
            overlay_rect = self.overlay_image.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
            blit_with_cache(cache_surface, self.overlay_image, overlay_rect)

            if self.selecting_pet:
                self.selector.draw(cache_surface)
            else:
                self.window_status.draw_page(cache_surface, self.page)

            self._cache_surface = cache_surface
            self._cache_key = cache_key

        # Blit cached surface to actual surface every frame
        surface.blit(self._cache_surface, (0, 0))

    def handle_event(self, input_action):
        changed = False
        if self.selecting_pet:
            if self.selector.handle_event(input_action):
                self.open_status()
                changed = True
        else:
            if input_action:
                if input_action == "RIGHT":
                    runtime_globals.game_sound.play("menu")
                    self.page = (self.page % 4) + 1
                    changed = True
                elif input_action == "LEFT":
                    runtime_globals.game_sound.play("menu")
                    self.page = (self.page - 2) % 4 + 1
                    changed = True
                elif input_action in ["UP", "DOWN"]:
                    self.selector.handle_event(input_action)
                    self.open_status(self.page)
                    changed = True
                elif input_action == "A" or input_action == "B":
                    runtime_globals.game_sound.play("menu")
                    self.selecting_pet = True
                    changed = True
                elif input_action == "START":
                    change_scene("game")

        if changed:
            self._cache_surface = None  # Invalidate cache to redraw next frame

    def open_status(self, page=1):
        pet = self.selector.get_selected_pet()
        self.window_status = WindowStatus(pet)
        self.pet = pet
        self.page = page
        self.selecting_pet = False
        self._cache_surface = None  # Invalidate cache for redraw
