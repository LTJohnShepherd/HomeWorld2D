import pygame
"""ExpeditionShip unit: mothership with an InventoryManager and Hangar.

This module defines the player-controlled `ExpeditionShip` which owns the
ship-level `InventoryManager` and a `Hangar` helper responsible for
light-craft pool and slot management. Keep this class focused on ship
state; hangar operations are handled by `Hangar`.
"""
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.core.hangar import Hangar
from spacegame.config import (
    HANGAR_SLOT_COUNT,
    INTERCEPTOR_POOL_SIZE,
    RESOURCE_COLLECTOR_POOL_SIZE,
    PLASMA_BOMBER_POOL_SIZE,
    IMAGES_DIR,
)
from spacegame.core.inventory_manager import InventoryManager

class ExpeditionShip(SpaceUnit):
    """Main player-controlled rectangle with a 3-slot hangar."""
    
    def shape_id(self):
        return "expeditionship"
    
    def get_tier(self) -> int:
        return 0

    def __init__(self, start_pos, **kwargs):
        # load sprite first
        sprite = pygame.image.load(IMAGES_DIR + "/ExpeditionShip.png").convert_alpha()

        # fix orientation (rotate -90 degrees clockwise)
        sprite = pygame.transform.rotate(sprite, -90)

        # use sprite size instead of tiny rectangle
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 4, sprite.get_height() // 4)
        )

        # update ship size
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), rarity="common", **kwargs)
        self.base_surf = scaled_sprite

        # Combat stats
        self.bullet_damage = 12.0
        self.armor_damage = 24.0

        # Health/armor
        self.max_health = 20000.0
        self.health = self.max_health
        self.max_armor = 3000.0
        self.armor = self.max_armor

        # Centralized inventory manager
        self.inventory_manager = InventoryManager(self)

        # Hangar system: create helper for light-craft pool/slot management.
        # The heavy lifting (deploy, recall, pool bookkeeping) lives in `Hangar`.
        self.hangar_system = Hangar(
            self,
            num_slots=HANGAR_SLOT_COUNT,
            interceptor_pool_size=INTERCEPTOR_POOL_SIZE,
            collector_pool_size=RESOURCE_COLLECTOR_POOL_SIZE,
            bomber_pool_size=PLASMA_BOMBER_POOL_SIZE,
            inventory_manager=self.inventory_manager,
        )

        # Remember the last selected light craft for convenience in input handling.
        self.last_selected_light_craft = None
        # Per-section capacity limits for internal modules (persisted on the ship)
        # Order: [left-section, middle-section, right-section]
        self.internal_section_capacity_limits = [170, 220, 170]
        # Initialize installed internal modules (3 sections: left, middle, right)
        # This is populated by the internal modules screen but starts empty
        self.installed_internal_modules = [[], [], []]
        # Attempt to load saved state (if present). Fail silently.
        try:
            from spacegame.core import save as _save
            try:
                _save.load_game(self)
            except Exception:
                pass
        except Exception:
            pass

    # Notification timing and lifecycle are handled by InventoryManager directly.

