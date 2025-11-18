from abc import ABC, abstractmethod
import pygame
from mover import Mover
from pygame.math import Vector2
import math

class SpaceUnit(ABC):
    # ---- Class-level defaults for player shapes ----
    DEFAULT_COLOR = (255, 200, 0)
    DEFAULT_SPEED = 300.0
    DEFAULT_ROT_SPEED = 360.0
    DEFAULT_FIRE_RANGE = 230.0
    DEFAULT_FIRE_COOLDOWN = 0.55
    DEFAULT_BULLET_DAMAGE = 12.0

    COLLISION_DPS = 20.0

    @abstractmethod
    def shape_id(self):
        """Abstract marker so this class cannot be instantiated."""
        pass

    def __init__(self, start_pos, ship_size=(60, 30), *, color=None, speed=None,
                 rotation_speed=None, is_enemy=False, fire_range=None,
                 fire_cooldown=None, bullet_damage=None):
        
        # resolve defaults from class
        self.ship_size = ship_size
        self.color = color if color is not None else self.DEFAULT_COLOR
        self.is_enemy = is_enemy
        self.fire_range = float(fire_range if fire_range is not None else self.DEFAULT_FIRE_RANGE)
        self.fire_cooldown = float(fire_cooldown if fire_cooldown is not None else self.DEFAULT_FIRE_COOLDOWN)
        self.bullet_damage = float(bullet_damage if bullet_damage is not None else self.DEFAULT_BULLET_DAMAGE)

        # base (unrotated) surface of the rectangle
        self.base_surf = pygame.Surface(ship_size, pygame.SRCALPHA)
        pygame.draw.rect(self.base_surf, self.color, self.base_surf.get_rect())

        # movement component
        spd = float(speed if speed is not None else self.DEFAULT_SPEED)
        rot_spd = float(rotation_speed if rotation_speed is not None else self.DEFAULT_ROT_SPEED)
        self.mover = Mover(start_pos, ship_size=ship_size, speed=spd, rotation_speed=rot_spd)

        # --- Health (floats) ---
        self.max_health = 100.0
        self.health = 100.0

        # --- Shooting cooldown ---
        self.cooldown_timer = 0.0

        # cache for collision mask by angle
        self._last_angle_for_mask = None
        self._last_mask = None
        self._last_rot_surf = None

    # --------------- Proxy properties to mover ---------------
    @property
    def pos(self) -> Vector2:
        return self.mover.world_pos

    @property
    def angle(self) -> float:
        return self.mover.angle

    @property
    def selected(self) -> bool:
        return self.mover.is_selected

    @selected.setter
    def selected(self, val: bool):
        if self.is_enemy:
            self.mover.is_selected = False
        else:
            self.mover.is_selected = val

    # --------------- Health API ---------------
    def set_health(self, value):
        v = float(value)
        self.health = max(0.0, min(v, float(self.max_health)))

    def take_damage(self, amount):
        self.set_health(self.health - float(amount))

    def heal(self, amount):
        self.set_health(self.health + float(amount))

    # --------------- Shooting API ---------------
    def update_cooldown(self, dt):
        self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def ready_to_fire(self) -> bool:
        return self.cooldown_timer <= 0.0

    def reset_cooldown(self):
        self.cooldown_timer = self.fire_cooldown

    # --------------- Helpers ---------------
    def get_rotated_sprite(self):
        # Return rotated surface at current angle (may reuse cached surf/mask).
        if self._last_angle_for_mask != self.angle or self._last_rot_surf is None:
            self._last_rot_surf = pygame.transform.rotate(self.base_surf, self.angle)
            self._last_mask = pygame.mask.from_surface(self._last_rot_surf)
            self._last_angle_for_mask = self.angle
        return self._last_rot_surf, self._last_mask

    def get_sprite_rect(self, surf):
        # Return rect of given surface centered at current position (always recomputed).
        return surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def collides_with(self, other) -> bool:
        # Pixel-perfect collision check between two rotated rectangles.
        surf_a, mask_a = self.get_rotated_sprite()
        rect_a = self.get_sprite_rect(surf_a)
        surf_b, mask_b = other.get_rotated_sprite()
        rect_b = other.get_sprite_rect(surf_b)
        offset = (rect_b.left - rect_a.left, rect_b.top - rect_a.top)
        return mask_a.overlap(mask_b, offset) is not None

    def bounding_radius(self) -> float:
        # radius of the rectangle's circumcircle
        return math.hypot(self.ship_size[0], self.ship_size[1]) * 0.5

    # --------------- Drawing ---------------
    def draw(self, surface, show_range=False):
        surf, _ = self.get_rotated_sprite()
        rect = self.get_sprite_rect(surf)
        surface.blit(surf, rect.topleft)

        if self.selected and not self.is_enemy:
            pygame.draw.rect(surface, (0, 255, 0), rect, 2, border_radius=2)

        # --- Optional: range circle (for players when selected) ---
        if show_range:
            pygame.draw.circle(surface, (70, 90, 120), (int(self.pos.x), int(self.pos.y)), int(self.fire_range), 1)

        # --- Floating health bar above the box ---
        bar_w = max(40, min(140, int(self.ship_size[0])))
        bar_h = 6
        pad = 6
        bar_x = rect.centerx - bar_w // 2
        bar_y = rect.top - pad - bar_h

        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (40, 40, 40), bg_rect, border_radius=3)

        pct = max(0.0, min(1.0, self.health / self.max_health)) if self.max_health > 0 else 0.0
        fill_w = int(bar_w * pct + 0.5)

        fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=3)

        pygame.draw.rect(surface, (10, 10, 10), bg_rect, 1, border_radius=3)

    def point_inside(self, point):
        return self.mover.point_inside(point)


class PirateFrigate(SpaceUnit):
    # ---- Enemy defaults ----
    DEFAULT_COLOR = (220, 60, 60)
    DEFAULT_SPEED = 140.0
    DEFAULT_ROT_SPEED = 240.0
    DEFAULT_FIRE_RANGE = 260.0
    DEFAULT_FIRE_COOLDOWN = 0.8
    DEFAULT_BULLET_DAMAGE = 10.0

    def shape_id(self):
        return "pirate"

    def __init__(self, start_pos, size=(60, 30), **kwargs):
        # Force enemy flags/defaults but allow explicit overrides via kwargs
        kwargs.setdefault('color', self.DEFAULT_COLOR)
        kwargs.setdefault('speed', self.DEFAULT_SPEED)
        kwargs.setdefault('rotation_speed', self.DEFAULT_ROT_SPEED)
        kwargs.setdefault('is_enemy', True)
        kwargs.setdefault('fire_range', self.DEFAULT_FIRE_RANGE)
        kwargs.setdefault('fire_cooldown', self.DEFAULT_FIRE_COOLDOWN)
        kwargs.setdefault('bullet_damage', self.DEFAULT_BULLET_DAMAGE)
        super().__init__(start_pos, ship_size=size, **kwargs)

class ExpeditionShip(SpaceUnit):
    """Main player-controlled rectangle with a 3-slot hangar."""

    def shape_id(self):
        return "expeditionship"

    def __init__(self, start_pos, **kwargs):
        super().__init__(start_pos, ship_size=(80, 40), **kwargs)

        # 3 hangar slots for light ships
        # True = interceptor in hangar (assigned & not currently deployed)
        self.hangar = [False, False, False]
        self.deployed = []                      # stores spawned Interceptor objects
        self.hangar_ships = [None, None, None]  # fighters for each slot (after deploy)
        self.last_selected_light_craft = None

        # Persistent interceptor pool for fleet management (5 total for now)
        if not hasattr(self, "interceptor_pool"):
            self.interceptor_pool = [
                {"id": i, "name": f"Interceptor {i+1}", "alive": True}
                for i in range(5)
            ]

        # Which pool interceptor is assigned to each hangar slot (or None)
        if not hasattr(self, "hangar_assignments"):
            self.hangar_assignments = [None, None, None]
            # Default: assign first interceptors to slots, up to 3
            alive_ids = [e["id"] for e in self.interceptor_pool if e.get("alive", False)]
            for slot in range(3):
                if slot < len(alive_ids):
                    self.hangar_assignments[slot] = alive_ids[slot]
                    self.hangar[slot] = True

    def can_deploy(self, slot):
        return 0 <= slot < 3 and self.hangar[slot]

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
        offset = Vector2(50, 0).rotate(-self.angle)
        icpt = Interceptor(self.pos + offset, interceptor_id=interceptor_id)
        icpt.mover.angle = self.angle    # start facing same direction

        # Remember which slot this light craft came from
        icpt.hangar_slot = slot
        icpt.recalling = False

        self.deployed.append(icpt)
        self.hangar_ships[slot] = icpt
        return icpt


class Frigate(SpaceUnit):
    """Escort frigate for the ExpeditionShip."""

    def shape_id(self):
        return "friagate"

    def __init__(self, start_pos, **kwargs):
        super().__init__(start_pos, ship_size=(70, 40), **kwargs)

class Interceptor(SpaceUnit):
    """Small deployable interceptor light craft."""

    def shape_id(self):
        return "interceptor"

    def __init__(self, start_pos, interceptor_id=None, **kwargs):
        super().__init__(start_pos, ship_size=(40, 40), **kwargs)

        # id in the ExpeditionShip's interceptor pool (if any)
        self.interceptor_id = interceptor_id

        # create triangle surface
        self.base_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(
            self.base_surf,
            self.color,
            [(20, 0), (0, 40), (40, 40)]
        )

        # recall state
        self.recalling = False
        self.hangar_slot = None