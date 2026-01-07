import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR

class Interceptor(SpaceUnit):
    """Small deployable interceptor light craft."""

    def shape_id(self):
        return "interceptor"
    
    def get_tier(self) -> int:
        # tier is stored per ship instance; default 0 like other ships.
        return getattr(self, "tier", 0)

    def __init__(self, start_pos, interceptor_id=None, tier: int = 0, **kwargs):
        # per-ship tier value
        self.tier = tier
        # load interceptor sprite
        sprite = pygame.image.load(IMAGES_DIR + "/Interceptor.png").convert_alpha()
        # rotate so it faces like the other ships (to the right at angle 0)
        sprite = pygame.transform.rotate(sprite, -90)

        # scale down (adjust factor if you want a different size)
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 24, sprite.get_height() // 24)
        )

        # use sprite size for collisions / drawing
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), rarity="common", **kwargs)
        self.base_surf = scaled_sprite

        # id in the ExpeditionShip's interceptor pool (if any)
        self.interceptor_id = interceptor_id

        # recall state
        self.recalling = False
        self.hangar_slot = None

        # Combat stats
        self.bullet_damage = 34.0
        self.armor_damage = 2.67

        # Health/armor
        self.max_health = 3990.0
        self.health = self.max_health
        self.max_armor = 0.0
        self.armor = 0.0
