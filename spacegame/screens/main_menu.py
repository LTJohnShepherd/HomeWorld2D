import pygame
from spacegame.ui.ui import Button
from spacegame.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

def main():
    pygame.display.set_caption("SpaceGame - Main Menu")
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    # Fonts
    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 48)

    title_surf = title_font.render("SpaceGame", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 150))
    
    # Buttons
    btn_w, btn_h = 240, 64
    play_button = Button((WIDTH // 2 - btn_w // 2, 300, btn_w, btn_h), "Play", btn_font)
    exit_button = Button((WIDTH // 2 - btn_w // 2, 390, btn_w, btn_h), "Exit", btn_font)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

            if play_button.handle_event(event):
                # tell state machine to switch to game
                return "game"

            if exit_button.handle_event(event):
                return "exit"

        # Clear the entire screen and fill it with a dark background color
        screen.fill((15, 15, 20))

        # Draw small static “star” dots across the background for a simple space effect
        for x in range(40, WIDTH, 80):
            for y in range(60, HEIGHT, 120):
                pygame.draw.circle(screen, (60, 60, 80), (x, y), 1)

        screen.blit(title_surf, title_rect)
        play_button.draw(screen)
        exit_button.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)