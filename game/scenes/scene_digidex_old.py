import os
import random
import pygame

from components.window_petselector import WindowPetSelector
from core import runtime_globals
import core.constants as constants
from core.game_digidex import is_pet_unlocked, load_digidex
from core.game_digidex_entry import GameDigidexEntry
from core.utils.module_utils import get_module
from core.utils.pygame_utils import blit_with_shadow, get_font, sprite_load_percent
from core.utils.scene_utils import change_scene
from core.utils.sprite_utils import load_pet_sprites
from core.utils.utils_unlocks import unlock_item

UNKNOWN_SPRITE_PATH = constants.UNKNOWN_SPRITE_PATH
SPRITE_BUFFER = 10 
SPRITE_FRAME = "0.png"
SPRITE_SIZE = int(48 * constants.UI_SCALE)

class SceneDigidex:
    def __init__(self):
        self.font = get_font(int(14 * constants.UI_SCALE))
        # Use new method for unknown sprite and scale
        self.unknown_sprite = sprite_load_percent(
            UNKNOWN_SPRITE_PATH, 
            percent=(SPRITE_SIZE / constants.SCREEN_HEIGHT) * 100, 
            keep_proportion=True, 
            base_on="height"
        )
        self.digidex_data = load_digidex()
        self.pets = self.build_pet_list()
        self.selector = WindowPetSelector()
        self.selector.pets = self.pets
        self.state = "menu"
        self.tree_root = None
        self.tree_data = {}
        self.tree_node_pos = {}
        self.tree_node_grid = {}
        self.tree_color_map = {}

        # Use new method for background, scale to screen height
        if constants.SCREEN_WIDTH > constants.SCREEN_HEIGHT:
            self.bg_sprite = sprite_load_percent(
                constants.DIGIDEX_BACKGROUND_PATH, 
                percent=600, 
                keep_proportion=True, 
                base_on="width"
            )
        else:
            self.bg_sprite = sprite_load_percent(
                constants.DIGIDEX_BACKGROUND_PATH, 
                percent=100, 
                keep_proportion=True, 
                base_on="height"
            )
        self.bg_frame = 0
        self.bg_timer = 0
        self.bg_frame_width = self.bg_sprite.get_width() // 6  # 326

        self._cache_surface = None
        self._cache_key = None
        self.update_sprite_cache()

    def build_pet_list(self):
        all_entries = []
        known_count_by_module = {}  # Track known pets per module
        
        for module in runtime_globals.game_modules.values():
            monsters = module.get_all_monsters()
            module_known_count = 0

            for monster in monsters:
                name = monster["name"]
                version = monster["version"]
                attribute = monster["attribute"]
                stage = monster["stage"]
                name_format = module.name_format
                known = is_pet_unlocked(name, module.name, version)

                if not known:
                    name = "????"
                    attribute = "???"
                    sprite = self.unknown_sprite
                else:
                    module_known_count += 1
                    sprite = None
                entry = GameDigidexEntry(name, attribute, stage, module.name, version, sprite, known, name_format)
                all_entries.append(entry)
            
            known_count_by_module[module.name] = module_known_count

        # Generic unlock logic for digidex unlocks - per module
        for module in runtime_globals.game_modules.values():
            unlocks = getattr(module, "unlocks", [])
            if isinstance(unlocks, list):
                module_known_count = known_count_by_module.get(module.name, 0)
                for unlock in unlocks:
                    if unlock.get("type") == "digidex" and "amount" in unlock:
                        if module_known_count >= unlock["amount"]:
                            unlock_item(module.name, "digidex", unlock["name"])

        # Ordena: estágio, nome do módulo, versão
        all_entries.sort(key=lambda e: (e.stage, e.module.lower(), e.version))
        return all_entries

    def update_sprite_cache(self):
        """
        Garante que apenas os sprites visíveis (e próximos) estejam carregados na memória.
        Atualiza os frames diretamente nos objetos self.pets[i].frames[0].
        """
        center = self.selector.selected_index
        min_index = max(0, center - SPRITE_BUFFER)
        max_index = min(len(self.pets), center + SPRITE_BUFFER + 1)

        for i, pet in enumerate(self.pets):
            if i < min_index or i >= max_index:
                # Fora da janela → descarrega sprite
                if pet.sprite:
                    pet.sprite = None
            else:
                # Dentro da janela → carrega sprite se necessário
                if not pet.sprite:
                    try:
                        module = get_module(pet.module)
                        module_path = f"modules/{module.name}"
                        
                        # Use the new sprite utilities to load pet sprites with fallback support
                        sprites_dict = load_pet_sprites(
                            pet.name, 
                            module_path, 
                            module.name_format,
                            module_high_definition_sprites=module.high_definition_sprites,
                            size=(SPRITE_SIZE, SPRITE_SIZE)
                        )
                        
                        # Get the first frame (0.png)
                        if "0" in sprites_dict:
                            pet.sprite = sprites_dict["0"]
                        else:
                            pet.sprite = self.unknown_sprite
                            
                    except Exception as e:
                        runtime_globals.game_console.log(f"[Digidex] Failed to load sprite for {pet.name}: {e}")
                        pet.sprite = self.unknown_sprite

    def update(self):
        if self.state == "menu":
            self.update_sprite_cache()
        elif self.state == "tree":
            self.update_visible_tree_sprites()
        
        self.bg_timer += 1
        if self.bg_timer >= 3 * (constants.FRAME_RATE / 30):
            self.bg_timer = 0
            self.bg_frame = (self.bg_frame + 1) % 6

    def draw(self, surface: pygame.Surface):
        # Always draw animated background first
        frame_rect = pygame.Rect(
            self.bg_frame * self.bg_frame_width, 
            0, 
            self.bg_frame_width, 
            constants.SCREEN_HEIGHT
        )
        surface.blit(self.bg_sprite, (0, 0), frame_rect)

        # Compose cache key based on state
        if self.state == "menu":
            cache_key = (
                "menu",
                self.selector.selected_index,
                tuple(pet.name for pet in self.pets),
            )
        elif self.state == "tree":
            # Use tree_root and tree_cursor for cache key
            cache_key = (
                "tree",
                getattr(self.tree_root, "name", None),
                getattr(self.tree_root, "module", None),
                getattr(self.tree_root, "version", None),
                getattr(self, "tree_cursor", (0, 0)),
            )
        else:
            cache_key = ("other",)

        # Only redraw if cache key changes or cache is empty
        if cache_key != self._cache_key or self._cache_surface is None:
            cache_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            if self.state == "menu":
                self.selector.draw(cache_surface)
            elif self.state == "tree":
                self.draw_tree(cache_surface)
            self._cache_surface = cache_surface
            self._cache_key = cache_key

        # Blit cached scene (menu or tree) over the background
        surface.blit(self._cache_surface, (0, 0))

    def handle_event(self, input_action):
        """
        Handles key inputs and GPIO button presses for navigating menus and evolution trees.
        """

        if self.state == "menu":
            if self.selector.handle_event(input_action):  # Handle selection input
                selected = self.selector.get_selected_pet()
                if selected.known:
                    self.tree_root = self.find_stage_zero_entry(selected)
                    self.tree_data = self.load_evolution_tree(selected)

                    # Preprocess the tree layout to get positions
                    self._build_tree_layout()

                    # Safely set the cursor position
                    self.tree_cursor = self.tree_node_pos.get(self.tree_root.name, (0, 0))
                    self.state = "tree"

            elif input_action == "B":  
                change_scene("game")

        elif self.state == "tree":
            if input_action == "B":  # Escape (Cancel/Menu)
                runtime_globals.game_sound.play("cancel")
                self.state = "menu"
            elif input_action:  # Handle navigation within tree
                runtime_globals.game_sound.play("menu")
                self.navigate_tree(input_action)

    def find_stage_zero_entry(self, pet):
        for entry in self.pets:
            if entry.module == pet.module and entry.version == pet.version and entry.stage == 0:
                return entry
        return pet 

    def navigate_tree(self, key):
        if not hasattr(self, "tree_cursor"):
            self.tree_cursor = (0, 0)

        dx, dy = 0, 0
        if key == "LEFT":
            dx = -1
        elif key == "RIGHT":
            dx = 1
        elif key == "UP":
            dy = -1
        elif key == "DOWN":
            dy = 1

        self.tree_cursor = (self.tree_cursor[0] + dx, self.tree_cursor[1] + dy)
        runtime_globals.game_console.log(f"Cursor moved to {self.tree_cursor}")

    def update_visible_tree_sprites(self):
        """
        Garante que os sprites dos pets visíveis na árvore estejam carregados.
        """
        visible_names = set(self.tree_node_pos.keys() if self.state == "tree" else [])

        for pet in self.pets:
            if pet.name in visible_names and not pet.sprite and pet.known:
                try:
                    module = get_module(pet.module)
                    module_path = f"modules/{module.name}"
                    
                    # Use the new sprite utilities to load pet sprites with fallback support
                    sprites_dict = load_pet_sprites(
                        pet.name, 
                        module_path, 
                        module.name_format,
                        module_high_definition_sprites=module.high_definition_sprites,
                        size=(SPRITE_SIZE, SPRITE_SIZE)
                    )
                    
                    # Get the first frame (0.png)
                    if "0" in sprites_dict:
                        pet.sprite = sprites_dict["0"]
                    else:
                        pet.sprite = self.unknown_sprite
                        
                except Exception as e:
                    runtime_globals.game_console.log(f"[Digidex] Failed to load sprite for {pet.name}: {e}")
                    pet.sprite = self.unknown_sprite
            elif pet.name not in visible_names and pet.sprite:
                pet.sprite = None

    def draw_tree(self, surface: pygame.Surface):
        if not self.tree_data or not self.tree_root:
            return

        self.tree_node_grid = {}
        self.tree_node_pos = {}

        stages = {}
        queue = [(self.tree_root.name, 0)]
        visited = set()

        while queue:
            current, depth = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            stages.setdefault(depth, []).append(current)
            for child in self.tree_data.get(current, []):
                queue.append((child, depth + 1))

        sprite_size = SPRITE_SIZE
        vertical_spacing = int(100 * constants.UI_SCALE)
        horizontal_spacing = int(80 * constants.UI_SCALE)

        if not hasattr(self, "tree_cursor"):
            self.tree_cursor = (0, 0)

        offset_x = constants.SCREEN_WIDTH // 2 - self.tree_cursor[0] * horizontal_spacing
        offset_y = constants.SCREEN_HEIGHT // 2 - self.tree_cursor[1] * vertical_spacing

        max_line_length = max(len(names) for names in stages.values())

        # 1. Salvar posições
        for y_idx, names in stages.items():
            line_width = (len(names) - 1) * horizontal_spacing
            total_width = (max_line_length - 1) * horizontal_spacing

            for x_idx, name in enumerate(names):
                px = x_idx
                py = y_idx
                self.tree_node_grid[(px, py)] = name
                self.tree_node_pos[name] = (px, py)

        # 2. Desenhar linhas entre nós (com a cor do nó de origem)
        for (x_idx, y_idx), name in self.tree_node_grid.items():
            children = self.tree_data.get(name, [])
            line = stages[y_idx]
            line_width = (len(line) - 1) * horizontal_spacing
            total_width = (max_line_length - 1) * horizontal_spacing
            center_adjust = (total_width - line_width) // 2

            px1 = x_idx * horizontal_spacing + offset_x + center_adjust + sprite_size // 2
            py1 = y_idx * vertical_spacing + offset_y + sprite_size // 2

            if y_idx < 3:
                color = pygame.Color(0, 128, 255)
            elif (x_idx, y_idx) in self.tree_color_map:
                color = self.tree_color_map[(x_idx, y_idx)]
            else:
                color = (random.randint(80,255), random.randint(80,255), random.randint(80,255))
                self.tree_color_map[x_idx, y_idx] = color

            for child_name in children:
                child_pos = next((k for k, v in self.tree_node_grid.items() if v == child_name), None)
                if not child_pos:
                    continue

                child_x, child_y = child_pos
                child_line = stages[child_y]
                child_line_width = (len(child_line) - 1) * horizontal_spacing
                child_adjust = (total_width - child_line_width) // 2

                px2 = child_x * horizontal_spacing + offset_x + child_adjust + sprite_size // 2
                py2 = child_y * vertical_spacing + offset_y + sprite_size // 2

                pygame.draw.line(surface, color, (px1, py1), (px2, py2), int(3 * constants.UI_SCALE))

        # 3. Desenhar pets e nomes por cima
        attr_colors = {
            "Da": (66, 165, 245),
            "Va": (102, 187, 106),
            "Vi": (237, 83, 80),
            "": (171, 71, 188),
            "???": (0, 0, 0)
        }
        center_adjust_by_row = {}
        for y_idx, names in stages.items():
            line_width = (len(names) - 1) * horizontal_spacing
            total_width = (max_line_length - 1) * horizontal_spacing
            center_adjust_by_row[y_idx] = (total_width - line_width) // 2

        for name, (px, py) in self.tree_node_pos.items():
            pet = self.get_entry_by_name(name)
            sprite = pet.sprite if pet and pet.sprite else self.unknown_sprite
            color = attr_colors.get(pet.attribute if pet else "???", (150, 150, 150))
            
            if py < 3:
                color2 = pygame.Color(0, 128, 255)
            elif (px, py) in self.tree_color_map:
                color2 = self.tree_color_map[(px, py)]
            else:
                color2 = (random.randint(80,255), random.randint(80,255), random.randint(80,255))
                self.tree_color_map[px, py] = color2

            center_adjust = center_adjust_by_row[py]
            screen_x = px * horizontal_spacing + offset_x + center_adjust
            screen_y = py * vertical_spacing + offset_y

            # Caixa de fundo
            pygame.draw.rect(
                surface, color, 
                (screen_x - int(4 * constants.UI_SCALE), screen_y - int(4 * constants.UI_SCALE), sprite_size + int(8 * constants.UI_SCALE), sprite_size + int(8 * constants.UI_SCALE))
            )
            surface.blit(sprite, (screen_x, screen_y))
            sprite_rect = pygame.Rect(
                screen_x - int(4 * constants.UI_SCALE), 
                screen_y - int(4 * constants.UI_SCALE), 
                sprite_size + int(8 * constants.UI_SCALE), 
                sprite_size + int(8 * constants.UI_SCALE)
            )
            pygame.draw.rect(surface, color2, sprite_rect, int(2 * constants.UI_SCALE))

            if pet and pet.known:
                label = self.font.render(pet.name, True, color)
                blit_with_shadow(surface, label, (screen_x, screen_y + sprite_size + int(2 * constants.UI_SCALE)))

    def load_evolution_tree(self, root_entry):
        """
        Carrega a árvore de evolução completa do pet (por módulo e versão).
        Retorna um dicionário onde cada chave é o nome do pet e o valor é uma lista de nomes dos filhos.
        """
        module = next((m for m in runtime_globals.game_modules.values() if m.name == root_entry.module), None)
        if not module:
            runtime_globals.game_console.log(f"[Digidex] Módulo '{root_entry.module}' não encontrado.")
            return {}

        tree = {}
        monsters = module.get_all_monsters()
        monsters = [m for m in monsters if m["version"] == root_entry.version]

        # Indexa os monstros por nome
        valid_names = {m["name"] for m in monsters}
        for monster in monsters:
            name = monster["name"]
            evolutions = monster.get("evolve", [])
            tree[name] = [evo["to"] for evo in evolutions if evo["to"] in valid_names]

        return tree
    
    def _build_tree_layout(self):
        """
        Gera self.tree_node_pos e self.tree_node_grid sem desenhar nada,
        usado para inicializar o cursor corretamente.
        """
        self.tree_node_grid = {}
        self.tree_node_pos = {}

        stages = {}
        queue = [(self.tree_root.name, 0)]
        visited = set()

        while queue:
            current, depth = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            stages.setdefault(depth, []).append(current)
            for child in self.tree_data.get(current, []):
                queue.append((child, depth + 1))

        max_line_length = max(len(names) for names in stages.values())
        for y_idx, names in stages.items():
            line_width = (len(names) - 1) * 1
            total_width = (max_line_length - 1)
            center_adjust = (total_width - line_width) // 2

            for x_idx, name in enumerate(names):
                px = x_idx + center_adjust
                py = y_idx
                self.tree_node_grid[(px, py)] = name
                self.tree_node_pos[name] = (px, py)

    def get_entry_by_name(self, name):
        for pet in self.pets:
            if pet.name == name and pet.module == self.tree_root.module and pet.version == self.tree_root.version:
                return pet
        return None
