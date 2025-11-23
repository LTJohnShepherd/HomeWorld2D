import pygame
from pygame.math import Vector2
from spacegame.units.fleet_unit import SpaceUnit
from spacegame.units.interceptor import Interceptor
from spacegame.config import (
    EXPEDITION_MAX_HEALTH,
    HANGAR_SLOT_COUNT,
    INTERCEPTOR_POOL_SIZE,
    IMAGES_DIR,
)

class ExpeditionShip(SpaceUnit):
    """Main player-controlled rectangle with a 3-slot hangar."""
    
    def shape_id(self):
        return "expeditionship"

    def __init__(self, start_pos, **kwargs):
        # load sprite first
        sprite = pygame.image.load(IMAGES_DIR / "ExpeditionShip.png").convert_alpha()

        # fix orientation (rotate -90 degrees clockwise)
        sprite = pygame.transform.rotate(sprite, -90)

        # use sprite size instead of tiny rectangle
        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (sprite.get_width() // 4, sprite.get_height() // 4)
        )

        # update ship size
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # Increase ExpeditionShip health
        self.max_health = EXPEDITION_MAX_HEALTH
        self.health = self.max_health

        # Hangar slots for light ships
        # True = interceptor in hangar (assigned & not currently deployed)
        self.hangar = [False] * HANGAR_SLOT_COUNT
        self.deployed = []                      # stores spawned Interceptor objects
        self.hangar_ships = [None] * HANGAR_SLOT_COUNT  # fighters for each slot (after deploy)
        self.last_selected_light_craft = None

        # Persistent interceptor pool for fleet management (5 total for now)
        if not hasattr(self, "interceptor_pool"):
            self.interceptor_pool = [
                {"id": i, "name": f"Interceptor {i+1}", "alive": True}
                for i in range(INTERCEPTOR_POOL_SIZE)
            ]

        # Which pool interceptor is assigned to each hangar slot (or None)
        if not hasattr(self, "hangar_assignments"):
            self.hangar_assignments = [None] * HANGAR_SLOT_COUNT
            # Default: assign first interceptors to slots, up to HANGAR_SLOT_COUNT
            alive_ids = [e["id"] for e in self.interceptor_pool if e.get("alive", False)]
            for slot in range(HANGAR_SLOT_COUNT):
                if slot < len(alive_ids):
                    self.hangar_assignments[slot] = alive_ids[slot]
                    self.hangar[slot] = True
                    
    def can_deploy(self, slot):
        return 0 <= slot < HANGAR_SLOT_COUNT and self.hangar[slot]

    def deploy(self, slot):
        """Spawn a light ship near the ExpeditionShip, behaving like a normal spaceship."""
        if not self.can_deploy(slot):
            return None

        # Mark slot as used (no interceptor in hangar now – one is deployed)
        self.hangar[slot] = False

        # Determine which interceptor from the pool is assigned to this slot (if any)
        interceptor_id = None
        if hasattr(self, "hangar_assignments") and 0 <= slot < len(self.hangar_assignments):
            interceptor_id = self.hangar_assignments[slot]

        # Spawn slightly in front of the rectangle
        offset = Vector2(70, 50).rotate(-self.angle)
        icpt = Interceptor(self.pos + offset, interceptor_id=interceptor_id)
        icpt.mover.angle = self.angle    # start facing same direction

        # Remember which slot this light craft came from
        icpt.hangar_slot = slot
        icpt.recalling = False

        self.deployed.append(icpt)
        self.hangar_ships[slot] = icpt
        return icpt
