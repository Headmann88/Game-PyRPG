import pygame
import sys
import random
import time

class Character:
    def __init__(self, pos, health):
        self.pos = list(pos)
        self.health = health

    def move(self, direction, game_map):
        new_pos = self.pos.copy()
        if direction == 'left':
            new_pos[0] -= 1
        elif direction == 'right':
            new_pos[0] += 1
        elif direction == 'up':
            new_pos[1] -= 1
        elif direction == 'down':
            new_pos[1] += 1

        if self.is_valid_move(new_pos, game_map):
            self.pos = new_pos

    def is_valid_move(self, new_pos, game_map):
        return (0 <= new_pos[0] < len(game_map[0]) and 
                0 <= new_pos[1] < len(game_map) and 
                game_map[new_pos[1]][new_pos[0]] != 'W')


class Player(Character):
    def __init__(self, start_pos):
        super().__init__(start_pos, health=100)
        self.inventory = []
        self.level = 1
        self.exp = 0
        self.exp_next_level = 100


class Enemy(Character):
    def __init__(self, name, pos):
        super().__init__(pos, health=20)
        self.name = name

    def random_move(self, game_map):
        directions = ['left', 'right', 'up', 'down']
        direction = random.choice(directions)
        self.move(direction, game_map)


class Game:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('PyRPG 1.4')
        self.clock = pygame.time.Clock()
        self.tile_width = 32
        self.tile_height = 32
        self.maps = [
            [
                ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
                ['W', 'P', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'D', 'W', 'W']
            ],
            [
                ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
                ['W', 'P', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', 'W', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', 'W', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 'W'],
                ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W']
            ]
        ]
        self.current_map_index = 0
        self.game_map = self.maps[self.current_map_index]
        self.player = Player(self.find_player_start())
        self.enemies = self.create_enemies()
        self.running = True
        self.enemy_move_counter = 0
        self.enemy_move_delay = 2
        self.in_battle = False
        self.current_enemy = None
        self.battle_options = ["Attack", "Defend", "Run"]
        self.selected_option = 0
        self.game_started = False
        self.start_screen = self.create_start_screen()
        self.battle_screen = self.create_battle_screen()
        self.battle_messages = []
        self.max_battle_messages = 5
        self.encounter_message = None
        self.encounter_message_time = 0

    def find_player_start(self):
        for y, row in enumerate(self.game_map):
            for x, tile in enumerate(row):
                if tile == 'P':
                    return [x, y]
        return [1, 1]  # Default position if 'P' is not found

    def create_enemies(self):
        enemies = []
        empty_spaces = []

        # Find all empty spaces on the map
        for y, row in enumerate(self.game_map):
            for x, tile in enumerate(row):
                if tile == ' ':
                    empty_spaces.append((x, y))

        # If there are empty spaces, spawn one enemy
        if empty_spaces:
            enemy_pos = random.choice(empty_spaces)
            enemy = Enemy("Goblin", enemy_pos)
            enemies.append(enemy)

        return enemies

    def render_map(self):
        map_width = len(self.game_map[0]) * self.tile_width
        map_height = len(self.game_map) * self.tile_height
        start_x = (self.screen_width - map_width) // 2
        start_y = (self.screen_height - map_height) // 2

        for y, row in enumerate(self.game_map):
            for x, tile in enumerate(row):
                tile_x = start_x + x * self.tile_width
                tile_y = start_y + y * self.tile_height
                if tile == 'W':
                    pygame.draw.rect(self.screen, (128, 128, 128), (tile_x, tile_y, self.tile_width, self.tile_height))
                elif tile == 'D':
                    pygame.draw.rect(self.screen, (139, 69, 19), (tile_x, tile_y, self.tile_width, self.tile_height))
                else:
                    pygame.draw.rect(self.screen, (0, 0, 0), (tile_x, tile_y, self.tile_width, self.tile_height))

        self.render_player(start_x, start_y)
        self.render_enemies(start_x, start_y)

    def render_player(self, start_x, start_y):
        tile_x = start_x + self.player.pos[0] * self.tile_width
        tile_y = start_y + self.player.pos[1] * self.tile_height
        pygame.draw.rect(self.screen, (255, 0, 0), (tile_x, tile_y, self.tile_width, self.tile_height))

    def render_enemies(self, start_x, start_y):
        for enemy in self.enemies:
            tile_x = start_x + enemy.pos[0] * self.tile_width
            tile_y = start_y + enemy.pos[1] * self.tile_height
            pygame.draw.rect(self.screen, (0, 255, 0), (tile_x, tile_y, self.tile_width, self.tile_height))

    def create_start_screen(self):
        start_screen = pygame.Surface((self.screen_width, self.screen_height))
        start_screen.fill((0, 0, 0))
        font_large = pygame.font.Font(None, 72)
        font_small = pygame.font.Font(None, 36)
        title_text = font_large.render("Welcome to PyRPG", True, (255, 255, 255))
        start_text = font_small.render("Press ENTER to start", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 3))
        start_rect = start_text.get_rect(center=(self.screen_width // 2, self.screen_height * 2 // 3))
        start_screen.blit(title_text, title_rect)
        start_screen.blit(start_text, start_rect)
        return start_screen

    def create_battle_screen(self):
        battle_screen = pygame.Surface((self.screen_width, self.screen_height))
        battle_screen.fill((0, 0, 0))
        return battle_screen

    def render_battle_screen(self):
        self.screen.blit(self.create_battle_screen(), (0, 0))
        font = pygame.font.Font(None, 36)
        
        # Render player and enemy
        player_text = font.render(f"Player (HP: {self.player.health})", True, (255, 255, 255))
        enemy_text = font.render(f"{self.current_enemy.name} (HP: {self.current_enemy.health})", True, (255, 0, 0))
        self.screen.blit(player_text, (50, 50))
        self.screen.blit(enemy_text, (self.screen_width - 250, 50))

        # Render battle options
        for i, option in enumerate(self.battle_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            option_text = font.render(option, True, color)
            self.screen.blit(option_text, (50, 300 + i * 50))

        # Render battle messages
        message_font = pygame.font.Font(None, 24)
        for i, message in enumerate(self.battle_messages[-self.max_battle_messages:]):
            message_text = message_font.render(message, True, (200, 200, 200))
            self.screen.blit(message_text, (50, self.screen_height - 150 + i * 30))

        # Render encounter message
        if self.encounter_message:
            current_time = time.time()
            if current_time - self.encounter_message_time < 2:
                alpha = int(255 * (1 - (current_time - self.encounter_message_time) / 2))
                encounter_font = pygame.font.Font(None, 48)
                encounter_text = encounter_font.render(self.encounter_message, True, (255, 255, 255))
                encounter_text.set_alpha(alpha)
                text_rect = encounter_text.get_rect(center=(self.screen_width // 2, 100))
                self.screen.blit(encounter_text, text_rect)
            else:
                self.encounter_message = None

    def add_battle_message(self, message):
        self.battle_messages.append(message)
        if len(self.battle_messages) > self.max_battle_messages:
            self.battle_messages.pop(0)

    def try_run_away(self):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # left, right, up, down
        random.shuffle(directions)  # Randomize directions to try

        for dx, dy in directions:
            new_x, new_y = self.player.pos[0] + dx, self.player.pos[1] + dy
            if self.player.is_valid_move([new_x, new_y], self.game_map):
                self.player.pos = [new_x, new_y]
                self.encounter_message = "You successfully ran away!"
                self.encounter_message_time = time.time()
                self.in_battle = False
                self.current_enemy = None
                return True

        self.add_battle_message("You couldn't find a way to escape!")
        return False

    def handle_battle_input(self, event):
        if event.key == pygame.K_UP:
            self.selected_option = (self.selected_option - 1) % len(self.battle_options)
        elif event.key == pygame.K_DOWN:
            self.selected_option = (self.selected_option + 1) % len(self.battle_options)
        elif event.key == pygame.K_RETURN:
            if self.battle_options[self.selected_option] == "Attack":
                damage = random.randint(5, 15)
                self.current_enemy.health -= damage
                self.add_battle_message(f"You dealt {damage} damage to {self.current_enemy.name}!")
            elif self.battle_options[self.selected_option] == "Defend":
                self.add_battle_message("You defended against the enemy's attack!")
            elif self.battle_options[self.selected_option] == "Run":
                if self.try_run_away():
                    return  # Return here to prevent further processing if running away

            if self.current_enemy and self.current_enemy.health <= 0:
                self.add_battle_message(f"You defeated the {self.current_enemy.name}!")
                self.enemies.remove(self.current_enemy)
                self.in_battle = False
                self.current_enemy = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.game_started = True
                if event.key == pygame.K_q:
                    self.running = False
                if self.game_started:
                    if self.in_battle:
                        self.handle_battle_input(event)
                    else:
                        if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                            if event.key == pygame.K_LEFT:
                                self.player.move('left', self.game_map)
                            elif event.key == pygame.K_RIGHT:
                                self.player.move('right', self.game_map)
                            elif event.key == pygame.K_UP:
                                self.player.move('up', self.game_map)
                            elif event.key == pygame.K_DOWN:
                                self.player.move('down', self.game_map)
                            
                            self.enemy_move_counter += 1
                            if self.enemy_move_counter >= self.enemy_move_delay:
                                self.enemy_move_counter = 0
                                for enemy in self.enemies:
                                    enemy.random_move(self.game_map)

        # Check for player-enemy collision
        if self.game_started and not self.in_battle:
            for enemy in self.enemies:
                if self.player.pos == enemy.pos:
                    self.encounter_message = f"You encountered a {enemy.name}!"
                    self.encounter_message_time = time.time()
                    self.in_battle = True
                    self.current_enemy = enemy
                    self.selected_option = 0

        # Check for map transition
        if self.game_started and not self.in_battle:
            x, y = self.player.pos
            if self.game_map[y][x] == 'D':
                self.transition_to_next_map()

    def transition_to_next_map(self):
        self.current_map_index = (self.current_map_index + 1) % len(self.maps)
        self.game_map = self.maps[self.current_map_index]
        self.player.pos = self.find_player_start()
        self.enemies = self.create_enemies()

    def run(self):
        while self.running:
            self.handle_events()
            
            if not self.game_started:
                self.screen.blit(self.start_screen, (0, 0))
            elif self.in_battle:
                self.render_battle_screen()
            else:
                self.screen.fill((0, 0, 0))
                self.render_map()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# Initialize and start the game
if __name__ == '__main__':
    game = Game()
    game.run()
