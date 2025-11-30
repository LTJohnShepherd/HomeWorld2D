import pygame
from spacegame.ui.ui import Button
from spacegame.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

def end_screen():
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game Over")

    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 48)

    title_surf = title_font.render("GAME OVER", True, (255, 80, 80))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 150))

    btn_w, btn_h = 260, 70
    restart_btn = Button((WIDTH // 2 - btn_w // 2, 300, btn_w, btn_h), "Restart", btn_font)
    menu_btn    = Button((WIDTH // 2 - btn_w // 2, 390, btn_w, btn_h), "Main Menu", btn_font)
    exit_btn    = Button((WIDTH // 2 - btn_w // 2, 480, btn_w, btn_h), "Exit", btn_font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

            if restart_btn.handle_event(event):
                return "game"

            if menu_btn.handle_event(event):
                return "main_menu"

            if exit_btn.handle_event(event):
                return "exit"

        screen.fill((10, 10, 15))
        screen.blit(title_surf, title_rect)

        restart_btn.draw(screen)
        menu_btn.draw(screen)
        exit_btn.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)