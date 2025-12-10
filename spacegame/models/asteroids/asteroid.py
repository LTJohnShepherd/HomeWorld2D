from abc import ABC
import pygame
from pygame.math import Vector2


class Asteroid(ABC):
    """Abstract asteroid: position, tier, ore_type (letter), purity (0..1), and radius."""

    def __init__(self, pos, tier: int, ore_type: str, purity: float, radius: int = 28):
        self.pos = Vector2(pos)
        self.tier = int(tier)
        self.ore_type = str(ore_type)
        self.purity = float(purity)
        self.radius = int(radius)

    def point_inside(self, point) -> bool:
        p = Vector2(point)
        return (p - self.pos).length_squared() <= (self.radius * self.radius)

    def bounding_radius(self) -> float:
        return float(self.radius)

    def draw(self, surface):
        """Draw asteroid using sprite if available, otherwise a simple circle."""
        # If subclass provided a sprite surface, prefer that
        img = getattr(self, "_sprite", None)
        if img is not None:
            rect = img.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            surface.blit(img, rect.topleft)
        else:
            pygame.draw.circle(surface, (90, 90, 100), (int(self.pos.x), int(self.pos.y)), self.radius)
            pygame.draw.circle(surface, (60, 60, 70), (int(self.pos.x), int(self.pos.y)), self.radius, 2)
