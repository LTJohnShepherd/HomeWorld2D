import pygame
from pygame.math import Vector2
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.models.units.pirate_frigate import PirateFrigate
from spacegame.models.units.expedition_ship import ExpeditionShip
from spacegame.models.units.frigate import Frigate
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.resource_collector import ResourceCollector
from spacegame.models.asteroids.asteroidm import MineableAsteroidM
from spacegame.core.mover import Mover
from spacegame.core.projectile import Projectile
from spacegame.ui.hud_ui import HudUI
from spacegame.ui.ui import Button, draw_triangle, draw_diamond, draw_dalton, draw_hex, OREM_PREVIEW_IMG
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    SEPARATION_ITER,
    IMAGES_DIR,
)
from spacegame.screens.internal_screen import internal_screen

def update_projectiles(projectiles, player_fleet, enemy_fleet, dt):
    """Update projectiles and apply hit damage, returning the filtered list."""
    for b in projectiles:
        b.update(dt)
        if not getattr(b, "is_active", False):
            continue

        # When owner_is_enemy=True, bullets fly from enemies toward player fleet.
        if getattr(b, "owner_is_enemy", False):
            hit = None
            for p in player_fleet:
                if b.collides_with_shape(p):
                    hit = p
                    break
            if hit is not None:
                # Apply armor damage first, if the ship has armor remaining.
                if getattr(hit, "max_armor", 0) > 0 and getattr(hit, "armor", 0) > 0:
                    hit.take_armor_damage(b.armor_damage)
                else:
                    hit.take_damage(b.hull_damage)
                b.is_active = False
        else:
            hit = None
            for e in enemy_fleet:
                if b.collides_with_shape(e):
                    hit = e
                    break
            if hit is not None:
                if getattr(hit, "max_armor", 0) > 0 and getattr(hit, "armor", 0) > 0:
                    hit.take_armor_damage(b.armor_damage)
                else:
                    hit.take_damage(b.hull_damage)
                b.is_active = False

    return [b for b in projectiles if getattr(b, "is_active", False)]


def handle_collisions(player_fleet, enemy_fleet, dt):
    """Handle separation and collision damage between ships."""
    # Separation: keep ships from overlapping too much
    for _ in range(SEPARATION_ITER):
        # Player-player separation
        for i, a in enumerate(player_fleet):
            for b in player_fleet[i + 1:]:
                # Light crafts push each other
                # but don't push larger ships
                if isinstance(a, (Interceptor, ResourceCollector)) and isinstance(b, (Interceptor, ResourceCollector)):
                    Mover.separate_rotated(a, b)
                elif not isinstance(a, (Interceptor, ResourceCollector)) and not isinstance(b, (Interceptor, ResourceCollector)):
                    Mover.separate_rotated(a, b)

        # Enemy-enemy separation
        for i, a in enumerate(enemy_fleet):
            for b in enemy_fleet[i + 1:]:
                Mover.separate_rotated(a, b)

        # NEW: Player-enemy separation (so big ships push enemies instead of clipping)
        for p in player_fleet:
            for e in enemy_fleet:
                Mover.separate_rotated(p, e)

    # Player-enemy collision damage (unchanged)
    for p in player_fleet:
        for e in enemy_fleet:
            if p.collides_with(e):
                dmg = SpaceUnit.COLLISION_DPS * dt
                if getattr(p, 'max_armor', 0) > 0 and getattr(p, 'armor', 0) > 0:
                    p.take_armor_damage(dmg)
                else:
                    p.take_damage(dmg)
                if getattr(e, 'max_armor', 0) > 0 and getattr(e, 'armor', 0) > 0:
                    e.take_armor_damage(dmg)
                else:
                    e.take_damage(dmg)


def draw_hex_button(surface, button, font, base_color, hover_color, header_text):
    rect = button.rect
    mouse_pos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mouse_pos) else base_color

    # hex body
    draw_hex(surface, rect.center, rect.width * 0.9, rect.height * 1.2, color, 3)

    # "INTERNAL" text at top-left of the hex
    label = font.render(header_text, True, color)
    label_rect = label.get_rect()
    # slightly above and to the left of the hex body
    label_rect.bottomleft = (rect.left, rect.top - 10)
    surface.blit(label, label_rect)


def run_game():
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SpaceGame")

    # --- Load skybox background ---
    background_img = pygame.image.load(IMAGES_DIR + "/Skybox.png").convert()
    background_img = pygame.transform.smoothscale(background_img, (WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    # --- Hangar UI setup ---
    font = pygame.font.SysFont(None, 20)
    hangar_interface = HudUI(font)

    # --- Fleet management button (top-left) ---
    fleet_btn_font = pygame.font.SysFont(None, 19)
    fleet_btn = Button((10, 40, 100, 30), "INTERNAL", fleet_btn_font)

    # --- Main player (ExpeditionShip with hangar) ---
    main_player = ExpeditionShip((400, 300))

    player_fleet = [
        main_player,
        Frigate((500, 400))
        ]

    # Spawn demo mineable asteroids (purity is 0.5 => 50%)
    asteroids = [MineableAsteroidM((600, 250), purity=0.5)]

    enemy_fleet = [
        #PirateFrigate((100, 100)),
        PirateFrigate((700, 120)),
        #PirateFrigate((120, 500)),
    ]

    projectiles = []

    is_selecting = False # Flag that indicates if the player is currently dragging a selection box with the mouse
    selection_start = (0, 0) # The starting mouse position where the left button was first pressed (selection begins here)
    selection_rect = pygame.Rect(0, 0, 0, 0) # ExpeditionShip used to visually and logically represent the drag-selection area

    while True:
        dt = clock.tick(FPS) / 1000.0
        # Ignore huge dt spikes (e.g. when coming back from INTERNAL screen)
        if dt > 0.3:      # threshold in seconds, tweak if you want
            dt = 0.0      # treat that frame as “paused”
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit" # "exit"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "main_menu" # "main_menu"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # First: fleet management button
                if fleet_btn.handle_event(event):
                    res = internal_screen(main_player, player_fleet)
                    if res == "to_game":
                        # Orange X from any internal screen chain: already back in game.
                        # Treat as a fresh slate; no extra action needed.
                        pass
                    # after returning, skip further handling of this click
                    continue

                # Then let the hangar UI handle deploy/recall buttons and preview toggles.
                clicked_ui = hangar_interface.handle_mouse_button_down(event.pos, main_player, player_fleet)

                if not clicked_ui:
                    hangar_interface.close_all_previews()

                # Check for click-to-mine / click-to-heal with selected resource collectors
                if not clicked_ui:
                    selected_collectors = [s for s in player_fleet if isinstance(s, ResourceCollector) and s.selected]
                    if selected_collectors:
                        # First: if clicking an asteroid, start mining
                        clicked_asteroid = None
                        for a in asteroids:
                            if a.point_inside(event.pos):
                                clicked_asteroid = a
                                break
                        if clicked_asteroid is not None:
                            for collector in selected_collectors:
                                collector.start_mining(clicked_asteroid)
                            clicked_ui = True
                        else:
                            # Otherwise, check if clicking on a ship that can be healed (not the collector itself)
                            target_ship = None
                            for ship in player_fleet:
                                if ship not in selected_collectors and ship.point_inside(event.pos):
                                    target_ship = ship
                                    break
                            if target_ship:
                                # Start healing with all selected collectors
                                for collector in selected_collectors:
                                    collector.start_healing(target_ship)
                                clicked_ui = True  # Mark as handled

                # Start selection if clicked elsewhere
                if not clicked_ui:
                    is_selecting = True  # Start drag-selection when the left mouse button is pressed
                    selection_start = event.pos  # Remember the mouse position at the moment selection started
                    # Initialize the selection rectangle starting at the mouse position
                    selection_rect = pygame.Rect(event.pos, (0, 0))
                    for spaceship in player_fleet:
                        # Select a spaceship immediately if the click is directly on it (without drag)
                        spaceship.selected = spaceship.point_inside(event.pos)
            elif event.type == pygame.MOUSEMOTION and is_selecting:
                mx, my = event.pos # Current mouse position while dragging
                sx, sy = selection_start # The initial selection starting point (mouse down position)
                selection_rect.width = mx - sx # Update selection rectangle width based on how far the mouse moved horizontally
                selection_rect.height = my - sy # Update selection rectangle height based on how far the mouse moved vertically
           
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                is_selecting = False # Stop drag-selection when the left mouse button is released
                rect = selection_rect.copy()
                rect.normalize() # Ensure the rectangle has positive width and height regardless of drag direction
                if rect.width > 5 and rect.height > 5:
                    for spaceship in player_fleet:
                        spaceship.selected = rect.collidepoint(spaceship.pos) # Mark shapes as selected if their position is inside the final selection rectangle
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Collect selected shapes, but ignore recalled fighters
                selected_shapes = [
                    s for s in player_fleet
                    if s.selected and not getattr(s, "recalling", False)
                ]
                if selected_shapes:
                    # Cancel healing for any selected resource collectors
                    for shape in selected_shapes:
                        if isinstance(shape, ResourceCollector):
                            # stop healing and also abort mining and clear the fill
                            shape.cancel_healing()
                            # stop_and_dump resets mining_fill and clears mining_target
                            try:
                                shape.stop_and_dump()
                            except Exception:
                                pass
                    
                    # Calculate the average position (center) of all selected shapes (formation center)
                    center = sum((s.pos for s in selected_shapes), Vector2(0, 0)) / len(selected_shapes)
                    for s in selected_shapes:
                        s.mover.formation_offset = s.pos - center # Store each spaceship's offset from the formation center (to preserve relative positions)
                    center_target = Vector2(event.pos)  # Target point for the group movement is where the player right-clicked
                    for s in selected_shapes:
                        s.mover.set_target(center_target + s.mover.formation_offset) # Set individual targets so shapes move in formation relative to the clicked position

        # --- Update cooldowns ---
        for s in player_fleet + enemy_fleet:
            s.update_cooldown(dt)

        # Update expedition ship notifications (timers)
        try:
            main_player.update_notifications(dt)
        except Exception:
            pass

        # --- Update healing and mining for resource collectors ---
        for collector in [s for s in player_fleet if isinstance(s, ResourceCollector)]:
            collector.update_healing(dt)
            collector.update_mining(dt)

        # --- Update movement ---
        for spaceship in player_fleet:
            spaceship.mover.update(dt)
        # --- Handle recalled fighters: fly back to main ship and re-dock ---
        recalled_done = []
        for spaceship in player_fleet:
            if isinstance(spaceship, (Interceptor, ResourceCollector)) and getattr(spaceship, "recalling", False):
                # Always steer toward the main ship
                spaceship.mover.set_target(main_player.pos)

                # When close enough, mark for docking
                if (spaceship.pos - main_player.pos).length() < 50:
                    recalled_done.append(spaceship)

        for craft in recalled_done:
            # Remove from active ships; Hangar will take care of internal lists.
            if craft in player_fleet:
                player_fleet.remove(craft)

            # Inform the Hangar that this craft has successfully docked so the corresponding slot becomes ready again.
            main_player.hangar_system.on_recalled(craft)
        # Enemies: approach to within range, then hold
        for e in enemy_fleet:
            if player_fleet:
                closest = min(player_fleet, key=lambda p: (p.pos - e.pos).length_squared())
                dist = (closest.pos - e.pos).length()
                if dist > e.fire_range * 0.95:
                    e.mover.set_target(closest.pos)  # approach
                else:
                    e.mover.set_target(e.pos)  # hold & shoot
            e.mover.update(dt)

        # --- Auto-fire: both sides ---
        for p in player_fleet:
            if not enemy_fleet:
                break
            # Skip firing if unit has 0 damage (e.g., ResourceCollector)
            if p.bullet_damage <= 0:
                continue
            nearest = min(enemy_fleet, key=lambda e: (e.pos - p.pos).length_squared())
            if p.is_target_in_range(nearest) and p.ready_to_fire():
                dirv = (nearest.pos - p.pos)
                projectiles.append(Projectile(p.pos, dirv,
                                        hull_damage=p.bullet_damage,
                                        armor_damage=p.armor_damage,
                                        color=(255,240,120), owner_is_enemy=False))
                p.reset_cooldown()

        for e in enemy_fleet:
            if not player_fleet:
                break
            # Skip firing if unit has 0 damage (shouldn't happen with enemies, but safe)
            if e.bullet_damage <= 0:
                continue
            nearest = min(player_fleet, key=lambda p: (p.pos - e.pos).length_squared())
            if e.is_target_in_range(nearest) and e.ready_to_fire():
                dirv = (nearest.pos - e.pos)
                projectiles.append(Projectile(e.pos, dirv,
                                        hull_damage=e.bullet_damage,
                                        armor_damage=e.armor_damage,
                                        color=(255,120,120), owner_is_enemy=True,
                                        speed=Projectile.SPEED*0.9))
                e.reset_cooldown()

                # --- Update projectiles & handle hits ---
        projectiles = update_projectiles(projectiles, player_fleet, enemy_fleet, dt)



        # Update hangar state for any light crafts that died this frame
        dead_crafts = [
            s for s in player_fleet
            if isinstance(s, (Interceptor, ResourceCollector)) and s.health <= 0.0
        ]
        for craft in dead_crafts:
            # Notify Hangar so it can mark the pool entry dead and clear any slot / assignment.
            main_player.hangar_system.on_interceptor_dead(craft)

        enemy_fleet = [s for s in enemy_fleet if s.health > 0.0]
        player_fleet = [s for s in player_fleet if s.health > 0.0]

        # --- End game when ExpeditionShip dies ---
        if main_player.health <= 0:
            return "end"  # "end"


        # --- Collisions (residual): small damage from touching using class-level DPS ---
        handle_collisions(player_fleet, enemy_fleet, dt)

# --- Draw ---
        screen.blit(background_img, (0, 0))
        # Draw asteroids under ships
        for a in asteroids:
                a.draw(screen)

        for spaceship in player_fleet:
            spaceship.draw(screen, show_range=spaceship.selected)
        for enemy in enemy_fleet:
            enemy.draw(screen)
        
        for spaceship in player_fleet:
            # diamond over frigate with same relative scale as ExpeditionShip hex
            if isinstance(spaceship, Frigate):
                ship_w, ship_h = spaceship.ship_size
                draw_diamond(
                    screen,
                    (spaceship.pos.x, spaceship.pos.y),
                    ship_w * 0.25,   # same width factor as ExpeditionShip hex
                    ship_h * 0.6,     # same height factor as ExpeditionShip hex
                    (80, 255, 190),
                    2
                )
            # triangle over deployed interceptors
            elif isinstance(spaceship, Interceptor) and not getattr(spaceship, "recalling", False):
                    ship_w, ship_h = spaceship.ship_size
                    draw_triangle(
                        screen,
                        (spaceship.pos.x, spaceship.pos.y),
                        ship_w * 1.2,   # Interceptor - relative to its size
                        (80, 255, 190),
                        2
                    )
            # dalton shape over deployed resource collectors (long end pointing down)
            elif isinstance(spaceship, ResourceCollector) and not getattr(spaceship, "recalling", False):
                    ship_w, ship_h = spaceship.ship_size
                    draw_dalton(
                        screen,
                        (spaceship.pos.x, spaceship.pos.y),
                        ship_w * 1.2,
                        ship_h * 1.5,   # ResourceCollector - make it taller
                        (80, 255, 190),
                        2
                    )


        # static outlined hex over the ExpeditionShip (does not rotate)
        moth_center = (main_player.pos.x, main_player.pos.y)
        draw_hex(screen, moth_center, 70, 32, (80, 255, 190), 3)

        for b in projectiles:
            b.draw(screen)

        if is_selecting:
            temp = selection_rect.copy()
            temp.normalize()
            pygame.draw.rect(screen, (100, 255, 100), temp, 1)

        # --- Draw hangar previews & deploy/recall buttons ---
        hangar_interface.draw(screen, main_player, player_fleet)

        # --- Draw fleet management ("INTERNAL") button as hex ---
        draw_hex_button(screen, fleet_btn, fleet_btn_font,
                        base_color=(120, 200, 255),
                        hover_color=(190, 230, 255),
                        header_text="INTERNAL")

        # --- Draw notifications from the mothership (left side under INTERNAL) ---
        # Use main_player.notifications entries (ore_letter, amount, elapsed, duration)
        notif_list = getattr(main_player, 'notifications', [])
        if notif_list:
            # popup sizing
            popup_w = 320
            popup_h = 40
            padding = 8
            icon_size = 32
            base_x = fleet_btn.rect.left
            base_y = fleet_btn.rect.bottom + 8
            small_font = pygame.font.Font(None, 20)
            for idx, n in enumerate(notif_list):
                nx = base_x
                ny = base_y + idx * (popup_h + 6)
                popup_rect = pygame.Rect(nx, ny, popup_w, popup_h)

                # Transparent, borderless popup: icon + text with subtle shadow for contrast
                # icon (use OREM preview for type 'M', otherwise skip)
                try:
                    icon = OREM_PREVIEW_IMG
                    icon_s = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                    screen.blit(icon_s, (nx + padding, ny + (popup_h - icon_size) // 2))
                except Exception:
                    pass

                # text with shadow for readability against varied backgrounds
                ore_letter = n.get('ore_letter', 'M')
                amount = n.get('amount', 0)
                ore_name = 'RU Type M Ore' if ore_letter == 'M' else f'Ore {ore_letter}'
                text = f"Gained: {amount} {ore_name}"
                tx = nx + padding + icon_size + 8
                # center vertically in popup area
                ty = ny + (popup_h - small_font.get_height()) // 2
                # shadow
                shadow_surf = small_font.render(text, True, (0, 0, 0))
                screen.blit(shadow_surf, (tx + 1, ty + 1))
                # main text
                text_surf = small_font.render(text, True, (108, 198, 219))
                screen.blit(text_surf, (tx, ty))

        pygame.display.flip()