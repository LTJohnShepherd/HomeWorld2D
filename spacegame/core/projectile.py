import pygame
from pygame.math import Vector2
from spacegame.config import (
    PROJECTILE_SPEED,
    PROJECTILE_RADIUS,
    PROJECTILE_LIFETIME,
)

class Projectile:
    # ---- Class-level defaults ----
    """
    מחלקה: Projectile
    תפקיד: ראה/י תיעוד הפונקציות והמאפיינים מטה. 
    """
    SPEED = PROJECTILE_SPEED
    RADIUS = PROJECTILE_RADIUS

    def __init__(self, pos, direction, *, speed=None, radius=None, damage=10.0, color=(255, 240, 120), lifetime=PROJECTILE_LIFETIME, owner_is_enemy=False):
        self.pos = Vector2(pos)
        self.direction = Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = float(self.SPEED if speed is None else speed)
        self.radius = int(self.RADIUS if radius is None else radius)
        self.damage = float(damage)
        self.color = color
        self.lifetime = float(lifetime)
        self.owner_is_enemy = owner_is_enemy
        self.is_active = True

    def update(self, dt):
        if not self.is_active:
            return
        self.pos += self.direction * self.speed * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_active = False

    def draw(self, surface):
        if not self.is_active:
            return
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

    def collides_with_shape(self, spaceship):
        # Circle vs spaceship-approx collision using spaceship's bounding circle
        dx = self.pos.x - spaceship.pos.x
        dy = self.pos.y - spaceship.pos.y
        dist2 = dx*dx + dy*dy
        hit_r = spaceship.bounding_radius()
        return dist2 <= (hit_r + self.radius) * (hit_r + self.radius)