import pygame
from pygame.math import Vector2
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.hangar import Hangar
from spacegame.config import (
    EXPEDITION_MAX_HEALTH,
    EXPEDITION_MAX_ARMOR,
    HANGAR_SLOT_COUNT,
    INTERCEPTOR_POOL_SIZE,
    IMAGES_DIR,
)

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
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), **kwargs)
        self.base_surf = scaled_sprite

        # Increase ExpeditionShip health / armor
        self.max_health = EXPEDITION_MAX_HEALTH
        self.health = self.max_health
        self.max_armor = EXPEDITION_MAX_ARMOR
        self.armor = self.max_armor

                # Hangar system: delegate light-craft management to Hangar helper.
        # Hangar keeps:
        #   - slots: which hangar slots currently have a ready interceptor
        #   - ships: which Interceptor objects are deployed from each slot
        #   - assignments: which pool id is assigned to each slot
        #   - pool: persistent interceptor data for fleet-management screens
        self.hangar_system = Hangar(self, num_slots=HANGAR_SLOT_COUNT, pool_size=INTERCEPTOR_POOL_SIZE)

        # Backwards-compatible aliases so existing screens (fleet management, HUD, etc.)
        # can keep using the older attributes. These all point into the Hangar instance.
        self.hangar = self.hangar_system.slots          # list[bool]: True = interceptor ready in hangar
        self.hangar_ships = self.hangar_system.ships    # list[Interceptor|None]: deployed per-slot ships
        self.interceptor_pool = self.hangar_system.pool # list[dict]: metadata (id, name, alive, tier)
        self.hangar_assignments = self.hangar_system.assignments  # list[int|None]: pool id per slot
        self.deployed = self.hangar_system.deployed     # list[Interceptor]: all currently deployed fighters

        # Remember the last selected light craft for convenience in input handling.
        self.last_selected_light_craft = None
    def can_deploy(self, slot):
        """Return True if the given slot currently has a ready interceptor in hangar."""
        # Delegate to the Hangar system; it owns slot readiness logic.
        return self.hangar_system.can_deploy(slot)

    def deploy(self, slot):
        """Deploy an interceptor from the given hangar slot, if available.

        The actual Interceptor object is spawned in front of the mothership and
        added to the active fleet externally; this method just constructs it and
        updates the Hangar's state.
        """
        if not self.can_deploy(slot):
            return None

        hangar = self.hangar_system

        # Determine which interceptor from the persistent pool is assigned to this slot (if any)
        interceptor_id = None
        if 0 <= slot < len(hangar.assignments):
            interceptor_id = hangar.assignments[slot]

        # Spawn slightly in front of the rectangle (relative to current facing)
        offset = Vector2(70, 50).rotate(-self.angle)

        # Look up this interceptor's tier from the Hangar pool data (per-ship).
        tier_value = 0
        if interceptor_id is not None:
            entry = hangar.get_entry_by_id(interceptor_id)
            if entry is not None and entry.alive:
                tier_value = entry.tier

        icpt = Interceptor(self.pos + offset, interceptor_id=interceptor_id, tier=tier_value)

        # Notify Hangar that an interceptor was deployed so it can update slots / bookkeeping.
        hangar.on_deployed(slot, icpt)

        return icpt
