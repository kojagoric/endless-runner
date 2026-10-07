import math
import pygame

from .player import Player
from .obstacle import Obstacle


WHITE = (255, 255, 255)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GRAY = (80, 80, 80)
LIGHT_GRAY = (220, 220, 220)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.difficulty = "Medium"

        self.sounds_enabled = True
        self._create_sounds()

        self.reset_game("Medium")

    def _create_tone(self, frequency, duration, volume=0.3):
        """Create a simple sound effect without external audio files."""
        sample_rate = 44100
        samples = int(sample_rate * duration)

        buffer = bytearray()

        for i in range(samples):
            envelope = 1.0 - (i / samples)
            value = int(
                32767
                * volume
                * envelope
                * math.sin(2 * math.pi * frequency * i / sample_rate)
            )

            buffer.extend(int(value).to_bytes(2, byteorder="little", signed=True))

        return pygame.mixer.Sound(buffer=bytes(buffer))

    def _create_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.jump_sound = self._create_tone(700, 0.12, 0.25)
            self.score_sound = self._create_tone(1000, 0.08, 0.20)
            self.game_over_sound = self._create_tone(180, 0.35, 0.30)

        except pygame.error:
            self.sounds_enabled = False

    def _play_sound(self, sound):
        if self.sounds_enabled:
            try:
                sound.play()
            except pygame.error:
                pass

    def reset_game(self, difficulty=None):
        if difficulty is not None:
            self.difficulty = difficulty

        settings = {
            "Easy": {
                "speed": 5.0,
                "max_speed": 8.0,
                "spawn_interval": 85,
            },
            "Medium": {
                "speed": 6.0,
                "max_speed": 10.0,
                "spawn_interval": 70,
            },
            "Hard": {
                "speed": 8.0,
                "max_speed": 13.0,
                "spawn_interval": 55,
            },
        }

        config = settings[self.difficulty]

        self.player = Player(80, self.ground_y)

        self.speed = config["speed"]
        self.max_speed = config["max_speed"]

        self.speed_increase_per_frame = 0.003

        self.spawn_interval = config["spawn_interval"]
        self.min_spawn_interval = max(35, config["spawn_interval"] - 20)

        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0

        self.game_over = False
        self.show_menu = False

        self.previous_obstacle_positions = {}

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.reset_game("Easy")

                elif event.key == pygame.K_2:
                    self.reset_game("Medium")

                elif event.key == pygame.K_3:
                    self.reset_game("Hard")

                elif event.key in (pygame.K_4, pygame.K_ESCAPE):
                    self.show_menu = True

            return

        if (
            event.type == pygame.KEYDOWN
            and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
        ):
            if self.player.jump():
                self._play_sound(self.jump_sound)

    def handle_input(self):
        pass

    def _check_collision_swept(self, obstacle, previous_x):
        """
        Detect collision using both the current rectangle and
        the horizontal path travelled during this frame.

        This prevents fast obstacles from jumping over the
        player's hitbox between two frames.
        """

        player_rect = self.player.rect()

        current_rect = obstacle.rect()

        if current_rect.colliderect(player_rect):
            return True

        previous_rect = pygame.Rect(
            previous_x,
            obstacle.y,
            obstacle.width,
            obstacle.height,
        )

        swept_left = min(previous_rect.left, current_rect.left)
        swept_right = max(previous_rect.right, current_rect.right)

        swept_rect = pygame.Rect(
            swept_left,
            obstacle.y,
            swept_right - swept_left,
            obstacle.height,
        )

        return swept_rect.colliderect(player_rect)

    def update(self):
        if self.game_over:
            return

        # Task 1:
        # Speed increases gradually but is capped.
        self.speed = min(
            self.speed + self.speed_increase_per_frame,
            self.max_speed,
        )

        self.player.update()

        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0

            self.obstacles.append(
                Obstacle(
                    self.width,
                    self.ground_y,
                    self.speed,
                )
            )

        previous_positions = {
            id(obstacle): obstacle.x
            for obstacle in self.obstacles
        }

        for obstacle in self.obstacles:
            obstacle.speed = self.speed
            obstacle.move()

        # Task 1:
        # Swept collision prevents tunnelling at high speeds.
        for obstacle in self.obstacles:
            previous_x = previous_positions[id(obstacle)]

            if self._check_collision_swept(obstacle, previous_x):
                self.game_over = True
                self._play_sound(self.game_over_sound)
                return

        # Task 4:
        # Score sound when an obstacle has been cleared.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1
                self._play_sound(self.score_sound)

        self.obstacles = [
            obstacle
            for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]

        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4,
        )

        pygame.draw.rect(
            screen,
            WHITE,
            self.player.rect(),
        )

        for obstacle in self.obstacles:
            pygame.draw.rect(
                screen,
                DARK_GREEN,
                obstacle.rect(),
            )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            BLACK,
        )

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            GRAY,
        )

        screen.blit(score_text, (10, 10))
        screen.blit(difficulty_text, (10, 45))

        # Task 2 + Task 3:
        # Proper Game Over screen and replay menu.
        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )

            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            game_over_text = self.big_font.render(
                "GAME OVER",
                True,
                RED,
            )

            final_score_text = self.font.render(
                f"Final Score: {self.score}",
                True,
                WHITE,
            )

            replay_text = self.small_font.render(
                "1: Easy    2: Medium    3: Hard",
                True,
                LIGHT_GRAY,
            )

            exit_text = self.small_font.render(
                "4: Exit",
                True,
                LIGHT_GRAY,
            )

            screen.blit(
                game_over_text,
                (
                    self.width // 2 - game_over_text.get_width() // 2,
                    100,
                ),
            )

            screen.blit(
                final_score_text,
                (
                    self.width // 2 - final_score_text.get_width() // 2,
                    170,
                ),
            )

            screen.blit(
                replay_text,
                (
                    self.width // 2 - replay_text.get_width() // 2,
                    230,
                ),
            )

            screen.blit(
                exit_text,
                (
                    self.width // 2 - exit_text.get_width() // 2,
                    270,
                ),
            )