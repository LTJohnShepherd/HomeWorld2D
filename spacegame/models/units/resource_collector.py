import pygame
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.config import IMAGES_DIR
from spacegame.core.effects import spawn_dust
from spacegame.core.sound_manager import get_sound_manager


class ResourceCollector(SpaceUnit):
    """Deployable support craft that can heal allied ships and mine asteroids.

    The collector handles two main responsibilities:
    - Healing: navigate to allied ships and transfer armor/health over time.
    - Mining: extract ore from asteroids, carry it, and unload at the mothership.
    """

    # Healing configuration: amount healed per second and effective range (pixels)
    HEAL_RATE = 15.0
    HEAL_RANGE = 60.0

    def shape_id(self):
        return "resource_collector"

    def get_tier(self) -> int:
        # tier is stored per ship instance; default 0 like other ships.
        return getattr(self, "tier", 0)

    def __init__(self, start_pos, collector_id=None, tier: int = 0, **kwargs):
        # per-instance tier (default 0)
        self.tier = tier

        # Load, orient, and scale the collector sprite used for rendering.
        sprite = pygame.image.load(IMAGES_DIR + "/ResourceCollector.png").convert_alpha()
        sprite = pygame.transform.rotate(sprite, -90)
        scaled_sprite = pygame.transform.smoothscale(sprite, (sprite.get_width() // 24, sprite.get_height() // 24))

        # Initialize base visual / collision size from the scaled sprite.
        super().__init__(start_pos, ship_size=scaled_sprite.get_size(), rarity="common", **kwargs)
        self.base_surf = scaled_sprite

        # Optional pool identifier assigned by the mothership's Hangar
        self.collector_id = collector_id

        # Hangar/docking flags
        self.recalling = False
        self.hangar_slot = None

        # Mothership reference is set by Hangar.on_deployed when spawned
        self.mothership = None

        # Combat/health values
        self.bullet_damage = 0.0
        self.armor_damage = 0.0
        self.max_health = 2100.0
        self.health = self.max_health
        self.max_armor = 210.0
        self.armor = self.max_armor

        # Healing state: target ship to heal (or None)
        self.healing_target = None

        # Mining state: current asteroid, carried fill and rates/capacity
        self.mining_target = None
        self.mining_fill = 0.0
        self.mining_capacity = 150.0
        self.MINE_RATE = 10.0
        self.MINE_RANGE = 60.0
        self.returning_to_ship = False
        self.UNLOAD_RATE = 75.0

        # Visual overlay radius used by UI; keep in sync with heal range
        self.fire_range = float(self.HEAL_RANGE)

    def start_healing(self, target):
        """Set the target ship to heal. This will cancel any previous healing."""
        self.cancel_mining()
        self.healing_target = target
        # Navigate to the target
        self.mover.set_target(target.pos)
        # Play repair command sound
        try:
            sound_manager = get_sound_manager()
            sound_manager.on_repair_command()
        except Exception:
            pass

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
        # Cancel any healing first
        self.cancel_healing()
        # If already carrying or filling, immediately dump current contents to space
        try:
            self.stop_and_dump()
        except Exception:
            # fallback: clear mining state fields
            self.mining_target = None
            self.mining_fill = 0.0
            self.returning_to_ship = False

        # Start mining the new asteroid
        self.mining_target = asteroid
        self.returning_to_ship = False
        # navigate to asteroid
        self.mover.set_target(asteroid.pos)
        
        # Play harvest command sound
        try:
            sound_manager = get_sound_manager()
            sound_manager.on_harvest_command()
        except Exception:
            pass

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

        # If we've been ordered to recall, cancel any active mining and go home.
        # We intentionally dump held resources to space (stop_and_dump) so the
        # collector does not try to unload or resume mining before docking.
        if getattr(self, "recalling", False):
            # Immediately stop mining and drop carried fill (dump to space)
            try:
                self.stop_and_dump()
            except Exception:
                # fallback: clear fields
                self.mining_target = None
                self.mining_fill = 0.0
                self.returning_to_ship = False
            # Ensure we head straight to mothership to dock
            if mothership is not None:
                self.mover.set_target(mothership.pos)


        # Active mining at asteroid
        if self.mining_target is not None and not self.returning_to_ship:
            # Distance to asteroid
            dist = (self.mining_target.pos - self.pos).length()
            if dist <= self.MINE_RANGE:
                # Stop moving and mine
                self.mover.set_target(self.pos)
                self.mining_fill = min(self.mining_capacity, self.mining_fill + self.MINE_RATE * dt)
                # Spawn a small dust cloud at the asteroid while mining
                try:
                    # match dust parameters used when ships fire projectiles
                    spawn_dust(self.mining_target.pos, color=(200, 180, 140), count=26, speed=44.0, radius=3.5, lifetime=0.825, scale=1.2)
                except Exception:
                    # Non-fatal: if effects subsystem isn't available, ignore
                    pass
                # When full, set to return to mothership
                if self.mining_fill >= self.mining_capacity:
                    self.mining_fill = self.mining_capacity
                    # Play resource collector full sound
                    try:
                        sound_manager = get_sound_manager()
                        sound_manager.on_resource_collector_full()
                    except Exception:
                        pass
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
                        # Add to mothership inventory via InventoryManager
                        # This intentionally requires a registered InventoryManager on the mothership.
                        if mothership is None:
                            raise RuntimeError("ResourceCollector has no mothership to deliver resources to")
                        inv = getattr(mothership, 'inventory_manager', None)
                        if inv is None:
                            raise RuntimeError("Mothership missing InventoryManager; migration required")
                        inv.add_resource(self.mining_target.ore_type, amount)
                        # Play resource transfer sound
                        try:
                            sound_manager = get_sound_manager()
                            sound_manager.on_resource_transfer()
                        except Exception:
                            pass
                    # Reset fill and continue mining loop (go back to asteroid)
                    self.mining_fill = 0.0
                    self.returning_to_ship = False
                    # If there's still a mining target, head back to it to continue mining
                    if self.mining_target is not None:
                        self.mover.set_target(self.mining_target.pos)

    # --------------- Drawing ---------------
    def draw_overlay(self, surface, show_range=False):
        # Draw overlays (sprite image is handled by sprite groups)
        super().draw_overlay(surface, show_range=show_range)

        # If currently carrying or filling, draw orange mining meter above health bar
        if self.mining_fill <= 0.0:
            return

        # Compute same bar geometry as SpaceUnit.draw_overlay
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
