import pygame
from pygame.math import Vector2
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR


class ResourceCollector(SpaceUnit):
    """Small deployable resource collector light craft.

    Resource collectors can heal the health and armor of large ships by
    navigating to them and transferring resources over time. They can also
    mine asteroids and carry resources back to their mothership.
    """

    # Healing configuration
    HEAL_RATE = 15.0  # health/armor healed per second
    HEAL_RANGE = 60.0  # must be within this distance to heal

    def shape_id(self):
        return "resource_collector"

    def get_tier(self) -> int:
        # tier is stored per ship instance; default 0 like other ships.
        return getattr(self, "tier", 0)

    def __init__(self, start_pos, collector_id=None, tier: int = 0, **kwargs):
        # per-ship tier value
        self.tier = tier
        # load resource collector sprite
        sprite = pygame.image.load(IMAGES_DIR + "/ResourceCollector.png").convert_alpha()
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

        # id in the ExpeditionShip's resource collector pool (if any)
        self.collector_id = collector_id

        # recall state
        self.recalling = False
        self.hangar_slot = None

        # link to mothership will be attached by Hangar.on_deployed
        self.mothership = None

        # Resource collectors do 0 damage
        self.bullet_damage = 0.0
        # Give resource collectors a small armor pool so they can take armor damage
        self.max_armor = 50.0
        self.armor = self.max_armor

        # ---- Healing state ----
        self.healing_target = None  # The ship being healed (or None)

        # ---- Mining state ----
        self.mining_target = None  # Asteroid instance being mined
        self.mining_fill = 0.0     # current filled units (0..mining_capacity)
        self.mining_capacity = 150.0  # amount of "space" in collector
        self.MINE_RATE = 10.0      # units filled per second while mining
        self.MINE_RANGE = 60.0     # must be within this distance to mine
        self.returning_to_ship = False
        self.UNLOAD_RATE = 75.0    # units unloaded per second when at mothership
        # Make the visible targeting circle match the heal/mining range
        self.fire_range = float(self.HEAL_RANGE)

    def start_healing(self, target):
        """Set the target ship to heal. This will cancel any previous healing."""
        self.cancel_mining()
        self.healing_target = target
        # Navigate to the target
        self.mover.set_target(target.pos)

    def cancel_healing(self):
        """Cancel the current healing operation."""
        self.healing_target = None

    def is_healing(self) -> bool:
        """Return True if actively healing a target."""
        return self.healing_target is not None

    def update_healing(self, dt: float) -> None:
        """Update healing state: navigate to target, heal when in range, apply damage/armor healing."""
        if self.healing_target is None:
            return

        # Check if target is still alive
        if self.healing_target.health <= 0.0:
            self.cancel_healing()
            return

        # Distance to target
        dist = (self.healing_target.pos - self.pos).length()

        # If close enough, heal and stop moving; otherwise navigate
        if dist <= self.HEAL_RANGE:
            # Stop moving by setting target to current position
            self.mover.set_target(self.pos)
            # Apply healing to the target
            self._apply_healing(self.healing_target, dt)
        else:
            # Keep navigating to target
            self.mover.set_target(self.healing_target.pos)

    def _apply_healing(self, target, dt: float) -> None:
        """Apply healing over time to the target's health and armor."""
        heal_amount = self.HEAL_RATE * dt

        # Heal armor first if it exists and is damaged
        if getattr(target, "max_armor", 0) > 0:
            armor_deficit = target.max_armor - target.armor
            if armor_deficit > 0:
                armor_heal = min(heal_amount, armor_deficit)
                target.armor += armor_heal
                heal_amount -= armor_heal  # Remaining heal goes to health

        # Heal health if there's remaining heal amount
        if heal_amount > 0:
            health_deficit = target.max_health - target.health
            if health_deficit > 0:
                health_heal = min(heal_amount, health_deficit)
                target.health += health_heal

    # ---------- Mining API ----------
    def start_mining(self, asteroid):
        """Begin mining the given asteroid (cancels healing)."""
        self.cancel_healing()
        self.mining_target = asteroid
        self.returning_to_ship = False
        # navigate to asteroid
        self.mover.set_target(asteroid.pos)

    def cancel_mining(self):
        """Stop mining operation (keeps collected fill)."""
        self.mining_target = None
        self.returning_to_ship = False

    def is_mining(self) -> bool:
        return (self.mining_target is not None) or (self.mining_fill > 0)

    def stop_and_dump(self):
        """Immediately stop mining and dump current contents (reset fill).

        This is used when the player gives a new move command: the collector
        should stop mining and the orange meter should disappear.
        """
        self.mining_target = None
        self.mining_fill = 0.0
        self.returning_to_ship = False

    def update_mining(self, dt: float) -> None:
        """Update mining state: approach asteroid, fill, return and unload."""
        # If we have no mothership (should be set by Hangar.on_deployed), nothing to do
        mothership = getattr(self, "mothership", None)

        # Active mining at asteroid
        if self.mining_target is not None and not self.returning_to_ship:
            # Distance to asteroid
            dist = (self.mining_target.pos - self.pos).length()
            if dist <= self.MINE_RANGE:
                # Stop moving and mine
                self.mover.set_target(self.pos)
                self.mining_fill = min(self.mining_capacity, self.mining_fill + self.MINE_RATE * dt)
                # When full, set to return to mothership
                if self.mining_fill >= self.mining_capacity:
                    self.mining_fill = self.mining_capacity
                    self.returning_to_ship = True
                    if mothership is not None:
                        self.mover.set_target(mothership.pos)
            else:
                # Navigate to asteroid
                self.mover.set_target(self.mining_target.pos)

        # Returning to mothership to unload
        if self.returning_to_ship and mothership is not None:
            # steer toward mothership
            self.mover.set_target(mothership.pos)
            # If close enough, start unloading
            dist_ms = (mothership.pos - self.pos).length()
            if dist_ms <= 60.0:
                # unload over time
                self.mining_fill = max(0.0, self.mining_fill - self.UNLOAD_RATE * dt)
                # When emptied, deliver goods and reset
                if self.mining_fill <= 0.0:
                    # Determine amount of ore delivered using asteroid purity
                    if self.mining_target is not None:
                        amount = int(round(self.mining_capacity * float(self.mining_target.purity)))
                        # Add to mothership inventory via method if available
                        if hasattr(mothership, 'add_resource'):
                            mothership.add_resource(self.mining_target.ore_type, amount)
                    # Reset fill and continue mining loop (go back to asteroid)
                    self.mining_fill = 0.0
                    self.returning_to_ship = False
                    # If there's still a mining target, head back to it to continue mining
                    if self.mining_target is not None:
                        self.mover.set_target(self.mining_target.pos)

    # --------------- Drawing ---------------
    def draw(self, surface, show_range=False):
        # Draw the ship sprite and health/armor bars from base class
        super().draw(surface, show_range=show_range)

        # If currently carrying or filling, draw orange mining meter above health bar
        if self.mining_fill <= 0.0:
            return

        # Compute same bar geometry as SpaceUnit.draw
        surf, _ = self.get_rotated_sprite()
        rect = self.get_sprite_rect(surf)

        bar_w = max(40, min(140, int(self.ship_size[0])))
        bar_h = 6
        pad = 6
        bar_x = rect.centerx - bar_w // 2
        bar_y = rect.top - pad - bar_h

        # Mining bar sits one bar above the health bar
        mining_y = bar_y - (bar_h + 4)

        pct = max(0.0, min(1.0, float(self.mining_fill) / float(self.mining_capacity)))

        bg_rect = pygame.Rect(bar_x, mining_y, bar_w, bar_h)
        pygame.draw.rect(surface, (40, 40, 40), bg_rect, border_radius=3)

        fill_w = int(bar_w * pct + 0.5)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, mining_y, fill_w, bar_h)
            pygame.draw.rect(surface, (255, 160, 40), fill_rect, border_radius=3)

        pygame.draw.rect(surface, (10, 10, 10), bg_rect, 1, border_radius=3)
