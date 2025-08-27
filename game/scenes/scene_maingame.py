"""
Scene Main Game
The main scene where pets live, eat, sleep, move, and interact.
"""
import platform
import random
import pygame
import datetime
import os
import time

from components.window_background import WindowBackground
from components.window_clock import WindowClock
from components.window_mainmenu import WindowMenu
from core import game_globals, runtime_globals
import game.core.constants as constants
from core.game_evolution_entity import GameEvolutionEntity
from core.utils.pet_utils import all_pets_hatched, distribute_pets_evenly, draw_pet_outline, get_selected_pets
from core.utils.pygame_utils import blit_with_cache, get_font
from core.utils.scene_utils import change_scene
from core.utils.inventory_utils import add_to_inventory, get_item_by_name
from game.core.utils.module_utils import get_module
from game.core.utils.quest_event_utils import generate_daily_quests, get_hourly_random_event
from core.utils.inventory_utils import add_to_inventory

HEARTS_SIZE = int(8 * constants.UI_SCALE)

#=====================================================================
# SceneMainGame
#=====================================================================
class SceneMainGame:
    """
    Handles the main game scene, including pets, menu navigation, and interactions.
    """

    def __init__(self) -> None:
        """
        Initializes the main game scene.
        """
        self.background = WindowBackground()
        self.menu = WindowMenu()
        self.clock = WindowClock()
        self.fade_out_timer = 1800
        self.selection_mode = "menu"
        self.pet_selection_index = 0
        self.fade_alpha = 0
        self.lock_inputs = False
        self.lock_updates = False

        self.sprites = {
            "heart_empty": pygame.transform.scale(pygame.image.load(constants.HEART_EMPTY_ICON_PATH).convert_alpha(), (HEARTS_SIZE, HEARTS_SIZE)),
            "heart_half": pygame.transform.scale(pygame.image.load(constants.HEART_HALF_ICON_PATH).convert_alpha(), (HEARTS_SIZE, HEARTS_SIZE)),
            "heart_full": pygame.transform.scale(pygame.image.load(constants.HEART_FULL_ICON_PATH).convert_alpha(), (HEARTS_SIZE, HEARTS_SIZE))
        }

        self.cleaning = False
        self.cleaning_x = constants.SCREEN_WIDTH
        self.cleaning_speed = constants.CLEANING_SPEED * constants.UI_SCALE * (30 / constants.FRAME_RATE)
        self._hearts_cache = {}
        self._fade_overlay_cache = None  # Cache fade overlay surface

        today = datetime.date.today()
        if game_globals.xai_date < today:
            game_globals.xai = random.randint(1, 7)
            game_globals.xai_date = today
            # Reset daily quests when day changes
            game_globals.quests = []
            runtime_globals.game_console.log(f"[SceneMainGame] New day detected, XAI set to {game_globals.xai}, quests reset")

        self.food_anims = {}  # {pet_index: [frames]} for animated food sprites
        self.load()

        self.frame_counter = 0  # Tracks frames for time updates
        # Ensure the global last-input frame is synced when the scene is created
        runtime_globals.last_input_frame = self.frame_counter
        self._static_last_frame = 0
        self.last_menu_index = -1
        self.cached_static_surface = None
        self._screensaver_cache = None
        self._screensaver_cache_last_frame = 0
        # Screensaver rendering caches (create fonts/sprites once)
        try:
            self._ss_time_font = pygame.font.Font(None, int(72 * constants.UI_SCALE))
        except Exception:
            self._ss_time_font = pygame.font.SysFont(None, int(72 * constants.UI_SCALE))
        # Use module font for smaller text where available
        try:
            self._ss_call_font = get_font(constants.FONT_SIZE_MEDIUM)
            self._ss_poop_font = get_font(constants.FONT_SIZE_SMALL)
        except Exception:
            self._ss_call_font = pygame.font.SysFont(None, int(28 * constants.UI_SCALE))
            self._ss_poop_font = pygame.font.SysFont(None, int(24 * constants.UI_SCALE))

        # Cached sprites (pulled lazily from main menu / runtime globals)
        self._ss_call_sprite = None
        self._ss_poop_sprite = None
        # Track state used in screensaver to allow immediate cache invalidation
        self._ss_last_pet_alert = bool(getattr(runtime_globals, 'pet_alert', False))
        self._ss_last_poop_count = len(game_globals.poop_list)
        # Track sick state for cache invalidation (show sick icon if any pet is sick)
        self._ss_last_sick_flag = any(p.sick > 0 for p in game_globals.pet_list)

        # Screensaver position randomizer: change position every minute (frame-based)
        self._ss_position = (0, 0)  # offset from center (x_offset, y_offset)
        self._ss_last_position_frame = self.frame_counter

        # Event system variables
        self.event_stage = 0  # 0 = no event, 1 = alert/choice, 2 = animation
        self.event_alert_blink = 0  # Counter for blinking alert icon
        self.event_gift_x = -100  # X position for gift animation
        self.event_gift_timer = 0  # Timer for gift animation phases
        self.event_sound_played = False  # Track if alert sound was played

        # Cached event sprites to avoid loading/scaling every frame
        self.event_sprites = {
            'alert': None,
            'gift': None
        }

        if game_globals.quests is None or len(game_globals.quests) == 0:
            game_globals.quests = generate_daily_quests()

        # Initialize event timer if not set
        if game_globals.event_time is None:
            game_globals.event_time = 60  # 60 minutes until first event check

    def update(self) -> None:
        """
        Updates all game objects (pets, background, poops, cleaning effect).
        """
        if self.lock_updates:
            self.check_evolution_start()
            return

        # Increment the frame counter
        self.frame_counter += 1
        # Ensure last_input_frame exists (use frames to avoid frequent time.time() calls)
        if not hasattr(runtime_globals, 'last_input_frame'):
            runtime_globals.last_input_frame = self.frame_counter

        # Update pets and poops only if necessary
        for pet in game_globals.pet_list:
            pet.update()

        for poop in game_globals.poop_list:
            poop.update()

        # Handle fade-out timer
        if self.fade_out_timer > 0:
            self.fade_out_timer -= 1
            if self.fade_out_timer <= 0:
                runtime_globals.main_menu_index = -1
                runtime_globals.selected_pets = []

        # Update cleaning animation only if active
        if self.cleaning:
            self.update_cleaning()

        # Update event system
        self.update_events()

        # Check evolution start
        self.check_evolution_start()

        # Update background and game messages
        self.background.update()
        runtime_globals.game_message.update()

    def check_evolution_start(self):
        """Begins evolution sequence when a pet is ready to evolve."""
        if runtime_globals.evolution_pet:
            # Update last input frame so screensaver will dismiss at next draw
            runtime_globals.last_input_frame = self.frame_counter
            self.start_evolution_sequence()

    def start_evolution_sequence(self):
        """Handles the epic evolution sequence based on music timing."""
        if self.lock_inputs:
            music_time = runtime_globals.game_sound.get_music_position()

            if music_time >= 5:
                self.lock_updates = True
                self.move_evolving_pet_to_center()

            if music_time >= 12:
                self.fade_out_except_evolving_pet()

            if music_time >= 18:
                evo = GameEvolutionEntity(
                    from_name = "MetalGreymon",
                    from_attribute = "Da",
                    from_sprite = runtime_globals.pet_sprites[game_globals.pet_list[0]][0],
                    to_attribute = "Vi",
                    to_name = "WarGreymon",
                    to_sprite = runtime_globals.pet_sprites[game_globals.pet_list[1]][0],
                    stage = 5)
                
                runtime_globals.evolution_data = [evo]
                change_scene("evolution")
        else:
            runtime_globals.game_sound.play("evolution_2020")  # 🔥 Start with fade-in
            self.lock_inputs = True

    def move_evolving_pet_to_center(self):
        """Moves the evolving pet toward the center of the screen."""
        pet = runtime_globals.evolution_pet
        if pet.x < (constants.SCREEN_WIDTH - constants.PET_WIDTH) // 2:
            pet.x += 1  # 🔥 Gradually move to center
            pet.direction = 1
            pet.set_state("moving")
        elif pet.x > (constants.SCREEN_WIDTH - constants.PET_WIDTH) // 2:
            pet.x -= 1
            pet.direction = -1
            pet.set_state("moving")
        else:
            pet.x = (constants.SCREEN_WIDTH - constants.PET_WIDTH) // 2
            pet.direction = -1
            pet.set_state("idle")

    def fade_out_except_evolving_pet(self):
        """Gradually dims the screen, leaving only the evolving pet visible."""
        self.fade_alpha = min(self.fade_alpha + 5, 255)

    def update_cleaning(self) -> None:
        """
        Updates the screen cleaning animation.
        """
        if not self.cleaning:
            return

        self.cleaning_x -= self.cleaning_speed
        for poop in game_globals.poop_list:
            poop.x -= self.cleaning_speed

        if self.cleaning_x <= -runtime_globals.misc_sprites["Wash"].get_width():
            game_globals.poop_list.clear()
            self.cleaning = False
            self.cleaning_x = constants.SCREEN_WIDTH
            runtime_globals.game_sound.play("happy")
            for pet in game_globals.pet_list:
                module = get_module(pet.module)
                if module.care_flush_disturbance_sleep:
                    pet.check_disturbed_sleep()
                    pet.set_state("happy2")
            runtime_globals.game_console.log("[SceneMainGame] Cleaning complete.")

    def update_events(self) -> None:
        """
        Updates the event system - checks for new events every hour based on XAI and pet awakeness.
        """
        # Stage 1: Check for new events every hour (optimized using frame counter)
        if game_globals.event is None and self.event_stage == 0:
            # Count minutes using frame rate - every 60 seconds * frame rate = 1 minute
            if self.frame_counter % (constants.FRAME_RATE * 60) == 0:
                game_globals.event_time -= 1
                if game_globals.event_time <= 0:
                    # Check if all pets are awake before triggering events
                    all_pets_awake = all(pet.state != "nap" and pet.state != "sleep" for pet in game_globals.pet_list)
                    
                    if all_pets_awake:
                        # Time to check for an event with XAI-based probability
                        game_globals.event = get_hourly_random_event()
                        runtime_globals.game_console.log(f"[Event] Event check with XAI {game_globals.xai} (all pets awake)")
                    else:
                        runtime_globals.game_console.log(f"[Event] Skipping event check - some pets are sleeping")
                    
                    game_globals.event_time = 60  # Reset timer for next hour
                    
                    if game_globals.event:
                        self.event_stage = 1  # Move to alert stage
                        self.event_sound_played = False
                        runtime_globals.game_console.log(f"[Event] New event: {game_globals.event.name}")
        
        # Stage 2: Alert stage - blink alert icon and wait for player input
        elif game_globals.event is not None and self.event_stage == 1:
            # Play alert sound once
            if not self.event_sound_played:
                runtime_globals.game_sound.play("need_attention")
                self.event_sound_played = True
            
            # Blink counter for alert icon
            self.event_alert_blink += 1
        
        # Stage 3: Animation stage - handle event execution
        elif game_globals.event is not None and self.event_stage == 2:
            from core.game_event import EventType
            
            if game_globals.event.type == EventType.ITEM_PACKAGE:
                self.update_gift_animation()
            elif game_globals.event.type == EventType.ENEMY_BATTLE:
                # Change to battle scene
                runtime_globals.game_console.log(f"[Event] Starting battle event: {game_globals.event.name}")
                # Set battle parameters based on event
                game_globals.battle_area[game_globals.event.module] = game_globals.event.area
                game_globals.battle_round[game_globals.event.module] = game_globals.event.round
                change_scene("battle")
                # Reset event
                game_globals.event = None
                self.event_stage = 0

    def update_gift_animation(self) -> None:
        """
        Handles the gift animation for ITEM_PACKAGE events.
        """
        gift_move_duration = 4 * constants.FRAME_RATE  # 4 seconds
        if self.event_gift_timer < gift_move_duration:
            # Smooth movement using easing
            progress = self.event_gift_timer / gift_move_duration
            # Ease-out cubic for smoother deceleration
            eased_progress = 1 - (1 - progress) ** 3
            start_x = -100
            end_x = constants.SCREEN_WIDTH // 2 - 24  # Center position
            self.event_gift_x = start_x + (end_x - start_x) * eased_progress
            self.event_gift_timer += 1
        
        # Phase 2: Gift "opens" - show item only (2 seconds)
        elif self.event_gift_timer < gift_move_duration + (2 * constants.FRAME_RATE):
            self.event_gift_x = constants.SCREEN_WIDTH // 2 - 24  # Keep centered

            # On first frame of this phase, add item to inventory using utils
            if self.event_gift_timer == gift_move_duration:
                item_name = game_globals.event.item
                item_quantity = game_globals.event.item_quantity
                module_name = game_globals.event.module
                
                # Get the item object to use its ID instead of name
                item_obj = get_item_by_name(module_name, item_name)
                if item_obj:
                    add_to_inventory(item_obj.id, item_quantity)
                    runtime_globals.game_console.log(f"[Event] Received {item_quantity}x {item_name} (ID: {item_obj.id})")
                else:
                    # Fallback: use item name as ID if item object not found
                    add_to_inventory(item_name, item_quantity)
                    runtime_globals.game_console.log(f"[Event] Received {item_quantity}x {item_name} (fallback)")

            self.event_gift_timer += 1
        
        # Phase 3: Animation complete, make pets happy and cleanup
        else:
            # Make all pets happy and play sound only once when cleaning up
            if self.event_gift_timer == gift_move_duration + (2 * constants.FRAME_RATE):
                for pet in game_globals.pet_list:
                    pet.set_state("happy2")
                runtime_globals.game_sound.play("happy")
            
            # Reset event system
            game_globals.event = None
            self.event_stage = 0
            self.event_gift_timer = 0
            self.event_gift_x = -100

    def load(self):
        """
        Loads the scene, preparing pets, background, and any necessary resources.
        """
        # Prepare food animations for pets that are eating
        self.food_anims = {}
        for pet_index, food_info in getattr(runtime_globals, "game_pet_eating", {}).items():
            # Use preloaded anim_frames if available, otherwise fallback to icon sprite
            anim_frames = food_info.get("anim_frames")
            icon = food_info.get("sprite")
            if anim_frames and isinstance(anim_frames, list) and len(anim_frames) == 4:
                self.food_anims[pet_index] = anim_frames
            else:
                # Fallback: use the icon itself as all frames
                self.food_anims[pet_index] = [icon] * 4

        # Also sync last-input-frame when the scene is (re)loaded so screensaver timing is correct
        runtime_globals.last_input_frame = getattr(self, 'frame_counter', 0)

    def update_static_surface(self) -> None:
        """
        Updates the cached surface for the background, menu, and clock.
        """
        menu_index_changed = self.last_menu_index != runtime_globals.main_menu_index
        clock_changed = (self.frame_counter - self._static_last_frame) > constants.FRAME_RATE  # Update once per second

        if not self.cached_static_surface or menu_index_changed or clock_changed:
            self._static_last_frame = self.frame_counter
            self.cached_static_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            
            # Draw background
            self.background.draw(self.cached_static_surface)
            
            # Draw menu
            self.menu.draw(self.cached_static_surface)
            self.last_menu_index = runtime_globals.main_menu_index
            
            # Draw clock
            if game_globals.showClock:
                self.clock.draw(self.cached_static_surface)

    def _render_screensaver_surface(self):
        """Render the full screensaver surface (clock + call sign + poop count)."""
        # Create surface once per cache refresh
        surf = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        surf.fill((0, 0, 0))

        self.menu.check_alert()  # Ensure alert state is updated

        now_dt = datetime.datetime.now()
        time_str = now_dt.strftime("%H:%M")
        text = self._ss_time_font.render(time_str, True, constants.FONT_COLOR_DEFAULT)

        # Use randomized offset from center (set once per minute)
        offset_x, offset_y = getattr(self, '_ss_position', (0, 0))
        center_x = (constants.SCREEN_WIDTH // 2) + offset_x
        center_y = (constants.SCREEN_HEIGHT // 2) + offset_y
        x = center_x - (text.get_width() // 2)
        y = center_y - (text.get_height() // 2)
        blit_with_cache(surf, text, (x, y))

        # Call sign: only show when pet_alert is true
        call_drawn = None
        if runtime_globals.pet_alert:
            call_drawn = True
            call_sprite = runtime_globals.misc_sprites.get('CallSignInverted')

        # Poop count with icon (always show count even if 0)
        poop_count = len(game_globals.poop_list)

        # Lazily grab poop and sick sprites from runtime globals
        poop_sprite = runtime_globals.misc_sprites.get('PoopInverted')

        sick_sprite = runtime_globals.misc_sprites.get('SickInverted')

        # Determine if any pet is sick right now
        sick_flag = any(p.sick > 0 for p in game_globals.pet_list)

        # place group under clock
        group_y = y + text.get_height()
        if poop_count > 0:
            blit_with_cache(surf, poop_sprite, (x, group_y))

        if sick_flag:
            blit_with_cache(surf, sick_sprite, (center_x - (sick_sprite.get_width() // 2), group_y))

        if call_drawn:
            blit_with_cache(surf, call_sprite, (x + text.get_width() - call_sprite.get_width(), group_y))

        return surf

    def update_mouse_hover(self):
        """Update menu selection based on mouse hover and handle pet area clicks."""
        if not runtime_globals.game_input.mouse_enabled or self.lock_inputs:
            return
        
        mouse_pos = runtime_globals.game_input.get_mouse_position()
        mouse_x, mouse_y = mouse_pos
        
        # Check if mouse is hovering over any menu icon
        hovered_index = self.get_hovered_menu_index(mouse_x, mouse_y)
        
        # Update menu index based on hover (-1 if not hovering any)
        if hovered_index != runtime_globals.main_menu_index:
            runtime_globals.main_menu_index = hovered_index

    def get_hovered_menu_index(self, mouse_x, mouse_y):
        """Get the menu index that the mouse is hovering over, or -1 if none."""
        icon_size = constants.MENU_ICON_SIZE * 2
        
        # Calculate menu positions (same logic as WindowMenu.calculate_spacing)
        spacing_x = (constants.SCREEN_WIDTH - (5 * icon_size)) // 5
        top_y = 20 * constants.UI_SCALE if game_globals.showClock else 5 * constants.UI_SCALE
        bottom_y = constants.SCREEN_HEIGHT - icon_size - 10
        
        # Check top row (icons 0-4)
        for i in range(5):
            icon_x = spacing_x + i * (icon_size + spacing_x)
            icon_rect = pygame.Rect(icon_x, top_y, icon_size, icon_size)
            if icon_rect.collidepoint(mouse_x, mouse_y):
                return i
        
        # Check bottom row (icons 5-8), not selecting Call icon
        for i in range(4):
            icon_x = spacing_x + i * (icon_size + spacing_x)
            icon_rect = pygame.Rect(icon_x, bottom_y, icon_size, icon_size)
            if icon_rect.collidepoint(mouse_x, mouse_y):
                return i + 5
        
        return -1

    def is_mouse_in_pet_area(self, mouse_pos):
        """Check if mouse is in the pet area (from pet Y to pet Y + height across full screen width)."""
        if not game_globals.pet_list:
            return False
        
        mouse_x, mouse_y = mouse_pos
        
        # Find the pet area bounds - use Y range from pets
        min_pet_y = min(pet.y for pet in game_globals.pet_list)
        max_pet_y = max(pet.y + constants.PET_HEIGHT for pet in game_globals.pet_list)
        
        # Pet area spans full screen width, from minimum pet Y to maximum pet Y + height
        pet_area_rect = pygame.Rect(0, min_pet_y, constants.SCREEN_WIDTH, max_pet_y - min_pet_y)
        
        return pet_area_rect.collidepoint(mouse_x, mouse_y)

    def draw(self, surface: pygame.Surface) -> None:
        """
        Draws the cached static surface and dynamic elements like pets, poops, and animations.
        """
        # Update mouse hover for menu items if mouse is enabled
        if runtime_globals.game_input.mouse_enabled:
            self.update_mouse_hover()
        
        # Screensaver: check timeout (seconds) using frame-based timing to avoid frequent time.time() calls
        timeout = getattr(game_globals, 'screen_timeout', 0)
        last_frame = getattr(runtime_globals, 'last_input_frame', self.frame_counter)
        elapsed_frames = self.frame_counter - last_frame
        timeout_frames = int(timeout * constants.FRAME_RATE) if timeout and timeout > 0 else 0

        if timeout and timeout > 0 and elapsed_frames >= timeout_frames:
            # Use cached screensaver surface and refresh every 5 seconds using the frame counter
            # Invalidate cache immediately if relevant state changed
            current_pet_alert = bool(getattr(runtime_globals, 'pet_alert', False))
            current_poop_count = len(game_globals.poop_list)
            current_sick_flag = any(p.sick > 0 for p in game_globals.pet_list)
            if current_pet_alert != self._ss_last_pet_alert or current_poop_count != self._ss_last_poop_count:
                self._screensaver_cache = None
                self._ss_last_pet_alert = current_pet_alert
                self._ss_last_poop_count = current_poop_count
            # Invalidate if sick state changed
            if current_sick_flag != self._ss_last_sick_flag:
                self._screensaver_cache = None
                self._ss_last_sick_flag = current_sick_flag

            # Change screensaver position once per minute (frame-based). If position changes, invalidate cache.
            minute_frames = constants.FRAME_RATE * 60
            if (self.frame_counter - getattr(self, '_ss_last_position_frame', 0)) >= minute_frames:
                # pick a new random offset but keep clock roughly on-screen
                max_x = int(constants.SCREEN_WIDTH * 0.25)
                max_y = int(constants.SCREEN_HEIGHT * 0.15)
                new_pos = (random.randint(-max_x, max_x), random.randint(-max_y, max_y))
                if new_pos != getattr(self, '_ss_position', (0, 0)):
                    self._ss_position = new_pos
                    self._screensaver_cache = None
                self._ss_last_position_frame = self.frame_counter

            refresh_frames = constants.FRAME_RATE * 5
            if (not self._screensaver_cache) or (self.frame_counter - self._screensaver_cache_last_frame) >= refresh_frames:
                try:
                    self._screensaver_cache = self._render_screensaver_surface()
                except Exception:
                    # Fallback simple render if anything fails
                    s = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    s.fill((0, 0, 0))
                    self._screensaver_cache = s
                self._screensaver_cache_last_frame = self.frame_counter

            surface.blit(self._screensaver_cache, (0, 0))
            return

        # Update the cached static surface if needed
        self.update_static_surface()

        # Blit the cached static surface
        surface.blit(self.cached_static_surface, (0, 0))

        # Draw pets and their overlays
        pets = game_globals.pet_list
        selected_pets = set(runtime_globals.selected_pets) if runtime_globals.selected_pets else set()
        show_hearts = runtime_globals.show_hearts

        for i, pet in enumerate(pets):
            self.draw_pet(surface, pet, i, selected_pets, show_hearts)

        # Draw poops only if present
        if game_globals.poop_list:
            for poop in game_globals.poop_list:
                poop.draw(surface)

        # Draw cleaning animation only if active
        if self.cleaning:
            self.draw_cleaning(surface)

        # Draw fade overlay and evolved pets only if fading
        if self.lock_inputs and self.fade_alpha > 0:
            self.draw_fade_overlay(surface)
            for i, pet in enumerate(pets):
                self.draw_pet_evolved(surface, pet, i)

        # Draw food animation for eating pets
        self.draw_food_anims(surface)

        # Draw event animations and alerts
        self.draw_events(surface)

        # Draw game messages last
        runtime_globals.game_message.draw(surface)

    def draw_pet(self, surface: pygame.Surface, pet, index: int, selected_pets: set, show_hearts: bool) -> None:
        """
        Draws a single pet with selection/outline indicators.
        """
        pet.draw(surface)

        frame_enum = pet.animation_frames[pet.frame_index]
        frame = runtime_globals.pet_sprites[pet][frame_enum.value]

        if pet.direction == 1:
            frame = pygame.transform.flip(frame, True, False)

        if pet in selected_pets:
            draw_pet_outline(surface, frame, pet.x, pet.y, color=constants.FONT_COLOR_BLUE)  # blue outline
        if self.selection_mode == "pet" and index == self.pet_selection_index:
            draw_pet_outline(surface, frame, pet.x, pet.y, color=constants.FONT_COLOR_YELLOW)  # yellow highlight

        if show_hearts:
            self.draw_hearts(surface, pet.x + (constants.PET_WIDTH // 4), pet.y + constants.PET_HEIGHT, pet.hunger)
            self.draw_hearts(surface, pet.x + (constants.PET_WIDTH // 4), pet.y + constants.PET_HEIGHT + (6 * constants.UI_SCALE), pet.strength)

    def draw_cleaning(self, surface: pygame.Surface) -> None:
        """
        Draws the cleaning animation.
        """
        wash_sprite = runtime_globals.misc_sprites.get("Wash")
        if wash_sprite:
            pet_x = (24 * constants.UI_SCALE) + (constants.SCREEN_HEIGHT - constants.PET_HEIGHT) // 2
            surface.blit(wash_sprite, (self.cleaning_x, pet_x - (wash_sprite.get_height() - constants.PET_HEIGHT)))

    def draw_fade_overlay(self, surface: pygame.Surface) -> None:
        """
        Draws the fade overlay, caching the surface for efficiency.
        """
        if not self._fade_overlay_cache or self._fade_overlay_cache.get_alpha() != self.fade_alpha:
            fade_overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            fade_overlay.fill((0, 0, 0))
            fade_overlay.set_alpha(self.fade_alpha)
            self._fade_overlay_cache = fade_overlay
        surface.blit(self._fade_overlay_cache, (0, 0))

    def draw_food_anims(self, surface: pygame.Surface) -> None:
        """
        Draws food animations for eating pets.
        """
        game_pet_eating = getattr(runtime_globals, "game_pet_eating", None)
        if game_pet_eating:
            for idx, pet in enumerate(game_globals.pet_list):
                if idx in game_pet_eating and pet.state == "eat":
                    anim_frames = self.food_anims.get(idx)
                    if anim_frames:
                        frame_duration = constants.FRAME_RATE
                        total_frames = 4
                        total_anim_time = frame_duration * total_frames
                        # Clamp frame_idx to last frame if animation_counter exceeds total_anim_time
                        if pet.animation_counter >= total_anim_time:
                            frame_idx = total_frames - 1
                        else:
                            frame_idx = (pet.animation_counter // frame_duration) % total_frames
                        food_sprite = anim_frames[frame_idx]
                        x = pet.x
                        # Prevent food from overlapping menu icons
                        y_offset = 20 * constants.UI_SCALE if game_globals.showClock else 5 * constants.UI_SCALE
                        y_min = y_offset + 2 * constants.MENU_ICON_SIZE
                        if constants.MAX_PETS == 4:
                            y = max(y_min, pet.y - (food_sprite.get_height() // 2))
                            surface.blit(food_sprite, (x, y))
                        else:
                            # Scale the food sprite
                            food_size = food_sprite.get_height()
                            food_size = food_size * max(constants.MAX_PETS, 2) // 4
                            food_sprite_scaled = pygame.transform.scale(food_sprite, (food_size, food_size))
                            y = max(y_min, pet.y - (food_size // 2))
                            surface.blit(food_sprite_scaled, (x, y))
                elif idx in self.food_anims:
                    # Clean up if pet is no longer eating
                    game_pet_eating.pop(idx, None)
                    self.food_anims.pop(idx, None)

    def draw_events(self, surface: pygame.Surface) -> None:
        """
        Draws event-related graphics: alert icon and gift animation.
        """
        # Stage 1: Draw blinking alert icon when event is available
        if game_globals.event is not None and self.event_stage == 1:
            # Blink every 30 frames (1 second at 30fps)
            if (self.event_alert_blink // 30) % 2 == 0:
                # Load and cache alert sprite if not already cached
                if not self.event_sprites['alert']:
                    try:
                        alert_sprite = pygame.image.load(constants.ALERT_ICON_PATH).convert_alpha()
                        self.event_sprites['alert'] = pygame.transform.scale(alert_sprite, 
                                                        (int(32 * constants.UI_SCALE), int(32 * constants.UI_SCALE)))
                    except:
                        # Create fallback sprite if file not found
                        self.event_sprites['alert'] = pygame.Surface((int(32 * constants.UI_SCALE), int(32 * constants.UI_SCALE)))
                        self.event_sprites['alert'].fill((255, 255, 0))  # Yellow square
                
                # Position in top-right corner
                x = 4 * constants.UI_SCALE
                y = 68 * constants.UI_SCALE if game_globals.showClock else 52 * constants.UI_SCALE
                surface.blit(self.event_sprites['alert'], (x, y))
        
        # Stage 2: Draw gift animation for ITEM_PACKAGE events
        elif game_globals.event is not None and self.event_stage == 2:
            from core.game_event import EventType
            
            if game_globals.event.type == EventType.ITEM_PACKAGE:
                gift_move_duration = 4 * constants.FRAME_RATE  # 4 seconds
                
                # Phase 1: Show gift sprite moving to center
                if self.event_gift_timer < gift_move_duration:
                    # Load and cache gift sprite if not already cached
                    if not self.event_sprites['gift']:
                        try:
                            gift_sprite = pygame.image.load(constants.GIFT_PATH).convert_alpha()
                            self.event_sprites['gift'] = pygame.transform.scale(gift_sprite,
                                                           (int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)))
                        except:
                            # Create fallback sprite if file not found
                            self.event_sprites['gift'] = pygame.Surface((int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)))
                            self.event_sprites['gift'].fill((255, 215, 0))  # Gold square
                    
                    # Calculate Y position with floating effect
                    base_y = constants.SCREEN_HEIGHT // 2 - self.event_sprites['gift'].get_height() // 2
                    float_offset = int(5 * constants.UI_SCALE * 
                                     pygame.math.Vector2(0, 1).rotate(self.event_gift_timer * 3).y)
                    y = base_y + float_offset
                    
                    surface.blit(self.event_sprites['gift'], (int(self.event_gift_x), y))
                
                # Phase 2: Show item sprite only (gift "opened")
                else:
                    item_name = game_globals.event.item
                    item_sprite = None
                    
                    # Try to load item sprite from modules
                    try:
                        item_sprite_path = f"modules/{game_globals.event.module}/items/{item_name}.png"
                        if os.path.exists(item_sprite_path):
                            item_sprite = pygame.image.load(item_sprite_path).convert_alpha()
                            item_sprite = pygame.transform.scale(item_sprite,
                                                               (int(48 * constants.UI_SCALE), int(48 * constants.UI_SCALE)))
                    except:
                        pass
                    
                    # Calculate center position
                    center_x = constants.SCREEN_WIDTH // 2
                    center_y = constants.SCREEN_HEIGHT // 2
                    
                    if item_sprite:
                        # Show item sprite with floating effect
                        float_offset = int(8 * constants.UI_SCALE * 
                                         pygame.math.Vector2(0, 1).rotate(self.event_gift_timer * 2).y)
                        item_x = center_x - item_sprite.get_width() // 2
                        item_y = center_y - item_sprite.get_height() // 2 + float_offset
                        surface.blit(item_sprite, (item_x, item_y))
                        
                        # Show quantity text below item
                        font = pygame.font.Font(None, int(20 * constants.UI_SCALE))
                        quantity_text = font.render(f"+{game_globals.event.item_quantity}", True, constants.FONT_COLOR_DEFAULT)
                        text_x = center_x - quantity_text.get_width() // 2
                        text_y = item_y + item_sprite.get_height() + 5
                        surface.blit(quantity_text, (text_x, text_y))
                    else:
                        # Fallback: show item name and quantity as text
                        font = pygame.font.Font(None, int(24 * constants.UI_SCALE))
                        text_surface = font.render(f"+{game_globals.event.item_quantity} {item_name}", 
                                                 True, constants.FONT_COLOR_DEFAULT)
                        text_x = center_x - text_surface.get_width() // 2
                        text_y = center_y - text_surface.get_height() // 2
                        surface.blit(text_surface, (text_x, text_y))

    def draw_hearts(self, surface: pygame.Surface, x: int, y: int, value: int, factor: int = 1) -> None:
        """
        Draws heart icons to represent hunger, strength or effort.
        Uses a cache to avoid redrawing every frame.
        """
        cache_key = (x, y, value, factor)
        now = time.time()
        cache_entry = self._hearts_cache.get(cache_key)

        # Refresh cache if older than 1 second or not present
        if not cache_entry or now - cache_entry[1] > 1:
            total_hearts = 4
            heart_surface = pygame.Surface((total_hearts * HEARTS_SIZE, HEARTS_SIZE), pygame.SRCALPHA)
            for i in range(total_hearts):
                heart_x = i * HEARTS_SIZE
                if value >= (i + 1) * factor:
                    heart_sprite = self.sprites["heart_full"]
                elif value >= i * factor + (factor / 2):
                    heart_sprite = self.sprites["heart_half"]
                else:
                    heart_sprite = self.sprites["heart_empty"]
                heart_surface.blit(heart_sprite, (heart_x, 0))
            self._hearts_cache[cache_key] = (heart_surface, now)
        else:
            heart_surface = cache_entry[0]

        blit_with_cache(surface, heart_surface, (x, y))

    def handle_event(self, input_action) -> None:
        """
        Handles keyboard and GPIO button inputs in the main game scene.
        """
        if input_action:
            self.fade_out_timer = 60 * constants.FRAME_RATE  # Reset on any input
            # Update last input frame so screensaver does not trigger erroneously
            runtime_globals.last_input_frame = getattr(self, 'frame_counter', 0)

        # Handle mouse clicks in pet area to toggle hearts view
        if input_action == "A" and runtime_globals.game_input.mouse_enabled:
            mouse_pos = runtime_globals.game_input.get_mouse_position()
            if self.is_mouse_in_pet_area(mouse_pos):
                runtime_globals.show_hearts = not runtime_globals.show_hearts
                runtime_globals.game_sound.play("menu")
                runtime_globals.game_console.log(f"[SceneMainGame] Hearts view toggled: {runtime_globals.show_hearts}")
                return

        if self.lock_inputs:
            return

        # Handle event system inputs
        if self.event_stage > 0 and game_globals.event:
            if self.event_stage == 1 and input_action in ["A", "B"]:
                # Alert stage - any button to proceed to animation
                self.event_stage = 2
                self.event_gift_timer = 0
                runtime_globals.game_sound.play("menu")
                runtime_globals.game_console.log(f"[Events] Proceeding to animation for event: {game_globals.event.name}")
                return
            elif self.event_stage == 2:
                # Animation stage input handling
                from core.game_event import EventType
                if game_globals.event.type == EventType.ITEM_PACKAGE:
                    gift_move_duration = 4 * constants.FRAME_RATE  # 4 seconds
                    if input_action == "A" and self.event_gift_timer > gift_move_duration:  # Accept item after gift opens
                        # Complete event (cleanup handled in update_gift_animation)
                        pass  # Let the animation finish naturally
                    elif input_action == "B":
                        # Decline item - immediate cleanup
                        game_globals.event = None
                        game_globals.event_time = None
                        self.event_stage = 0
                        self.event_gift_timer = 0
                        runtime_globals.game_sound.play("menu")
                        runtime_globals.game_console.log(f"[Events] Declined event")
                        return
                else:
                    # Other event types - A to complete after 0.5 seconds
                    if input_action == "A" and self.event_gift_timer > constants.FRAME_RATE // 2:
                        game_globals.event = None
                        game_globals.event_time = None
                        self.event_stage = 0
                        self.event_gift_timer = 0
                        runtime_globals.game_sound.play("menu")
                        runtime_globals.game_console.log(f"[Events] Completed event")
                        return
            # Return early if in event mode to prevent normal input processing
            if self.event_stage > 0:
                return

        if not all_pets_hatched():
            if input_action == "Y" or input_action == "SHAKE":
                for pet in game_globals.pet_list:
                    pet.shake_counter += 1
            
        if input_action == "B":
            for pet in game_globals.pet_list:
                pet.death_save_counter += 1

        if input_action == "SELECT":
            self.selection_mode = "pet" if self.selection_mode == "menu" else "menu"
            runtime_globals.game_sound.play("menu")
            runtime_globals.game_console.log(f"[SceneMainGame] Switched selection mode to {self.selection_mode}")
            return

        self.handle_debug_keys(input_action)

        if self.selection_mode == "menu":
            self.handle_navigation_keys(input_action)
            self.handle_action_keys(input_action)
        elif self.selection_mode == "pet":
            self.handle_pet_selection_keys(input_action)

    def handle_debug_keys(self, input_action) -> None:
        """
        Debugging shortcuts (F12).
        """
        if input_action == "F12" and constants.DEBUG_MODE:
            # Open debug scene
            runtime_globals.game_sound.play("menu")
            change_scene("debug")
            runtime_globals.game_console.log("[DEBUG] Opening debug scene")

    def handle_navigation_keys(self, input_action) -> None:
        """Handles cyclic LEFT, RIGHT, UP, DOWN for menu navigation."""
        rows, cols = 2, 5  # 🔹 Menu layout (2 rows × 5 columns)
        max_index = rows * cols - 1  # 🔹 Maximum valid index (8)
        if runtime_globals.main_menu_index < 0 and input_action in ["LEFT","RIGHT","UP","DOWN"]:
            runtime_globals.game_sound.play("menu")
            runtime_globals.main_menu_index = 0
        elif input_action == "LEFT":
            runtime_globals.game_sound.play("menu")
            if runtime_globals.main_menu_index in [0, 5, -1]:  
                runtime_globals.main_menu_index = runtime_globals.main_menu_index + 4
            else:
                runtime_globals.main_menu_index -= 1

        elif input_action == "RIGHT":
            runtime_globals.game_sound.play("menu")
            if runtime_globals.main_menu_index in [4, 8, -1]:  
                runtime_globals.main_menu_index = runtime_globals.main_menu_index - 4
            else:
                runtime_globals.main_menu_index += 1

        elif input_action == "UP":
            runtime_globals.game_sound.play("menu")
            if runtime_globals.main_menu_index in range(0, cols) or runtime_globals.main_menu_index == -1:
                runtime_globals.main_menu_index += 5  # 🔹 Wrap from top to bottom
            else:
                runtime_globals.main_menu_index -= 5

        elif input_action == "DOWN":
            runtime_globals.game_sound.play("menu")
            if runtime_globals.main_menu_index in range(5, max_index + 1) or runtime_globals.main_menu_index == -1:
                runtime_globals.main_menu_index -= 5  # 🔹 Wrap from bottom to top
            else:
                runtime_globals.main_menu_index += 5

        # 🔹 Handle `-1` case correctly
        if runtime_globals.main_menu_index == 9:
            runtime_globals.main_menu_index = -1

        if runtime_globals.main_menu_index != -1:
            runtime_globals.main_menu_index %= (max_index + 1)  # 🔥 Ensure cyclic behavior

    def handle_action_keys(self, input_action) -> None:
        """
        Handles Enter, Escape, and equivalent GPIO button actions for menu selection.
        """
        index = runtime_globals.main_menu_index

        if input_action == "A":
            if index == 0:
                runtime_globals.game_sound.play("menu")
                self.start_scene("status")
            elif index == 1:
                runtime_globals.game_sound.play("menu")
                self.start_scene("feeding")
            elif index == 2:
                self.start_training()
            elif index == 3:
                self.start_battle()
            elif index == 4:
                self.start_cleaning()
            elif index == 5:
                self.start_scene("sleepmenu")
            elif index == 6:
                self.heal_sick_pets()
            elif index == 7:
                runtime_globals.game_sound.play("menu")
                self.start_scene("library")
            elif index == 8:
                self.start_scene("connect")

        elif input_action == "START" or (platform.system() == "Windows" and input_action == "B"):  # Maps to ESC (PC) & "START" button (Pi)
            runtime_globals.game_sound.play("cancel")
            self.start_scene("settings")

        elif input_action == "L":  # Rotate screen upside-down
            runtime_globals.game_sound.play("menu")
            game_globals.rotated = True

        elif input_action == "R":
            runtime_globals.game_sound.play("menu")
            distribute_pets_evenly()

        elif input_action == "X":
            runtime_globals.game_sound.play("menu")
            runtime_globals.show_hearts = not runtime_globals.show_hearts


    def start_scene(self, scene_name: str) -> None:
        """
        Helper to start a new scene.
        """
        runtime_globals.game_state = scene_name
        runtime_globals.game_state_update = True
        runtime_globals.game_console.log(f"[SceneMainGame] Switched to {scene_name}")

    def handle_pet_selection_keys(self, input_action) -> None:
        total_pets = len(game_globals.pet_list)

        if input_action == "LEFT":
            self.pet_selection_index = (self.pet_selection_index - 1) % total_pets
            runtime_globals.game_sound.play("menu")

        elif input_action == "RIGHT":
            self.pet_selection_index = (self.pet_selection_index + 1) % total_pets
            runtime_globals.game_sound.play("menu")

        elif input_action == "A":
            self.toggle_pet_selection(self.pet_selection_index)
            runtime_globals.game_sound.play("menu")


    def toggle_pet_selection(self, pet_index: int) -> None:
        """
        Toggles pet selection on Enter press.
        """
        pet = game_globals.pet_list[pet_index]
        if pet in runtime_globals.selected_pets:
            runtime_globals.selected_pets.remove(pet)
            runtime_globals.game_console.log(f"[SceneMainGame] Deselected {pet.name}")
        else:
            runtime_globals.selected_pets.append(pet)
            runtime_globals.game_console.log(f"[SceneMainGame] Selected {pet.name}")

    def start_training(self) -> None:
        """
        Checks if training is possible and starts it.
        """
        can_train = any(pet.can_train() for pet in get_selected_pets())
        if can_train:
            runtime_globals.game_sound.play("menu")
            self.start_scene("training")
        else:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log("[SceneMainGame] Cannot start training: no eligible pets.")

    def start_battle(self) -> None:
        """
        Checks if battle is possible and starts it.
        """
        can_train = any(pet.can_battle() for pet in get_selected_pets())
        if can_train:
            runtime_globals.game_sound.play("menu")
            self.start_scene("battle")
        else:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log("[SceneMainGame] Cannot start battle: no eligible pets.")

    def start_cleaning(self) -> None:
        """
        Starts the screen cleaning action if there are poops.
        """
        if not game_globals.poop_list:
            runtime_globals.game_sound.play("cancel")
            return
        runtime_globals.game_sound.play("menu")
        self.cleaning = True
        self.cleaning_x = constants.SCREEN_WIDTH

    def heal_sick_pets(self) -> None:
        """
        Heals sick pets by 1 sickness point, playing angry animation.
        """
        sick_pets = [pet for pet in game_globals.pet_list if pet.sick > 0]

        if not sick_pets:
            runtime_globals.game_sound.play("cancel")
            runtime_globals.game_console.log("[SceneMainGame] No sick pets to heal.")
            return

        runtime_globals.game_sound.play("fail")
        distribute_pets_evenly()

        for pet in sick_pets:
            pet.sick = max(0, pet.sick - 1)
            pet.set_state("angry")
            runtime_globals.game_console.log(f"[SceneMainGame] {pet.name} healed. Remaining sickness: {pet.sick}")
