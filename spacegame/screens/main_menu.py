import pygame
import sys
from spacegame.screens.game_screen import run_game
from spacegame.ui.ui import Button
from spacegame.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

def main():
   
    pygame.init() # Initialize all imported Pygame modules (must be called before using Pygame features)
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SpaceGame - Main Menu")

    clock = pygame.time.Clock()

    # fonts
    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 48)

    # title
    title_surf = title_font.render("SpaceGame", True, (255,255,255))
    title_rect = title_surf.get_rect(center=(WIDTH//2, 150))

    # buttons
    btn_w, btn_h = 240, 64
    play_button = Button((WIDTH//2 - btn_w//2, 300, btn_w, btn_h), "Play", btn_font)
    exit_button = Button((WIDTH//2 - btn_w//2, 390, btn_w, btn_h), "Exit", btn_font)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if play_button.handle_event(event):
                # run the user's game; return here after ESC or window close inside the game
                run_game()
                # Recreate title surface after returning (safe on some platforms)
                title_surf = title_font.render("SpaceGame", True, (255,255,255))

            if exit_button.handle_event(event):
                running = False

        # Clear the entire screen and fill it with a dark background color
        screen.fill((15, 15, 20))

        # Draw small static “star” dots across the background for a simple space effect
        for x in range(40, WIDTH, 80):
            for y in range(60, HEIGHT, 120):

                # Draw a tiny dot (star) at position (x, y)
                pygame.draw.circle(screen, (60,60,80), (x, y), 1)

        screen.blit(title_surf, title_rect)
        play_button.draw(screen)
        exit_button.draw(screen)

        pygame.display.flip() # Update the entire screen to show everything drawn in this frame
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()