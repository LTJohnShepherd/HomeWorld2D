import pygame
from pygame.math import Vector2
from fleet_unit import SpaceUnit, PirateFrigate, Mothership, Frigate, Interceptor
from mover import Mover
from projectile import Projectile
from hangar_ui import HangarUI
import sys

SEPARATION_ITER = 2  # How many times to push shapes apart when they overlap

def in_range(a, b, r): # Helper function: checks if the distance between objects a and b is within range r

    return (a.pos - b.pos).length_squared() <= r * r

def run_game():
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("SpaceGame")

    clock = pygame.time.Clock()

    # --- Hangar UI setup ---
    font = pygame.font.SysFont(None, 20)
    hangar_interface = HangarUI(font)

    # --- Main player (Mothership with hangar) ---
    main_player = Mothership((400, 300))

    player_fleet = [
        main_player,
        Frigate((500, 400))
        ]

    enemy_fleet = [
        PirateFrigate((100, 100)),
        #PirateFrigate((700, 120)),
        #PirateFrigate((120, 500)),
    ]

    projectiles = []

    is_selecting = False # Flag that indicates if the player is currently dragging a selection box with the mouse
    selection_start = (0, 0) # The starting mouse position where the left button was first pressed (selection begins here)
    selection_rect = pygame.Rect(0, 0, 0, 0) # Mothership used to visually and logically represent the drag-selection area

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # First let the hangar UI handle deploy/recall buttons and preview toggles.
                clicked_ui = hangar_interface.handle_mouse_button_down(event.pos, main_player, player_fleet)

                if not clicked_ui:
                    hangar_interface.close_all_previews()

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

        # --- Update movement ---
        for spaceship in player_fleet:
            spaceship.mover.update(dt)
        # --- Handle recalled fighters: fly back to main ship and re-dock ---
        recalled_done = []
        for spaceship in player_fleet:
            if isinstance(spaceship, Interceptor) and getattr(spaceship, "recalling", False):
                # Always steer toward the main ship
                spaceship.mover.set_target(main_player.pos)

                # When close enough, mark for docking
                if (spaceship.pos - main_player.pos).length() < 50:
                    recalled_done.append(spaceship)

        for icpt in recalled_done:
            # Remove from active shapes
            if icpt in player_fleet:
                player_fleet.remove(icpt)
            if icpt in main_player.deployed:
                main_player.deployed.remove(icpt)

            slot = getattr(icpt, "hangar_slot", None)
            if slot is not None and 0 <= slot < len(main_player.hangar):
                # Make slot available again
                main_player.hangar[slot] = True
                main_player.hangar_ships[slot] = None

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
            nearest = min(enemy_fleet, key=lambda e: (e.pos - p.pos).length_squared())
            if in_range(p, nearest, p.fire_range) and p.ready_to_fire():
                dirv = (nearest.pos - p.pos)
                projectiles.append(Projectile(p.pos, dirv, damage=p.bullet_damage, color=(255,240,120), owner_is_enemy=False))
                p.reset_cooldown()

        for e in enemy_fleet:
            if not player_fleet:
                break
            nearest = min(player_fleet, key=lambda p: (p.pos - e.pos).length_squared())
            if in_range(e, nearest, e.fire_range) and e.ready_to_fire():
                dirv = (nearest.pos - e.pos)
                projectiles.append(Projectile(e.pos, dirv, damage=e.bullet_damage, color=(255,120,120), owner_is_enemy=True, speed=Projectile.SPEED*0.9))
                e.reset_cooldown()

        # --- Update projectiles & handle hits ---
        for b in projectiles:
            b.update(dt)
            if not b.is_active:
                continue
            if b.owner_is_enemy:
                hit = None
                for p in player_fleet:
                    if b.collides_with_shape(p):
                        hit = p
                        break
                if hit:
                    hit.take_damage(b.damage)
                    b.is_active = False
            else:
                hit = None
                for e in enemy_fleet:
                    if b.collides_with_shape(e):
                        hit = e
                        break
                if hit:
                    hit.take_damage(b.damage)
                    b.is_active = False

        # Cleanup
        projectiles = [b for b in projectiles if b.is_active]
        enemy_fleet = [s for s in enemy_fleet if s.health > 0.0]
        player_fleet = [s for s in player_fleet if s.health > 0.0]
        # --- End game when mothership dies ---
        if main_player.health <= 0:
            from end_screen import end_screen
            end_screen()
            return

        # --- Collisions (residual): small damage from touching using class-level DPS ---
        for _ in range(SEPARATION_ITER):
            # Player-player separation:
            # - Light crafts still push other Light crafts.
            # - Light crafts do NOT push the main ship (or any non-triangle player spaceship).
            for i, a in enumerate(player_fleet):
                for b in player_fleet[i + 1:]:
                    if isinstance(a, Interceptor) and isinstance(b, Interceptor):
                        Mover.separate_rotated(a, b)
                    elif not isinstance(a, Interceptor) and not isinstance(b, Interceptor):
                        Mover.separate_rotated(a, b)
            # Enemy-enemy separation unchanged.
            for i, a in enumerate(enemy_fleet):
                for b in enemy_fleet[i + 1:]:
                    Mover.separate_rotated(a, b)

        # Player-enemy collision damage still applies, but Light crafts do not push enemies.
        for p in player_fleet:
            for e in enemy_fleet:
                if p.collides_with(e):
                    dmg = SpaceUnit.COLLISION_DPS * dt
                    p.take_damage(dmg)
                    e.take_damage(dmg)
                    if not isinstance(p, Interceptor):
                        for _ in range(SEPARATION_ITER):
                            Mover.separate_rotated(p, e)

        # --- Draw ---
        screen.fill((20, 20, 26))
        for spaceship in player_fleet:
            spaceship.draw(screen, show_range=spaceship.selected)
        for enemy in enemy_fleet:
            enemy.draw(screen)

        for b in projectiles:
            b.draw(screen)

        if is_selecting:
            temp = selection_rect.copy()
            temp.normalize()
            pygame.draw.rect(screen, (100, 255, 100), temp, 1)

        # --- Draw hangar previews & deploy/recall buttons ---
        hangar_interface.draw(screen, main_player, player_fleet)

        pygame.display.flip()
