import pygame
from pygame.math import Vector2
from spacegame.config import (
    PROJECTILE_SPEED,
    PROJECTILE_RADIUS,
    PROJECTILE_LIFETIME,
    PROJECTILE_DEFAULT_HULL,
    PROJECTILE_DEFAULT_ARMOR,
)
from spacegame.core.effects import add_explosion


class Projectile(pygame.sprite.Sprite):
    """Projectile sprite. Use in a `pygame.sprite.Group` for bulk update/draw.

    Note: collision with `SpaceUnit` instances is still performed via
    `collides_with_shape()` which uses the unit's rotated mask.
    """
    SPEED = PROJECTILE_SPEED
    RADIUS = PROJECTILE_RADIUS

    def __init__(self, pos, direction, *, speed=None, radius=None,
                 hull_damage=None, armor_damage=None,
                 color=(255, 240, 120), lifetime=PROJECTILE_LIFETIME,
                 owner_is_enemy=False):
        super().__init__()
        self.pos = Vector2(pos)
        self.direction = Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = float(self.SPEED if speed is None else speed)
        self.radius = int(self.RADIUS if radius is None else radius)

        if hull_damage is None:
            hull_damage = PROJECTILE_DEFAULT_HULL
        if armor_damage is None:
            # default to provided armor or fall back to projectile default
            armor_damage = PROJECTILE_DEFAULT_ARMOR if armor_damage is None else armor_damage

        self.hull_damage = float(hull_damage)
        self.armor_damage = float(armor_damage)
        self.color = color
        self.lifetime = float(lifetime)
        self.owner_is_enemy = owner_is_enemy

        # Create image, rect and mask for sprite rendering & collisions
        size = self.radius * 2 + 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (size // 2, size // 2), self.radius)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def update(self, dt: float = 0.016):
        # Move by velocity*dt and decrement lifetime; kill when expired
        self.pos += self.direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.lifetime -= dt
        if self.lifetime <= 0:
            try:
                # small expiry puff (small particles)
                add_explosion(self.pos, color=self.color, count=6, speed=self.speed * 0.25, radius=1, lifetime=0.25, scale=0.5)
            except Exception:
                pass
            self.kill()

    def explode(self):
        """Spawn an impact explosion effect at the projectile position and remove the projectile."""
        try:
            # impact explosion: small particles regardless of projectile radius
            add_explosion(self.pos, color=self.color, count=18, speed=self.speed * 0.45, radius=max(1, int(self.radius * 0.25)), lifetime=0.45, scale=0.9)
        except Exception:
            pass
        try:
            self.kill()
        except Exception:
            pass

    def collides_with_shape(self, spaceship):
        # Circle vs sprite mask collision detection with an arbitrary SpaceUnit
        surf, mask = spaceship.get_rotated_sprite()
        rect = spaceship.get_sprite_rect(surf)

        projectile_rect = pygame.Rect(
            int(self.pos.x - self.radius),
            int(self.pos.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

        if not projectile_rect.colliderect(rect):
            return False

        import math
        test_points = [(int(self.pos.x), int(self.pos.y))]
        steps = 16
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            px = int(self.pos.x + self.radius * math.cos(angle))
            py = int(self.pos.y + self.radius * math.sin(angle))
            test_points.append((px, py))

        for px, py in test_points:
            local_x = px - rect.left
            local_y = py - rect.top
            if (0 <= local_x < mask.get_size()[0] and 0 <= local_y < mask.get_size()[1]):
                if mask.get_at((local_x, local_y)):
                    return True

        return False