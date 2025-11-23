import pygame
from spacegame.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR

class Frigate(SpaceUnit):
    """Escort frigate for the ExpeditionShip."""

    def shape_id(self):
        return "friagate"

    def __init__(self, start_pos, **kwargs):
        # load frigate sprite
        sprite = pygame.image.load(IMAGES_DIR / "Frigate.png").convert_alpha()

        # rotate so it faces horizontally like the other ships
        sprite = pygame.transform.rotate(sprite, -90)

        # scale to of sprite
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 6, sprite.get_height() // 6)
        )

        # use sprite size for collisions / drawing
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite
