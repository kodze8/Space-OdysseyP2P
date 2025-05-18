import random

import pygame

WIDTH, HEIGHT = 800, 600
DARK_BLUE = (10, 10, 50)
SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 75
spaceship_speed = 5
DURATION = 60000


def random_generator():
    return random.randint(0, WIDTH), random.randint(0, HEIGHT)


class Spaceship:

    def __init__(self, x, y, player_locations):
        #  players  -> port: (x, y)
        self.player_locations = player_locations
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spaceship Movement")
        self.spaceship_x = x
        self.spaceship_y = y
        self.score = 0
        self.peer_scores = {port: 0 for port in self.player_locations}
        self.dots = []

        self.spaceship_img = pygame.image.load("spaceship.png").convert_alpha()
        self.spaceship_img = pygame.transform.scale(self.spaceship_img, (SPACESHIP_WIDTH, SPACESHIP_HEIGHT))

    def draw_me(self):
        img_rect = self.spaceship_img.get_rect(center=(self.spaceship_x, self.spaceship_y))
        self.screen.blit(self.spaceship_img, img_rect)

        font = pygame.font.SysFont(None, 28)
        score_surface = font.render(f"Score: {self.score}", True, (255, 255, 0))
        text_rect = score_surface.get_rect(center=(self.spaceship_x, self.spaceship_y - SPACESHIP_HEIGHT // 2 - 15))
        self.screen.blit(score_surface, text_rect)


    def draw_other(self, loc, port):
        pygame.draw.circle(self.screen, (205, 205, 155), loc, 20)

        # Draw peer score
        score = self.peer_scores.get(port, 0)
        font = pygame.font.SysFont(None, 28)
        score_surface = font.render(f"{port}: {score}", True, (255, 215, 0))
        score_rect = score_surface.get_rect(center=(loc[0], loc[1] - 30))
        self.screen.blit(score_surface, score_rect)

    def draw_dot(self, loc):
        pygame.draw.circle(self.screen, (255, 222, 33), loc, 10)

    def draw_final_scores(self):
        self.screen.fill(DARK_BLUE)
        font = pygame.font.SysFont(None, 36)
        heading = font.render("Final Scores", True, (255, 255, 255))
        self.screen.blit(heading, (WIDTH // 2 - heading.get_width() // 2, 50))

        box_font = pygame.font.SysFont(None, 30)
        box_width = 300
        box_height = 40
        spacing = 20
        start_y = 120

        all_scores = {"YOU": self.score}
        for port, score in self.peer_scores.items():
            all_scores[str(port)] = score

        for i, (port, score) in enumerate(all_scores.items()):
            y = start_y + i * (box_height + spacing)
            x = WIDTH // 2 - box_width // 2
            pygame.draw.rect(self.screen, (30, 30, 100), (x, y, box_width, box_height), border_radius=10)
            text = box_font.render(f"{port}: {score}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(WIDTH // 2, y + box_height // 2))
            self.screen.blit(text, text_rect)

        pygame.display.flip()

        # Wait until the user closes the window
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False

    def move(self):
        clock = pygame.time.Clock()
        running = True
        start_time = pygame.time.get_ticks()
        font = pygame.font.SysFont(None, 32)

        while running:
            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - start_time
            if elapsed_time >= DURATION:
                running = False
                break

            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.spaceship_x -= spaceship_speed
            if keys[pygame.K_RIGHT]:
                self.spaceship_x += spaceship_speed
            if keys[pygame.K_UP]:
                self.spaceship_y -= spaceship_speed
            if keys[pygame.K_DOWN]:
                self.spaceship_y += spaceship_speed

            self.spaceship_x = max(0, min(WIDTH - SPACESHIP_WIDTH, self.spaceship_x))
            self.spaceship_y = max(0, min(HEIGHT - SPACESHIP_HEIGHT, self.spaceship_y))

            self.screen.fill(DARK_BLUE)

            self.draw_me()
            for p, loc in list(self.player_locations.items()):
                self.draw_other(loc, p)

            for loc in self.dots:
                self.draw_dot(loc)

            timer_surface = font.render(f"Time: {(DURATION - elapsed_time) // 1000}", True, (255, 255, 255))
            self.screen.blit(timer_surface, (WIDTH - 150, 20))

            pygame.display.flip()
            clock.tick(60)
        self.draw_final_scores()
