from abc import ABC
import pygame
from pygame.math import Vector2


class Asteroid(pygame.sprite.Sprite, ABC):
    """Abstract asteroid: position, tier, ore_type (letter), purity (0..1), and radius.

    Subclasses should call `self.set_sprite(surface)` after creating a scaled
    surface for the asteroid so that the sprite image/rect/mask are initialized.
    """

    def __init__(self, pos, tier: int, ore_type: str, purity: float, radius: int = 28):
        pygame.sprite.Sprite.__init__(self)
        self.pos = Vector2(pos)
        self.tier = int(tier)
        self.ore_type = str(ore_type)
        self.purity = float(purity)
        self.radius = int(radius)
        self.image = None
        self.rect = pygame.Rect(int(self.pos.x - self.radius), int(self.pos.y - self.radius), self.radius * 2, self.radius * 2)
        self.mask = None

    def set_sprite(self, surf: pygame.Surface):
        """Assign the sprite surface and compute rect/mask."""
        self.image = surf
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

    def point_inside(self, point) -> bool:
        p = Vector2(point)
        return (p - self.pos).length_squared() <= (self.radius * self.radius)

    def bounding_radius(self) -> float:
        return float(self.radius)

