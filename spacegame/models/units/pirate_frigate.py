import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import (
    PIRATE_DEFAULT_SPEED,
    PIRATE_DEFAULT_ROT_SPEED,
    PIRATE_DEFAULT_FIRE_RANGE,
    PIRATE_DEFAULT_FIRE_COOLDOWN,
    PIRATE_DEFAULT_BULLET_DAMAGE,
    PIRATE_DEFAULT_ARMOR_DAMAGE,
    IMAGES_DIR
)

class PirateFrigate(SpaceUnit):
    # ---- Enemy defaults ----
    DEFAULT_COLOR = (220, 60, 60)
    DEFAULT_SPEED = PIRATE_DEFAULT_SPEED
    DEFAULT_ROT_SPEED = PIRATE_DEFAULT_ROT_SPEED
    DEFAULT_FIRE_RANGE = PIRATE_DEFAULT_FIRE_RANGE
    DEFAULT_FIRE_COOLDOWN = PIRATE_DEFAULT_FIRE_COOLDOWN
    DEFAULT_BULLET_DAMAGE = PIRATE_DEFAULT_BULLET_DAMAGE
    DEFAULT_ARMOR_DAMAGE = PIRATE_DEFAULT_ARMOR_DAMAGE

    def shape_id(self):
        return "pirate"
    
    def get_tier(self) -> int:
        return 0

    def __init__(self, start_pos, **kwargs):
        # load pirate sprite
        sprite = pygame.image.load(IMAGES_DIR + "/PirateCruiser.png").convert_alpha()

        # rotate so it faces to the right (like other ships)
        sprite = pygame.transform.rotate(sprite, -90)

        # scale it down (adjust divisor for size)
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 6, sprite.get_height() // 6)
        )

        # use sprite size for collisions / drawing
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # Combat stats
        self.bullet_damage = 67.0
        self.armor_damage = 10.7

        # Health/armor
        self.max_health = 4200.0
        self.health = self.max_health
        self.max_armor = 540.0
        self.armor = self.max_armor
