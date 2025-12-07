"""
Omnipet Virtual Pet - Android Entry Point
"""
import pygame
import sys
import os


def main():
    # Initialize pygame
    pygame.init()
    
    # Use fullscreen with device/native resolution on Android
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except Exception:
        screen = pygame.display.set_mode((800, 480))
    
    pygame.display.set_caption("Omnipet")
    
    try:
        # Import and configure Android environment BEFORE any other game imports
        from core import runtime_globals
        runtime_globals.APP_ROOT = os.getcwd()
        runtime_globals.IS_ANDROID = True
        
        # Update runtime resolution based on actual device screen size
        width, height = screen.get_size()
        runtime_globals.update_resolution_constants(width, height)
        
        # Now import game after environment is configured
        from vpet import VirtualPetGame
        game = VirtualPetGame()
        
        # Main game loop
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.handle_event(event)
            
            game.update()
            game.draw(screen, clock)
            pygame.display.flip()
            clock.tick(30)
        
        game.save()
        
    except Exception as e:
        # Show error screen with crash info
        import traceback
        font = pygame.font.Font(None, 32)
        
        error_lines = ["Oops, the game crashed!", "", str(e), ""]
        error_lines.extend(traceback.format_exc().split('\n'))
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = False
            
            screen.fill((120, 0, 0))  # Dark red background
            y = 10
            for line in error_lines[:25]:  # Show up to 25 lines
                text = font.render(line[:70], True, (255, 255, 255))
                screen.blit(text, (10, y))
                y += 28
            
            pygame.display.flip()
            clock = pygame.time.Clock()
            clock.tick(30)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
