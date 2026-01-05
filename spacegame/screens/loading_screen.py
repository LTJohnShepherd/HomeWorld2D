import pygame
import math


class LoadingSprite(pygame.sprite.Sprite):
    def __init__(self, radius=36, dot_count=12, color=(180, 220, 255)):
        super().__init__()
        size = radius * 2 + 8
        self.base = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        self.radius = radius
        self.dot_count = dot_count
        self.color = color
        # draw dots into base surface
        for i in range(dot_count):
            ang = 2 * math.pi * i / dot_count
            x = int(cx + math.cos(ang) * radius)
            y = int(cy + math.sin(ang) * radius)
            alpha = int(255 * (0.4 + 0.6 * (i / dot_count)))
            col = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(self.base, col, (x, y), 6)

        self.image = self.base.copy()
        self.rect = self.image.get_rect()
        self._angle = 0.0

    def update(self, dt=0.016):
        # rotate a bit each frame
        self._angle = (self._angle + 180 * dt) % 360
        self.image = pygame.transform.rotozoom(self.base, -self._angle, 1.0)
        self.rect = self.image.get_rect(center=self.rect.center)


def loading_screen(preload_thread, message="Loading..."):
    """Display an animated loading circle while `preload_thread` is alive.

    This function takes over the main loop and returns when the thread finishes.
    If the user closes the window it returns the string "exit".
    """
    
    screen = pygame.display.get_surface()
    if screen is None:
        # fallback to standard size
        from spacegame.config import SCREEN_WIDTH, SCREEN_HEIGHT
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    clock = pygame.time.Clock()

    sprite = LoadingSprite(radius=40, dot_count=12)
    sprite.rect.center = (width // 2, height // 2)
    group = pygame.sprite.Group(sprite)

    font = pygame.font.Font(None, 28)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "exit"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                # allow esc to cancel loading
                return "exit"

        # update sprite
        group.update(dt)

        screen.fill((6, 10, 20))
        group.draw(screen)

        # message under sprite
        text_s = font.render(message, True, (200, 220, 240))
        trect = text_s.get_rect(center=(width // 2, sprite.rect.bottom + 28))
        screen.blit(text_s, trect)

        pygame.display.flip()

        # stop when the preload thread finishes
        if not preload_thread.is_alive():
            running = False

    return None
