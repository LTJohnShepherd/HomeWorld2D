import pygame
import random
import json
from pygame.math import Vector2
from spacegame.models.units.fleet_unit import SpaceUnit
from spacegame.models.units.pirate_frigate import PirateFrigate
from spacegame.models.units.expedition_ship import ExpeditionShip
from spacegame.models.units.frigate import Frigate
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.resource_collector import ResourceCollector
from spacegame.models.units.plasma_bomber import PlasmaBomber
from spacegame.models.units.space_station import SpaceStation
from spacegame.models.asteroids.asteroida import MineableAsteroidA
from spacegame.models.asteroids.asteroidb import MineableAsteroidB
from spacegame.models.asteroids.asteroidc import MineableAsteroidC
from spacegame.models.asteroids.asteroidm import MineableAsteroidM
from spacegame.core.mover import Mover
from spacegame.core import effects
from spacegame.core.utils import spawn_enemy_wave, handle_auto_fire, handle_projectile_collisions
from spacegame.core import events
from spacegame.ui.hud_ui import HudUI
from spacegame.ui.ui import Button, draw_triangle, draw_diamond, draw_dalton, draw_hex, OREM_PREVIEW_IMG
from spacegame.core.fabrication import get_fabrication_manager
from spacegame.core.sound_manager import get_sound_manager
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    MAX_DT,
    SEPARATION_ITER,
    IMAGES_DIR,
    PREVIEWS_DIR,
    ENEMY_SPAWN_INTERVAL,
    ENEMY_SPAWN_COUNT,
    JUMP_CINEMATIC_BAR_FACTOR,
    JUMP_CINEMATIC_CLOSE_SPEED,
    STATION_HEALING_RATE,
    SELECTION_MIN_PIXELS
)
from spacegame.screens.internal_screen import internal_screen
from spacegame.screens.galactic_map_screen import galactic_map_screen, _init_galactic_map_cache, preload_map_images
from spacegame.screens.star_system_map import star_system_map
import threading
from spacegame.screens.loading_screen import loading_screen




def handle_collisions(player_fleet, enemy_fleet, dt):
    """Handle separation and collision damage between ships."""
    # Separation: keep ships from overlapping too much
    for _ in range(SEPARATION_ITER):
        # Player-player separation
        for i, a in enumerate(player_fleet):
            for b in player_fleet[i + 1:]:
                # Light crafts push each other
                # but don't push larger ships
                if isinstance(a, (Interceptor, ResourceCollector, PlasmaBomber)) and isinstance(b, (Interceptor, ResourceCollector, PlasmaBomber)):
                    Mover.separate_rotated(a, b)
                elif not isinstance(a, (Interceptor, ResourceCollector, PlasmaBomber)) and not isinstance(b, (Interceptor, ResourceCollector, PlasmaBomber)):
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


# Helper functions moved to `spacegame.core.utils` to reduce screen complexity


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


def get_location_data(main_player):
    """Load location data from star_systems.json and return the current location visitable data."""
    try:
        with open('spacegame/data/star_systems.json', 'r', encoding='utf-8') as fh:
            systems_data = json.load(fh)
    except Exception:
        return None
    
    location_system = getattr(main_player, 'location_system', 'Lazarus')
    location_area = getattr(main_player, 'location_area', 'Lazarus Station')
    
    # Find the system
    key_variants = [str(location_system), str(location_system).title(), str(location_system).upper()]
    sys_entry = None
    for k in key_variants:
        if k in systems_data:
            sys_entry = systems_data[k]
            break
    
    if not sys_entry:
        return None
    
    # Find the visitable within the system
    visitables = sys_entry.get('visitables', [])
    for v in visitables:
        if v.get('name') == location_area:
            return v
    
    return None


def spawn_asteroids_for_location(location_data):
    """Return a list of asteroids appropriate for the given location with random positions and counts."""
    if location_data is None or location_data.get('type') != 'Asteroids':
        return []

    tier = location_data.get('tier', 0)
    ore_type = location_data.get('ore', 'M')

    asteroids = []

    # Generate random spawn area (roughly in visible area with padding)
    spawn_margin = 100
    max_x = SCREEN_WIDTH - spawn_margin
    max_y = SCREEN_HEIGHT - spawn_margin
    min_x = spawn_margin
    min_y = spawn_margin

    # Determine spawn count independent of tier: all locations have at most 10 asteroids.
    # Tier affects asteroid tier and ore tier only, not count.
    if ore_type == 'M':
        count = random.randint(4, 10)
    else:
        count = random.randint(5, 10)

    # If the visitable's ore is M, spawn only M asteroids at high purity
    if ore_type == 'M':
        for _ in range(count):
            pos = (random.randint(min_x, max_x), random.randint(min_y, max_y))
            asteroids.append(MineableAsteroidM(pos, tier=tier, purity=0.5))
        return asteroids

    # For non-M visitables, spawn A/B/C asteroids. The designated ore_type gets high purity (0.5),
    # others get low purity (0.13).
    high_purity = 0.5
    low_purity = 0.13
    ore_purities = {
        'A': high_purity if ore_type == 'A' else low_purity,
        'B': high_purity if ore_type == 'B' else low_purity,
        'C': high_purity if ore_type == 'C' else low_purity,
    }

    asteroid_map = {'A': MineableAsteroidA, 'B': MineableAsteroidB, 'C': MineableAsteroidC}

    # Ensure at least one asteroid of each type A/B/C is present for non-M visitables.
    ore_choices = ['A', 'B', 'C']
    if count > 3:
        ore_choices += [random.choice(['A', 'B', 'C']) for _ in range(count - 3)]
    random.shuffle(ore_choices)

    for ore_key in ore_choices:
        pos = (random.randint(min_x, max_x), random.randint(min_y, max_y))
        asteroid_class = asteroid_map[ore_key]
        purity_val = ore_purities.get(ore_key, low_purity)
        asteroids.append(asteroid_class(pos, tier=tier, purity=purity_val))

    return asteroids


def spawn_station_for_location(location_data):
    """Return a space station if the location is a station type, positioned at a fixed location."""
    if location_data is None or location_data.get('type') != 'Station':
        return None
    
    # Get the position from location data, or use center screen as default
    position = location_data.get('position')
    if position:
        # Position is [x, y] from json, convert to screen coordinates
        # Assuming position is relative; center on screen plus offset
        spawn_x = SCREEN_WIDTH // 2 + position[0] - 300
        spawn_y = SCREEN_HEIGHT // 2 + position[1]
    else:
        # Default to center of screen if no position specified
        spawn_x = SCREEN_WIDTH // 2
        spawn_y = SCREEN_HEIGHT // 2
    
    station = SpaceStation((spawn_x, spawn_y))
    return station


def play_jump_cinematic(main_player, player_fleet, prev_system, new_system, prev_area, new_area):
    """Play a blocking cinematic for jumps:
    - recall all deployed ships to mothership
    - animate black bars closing
    - show galactic map movement if changing systems
    - show star system entry animation for fleet icon
    This function is intentionally blocking and disables player input while active.
    """
    import time
    screen = pygame.display.get_surface()
    if screen is None:
        return

    # Play hyperspace launch sound
    try:
        sound_manager = get_sound_manager()
        sound_manager.on_hyperspace_launch()
    except Exception:
        pass

    clock = pygame.time.Clock()
    inv = getattr(main_player, 'inventory_manager', None)
    hangar = getattr(inv, 'hangar', None) if inv is not None else None

    # Issue recall for all deployed ships tracked by hangar
    if hangar is not None:
        for craft in list(hangar.deployed):
            try:
                craft.recalling = True
            except Exception:
                pass
            # ensure craft is present in active player_fleet
            if craft not in player_fleet:
                player_fleet.append(craft)

    # Animate black bars while ships fly home
    # Bars start off-screen and slide into position from above/below.
    target_h = max(24, int(SCREEN_HEIGHT * JUMP_CINEMATIC_BAR_FACTOR))
    # positions: top_y moves from -target_h -> 0; bot_y moves from SCREEN_HEIGHT -> SCREEN_HEIGHT-target_h
    top_y = -target_h
    bot_y = SCREEN_HEIGHT
    # close_speed controls how many pixels per second the bars move; keep reasonable default
    close_speed = float(JUMP_CINEMATIC_CLOSE_SPEED)

    # We'll manually update recalled ships here while animating bars.
    recall_timeout = 10.0
    elapsed = 0.0

    # Compute deterministic duration to fully close bars (distance = target_h for each bar)
    close_duration = target_h / close_speed if close_speed > 0 else 0.0
    anim_elapsed = 0.0

    while True:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        anim_elapsed += dt

        # update positions of recalling crafts
        if hangar is not None:
            for craft in list(hangar.deployed):
                # steer toward mothership
                try:
                    craft.mover.set_target(main_player.pos)
                    craft.mover.update(dt)
                    # when close enough, dock
                    if (craft.pos - main_player.pos).length() < 50:
                        # remove from active list and inform hangar
                        try:
                            if craft in player_fleet:
                                player_fleet.remove(craft)
                        except Exception:
                            pass
                        try:
                            inv.hangar.on_recalled(craft)
                        except Exception:
                            pass
                        try:
                            # remove sprite from any sprite groups so it no longer draws
                            if isinstance(craft, pygame.sprite.Sprite):
                                craft.kill()
                        except Exception:
                            pass
                except Exception:
                    pass

        # Animate black bars sliding into place over the computed duration
        if close_duration > 0:
            frac = min(1.0, anim_elapsed / close_duration)
            top_y = -target_h + target_h * frac
            bot_y = SCREEN_HEIGHT - target_h * frac

        # Draw current frame behind bars (simple snapshot)
        try:
            bg = screen.copy()
            screen.blit(bg, (0, 0))
        except Exception:
            pass

        # draw bars at current animated positions
        try:
            pygame.draw.rect(screen, (0, 0, 0), (0, int(top_y), SCREEN_WIDTH, int(target_h)))
            pygame.draw.rect(screen, (0, 0, 0), (0, int(bot_y), SCREEN_WIDTH, int(target_h)))
        except Exception:
            # fallback to simple full-edge bars
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, int(target_h)))
            pygame.draw.rect(screen, (0, 0, 0), (0, SCREEN_HEIGHT - int(target_h), SCREEN_WIDTH, int(target_h)))
        pygame.display.flip()

        # Exit condition: animation finished AND no more deployed ships (or timeout)
        deployed_empty = (hangar is None) or (len(hangar.deployed) == 0)
        if (anim_elapsed >= close_duration) and (deployed_empty or elapsed > recall_timeout):
            break

    # Ensure bars fully closed briefly (hold their final positions)
    end_wait = 0.25
    wait_elapsed = 0.0
    while wait_elapsed < end_wait:
        dt = clock.tick(60) / 1000.0
        wait_elapsed += dt
        try:
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, int(target_h)))
            pygame.draw.rect(screen, (0, 0, 0), (0, SCREEN_HEIGHT - int(target_h), SCREEN_WIDTH, int(target_h)))
        except Exception:
            pass
        pygame.display.flip()

    # Transition: if system changed, show galactic map with a fleet move animation
    try:
        # Annotate main_player so map screens draw the cinematic bars overlay
        try:
            setattr(main_player, '_cinematic_bars', {
                'target_h': int(target_h),
                'top_y': 0,
                'bot_y': SCREEN_HEIGHT - int(target_h),
                'close_speed': close_speed,
            })
        except Exception:
            pass
        if prev_system and new_system and prev_system != new_system:
            # annotate main_player so galactic_map_screen picks up animation request
            try:
                setattr(main_player, '_fleet_move', (prev_system, new_system))
                # request the galactic map to auto-close after the animation
                setattr(main_player, '_fleet_move_auto', True)
            except Exception:
                pass
            from spacegame.screens.galactic_map_screen import galactic_map_screen as _gms
            _gms(main_player, player_fleet)
        # After galactic map (or if same system), show star system map and animate fleet entry
        try:
            # annotate main_player so star_system_map can animate entry
            # include auto_return so the map closes automatically after the animation
            entry = {'from_area': prev_area, 'auto_return': True} if prev_area else {'from_outside': True, 'auto_return': True}
            setattr(main_player, '_fleet_entry', entry)
        except Exception:
            pass
        from spacegame.screens.star_system_map import star_system_map as _ssm
        _ssm(main_player, player_fleet, system_name=new_system)

        # Return the cinematic bars data to the caller so the gameplay loop can animate them off
        try:
            bars = getattr(main_player, '_cinematic_bars', None)
            return bars
        except Exception:
            return None
    except Exception:
        pass
    return None


def run_game():
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SpaceGame")
    
    # Pre-initialize galactic map resources and system previews in background for instant transitions
    _init_galactic_map_cache()
    try:
        # Start preloading on a background thread so the main loop isn't blocked.
        t = threading.Thread(target=preload_map_images, daemon=True)
        t.start()
        # Show an animated loading screen while preload runs; if user quits, propagate exit
        res = loading_screen(t)
        if res == "exit":
            return "exit"
    except Exception:
        pass

    # --- Load skybox background ---
    background_img = pygame.image.load(IMAGES_DIR + "/nebula_15.png").convert()
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
    # Default starting location for the player's fleet (safe starter system)
    try:
        main_player.location_system = getattr(main_player, 'location_system', None) or 'Lazarus'
        main_player.location_area = getattr(main_player, 'location_area', None) or 'Lazarus Station'
    except Exception:
        main_player.location_system = 'Lazarus'
        main_player.location_area = 'Lazarus Station'

    player_fleet = [
        main_player,
        Frigate((500, 400))
        ]

    # Sprite groups for bulk updates/draws
    player_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    for s in player_fleet:
        if isinstance(s, pygame.sprite.Sprite):
            player_group.add(s)

    # Single projectile group for all projectiles
    projectile_group = pygame.sprite.Group()

    # Load location data and spawn appropriate asteroids/enemies based on location type
    location_data = get_location_data(main_player)
    asteroids = spawn_asteroids_for_location(location_data)
    # asteroid sprite group
    asteroid_group = pygame.sprite.Group()
    for a in asteroids:
        if isinstance(a, pygame.sprite.Sprite):
            asteroid_group.add(a)

    # Spawn station if at a station location
    station = spawn_station_for_location(location_data)
    station_group = pygame.sprite.Group()
    if station is not None and isinstance(station, pygame.sprite.Sprite):
        station_group.add(station)

    # Only spawn enemies if at an asteroid location (not at a station)
    enemy_fleet = []
    if location_data and location_data.get('type') == 'Asteroids':
        enemy_fleet = [
            PirateFrigate((700, 120)),
        ]
    
    for e in enemy_fleet:
        if isinstance(e, pygame.sprite.Sprite):
            enemy_group.add(e)

    # Spawn timer for enemy waves
    spawn_timer = ENEMY_SPAWN_INTERVAL
    # Track current system name so we can detect inter-system jumps
    current_system_name = getattr(main_player, 'location_system', None)

    is_selecting = False # Flag that indicates if the player is currently dragging a selection box with the mouse
    selection_start = (0, 0) # The starting mouse position where the left button was first pressed (selection begins here)
    selection_rect = pygame.Rect(0, 0, 0, 0) # ExpeditionShip used to visually and logically represent the drag-selection area

    # --- HUD Icons (top right: Map, Sys, Battle) ---
    hud_icon_cache = {}
    hud_icon_names = ['Map', 'Sys', 'Battle']
    hud_selected_index = 2  # Track which icon is selected (0=Map, 1=Sys, 2=Battle); default leftmost
    
    def load_hud_icon(name: str, selected: bool = False) -> pygame.Surface | None:
        """Load a HUD icon from the previews folder with caching."""
        suffix = "Selected" if selected else "Unselected"
        filename = f"HudIcon_{name}_{suffix}.png"
        cache_key = f"{name}_{suffix}"
        
        if cache_key not in hud_icon_cache:
            try:
                icon = pygame.image.load(f"{PREVIEWS_DIR}/{filename}").convert_alpha()
                hud_icon_cache[cache_key] = icon
            except Exception:
                hud_icon_cache[cache_key] = None
        
        return hud_icon_cache.get(cache_key)
    
    def load_hud_separator() -> pygame.Surface | None:
        """Load the HUD separator image."""
        if 'separator' not in hud_icon_cache:
            try:
                sep = pygame.image.load(f"{PREVIEWS_DIR}/HudIcon_Separator.png").convert_alpha()
                hud_icon_cache['separator'] = sep
            except Exception:
                hud_icon_cache['separator'] = None
        
        return hud_icon_cache.get('separator')
    
    # Pre-load all HUD icons
    for name in hud_icon_names:
        load_hud_icon(name, selected=False)
        load_hud_icon(name, selected=True)
    load_hud_separator()

    while True:
        dt = clock.tick(FPS) / 1000.0
        # Ignore huge dt spikes (e.g. when coming back from INTERNAL screen)
        if dt > MAX_DT:      # threshold in seconds, tweak if you want
            dt = 0.0      # treat that frame as “paused"        
        # Reload location data each frame to stay in sync with player's current location
        # This ensures asteroids/enemies spawn correctly when returning from star system map
        new_location_data = get_location_data(main_player)
        
        # If location changed, play cinematic then respawn asteroids
        if new_location_data != location_data:
            # Remember previous system/area for animation decisions
            prev_system = current_system_name
            prev_area = None
            if location_data is not None:
                prev_area = location_data.get('name')

            # Update tracked system name now (main_player.location_system is already set by map UI)
            current_system_name = getattr(main_player, 'location_system', None)

            # Before playing the jump cinematic: clear active projectiles and visual effects
            try:
                projectile_group.empty()
            except Exception:
                pass
            try:
                # remove any lingering particles/explosions/smoke
                effects.effects_group.empty()
            except Exception:
                pass

            # Play the jump cinematic which will recall deployed ships and run map animations
            bars = None
            try:
                bars = play_jump_cinematic(main_player, player_fleet, prev_system, current_system_name, prev_area, getattr(main_player, 'location_area', None))
            except Exception:
                # Fail gracefully; continue without cinematic
                bars = None

            # If cinematic provided bars data, animate them opening while drawing gameplay
            if bars:
                try:
                    th = int(bars.get('target_h') or max(24, int(SCREEN_HEIGHT * 0.12)))
                    speed = float(bars.get('close_speed') or 160.0)
                    tdur = th / speed if speed > 0 else 0.0
                    open_clock = pygame.time.Clock()
                    open_elapsed = 0.0
                    while open_elapsed < tdur:
                        dt_o = open_clock.tick(60) / 1000.0
                        open_elapsed += dt_o
                        frac = min(1.0, open_elapsed / tdur) if tdur > 0 else 1.0
                        top_y = 0 - th * frac
                        bot_y = (SCREEN_HEIGHT - th) + th * frac

                        # Draw gameplay frame underneath
                        try:
                            screen = pygame.display.get_surface()
                            # background_img is available in this scope
                            try:
                                screen.blit(background_img, (0, 0))
                            except Exception:
                                screen.fill((6, 10, 20))
                            try:
                                asteroid_group.draw(screen)
                            except Exception:
                                pass
                            try:
                                enemy_group.draw(screen)
                            except Exception:
                                pass
                            try:
                                projectile_group.draw(screen)
                            except Exception:
                                pass
                            try:
                                player_group.draw(screen)
                            except Exception:
                                pass
                            try:
                                hangar_interface.draw(screen, main_player, player_fleet)
                            except Exception:
                                pass
                        except Exception:
                            pass

                        # Draw bars on top
                        try:
                            pygame.draw.rect(screen, (0, 0, 0), (0, int(top_y), SCREEN_WIDTH, int(th)))
                            pygame.draw.rect(screen, (0, 0, 0), (0, int(bot_y), SCREEN_WIDTH, int(th)))
                        except Exception:
                            pass
                        pygame.display.flip()

                    # cleanup annotation
                    try:
                        delattr(main_player, '_cinematic_bars')
                    except Exception:
                        try:
                            del main_player._cinematic_bars
                        except Exception:
                            pass
                except Exception:
                    pass

            # Now update in-game location and respawn content for the new location
            location_data = new_location_data
            # Clear old asteroids
            asteroid_group.empty()
            asteroids = spawn_asteroids_for_location(location_data)
            for a in asteroids:
                if isinstance(a, pygame.sprite.Sprite):
                    asteroid_group.add(a)

            # Respawn station if at a station location
            station_group.empty()
            station = spawn_station_for_location(location_data)
            if station is not None and isinstance(station, pygame.sprite.Sprite):
                station_group.add(station)

            # Play hyperspace complete sound (asteroids/station now drawn)
            try:
                sound_manager = get_sound_manager()
                sound_manager.on_hyperspace_complete()
            except Exception:
                pass

            # Clear all enemies when location changes
            enemy_fleet = []
            enemy_group.empty()

            # Restart enemy spawn timer when location changes
            spawn_timer = ENEMY_SPAWN_INTERVAL
        
        # Heal player fleet if at a station
        if location_data and location_data.get('type') == 'Station':
            healing_rate = float(STATION_HEALING_RATE)  # HP per second
            for ship in player_fleet:
                if ship.health < ship.max_health:
                    ship.heal(healing_rate * dt)
                if ship.armor < ship.max_armor:
                    ship.set_armor(ship.armor + healing_rate * dt)
            
        for event in pygame.event.get():
            # Handle custom save event posted by InventoryManager and other systems
            try:
                if event.type == events.SAVE_GAME_EVENT:
                    try:
                        from spacegame.core import save as _save
                        owner = getattr(event, 'owner', None)
                        if owner is None:
                            owner = main_player
                        _save.save_game(owner)
                    except Exception:
                        pass
                    # do not process this event further
                    continue
            except Exception:
                # if events module is not available or event doesn't have type, ignore
                pass

            if event.type == pygame.QUIT:
                return "exit" # "exit"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "main_menu" # "main_menu"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_ui = False  # Initialize click tracking
                
                # First: fleet management button
                if fleet_btn.handle_event(event):
                    res = internal_screen(main_player, player_fleet)
                    if res == "to_game":
                        # Orange X from any internal screen chain: already back in game.
                        # Treat as a fresh slate; no extra action needed.
                        pass
                    # after returning, skip further handling of this click
                    continue

                # Check for HUD icon clicks (top right)
                hud_icon_y = 20
                hud_icon_spacing = 140
                hud_start_x = WIDTH - 50
                
                for i, name in enumerate(hud_icon_names):
                    x = hud_start_x - i * hud_icon_spacing
                    # Estimate rect size based on typical HUD icon size
                    rect = pygame.Rect(x - 40, hud_icon_y, 80, 80)
                    
                    if rect.collidepoint(event.pos):
                        # Icon was clicked
                        # Leftmost icon (i==0) opens the Galactic Map
                        if i == 0:
                            try:
                                res = galactic_map_screen(main_player, player_fleet)
                                if res == "exit":
                                    return "exit"
                            except Exception:
                                hud_selected_index = 2
                            clicked_ui = True
                            break
                        # Middle icon (i==1) opens the Star System Map for current fleet location
                        if i == 1:
                            try:
                                current_system = getattr(main_player, 'location_system', None) or 'Lazarus'
                                res = star_system_map(main_player, player_fleet, system_name=current_system)
                                if res == "exit":
                                    return "exit"
                            except Exception:
                                hud_selected_index = 2
                            clicked_ui = True
                            break
                        else:
                            hud_selected_index = i
                            clicked_ui = True
                            break

                # Then let the hangar UI handle deploy/recall buttons and preview toggles.
                if not clicked_ui:
                    clicked_ui = hangar_interface.handle_mouse_button_down(event.pos, main_player, player_fleet)
                    # If the hangar deployed a new craft it will be appended to player_fleet;
                    # ensure it's also added to the sprite group so it gets drawn/updated.
                    for s in player_fleet:
                        if isinstance(s, pygame.sprite.Sprite) and s not in player_group:
                            player_group.add(s)

                # If the HUD row was clicked but the handler somehow did not claim the event,
                # treat clicks inside the HUD area as consumed to avoid accidentally
                # starting a world selection which would immediately clear the HUD selection.
                if not clicked_ui:
                    try:
                        # determine approximate top of HUD by using the first hangar slot preview y
                        hud_preview_y = hangar_interface.hangar_slots[0]['preview_position'].y
                        hud_threshold = int(hud_preview_y - hangar_interface.preview_size * 0.6)
                        if event.pos[1] >= hud_threshold:
                            clicked_ui = True
                    except Exception:
                        # fallback: if anything goes wrong, keep existing behavior
                        pass

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
                if rect.width > SELECTION_MIN_PIXELS and rect.height > SELECTION_MIN_PIXELS:
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
                    
                    # Play move command sound
                    try:
                        sound_manager = get_sound_manager()
                        sound_manager.on_move_command()
                    except Exception:
                        pass

        # --- Update cooldowns ---
        for s in player_fleet + enemy_fleet:
            s.update_cooldown(dt)
        # Ensure fabrications are advanced/finalized even while in gameplay.
        try:
            fm = get_fabrication_manager(main_player)
            if fm is not None:
                fm.update()
        except Exception:
            pass
        # Update expedition ship notifications (timers) via InventoryManager
        try:
            inv = getattr(main_player, 'inventory_manager', None)
            if inv is not None:
                inv.update(dt)
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
            if isinstance(spaceship, (Interceptor, ResourceCollector, PlasmaBomber)) and getattr(spaceship, "recalling", False):
                # Always steer toward the main ship
                spaceship.mover.set_target(main_player.pos)

                # When close enough, mark for docking
                if (spaceship.pos - main_player.pos).length() < 50:
                    recalled_done.append(spaceship)

        for craft in recalled_done:
            # Remove from active ships; Hangar will take care of internal lists.
            if craft in player_fleet:
                player_fleet.remove(craft)

            # Play ship docking sound
            try:
                sound_manager = get_sound_manager()
                sound_manager.on_ship_docking()
            except Exception:
                pass

            # Inform the Hangar (via InventoryManager) that this craft has successfully docked
            # so the corresponding slot becomes ready again.
            inv = getattr(main_player, 'inventory_manager', None)
            if inv is None or getattr(inv, 'hangar', None) is None:
                raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
            inv.hangar.on_recalled(craft)
            try:
                # ensure sprite is removed from any drawing groups
                if isinstance(craft, pygame.sprite.Sprite):
                    craft.kill()
            except Exception:
                pass
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

        # Sync sprite images/rects to mover state
        try:
            player_group.update(dt)
        except Exception:
            pass
        try:
            enemy_group.update(dt)
        except Exception:
            pass

        # --- Enemy spawning (timed waves) ---
        if ENEMY_SPAWN_INTERVAL > 0:
            spawn_timer -= dt
            if spawn_timer <= 0:
                spawn_timer = ENEMY_SPAWN_INTERVAL
                # Only spawn enemies if at an asteroid location
                if location_data and location_data.get('type') == 'Asteroids':
                    # spawn N pirates at random edge positions via helper
                    spawn_enemy_wave(WIDTH, HEIGHT, location_data, enemy_group, enemy_fleet, count=ENEMY_SPAWN_COUNT)

        # --- Auto-fire: both sides (delegated to helper) ---
        handle_auto_fire(player_fleet, enemy_fleet, projectile_group, owner_is_enemy=False, color=(255,240,120), speed_factor=1.0)
        handle_auto_fire(enemy_fleet, player_fleet, projectile_group, owner_is_enemy=True, color=(255,120,120), speed_factor=0.9)

        # --- Update projectiles (group) & handle hits ---
        projectile_group.update(dt)
        # update effects (particles, explosions)
        try:
            effects.effects_group.update(dt)
        except Exception:
            pass

        # --- Update projectiles (group) & handle hits ---
        handle_projectile_collisions(projectile_group, player_fleet, enemy_fleet)



        # Update hangar state for any light crafts that died this frame
        dead_crafts = [
            s for s in player_fleet
            if isinstance(s, (Interceptor, ResourceCollector, PlasmaBomber)) and s.health <= 0.0
        ]
        for craft in dead_crafts:
            # Play appropriate destruction sound
            try:
                sound_manager = get_sound_manager()
                if isinstance(craft, ResourceCollector):
                    sound_manager.on_unit_destroyed_collector()
                elif isinstance(craft, (Interceptor, PlasmaBomber)):
                    # Group interceptors and plasma bombers as strikegroup
                    sound_manager.on_unit_destroyed_strikegroup()
            except Exception:
                pass
            
            inv = getattr(main_player, 'inventory_manager', None)
            if inv is None or getattr(inv, 'hangar', None) is None:
                raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
            inv.hangar.on_interceptor_dead(craft)
            # handled above; asteroid drawing happens in the main draw section

        prev_enemies = list(enemy_fleet)
        prev_players = list(player_fleet)

        enemy_fleet = [s for s in enemy_fleet if s.health > 0.0]
        player_fleet = [s for s in player_fleet if s.health > 0.0]

        # remove sprites for any ships that were filtered out
        for e in prev_enemies:
            if e not in enemy_fleet:
                # Play destruction sound for enemy frigates
                try:
                    if isinstance(e, PirateFrigate):
                        sound_manager = get_sound_manager()
                        sound_manager.on_unit_destroyed_frigate()
                except Exception:
                    pass
                try:
                    e.kill()
                except Exception:
                    pass
        for p in prev_players:
            if p not in player_fleet:
                try:
                    p.kill()
                except Exception:
                    pass

        # --- End game when ExpeditionShip dies ---
        if main_player.health <= 0:
            return "end"  # "end"


        # --- Collisions (residual): small damage from touching using class-level DPS ---
        handle_collisions(player_fleet, enemy_fleet, dt)

# --- Draw ---
        screen.blit(background_img, (0, 0))
        # Draw asteroids under ships (prefer sprite group draw)
        try:
            asteroid_group.draw(screen)
        except Exception:
            for a in asteroids:
                a.draw(screen)

        # Draw station if present
        try:
            station_group.draw(screen)
        except Exception:
            pass

        # Draw unit sprites (images)
        try:
            enemy_group.draw(screen)
        except Exception:
            pass
        try:
            player_group.draw(screen)
        except Exception:
            pass
        
        for spaceship in player_fleet:
            # diamond over frigate with same relative scale as ExpeditionShip hex
            # draw overlays (health bars / range)
            try:
                spaceship.draw_overlay(screen, show_range=spaceship.selected)
            except Exception:
                pass

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
            elif isinstance(spaceship, (Interceptor, PlasmaBomber)) and not getattr(spaceship, "recalling", False):
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

        # Draw projectiles
        projectile_group.draw(screen)

        # Draw effects (particles/explosions) on top of projectiles
        try:
            effects.effects_group.draw(screen)
        except Exception:
            pass

        # Draw enemy overlays (health bars / ranges)
        for enemy in enemy_fleet:
            try:
                enemy.draw_overlay(screen, show_range=False)
            except Exception:
                pass

        if is_selecting:
            temp = selection_rect.copy()
            temp.normalize()
            pygame.draw.rect(screen, (100, 255, 100), temp, 1)

        # --- Draw hangar previews & deploy/recall buttons ---
        hangar_interface.draw(screen, main_player, player_fleet)

        # --- Draw HUD Icons (top right: Map, Sys, Battle) ---
        hud_icon_y = 20
        hud_icon_spacing = 140
        hud_start_x = WIDTH - 50
        
        for i, name in enumerate(hud_icon_names):
            x = hud_start_x - i * hud_icon_spacing
            
            # Draw separator (between icons, not before first or after last)
            if i > 0:
                separator = load_hud_separator()
                if separator:
                    sep_scaled = pygame.transform.smoothscale(separator, (20, 10))
                    sep_rect = sep_scaled.get_rect(center=(x + 70, hud_icon_y + 40))
                    screen.blit(sep_scaled, sep_rect)
            
            # Draw the icon (selected or unselected based on hud_selected_index)
            is_selected = (i == hud_selected_index)
            icon = load_hud_icon(name, selected=is_selected)
            
            if icon:
                # Scale icon to reasonable size
                icon_scaled = pygame.transform.smoothscale(icon, (80, 80))
                icon_rect = icon_scaled.get_rect(topleft=(x - 40, hud_icon_y))
                screen.blit(icon_scaled, icon_rect)

        # --- Draw fleet management ("INTERNAL") button as hex ---
        draw_hex_button(screen, fleet_btn, fleet_btn_font,
                        base_color=(120, 200, 255),
                        hover_color=(190, 230, 255),
                        header_text="INTERNAL")

        # --- Draw notifications from the mothership (left side under INTERNAL) ---
        # Use InventoryManager notifications (centralized)
        inv_mgr = getattr(main_player, 'inventory_manager', None)
        notif_list = getattr(inv_mgr, 'notifications', []) if inv_mgr is not None else []
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
                # Support multiple notification types. Default is ore delivery.
                notif_type = n.get('type', 'ore')
                tx = nx + padding
                ty = ny + (popup_h - small_font.get_height()) // 2

                if notif_type == 'fabrication':
                    # try blueprint preview (from PREVIEWS_DIR), otherwise fallback to OREM_PREVIEW_IMG
                    preview_fn = n.get('preview')
                    if preview_fn:
                        try:
                            icon = pygame.image.load(PREVIEWS_DIR + "/" + preview_fn).convert_alpha()
                            icon_s = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                            screen.blit(icon_s, (nx + padding, ny + (popup_h - icon_size) // 2))
                        except Exception:
                            try:
                                icon = OREM_PREVIEW_IMG
                                icon_s = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                                screen.blit(icon_s, (nx + padding, ny + (popup_h - icon_size) // 2))
                            except Exception:
                                pass
                    else:
                        try:
                            icon = OREM_PREVIEW_IMG
                            icon_s = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                            screen.blit(icon_s, (nx + padding, ny + (popup_h - icon_size) // 2))
                        except Exception:
                            pass

                    title = n.get('title', 'Fabrication Complete')
                    text = f"Fabrication complete: {title}"
                    tx = nx + padding + icon_size + 8
                    # shadow
                    shadow_surf = small_font.render(text, True, (0, 0, 0))
                    screen.blit(shadow_surf, (tx + 1, ty + 1))
                    # main text
                    text_surf = small_font.render(text, True, (108, 198, 219))
                    screen.blit(text_surf, (tx, ty))
                else:
                    # default: ore delivery notification (existing behaviour)
                    try:
                        # Use provided preview filename if the notification included one
                        preview_fn = n.get('preview')
                        if preview_fn:
                            try:
                                icon = pygame.image.load(PREVIEWS_DIR + "/" + preview_fn).convert_alpha()
                            except Exception:
                                icon = OREM_PREVIEW_IMG
                        else:
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
                    # shadow
                    shadow_surf = small_font.render(text, True, (0, 0, 0))
                    screen.blit(shadow_surf, (tx + 1, ty + 1))
                    # main text
                    text_surf = small_font.render(text, True, (108, 198, 219))
                    screen.blit(text_surf, (tx, ty))

        pygame.display.flip()