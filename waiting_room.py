import sys
import threading

import pygame

pygame.init()

# UI setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Odyssey")
title_font = pygame.font.Font(None, 60)
font = pygame.font.Font(None, 36)

# Colors
BLUE = (10, 10, 50)
WHITE = (245, 245, 220)
BOX_COLOR = (10, 30, 90)
YELLOW = (255, 99, 71)

# State variables
username = ""
port = ""
focused_input = "username"
user_list = []
error_message = ""
scroll_offset = 0
inputs_visible = True

lock = threading.Lock()


def draw_main_screen():
    screen.fill(BLUE)
    title = title_font.render("Space Odyssey", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

    if inputs_visible:
        screen.blit(font.render("Username:", True, WHITE), (50, 130))
        screen.blit(font.render("Port:", True, WHITE), (50, 230))

        username_border = 4 if focused_input == "username" else 2
        port_border = 4 if focused_input == "port" else 2
        pygame.draw.rect(screen, WHITE, (200, 125, 300, 40), username_border)
        pygame.draw.rect(screen, WHITE, (200, 225, 300, 40), port_border)

        screen.blit(font.render(username, True, WHITE), (210, 130))
        screen.blit(font.render(port, True, WHITE), (210, 230))

        if error_message:
            screen.blit(font.render(error_message, True, (255, 100, 100)), (50, 280))

    pygame.display.flip()


def get_user_input(error=""):
    global username, port, error_message, inputs_visible, focused_input
    clock = pygame.time.Clock()

    if error:
        error_message = error

    while True:
        draw_main_screen()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if 200 <= mx <= 500:
                    if 125 <= my <= 165:
                        focused_input = "username"
                    elif 225 <= my <= 265:
                        focused_input = "port"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if focused_input == "username":
                        username = username[:-1]
                    else:
                        port = port[:-1]
                elif event.key == pygame.K_RETURN:

                    if username.strip() == "":
                        error_message = "Username cannot be empty."
                    elif not port.isdigit() or not (1000 <= int(port) <= 99999):
                        error_message = "Port must be 1000–99999."
                    else:
                        # error_message = ""
                        # inputs_visible = False
                        return username, int(port)
                else:
                    if focused_input == "username":
                        username += event.unicode
                    else:
                        port += event.unicode

        clock.tick(30)


running = True


def run_waiting_room():
    global scroll_offset, running
    clock = pygame.time.Clock()
    button_rect = pygame.Rect(WIDTH // 2 - 75, 80, 150, 50)

    while running:
        screen.fill(BLUE)
        title = title_font.render("Waiting Room", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        pygame.draw.rect(screen, BOX_COLOR, button_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, button_rect, 2, border_radius=10)
        start_text = font.render("Start", True, WHITE)
        screen.blit(start_text, (
            button_rect.centerx - start_text.get_width() // 2,
            button_rect.centery - start_text.get_height() // 2
        ))

        y = 160 + scroll_offset
        lock.acquire()
        for user in user_list:
            pygame.draw.rect(screen, BOX_COLOR, (50, y, 600, 40), border_radius=10)
            screen.blit(font.render(user, True, WHITE), (60, y + 8))
            y += 50
        lock.release()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    print("Start clicked!")
                    running = False

                elif event.button == 4:
                    scroll_offset = min(scroll_offset + 20, 0)
                elif event.button == 5:
                    max_scroll = -max(0, len(user_list) * 50 - 300)
                    scroll_offset = max(scroll_offset - 20, max_scroll)

        clock.tick(30)
    print("Waiting Room Closed")
