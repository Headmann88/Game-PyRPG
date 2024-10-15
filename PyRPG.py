import pygame
import sys
import random
import time
import json
import os

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32
FPS = 60
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# New Item class
class Item:
    def __init__(self, name, effect, symbol, color):
        self.name = name
        self.effect = effect
        self.symbol = symbol
        self.color = color

    def use(self, character):
        if self.effect == 'heal':
            heal_amount = 20
            character.health = min(character.health + heal_amount, 100)
            print(f"{character.__class__.__name__} used {self.name} and healed for {heal_amount} HP.")
        # Add more effects as needed

# New Inventory class
class Inventory:
    def __init__(self, size=8):
        self.items = [None] * size
        self.size = size

    def add_item(self, item):
        for i in range(self.size):
            if self.items[i] is None:
                self.items[i] = item
                return True
        return False  # Inventory is full

    def remove_item(self, index):
        if 0 <= index < self.size and self.items[index]:
            item = self.items[index]
            self.items[index] = None
            return item
        return None

    def get_item_by_name(self, name):
        for item in self.items:
            if item and item.name.lower() == name.lower():
                return item
        return None

# Update Character class to include inventory
class Character:
    def __init__(self, pos, health):
        self.pos = list(pos)
        self.health = health
        self.inventory = Inventory()

    def move(self, direction, game_map):
        dx, dy = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}.get(direction, (0, 0))
        new_pos = [self.pos[0] + dx, self.pos[1] + dy]
        if self.is_valid_move(new_pos, game_map):
            self.pos = new_pos

    def is_valid_move(self, new_pos, game_map):
        x, y = new_pos
        return (0 <= x < len(game_map[0]) and 
                0 <= y < len(game_map) and 
                game_map[y][x] != 'W')

    def use_item(self, item_name):
        item = self.inventory.get_item_by_name(item_name)
        if item:
            index = self.inventory.items.index(item)
            self.inventory.remove_item(index)
            item.use(self)
        else:
            print(f"{self.__class__.__name__} doesn't have {item_name}.")

# Update Player class
class Player(Character):
    def __init__(self, start_pos):
        super().__init__(start_pos, health=100)
        self.level = 1
        self.exp = 0
        self.exp_next_level = 100

# Update Enemy class
class Enemy(Character):
    def __init__(self, name, pos):
        super().__init__(pos, health=20)
        self.name = name

    def random_move(self, game_map):
        direction = random.choice(['left', 'right', 'up', 'down'])
        self.move(direction, game_map)

# Update Game class
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyRPG 1.4')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.maps = self.load_maps()
        self.current_map_index = 0
        self.game_map = self.maps[self.current_map_index]['layout']
        self.items_on_map = []
        self.load_items()
        self.player = Player(self.find_player_start())
        self.enemies = self.create_enemies()

        self.running = True
        self.game_started = False
        self.in_battle = False
        self.current_enemy = None
        self.battle_options = ["Attack", "Defend", "Run"]
        self.selected_option = 0
        self.battle_messages = []
        self.encounter_message = None
        self.encounter_message_time = 0
        self.player_dead = False
        self.show_inventory = False

    def load_maps(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        maps_path = os.path.join(script_dir, 'maps.json')
        try:
            with open(maps_path, 'r') as f:
                data = json.load(f)
                maps = data['maps']
                for map_data in maps:
                    map_data['layout'] = [list(row) for row in map_data['layout']]
                return maps
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading maps: {e}")
            sys.exit(1)

    def find_player_start(self):
        for y, row in enumerate(self.game_map):
            if 'P' in row:
                return [row.index('P'), y]
        return [1, 1]  # Default position if 'P' is not found

    def create_enemies(self):
        return [Enemy("Goblin", (x, y)) 
                for y, row in enumerate(self.game_map) 
                for x, cell in enumerate(row) if cell == 'g']

    def load_items(self):
        self.items_on_map = []
        for y, row in enumerate(self.game_map):
            for x, cell in enumerate(row):
                if cell == 'H':
                    item = Item("Health Potion", "heal", 'H', RED)
                    self.items_on_map.append((item, (x, y)))
                    self.game_map[y][x] = ' '

    def render_map(self):
        map_width = len(self.game_map[0]) * TILE_SIZE
        map_height = len(self.game_map) * TILE_SIZE
        start_x = (SCREEN_WIDTH - map_width) // 2
        start_y = (SCREEN_HEIGHT - map_height) // 2

        for y, row in enumerate(self.game_map):
            for x, cell in enumerate(row):
                color = {
                    'W': (128, 128, 128),
                    'D': (139, 69, 19),
                }.get(cell, BLACK)
                pygame.draw.rect(self.screen, color, 
                                 (start_x + x * TILE_SIZE, start_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Render player
        pygame.draw.rect(self.screen, RED, 
                         (start_x + self.player.pos[0] * TILE_SIZE, 
                          start_y + self.player.pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Render enemies
        for enemy in self.enemies:
            pygame.draw.rect(self.screen, GREEN, 
                             (start_x + enemy.pos[0] * TILE_SIZE, 
                              start_y + enemy.pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Render items
        for item, pos in self.items_on_map:
            x, y = pos
            pygame.draw.rect(self.screen, item.color, 
                             (start_x + x * TILE_SIZE, 
                              start_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def render_battle_screen(self):
        self.screen.fill(BLACK)
        player_text = self.font.render(f"Player (HP: {self.player.health})", True, WHITE)
        enemy_text = self.font.render(f"{self.current_enemy.name} (HP: {self.current_enemy.health})", True, RED)
        self.screen.blit(player_text, (50, 50))
        self.screen.blit(enemy_text, (SCREEN_WIDTH - 250, 50))

        for i, option in enumerate(self.battle_options):
            color = YELLOW if i == self.selected_option else WHITE
            option_text = self.font.render(option, True, color)
            self.screen.blit(option_text, (50, 300 + i * 50))

        for i, message in enumerate(self.battle_messages[-5:]):
            message_text = self.small_font.render(message, True, (200, 200, 200))
            self.screen.blit(message_text, (50, SCREEN_HEIGHT - 150 + i * 30))

        if self.encounter_message:
            current_time = time.time()
            if current_time - self.encounter_message_time < 2:
                alpha = int(255 * (1 - (current_time - self.encounter_message_time) / 2))
                encounter_text = self.font.render(self.encounter_message, True, WHITE)
                encounter_text.set_alpha(alpha)
                text_rect = encounter_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
                self.screen.blit(encounter_text, text_rect)
            else:
                self.encounter_message = None

    def render_inventory(self):
        inventory_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        inventory_surface.set_alpha(200)
        inventory_surface.fill(BLACK)
        self.screen.blit(inventory_surface, (0, 0))

        start_x = (SCREEN_WIDTH - (4 * TILE_SIZE + 3 * 10)) // 2
        start_y = (SCREEN_HEIGHT - (2 * TILE_SIZE + 10)) // 2

        for i in range(8):
            x = start_x + (i % 4) * (TILE_SIZE + 10)
            y = start_y + (i // 4) * (TILE_SIZE + 10)
            pygame.draw.rect(self.screen, WHITE, (x, y, TILE_SIZE, TILE_SIZE), 2)
            
            item = self.player.inventory.items[i]
            if item:
                pygame.draw.rect(self.screen, item.color, (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                text = self.small_font.render(item.symbol, True, WHITE)
                text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                self.screen.blit(text, text_rect)

        inventory_text = self.font.render("Inventory", True, WHITE)
        self.screen.blit(inventory_text, (SCREEN_WIDTH // 2 - inventory_text.get_width() // 2, start_y - 50))

    def handle_battle_input(self, event):
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.battle_options)
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.battle_options)
        elif event.key == pygame.K_RETURN:
            action = self.battle_options[self.selected_option]
            if action == "Attack":
                self.battle_attack()
            elif action == "Defend":
                self.battle_defend()
            elif action == "Run":
                self.battle_run()

    def battle_attack(self):
        player_damage = random.randint(5, 15)
        self.current_enemy.health -= player_damage
        self.battle_messages.append(f"You dealt {player_damage} damage to {self.current_enemy.name}!")
        
        if self.current_enemy.health <= 0:
            self.battle_messages.append(f"You defeated the {self.current_enemy.name}!")
            self.enemies.remove(self.current_enemy)
            self.game_map[self.current_enemy.pos[1]][self.current_enemy.pos[0]] = ' '
            self.in_battle = False
            self.current_enemy = None
        else:
            self.enemy_attack()

    def battle_defend(self):
        self.battle_messages.append("You defended against the enemy's attack!")
        self.enemy_attack(damage_reduction=True)

    def battle_run(self):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)
        for dx, dy in directions:
            new_x, new_y = self.player.pos[0] + dx, self.player.pos[1] + dy
            if self.player.is_valid_move([new_x, new_y], self.game_map):
                self.player.pos = [new_x, new_y]
                self.encounter_message = "You successfully ran away!"
                self.encounter_message_time = time.time()
                self.in_battle = False
                self.current_enemy = None
                return
        self.battle_messages.append("You couldn't find a way to escape!")
        self.enemy_attack()

    def enemy_attack(self, damage_reduction=False):
        enemy_damage = random.randint(3, 10)
        if damage_reduction:
            enemy_damage = max(1, enemy_damage // 2)
        self.player.health -= enemy_damage
        self.battle_messages.append(f"{self.current_enemy.name} dealt {enemy_damage} damage to you!")
        
        if self.player.health <= 0:
            self.player_dead = True
            self.in_battle = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.game_started = True
                if event.key == pygame.K_q:
                    self.running = False
                if event.key == pygame.K_i:
                    self.show_inventory = not self.show_inventory
                if self.game_started:
                    if self.in_battle:
                        self.handle_battle_input(event)
                    else:
                        self.handle_movement(event)
                        if event.key == pygame.K_u:
                            self.player.use_item("Health Potion")

        if self.game_started and not self.in_battle:
            self.check_for_encounter()
            self.check_for_map_transition()

    def handle_movement(self, event):
        direction = {
            pygame.K_LEFT: 'left',
            pygame.K_RIGHT: 'right',
            pygame.K_UP: 'up',
            pygame.K_DOWN: 'down'
        }.get(event.key)
        
        if direction:
            self.player.move(direction, self.game_map)
            self.check_for_item_pickup()
            for enemy in self.enemies:
                enemy.random_move(self.game_map)

    def check_for_encounter(self):
        for enemy in self.enemies:
            if self.player.pos == enemy.pos:
                self.encounter_message = f"You encountered a {enemy.name}!"
                self.encounter_message_time = time.time()
                self.in_battle = True
                self.current_enemy = enemy
                self.selected_option = 0
                break

    def check_for_map_transition(self):
        x, y = self.player.pos
        if self.game_map[y][x] == 'D':
            self.transition_to_next_map()

    def transition_to_next_map(self):
        self.current_map_index = (self.current_map_index + 1) % len(self.maps)
        self.game_map = self.maps[self.current_map_index]['layout']
        self.player.pos = self.find_player_start()
        self.enemies = self.create_enemies()
        self.load_items()

    def check_for_item_pickup(self):
        for item, pos in self.items_on_map[:]:
            if tuple(self.player.pos) == pos:
                if self.player.inventory.add_item(item):
                    self.items_on_map.remove((item, pos))
                    print(f"Picked up {item.name}")
                else:
                    print("Inventory is full")

    def run(self):
        while self.running:
            self.handle_events()
            self.screen.fill(BLACK)
            
            if not self.game_started:
                self.render_start_screen()
            elif self.in_battle:
                self.render_battle_screen()
            elif self.player_dead:
                self.render_death_screen()
            else:
                self.render_map()
                if self.show_inventory:
                    self.render_inventory()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def render_start_screen(self):
        title_text = self.font.render("Welcome to PyRPG", True, WHITE)
        start_text = self.small_font.render("Press ENTER to start", True, WHITE)
        self.screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)))
        self.screen.blit(start_text, start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3)))

    def render_death_screen(self):
        death_text = self.font.render("You Died", True, RED)
        restart_text = self.small_font.render("Press R to restart", True, WHITE)
        self.screen.blit(death_text, death_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)))
        self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3)))

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()

    def reset_game(self):
        self.current_map_index = 0
        self.game_map = self.maps[self.current_map_index]['layout']
        self.player = Player(self.find_player_start())
        self.enemies = self.create_enemies()
        self.load_items()
        self.player_dead = False
        self.in_battle = False
        self.current_enemy = None
        self.battle_messages = []
        self.game_started = False

if __name__ == '__main__':
    game = Game()
    game.run()
