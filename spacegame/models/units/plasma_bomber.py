import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR


class PlasmaBomber(SpaceUnit):
    """Plasma Bomber: heavy light-craft similar to Interceptor but trades speed for damage/health."""

    def shape_id(self):
        return "plasma_bomber"

    def get_tier(self) -> int:
        return getattr(self, "tier", 0)

    def __init__(self, start_pos, bomber_id=None, tier: int = 0, **kwargs):
        # per-ship tier
        self.tier = tier

        # load bomber sprite (use TorpedoBomber.png if present)
        try:
            sprite = pygame.image.load(IMAGES_DIR + "/TorpedoBomber.png").convert_alpha()
        except Exception:
            # fallback to a simple rect surface
            sprite = pygame.Surface((48, 24), pygame.SRCALPHA)
            pygame.draw.rect(sprite, (200, 80, 80), sprite.get_rect())

        # rotate so it faces like the other ships (to the right at angle 0)
        try:
            sprite = pygame.transform.rotate(sprite, -90)
        except Exception:
            pass

        # scale down: make the bomber slightly larger than the interceptor
        # (interceptor used //24); use a smaller divisor so bomber appears bigger
        try:
            target_w = max(8, sprite.get_width() // 16)
            target_h = max(8, sprite.get_height() // 16)
            scaled_sprite = pygame.transform.smoothscale(sprite, (target_w, target_h))
        except Exception:
            scaled_sprite = sprite

        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # id in hangar pool (if any)
        self.bomber_id = bomber_id

        # recall / hangar state
        self.recalling = False
        self.hangar_slot = None

        # Combat stats
        self.bullet_damage = 12.0
        self.armor_damage = 24.0

        # Health/armor
        self.max_health = 4500.0
        self.health = self.max_health
        self.max_armor = 0.0
        self.armor = 0.0
