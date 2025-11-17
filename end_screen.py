# end_screen.py
import pygame
import sys
from ui import Button
from gameScreen import run_game
from main_menu import main as main_menu

def end_screen():
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game Over")

    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 48)

    title_surf = title_font.render("GAME OVER", True, (255, 80, 80))
    title_rect = title_surf.get_rect(center=(WIDTH//2, 150))

    btn_w, btn_h = 260, 70
    restart_btn = Button((WIDTH//2 - btn_w//2, 300, btn_w, btn_h), "Restart", btn_font)
    menu_btn    = Button((WIDTH//2 - btn_w//2, 390, btn_w, btn_h), "Main Menu", btn_font)
    exit_btn    = Button((WIDTH//2 - btn_w//2, 480, btn_w, btn_h), "Exit", btn_font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if restart_btn.handle_event(event):
                run_game()         # restart gameplay
                return

            if menu_btn.handle_event(event):
                main_menu()        # return to main menu
                return

            if exit_btn.handle_event(event):
                pygame.quit()
                sys.exit()

        screen.fill((10, 10, 15))
        screen.blit(title_surf, title_rect)

        restart_btn.draw(screen)
        menu_btn.draw(screen)
        exit_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)