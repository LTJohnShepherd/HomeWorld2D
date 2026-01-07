import pygame
from spacegame.models.asteroids.asteroid import Asteroid
from spacegame.config import IMAGES_DIR

class MineableAsteroidA(Asteroid):
    """Mineable asteroid that yields RU TYPE A ore.

    Purity is a float between 0.0 and 1.0 (e.g. 0.5 means 50% yield).
    """

    def __init__(self, pos, tier: int = 0, purity: float = 0.5):
        super().__init__(pos, tier=tier, ore_type="A", purity=purity, radius=34)
        # Try to load asteroid sprite; scale to asteroid radius if possible.
        try:
            surf = pygame.image.load(IMAGES_DIR + "/AsteroidRUAOre.png").convert_alpha()
            # scale to diameter
            diameter = max(4, int(self.radius * 2))
            surf = pygame.transform.smoothscale(surf, (diameter, diameter))
            self.set_sprite(surf)
        except Exception:
            pass