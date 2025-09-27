"""
Color Picker Tool for Omnimon
Allows you to adjust RGB values for the 3-color theme system and see them in real-time
"""
import pygame
import sys
import json

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Omnimon Color Picker")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

# Fonts
font = pygame.font.Font(None, 24)
small_font = pygame.font.Font(None, 18)

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value(event.pos[0])
            
    def update_value(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        relative_x = max(0, min(relative_x, self.rect.width))
        ratio = relative_x / self.rect.width
        self.val = int(self.min_val + ratio * (self.max_val - self.min_val))
        
    def draw(self, surface):
        # Draw slider track
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Draw slider handle
        handle_x = self.rect.x + (self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 2, 10, self.rect.height + 4)
        pygame.draw.rect(surface, WHITE, handle_rect)
        pygame.draw.rect(surface, BLACK, handle_rect, 2)
        
        # Draw label and value
        label_text = small_font.render(f"{self.label}: {self.val}", True, BLACK)
        surface.blit(label_text, (self.rect.x, self.rect.y - 20))

class ColorPicker:
    def __init__(self):
        # Starting with current purple values
        self.colors = {
            'DARK': [53, 39, 57],     # PURPLE_DARK
            'NORMAL': [204, 82, 133], # PURPLE
            'LIGHT': [255, 238, 217]  # PURPLE_LIGHT
        }
        
        self.current_color = 'DARK'
        self.sliders = {}
        self.setup_sliders()
        
    def setup_sliders(self):
        # Create sliders for each color component
        y_start = 100
        slider_width = 200
        slider_height = 20
        
        for i, color_name in enumerate(['DARK', 'NORMAL', 'LIGHT']):
            x_base = 50 + i * 250
            y_base = y_start + i * 120
            
            self.sliders[f'{color_name}_R'] = Slider(
                x_base, y_base, slider_width, slider_height, 0, 255, 
                self.colors[color_name][0], f'{color_name} Red'
            )
            self.sliders[f'{color_name}_G'] = Slider(
                x_base, y_base + 40, slider_width, slider_height, 0, 255, 
                self.colors[color_name][1], f'{color_name} Green'
            )
            self.sliders[f'{color_name}_B'] = Slider(
                x_base, y_base + 80, slider_width, slider_height, 0, 255, 
                self.colors[color_name][2], f'{color_name} Blue'
            )
            
    def update_colors(self):
        for color_name in ['DARK', 'NORMAL', 'LIGHT']:
            self.colors[color_name][0] = self.sliders[f'{color_name}_R'].val
            self.colors[color_name][1] = self.sliders[f'{color_name}_G'].val
            self.colors[color_name][2] = self.sliders[f'{color_name}_B'].val
            
    def handle_event(self, event):
        for slider in self.sliders.values():
            slider.handle_event(event)
        self.update_colors()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.save_colors()
            elif event.key == pygame.K_c:
                self.copy_to_clipboard()
                
    def save_colors(self):
        """Save colors to a JSON file"""
        color_data = {
            'PURPLE_DARK': tuple(self.colors['DARK']),
            'PURPLE': tuple(self.colors['NORMAL']),
            'PURPLE_LIGHT': tuple(self.colors['LIGHT'])
        }
        
        with open('picked_colors.json', 'w') as f:
            json.dump(color_data, f, indent=2)
        print("Colors saved to picked_colors.json")
        
    def copy_to_clipboard(self):
        """Print color values in format ready for ui_constants.py"""
        output = f"""PURPLE_DARK = {tuple(self.colors['DARK'])}
PURPLE = {tuple(self.colors['NORMAL'])}
PURPLE_LIGHT = {tuple(self.colors['LIGHT'])}"""
        print("\nCopy these lines to ui_constants.py:")
        print("-" * 40)
        print(output)
        print("-" * 40)
        
    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title = font.render("Omnimon Color Picker - Adjust RGB values for theme colors", True, BLACK)
        surface.blit(title, (50, 20))
        
        # Instructions
        instructions = [
            "Adjust sliders to match your target colors",
            "Press 'S' to save colors to picked_colors.json",
            "Press 'C' to copy color values to console",
            "Press ESC to quit"
        ]
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, BLACK)
            surface.blit(text, (50, 50 + i * 15))
        
        # Draw color preview rectangles
        preview_y = 450
        preview_width = 200
        preview_height = 100
        
        for i, (color_name, color_values) in enumerate(self.colors.items()):
            x = 50 + i * 250
            
            # Draw color rectangle
            color_rect = pygame.Rect(x, preview_y, preview_width, preview_height)
            pygame.draw.rect(surface, tuple(color_values), color_rect)
            pygame.draw.rect(surface, BLACK, color_rect, 2)
            
            # Draw color name and RGB values
            name_text = font.render(color_name, True, BLACK)
            surface.blit(name_text, (x, preview_y - 30))
            
            rgb_text = small_font.render(f"RGB: {tuple(color_values)}", True, BLACK)
            surface.blit(rgb_text, (x, preview_y + preview_height + 5))
            
            # Draw hex value
            hex_color = "#{:02x}{:02x}{:02x}".format(*color_values)
            hex_text = small_font.render(f"HEX: {hex_color}", True, BLACK)
            surface.blit(hex_text, (x, preview_y + preview_height + 25))
        
        # Draw sliders
        for slider in self.sliders.values():
            slider.draw(surface)
            
        # Draw current RGB values on screen
        values_y = 380
        for i, (color_name, color_values) in enumerate(self.colors.items()):
            x = 50 + i * 250
            rgb_str = f"R:{color_values[0]} G:{color_values[1]} B:{color_values[2]}"
            values_text = small_font.render(rgb_str, True, BLACK)
            surface.blit(values_text, (x, values_y))

def main():
    clock = pygame.time.Clock()
    color_picker = ColorPicker()
    running = True
    
    print("Color Picker Started!")
    print("Use sliders to adjust RGB values")
    print("Press 'S' to save, 'C' to copy to console, ESC to quit")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            color_picker.handle_event(event)
        
        color_picker.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Print final colors when exiting
    color_picker.copy_to_clipboard()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
