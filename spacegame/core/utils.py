import random
import pygame
from spacegame.core.projectile import Projectile
from spacegame.models.units.pirate_frigate import PirateFrigate


def spawn_enemy_wave(width, height, location_data, enemy_group, enemy_fleet, count=1):
    """Spawn `count` PirateFrigate enemies at random edge positions and add them to groups."""
    margin = 40
    for _ in range(max(1, count)):
        edge = random.randrange(4)
        if edge == 0:  # top
            x = random.uniform(margin, width - margin)
            y = -random.uniform(20, 120)
        elif edge == 1:  # right
            x = width + random.uniform(20, 120)
            y = random.uniform(margin, height - margin)
        elif edge == 2:  # bottom
            x = random.uniform(margin, width - margin)
            y = height + random.uniform(20, 120)
        else:  # left
            x = -random.uniform(20, 120)
            y = random.uniform(margin, height - margin)

        new_enemy = PirateFrigate((x, y))
        enemy_fleet.append(new_enemy)
        if isinstance(new_enemy, pygame.sprite.Sprite):
            enemy_group.add(new_enemy)


def handle_auto_fire(source_fleet, target_fleet, projectile_group, owner_is_enemy=False, color=(255, 240, 120), speed_factor=1.0):
    """Auto-fire helper: iterate source_fleet and spawn projectiles toward nearest targets in target_fleet.
    `speed_factor` multiplies `Projectile.SPEED` when constructing enemy projectiles.
    """
    if not target_fleet:
        return
    for s in source_fleet:
        if getattr(s, 'bullet_damage', 0) <= 0:
            continue
        nearest = min(target_fleet, key=lambda e: (e.pos - s.pos).length_squared())
        if s.is_target_in_range(nearest) and s.ready_to_fire():
            dirv = (nearest.pos - s.pos)
            kwargs = {
                'hull_damage': s.bullet_damage,
                'armor_damage': getattr(s, 'armor_damage', 0),
                'color': color,
                'owner_is_enemy': owner_is_enemy,
            }
            if speed_factor != 1.0:
                kwargs['speed'] = Projectile.SPEED * float(speed_factor)

            proj = Projectile(s.pos, dirv, **kwargs)
            projectile_group.add(proj)
            try:
                s.reset_cooldown()
            except Exception:
                pass


def handle_projectile_collisions(projectile_group, player_fleet, enemy_fleet):
    """Resolve projectile collisions and apply damage to fleets."""
    for proj in list(projectile_group):
        try:
            if getattr(proj, 'owner_is_enemy', False):
                for p in player_fleet:
                    if proj.collides_with_shape(p):
                        if getattr(p, 'max_armor', 0) > 0 and getattr(p, 'armor', 0) > 0:
                            p.take_armor_damage(proj.armor_damage)
                        else:
                            p.take_damage(proj.hull_damage)
                        try:
                            proj.explode()
                        except Exception:
                            try:
                                proj.kill()
                            except Exception:
                                pass
                        break
            else:
                for e in enemy_fleet:
                    if proj.collides_with_shape(e):
                        if getattr(e, 'max_armor', 0) > 0 and getattr(e, 'armor', 0) > 0:
                            e.take_armor_damage(proj.armor_damage)
                        else:
                            e.take_damage(proj.hull_damage)
                        try:
                            proj.explode()
                        except Exception:
                            try:
                                proj.kill()
                            except Exception:
                                pass
                        break
        except Exception:
            try:
                proj.explode()
            except Exception:
                try:
                    proj.kill()
                except Exception:
                    pass
