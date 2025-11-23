import pygame
from spacegame.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR

class Interceptor(SpaceUnit):
    """Small deployable interceptor light craft."""

    def shape_id(self):
        return "interceptor"

    def __init__(self, start_pos, interceptor_id=None, **kwargs):
        # load interceptor sprite
        sprite = pygame.image.load(IMAGES_DIR / "Interceptor.png").convert_alpha()
        # rotate so it faces like the other ships (to the right at angle 0)
        sprite = pygame.transform.rotate(sprite, -90)

        # scale down (adjust factor if you want a different size)
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 24, sprite.get_height() // 24)
        )

        # use sprite size for collisions / drawing
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # id in the ExpeditionShip's interceptor pool (if any)
        self.interceptor_id = interceptor_id

        # recall state
        self.recalling = False
        self.hangar_slot = None
