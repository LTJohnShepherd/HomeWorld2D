import pygame
import random
from pygame.math import Vector2

# Central effects group used by the game loop for updates/draws
effects_group = pygame.sprite.Group()


class Particle(pygame.sprite.Sprite):
    """Simple particle: circle that moves, fades, and dies."""

    def __init__(self, pos, vel, color, radius=1, lifetime=0.6):
        super().__init__()
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.color = tuple(color)
        self.radius = int(radius)
        self.lifetime = float(lifetime)
        self.max_life = float(lifetime)

        size = max(2, self.radius * 2 + 2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (size // 2, size // 2), self.radius)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt: float = 0.016):
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.lifetime -= dt
        # simple damping so particles slow and don't travel too far
        try:
            self.vel *= max(0.0, 1.0 - 3.0 * dt)
        except Exception:
            pass
        # fade out
        if self.max_life > 0:
            alpha = int(255 * max(0.0, min(1.0, self.lifetime / self.max_life)))
            try:
                self.image.set_alpha(alpha)
            except Exception:
                pass
        if self.lifetime <= 0:
            self.kill()


def spawn_explosion(pos, *, color=(255, 180, 80), count=16, speed=120.0, spread=360, radius=1, lifetime=0.8, scale=1.0):
    """Create a burst of particles at `pos` and add them to the global `effects_group`.

    Args:
        pos: center position (x,y) of the explosion
        color: base particle color
        count: number of particles
        speed: base particle speed
        spread: angular spread in degrees (360 = full circle)
        radius: particle radius (px)
        lifetime: particle lifetime (seconds)
        scale: multiplier for speed/radius
    """
    s = float(speed) * float(scale)
    r = max(1, int(radius * scale))
    life = float(lifetime) * max(0.25, scale)
    for i in range(count):
        angle = random.random() * (spread / 180.0) * 3.14159265
        # random direction
        dx = random.uniform(-1.0, 1.0)
        dy = random.uniform(-1.0, 1.0)
        vel = Vector2(dx, dy)
        if vel.length_squared() == 0:
            vel = Vector2(1, 0)
        vel = vel.normalize() * (s * random.uniform(0.1, 0.5))
        p = Particle(pos, vel, color, radius=r, lifetime=life)
        effects_group.add(p)


def spawn_dust(pos, *, color=(180, 160, 120), count=20, speed=64.0, radius=3, lifetime=0.8, scale=1.0):
    """Spawn a short-lived, low-speed dust cloud at `pos`.

    Dust particles are slower and fade quickly, intended as a muzzle/launch puff.
    """
    s = float(speed) * float(scale)
    r = max(1, int(radius * scale))
    life = float(lifetime) * max(0.1, scale)
    for i in range(count):
        dx = random.uniform(-1.0, 1.0)
        dy = random.uniform(-1.0, 1.0)
        vel = Vector2(dx, dy)
        if vel.length_squared() == 0:
            vel = Vector2(0.1, -0.1)
        vel = vel.normalize() * (s * random.uniform(0.175, 0.75))
        # slight upward bias
        vel.y -= abs(random.uniform(0.0, 0.2) * s * 0.02)
        p = Particle(pos, vel, color, radius=r, lifetime=life)
        effects_group.add(p)




# Convenience alias used by other modules
def add_explosion(*a, **k):
    spawn_explosion(*a, **k)


def add_dust(*a, **k):
    spawn_dust(*a, **k)
