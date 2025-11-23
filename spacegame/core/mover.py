import pygame
import math
from pygame.math import Vector2

class Mover:
  
    def __init__(self, start_pos, ship_size=(60, 30), speed=300, rotation_speed=360):
        self.world_pos = Vector2(start_pos)
        self.target_pos = Vector2(start_pos)
        self.ship_size = ship_size
        self.speed = speed
        self.rotation_speed = rotation_speed
        self.angle = 0.0
        self.is_selected = False
        self.formation_offset = Vector2()

    def set_target(self, position):
        self.target_pos = Vector2(position)

    def update(self, dt):
        """Move and rotate smoothly toward the target."""
        direction = self.target_pos - self.world_pos
        distance = direction.length()

        if distance > 0.1:
            move_dist = self.speed * dt
            if move_dist >= distance:
                self.world_pos = self.target_pos
            else:
                self.world_pos += direction.normalize() * move_dist

            desired_angle = math.degrees(math.atan2(-direction.y, direction.x))
            delta_angle = (desired_angle - self.angle + 180) % 360 - 180
            max_rotate = self.rotation_speed * dt

            if abs(delta_angle) < max_rotate:
                self.angle = desired_angle
            else:
                self.angle += max_rotate * (1 if delta_angle > 0 else -1)

    def point_inside(self, point):
        """Axis-aligned bounding box check around self.pos (centered)."""
        w, h = self.ship_size
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.world_pos.x), int(self.world_pos.y))
        return rect.collidepoint(point)

    # ---------------- Collision ----------------
    @staticmethod
    def separate_rotated(ship_a, ship_b):
        """
        Pixel-based collision resolver between two ships.
        Uses their rotated sprite masks instead of big AABBs.
        """
        a = ship_a.mover
        b = ship_b.mover

        surf_a, mask_a = ship_a.get_rotated_sprite()
        surf_b, mask_b = ship_b.get_rotated_sprite()

        rect_a = ship_a.get_sprite_rect(surf_a)
        rect_b = ship_b.get_sprite_rect(surf_b)

        # pixel-perfect overlap check
        offset = (rect_b.left - rect_a.left, rect_b.top - rect_a.top)
        if mask_a.overlap(mask_b, offset) is None:
            return

        dx = rect_a.centerx - rect_b.centerx
        dy = rect_a.centery - rect_b.centery
        overlap_x = (rect_a.width + rect_b.width) / 2 - abs(dx)
        overlap_y = (rect_a.height + rect_b.height) / 2 - abs(dy)

        if overlap_x <= 0 or overlap_y <= 0:
            return

        MAX_PUSH = 2.0  # cap per call

        if overlap_x < overlap_y:
            push_mag = min(overlap_x / 2.0, MAX_PUSH)
            push = Vector2(push_mag * (1 if dx > 0 else -1), 0)
        else:
            push_mag = min(overlap_y / 2.0, MAX_PUSH)
            push = Vector2(0, push_mag * (1 if dy > 0 else -1))

        push *= 0.95
        a.world_pos += push
        b.world_pos -= push