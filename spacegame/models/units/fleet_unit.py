from abc import ABC, abstractmethod
import pygame
from spacegame.core.mover import Mover
from pygame.math import Vector2
from spacegame.config import (
    PLAYER_DEFAULT_SPEED,
    PLAYER_DEFAULT_ROT_SPEED,
    PLAYER_DEFAULT_FIRE_RANGE,
    PLAYER_DEFAULT_FIRE_COOLDOWN,
    PLAYER_DEFAULT_BULLET_DAMAGE,
    PLAYER_DEFAULT_ARMOR_DAMAGE,
)
import math

class SpaceUnit(pygame.sprite.Sprite, ABC):
    # ---- Class-level defaults for player shapes ----
    DEFAULT_COLOR = (255, 200, 0)
    DEFAULT_SPEED = PLAYER_DEFAULT_SPEED
    DEFAULT_ROT_SPEED = PLAYER_DEFAULT_ROT_SPEED
    DEFAULT_FIRE_RANGE = PLAYER_DEFAULT_FIRE_RANGE
    DEFAULT_FIRE_COOLDOWN = PLAYER_DEFAULT_FIRE_COOLDOWN
    DEFAULT_BULLET_DAMAGE = PLAYER_DEFAULT_BULLET_DAMAGE
    DEFAULT_ARMOR_DAMAGE  = PLAYER_DEFAULT_ARMOR_DAMAGE

    COLLISION_DPS = 20.0

    @abstractmethod
    def shape_id(self):
        """Abstract marker so this class cannot be instantiated."""
        pass

    @abstractmethod
    def get_tier(self) -> int:
        """Return this unit's tier."""
        pass

    def __init__(self, start_pos, ship_size=(60, 30), *, color=None, speed=None,
                 rotation_speed=None, is_enemy=False, fire_range=None,
                 fire_cooldown=None, bullet_damage=None, armor_damage=None, rarity: str = "common"):
        # initialize as sprite
        pygame.sprite.Sprite.__init__(self)

        # resolve defaults from class
        self.ship_size = ship_size
        self.color = color if color is not None else self.DEFAULT_COLOR
        self.is_enemy = is_enemy
        self.rarity = str(rarity).lower()
        self.fire_range = float(fire_range if fire_range is not None else self.DEFAULT_FIRE_RANGE)
        self.fire_cooldown = float(fire_cooldown if fire_cooldown is not None else self.DEFAULT_FIRE_COOLDOWN)
        self.bullet_damage = float(bullet_damage if bullet_damage is not None else self.DEFAULT_BULLET_DAMAGE)
        self.armor_damage = float(armor_damage if armor_damage is not None else self.DEFAULT_ARMOR_DAMAGE)

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

        # --- Armor (floats) ---
        self.max_armor = 0.0
        self.armor = 0.0

        # --- Shooting cooldown ---
        self.cooldown_timer = 0.0

        # cache for collision mask by angle
        self._last_angle_for_mask = None
        self._last_mask = None
        self._last_rot_surf = None

        # initialize sprite image/rect/mask
        self.image = self.base_surf.copy()
        self.rect = self.image.get_rect(center=(int(self.mover.world_pos.x), int(self.mover.world_pos.y)))
        try:
            self.mask = pygame.mask.from_surface(self.image)
        except Exception:
            self.mask = None

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

    # --------------- Armor API ---------------
    def set_armor(self, value):
        v = float(value)
        self.armor = max(0.0, min(v, float(self.max_armor)))

    def take_armor_damage(self, amount):
        self.set_armor(self.armor - float(amount))

    def heal_armor(self, amount):
        self.set_armor(self.armor + float(amount))

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

    def update(self, dt: float = 0.016):
        # Keep sprite image/rect/mask in sync with mover/rotation
        # Update mover is done externally; here we recompute rotated image
        surf, mask = self.get_rotated_sprite()
        self.image = surf
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        try:
            self.mask = mask
        except Exception:
            try:
                self.mask = pygame.mask.from_surface(self.image)
            except Exception:
                self.mask = None

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


    def is_target_in_range(self, other: "SpaceUnit", radius: float | None = None) -> bool:
        """Return True if a targeting circle around this unit reaches any part of 'other'.

        The effective radius is:
            (radius or self.fire_range) + other.bounding_radius().

        This matches the previous in_range(a, b, r) helper from gameScreen.py.
        """
        r = radius if radius is not None else self.fire_range
        dist2 = (self.pos - other.pos).length_squared()
        eff_r = r + other.bounding_radius()
        return dist2 <= eff_r * eff_r

    # --------------- Drawing ---------------
    def draw_overlay(self, surface, show_range=False):
        # Draw optional range circle (for players when selected)
        rect = self.rect
        if show_range:
            pygame.draw.circle(surface, (70, 90, 120), (int(self.pos.x), int(self.pos.y)), int(self.fire_range), 1)

        # Floating health bar above the ship
        show_bars = False
        try:
            if getattr(self, 'max_health', 0) > 0 and self.health < self.max_health:
                show_bars = True
            if getattr(self, 'max_armor', 0) > 0 and self.armor < self.max_armor:
                show_bars = True
        except Exception:
            show_bars = False

        if show_bars:
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
            # health bar border
            pygame.draw.rect(surface, (10, 10, 10), bg_rect, 1, border_radius=3)

            # Armor bar (if this unit has armor)
            if getattr(self, 'max_armor', 0) > 0:
                armor_bar_y = bar_y + bar_h + 2
                armor_bg_rect = pygame.Rect(bar_x, armor_bar_y, bar_w, bar_h)
                pygame.draw.rect(surface, (20, 40, 70), armor_bg_rect, border_radius=3)

                armor_pct = max(0.0, min(1.0, self.armor / self.max_armor)) if self.max_armor > 0 else 0.0
                armor_fill_w = int(bar_w * armor_pct + 0.5)
                if armor_fill_w > 0:
                    armor_fill_rect = pygame.Rect(bar_x, armor_bar_y, armor_fill_w, bar_h)
                    pygame.draw.rect(surface, (90, 190, 255), armor_fill_rect, border_radius=3)

                pygame.draw.rect(surface, (10, 10, 10), armor_bg_rect, 1, border_radius=3)

    def point_inside(self, point):
        return self.mover.point_inside(point)
