import pygame
import json
import os
from spacegame.config import PREVIEWS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, UI_SECTION_TEXT_COLOR, UI_TOP_BAR_HEIGHT, UI_NAV_LINE_COLOR, UI_ICON_BLUE
from spacegame.ui.ui import Button, draw_hex
from spacegame.screens.internal_screen import internal_screen


def _load_image(filename: str):
    try:
        img = pygame.image.load(filename)
        return img.convert_alpha() if hasattr(img, 'convert_alpha') else img.convert()
    except Exception:
        return None


def star_system_map(main_player, player_fleet, system_name: str | None = None):
    """Simple star system map viewer.

    - `system_name`: optional name like 'LAZARUS' or 'Iniim'. If None, uses
      `main_player.location` if present, otherwise defaults to 'Lazarus'.
    Controls:
    - ESC: go back
    """
    pygame.init()
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # resolve system name -> preview filename
    name = None
    if system_name:
        name = system_name
    else:
        name = getattr(main_player, 'location', None)
    if not name:
        name = 'None'

    # Try to use preloaded system preview if available (cached by galactic_map_screen.preload_map_images)
    bg_img = None
    try:
        from spacegame.screens.galactic_map_screen import _GALACTIC_MAP_CACHE as _GMC
        sys_previews = _GMC.get('system_previews', {})
        bg_img = sys_previews.get(str(name).title()) if sys_previews else None
    except Exception:
        bg_img = None

    # fallback to loading file directly
    if bg_img is None:
        preview_fn = f"{PREVIEWS_DIR}/Map_{str(name).title()}.png"
        bg_img = _load_image(preview_fn)
    if bg_img is None:
        bg_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_img.fill((6, 10, 20))
    else:
        try:
            bg_img = pygame.transform.smoothscale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    # Prepare zoom/pan similar to galactic_map_screen
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    width, height = screen.get_size()

    bg_w, bg_h = bg_img.get_size()
    fit_zoom = min(width / bg_w, height / bg_h) if bg_w and bg_h else 1.0
    zoom = fit_zoom
    MAX_SCALED_DIMENSION = 8192
    max_zoom = min(4.0, MAX_SCALED_DIMENSION / max(bg_w, bg_h)) if max(bg_w, bg_h) > 0 else 4.0
    min_zoom, max_zoom = fit_zoom, max_zoom

    cached_zoom = None
    cached_bg_scaled = None

    offset = pygame.math.Vector2((width - bg_w * zoom) / 2, (height - bg_h * zoom) / 2)

    def clamp_offset():
        scaled_w = bg_w * zoom
        scaled_h = bg_h * zoom
        if scaled_w <= width:
            offset.x = (width - scaled_w) / 2
        else:
            offset.x = max(min(offset.x, 0), width - scaled_w)
        if scaled_h <= height:
            offset.y = (height - scaled_h) / 2
        else:
            offset.y = max(min(offset.y, 0), height - scaled_h)

    panning = False
    pan_last = (0, 0)

    # Top-left INTERNAL button (hex style)
    fleet_btn_font = pygame.font.SysFont(None, 19)
    fleet_btn = Button((10, 40, 100, 30), "INTERNAL", fleet_btn_font)

    # Load system visitable definitions from data file (simple JSON, no pathlib)
    systems_data = {}
    try:
        with open('spacegame/data/star_systems.json', 'r', encoding='utf-8') as fh:
            systems_data = json.load(fh)
    except Exception:
        systems_data = {}

    # HUD icons (top-right): Map, Sys, Battle
    hud_icon_cache = {}
    hud_icon_names = ['Map', 'Sys', 'Battle']
    hud_selected_index = 1

    # visitable map icons cache (UI_Map_Asteroirds, UI_Map_Station)
    visitable_icon_cache = {}
    ICON_SIZE = 24
    def load_map_icon(area_type: str):
        # Normalize type and choose filename
        t = (area_type or '').lower()
        if 'station' in t:
            fname = f"{PREVIEWS_DIR}/UI_Map_Station.png"
            key = 'station'
        else:
            # default -> asteroids (note naming follows galactic_map_screen)
            fname = f"{PREVIEWS_DIR}/UI_Map_Asteroirds.png"
            key = 'asteroids'

        if key not in visitable_icon_cache:
            try:
                visitable_icon_cache[key] = pygame.image.load(fname).convert_alpha()
            except Exception:
                visitable_icon_cache[key] = None
        return visitable_icon_cache.get(key)

    def load_hud_icon(name: str, selected: bool = False):
        suffix = 'Selected' if selected else 'Unselected'
        fname = f"{PREVIEWS_DIR}/HudIcon_{name}_{suffix}.png"
        key = f"{name}_{suffix}"
        if key not in hud_icon_cache:
            try:
                hud_icon_cache[key] = pygame.image.load(fname).convert_alpha()
            except Exception:
                hud_icon_cache[key] = None
        return hud_icon_cache.get(key)

    # pre-load
    for n in hud_icon_names:
        load_hud_icon(n, selected=False)
        load_hud_icon(n, selected=True)
    try:
        hud_separator = pygame.image.load(f"{PREVIEWS_DIR}/HudIcon_Separator.png").convert_alpha()
    except Exception:
        hud_separator = None
    
    # Load fleet icon
    try:
        fleet_icon = pygame.image.load(f"{PREVIEWS_DIR}/FleetIcon.png").convert_alpha()
    except Exception:
        fleet_icon = None

    # Selected visitable area in this system (None or dict)
    selected_area = None

    # If caller annotated a fleet entry animation, perform it once before entering interactive loop
    fleet_entry = getattr(main_player, '_fleet_entry', None)
    if fleet_entry:
        try:
            # Determine target screen coordinates for the destination area (new_area)
            target_area_name = getattr(main_player, 'location_area', None) or (fleet_entry.get('to_area') if isinstance(fleet_entry, dict) else None)
            # Find visitables for mapping
            visitables = []
            key_variants = [str(name), str(name).title(), str(name).upper()]
            sys_entry = None
            try:
                with open('spacegame/data/star_systems.json', 'r', encoding='utf-8') as fh:
                    systems_data = json.load(fh)
            except Exception:
                systems_data = {}
            for k in key_variants:
                if k in systems_data:
                    sys_entry = systems_data[k]
                    break
            if sys_entry and isinstance(sys_entry, dict):
                visitables = list(sys_entry.get('visitables', []))

            # compute map center
            map_center_x = bg_w / 2
            map_center_y = bg_h / 2
            dest_pos = None
            for v in visitables:
                if v.get('name') == target_area_name:
                    pos = v.get('position')
                    if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        world_x = map_center_x + float(pos[0])
                        world_y = map_center_y + float(pos[1])
                    else:
                        world_x, world_y = map_center_x, map_center_y
                    dest_pos = (world_x * zoom + offset.x, world_y * zoom + offset.y)
                    break

            # Decide start position
            start_pos = None
            if isinstance(fleet_entry, dict) and fleet_entry.get('from_area'):
                # find from_area coordinates
                from_name = fleet_entry.get('from_area')
                for v in visitables:
                    if v.get('name') == from_name:
                        pos = v.get('position')
                        if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                            world_x = map_center_x + float(pos[0])
                            world_y = map_center_y + float(pos[1])
                        else:
                            world_x, world_y = map_center_x, map_center_y
                        start_pos = (world_x * zoom + offset.x, world_y * zoom + offset.y)
                        break

            if dest_pos is None:
                # nothing to animate
                try:
                    delattr(main_player, '_fleet_entry')
                except Exception:
                    try:
                        del main_player._fleet_entry
                    except Exception:
                        pass
            else:
                # If start not provided, use off-screen entry from left
                if start_pos is None:
                    start_pos = (-80, dest_pos[1])
                # Simple animation
                anim_clock = pygame.time.Clock()
                t = 0.0
                dur = 1.0
                fleet_icon_local = fleet_icon
                
                # Pre-render the static parts of the background (scaled/offset)
                if cached_bg_scaled is None and bg_img:
                    try:
                        cached_bg_scaled = pygame.transform.smoothscale(bg_img, (int(bg_w * zoom), int(bg_h * zoom)))
                    except Exception:
                        cached_bg_scaled = pygame.transform.scale(bg_img, (int(bg_w * zoom), int(bg_h * zoom)))
                
                while t < dur:
                    dt = anim_clock.tick(60) / 1000.0
                    t += dt
                    alpha = min(1.0, t / dur)
                    ix = start_pos[0] + (dest_pos[0] - start_pos[0]) * alpha
                    iy = start_pos[1] + (dest_pos[1] - start_pos[1]) * alpha
                    
                    # Draw background with all locations and icons
                    if cached_bg_scaled:
                        screen.blit(cached_bg_scaled, (int(offset.x), int(offset.y)))
                    else:
                        screen.fill((6, 10, 20))
                    
                    # Redraw all visitable markers
                    for v in visitables:
                        pos = v.get('position')
                        if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                            world_x = map_center_x + float(pos[0])
                            world_y = map_center_y + float(pos[1])
                        else:
                            world_x, world_y = map_center_x, map_center_y
                        
                        area_screen_x = world_x * zoom + offset.x
                        area_screen_y = world_y * zoom + offset.y
                        
                        if -50 < area_screen_x < width + 50 and -50 < area_screen_y < height + 50:
                            try:
                                map_icon = load_map_icon(v.get('type'))
                                if map_icon:
                                    icon_s = pygame.transform.smoothscale(map_icon, (ICON_SIZE, ICON_SIZE))
                                    icon_rect = icon_s.get_rect(center=(int(area_screen_x), int(area_screen_y)))
                                    screen.blit(icon_s, icon_rect)
                                else:
                                    color = (120, 180, 255)
                                    glow_color = (150, 200, 255)
                                    pygame.draw.circle(screen, glow_color, (int(area_screen_x), int(area_screen_y)), 18, 2)
                                    pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 10, 2)
                                    pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 3)
                            except Exception:
                                color = (120, 180, 255)
                                pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 10, 2)
                            
                            # Draw location name
                            try:
                                small_font = pygame.font.SysFont(None, 18)
                                title_surf = small_font.render(v.get('name', ''), True, (220, 230, 255))
                                box_x = int(area_screen_x + ICON_SIZE // 2 + 8)
                                box_y = int(area_screen_y - title_surf.get_height() - 6)
                                screen.blit(small_font.render(v.get('name', ''), True, (0, 0, 0)), (box_x + 1, box_y + 1))
                                screen.blit(title_surf, (box_x, box_y))
                            except Exception:
                                pass
                    
                    # Draw fleet icon moving
                    if fleet_icon_local:
                        try:
                            icon = pygame.transform.smoothscale(fleet_icon_local, (40, 40))
                            screen.blit(icon, (int(ix - 20), int(iy - 20)))
                        except Exception:
                            pass
                    # Draw cinematic bars overlay if requested
                    try:
                        bars = getattr(main_player, '_cinematic_bars', None)
                        if bars:
                            th = int(bars.get('target_h', SCREEN_HEIGHT * 0.12))
                            top_y = int(bars.get('top_y', 0))
                            bot_y = int(bars.get('bot_y', SCREEN_HEIGHT - th))
                            pygame.draw.rect(screen, (0, 0, 0), (0, top_y, SCREEN_WIDTH, th))
                            pygame.draw.rect(screen, (0, 0, 0), (0, bot_y, SCREEN_WIDTH, th))
                    except Exception:
                        pass
                    pygame.display.flip()

                # clear annotation
                try:
                    delattr(main_player, '_fleet_entry')
                except Exception:
                    try:
                        del main_player._fleet_entry
                    except Exception:
                        pass
                # If caller requested auto-return after the fleet entry animation, exit the map screen now
                try:
                    if isinstance(fleet_entry, dict) and fleet_entry.get('auto_return'):
                        return "back"
                except Exception:
                    pass
        except Exception:
            try:
                delattr(main_player, '_fleet_entry')
            except Exception:
                try:
                    del main_player._fleet_entry
                except Exception:
                    pass

    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "exit"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "back"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Check INTERNAL button first
                if fleet_btn.handle_event(ev):
                    try:
                        res = internal_screen(main_player, player_fleet)
                        if res == 'to_game':
                            pass
                    except Exception:
                        pass
                    continue

                # HUD icon clicks (top-right)
                hud_icon_y = 20
                hud_icon_spacing = 140
                hud_start_x = SCREEN_WIDTH - 50
                clicked_ui = False
                for i, hud_name in enumerate(hud_icon_names):
                    x = hud_start_x - i * hud_icon_spacing
                    rect = pygame.Rect(x - 40, hud_icon_y, 80, 80)
                    if rect.collidepoint(ev.pos):
                        # Map (i==0) -> open galactic map (lazy import to avoid circular)
                        if i == 0:
                            try:
                                from spacegame.screens.galactic_map_screen import galactic_map_screen as _gms
                                res = _gms(main_player, player_fleet)
                                return res
                            except Exception:
                                pass
                            clicked_ui = True
                            break
                        # Sys (i==1) -> already in star system, do nothing
                        if i == 1:
                            clicked_ui = True
                            break
                        # Battle (i==2) -> return to game
                        if i == 2:
                            return 'to_game'

                if clicked_ui:
                    continue

                # If a details panel is visible for a selected area, detect clicks on its JUMP button
                if selected_area:
                    panel_width = 300
                    panel_height = 180
                    panel_x = width - panel_width - 18
                    panel_y = 120
                    padding = 12
                    btn_h = 32
                    jump_rect_screen = pygame.Rect(panel_x + padding, panel_y + panel_height - padding - btn_h, panel_width - padding*2, btn_h)
                    if jump_rect_screen.collidepoint(ev.pos):
                        try:
                            main_player.location_system = str(name)
                            main_player.location_area = selected_area.get('name')
                        except Exception:
                            pass
                        return 'to_game'

                # Check for clicks on visitable areas (use same lookup as drawing)
                try:
                    # load visitables for this system
                    visitables = []
                    key_variants = [str(name), str(name).title(), str(name).upper()]
                    sys_entry = None
                    for k in key_variants:
                        if k in systems_data:
                            sys_entry = systems_data[k]
                            break
                    if sys_entry and isinstance(sys_entry, dict):
                        visitables = list(sys_entry.get('visitables', []))

                    # compute map center used when drawing
                    map_center_x = bg_w / 2
                    map_center_y = bg_h / 2
                    clicked_area = False
                    # local icon size uses shared constant
                    icon_size = ICON_SIZE
                    for v in visitables:
                        pos = v.get('position')
                        if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                            world_x = map_center_x + float(pos[0])
                            world_y = map_center_y + float(pos[1])
                        else:
                            world_x, world_y = map_center_x, map_center_y

                        area_screen_x = world_x * zoom + offset.x
                        area_screen_y = world_y * zoom + offset.y
                        # use icon hitbox for clicks (match icon_size used when drawing)
                        hit_radius = ICON_SIZE // 2
                        area_rect = pygame.Rect(area_screen_x - hit_radius, area_screen_y - hit_radius, hit_radius * 2, hit_radius * 2)
                        if area_rect.collidepoint(ev.pos):
                            selected_area = v
                            clicked_area = True
                            break
                    # if click wasn't on any visitable, deselect
                    if not clicked_area:
                        selected_area = None
                    else:
                        continue
                except Exception:
                    pass

                # Start panning when clicking empty map area (only if scaled map larger than screen)
                scaled_w = bg_w * zoom
                scaled_h = bg_h * zoom
                if scaled_w > width or scaled_h > height:
                    panning = True
                    pan_last = ev.pos
                else:
                    panning = False

        screen.fill((0, 0, 0))
        # Draw scaled background at offset (use cache)
        if zoom != cached_zoom:
            cached_zoom = zoom
            scaled_size = (max(1, int(bg_w * zoom)), max(1, int(bg_h * zoom)))
            if scaled_size[0] > MAX_SCALED_DIMENSION or scaled_size[1] > MAX_SCALED_DIMENSION:
                scale_factor = min(MAX_SCALED_DIMENSION / scaled_size[0], MAX_SCALED_DIMENSION / scaled_size[1])
                scaled_size = (max(1, int(scaled_size[0] * scale_factor)), max(1, int(scaled_size[1] * scale_factor)))
            try:
                cached_bg_scaled = pygame.transform.smoothscale(bg_img, scaled_size)
            except Exception:
                try:
                    cached_bg_scaled = pygame.transform.scale(bg_img, scaled_size)
                except Exception:
                    cached_bg_scaled = bg_img

        if cached_bg_scaled:
            screen.blit(cached_bg_scaled, (int(offset.x), int(offset.y)))

            # Top title (centered) similar to other screens
            title_font = pygame.font.Font(None, 40)
            title_text = str(name).upper()
            title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
            title_rect = title_surf.get_rect(center=(width // 2, UI_TOP_BAR_HEIGHT // 2 - 22))
            screen.blit(title_surf, title_rect)

            # Determine visitable areas for this system from JSON data
            visitables = []
            try:
                # support several key casings
                key_variants = [str(name), str(name).title(), str(name).upper()]
                sys_entry = None
                for k in key_variants:
                    if k in systems_data:
                        sys_entry = systems_data[k]
                        break
                if sys_entry is None:
                    sys_entry = systems_data.get(str(name).title()) or systems_data.get(str(name).upper())
                if sys_entry and isinstance(sys_entry, dict):
                    visitables = list(sys_entry.get('visitables', []))
            except Exception:
                visitables = []

            # compute center of the (already scaled) background - use original image size
            map_center_x = bg_w / 2
            map_center_y = bg_h / 2

            # Draw visitable markers
            for v in visitables:
                # if visitable has 'position' treat as offset relative to center
                pos = v.get('position')
                if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    world_x = map_center_x + float(pos[0])
                    world_y = map_center_y + float(pos[1])
                else:
                    # fallback to center
                    world_x, world_y = map_center_x, map_center_y

                # convert to screen coordinates using offset/zoom (here zoom==fit_zoom)
                area_screen_x = world_x * zoom + offset.x
                area_screen_y = world_y * zoom + offset.y

                # Only draw if on screen
                if -50 < area_screen_x < width + 50 and -50 < area_screen_y < height + 50:
                    # Try to draw an icon based on type
                    try:
                        map_icon = load_map_icon(v.get('type'))
                        if map_icon:
                            icon_s = pygame.transform.smoothscale(map_icon, (ICON_SIZE, ICON_SIZE))
                            icon_rect = icon_s.get_rect(center=(int(area_screen_x), int(area_screen_y)))
                            screen.blit(icon_s, icon_rect)
                        else:
                            # fallback to simple circles
                            is_selected = (selected_area is not None and selected_area.get('name') == v.get('name'))
                            color = (255, 200, 50) if is_selected else (120, 180, 255)
                            glow_color = (255, 220, 100) if is_selected else (150, 200, 255)
                            pygame.draw.circle(screen, glow_color, (int(area_screen_x), int(area_screen_y)), 18, 2)
                            pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 10, 2)
                            pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 3)

                    except Exception:
                        # drawing fallback
                        is_selected = (selected_area is not None and selected_area.get('name') == v.get('name'))
                        color = (255, 200, 50) if is_selected else (120, 180, 255)
                        pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 10, 2)

                    # small name overlay to the right
                    try:
                        small_font = pygame.font.SysFont(None, 18)
                        title_surf = small_font.render(v.get('name', ''), True, (220, 230, 255))
                        box_x = int(area_screen_x + ICON_SIZE // 2 + 8)
                        box_y = int(area_screen_y - title_surf.get_height() - 6)
                        # draw shadow + text
                        screen.blit(small_font.render(v.get('name', ''), True, (0,0,0)), (box_x + 1, box_y + 1))
                        screen.blit(title_surf, (box_x, box_y))
                    except Exception:
                        pass

            # Draw fleet icon at current location in this system (only if player is in this system)
            try:
                if fleet_icon:
                    current_location_area = getattr(main_player, 'location_area', None)
                    # Only draw if this system matches and we have a visitable location
                    if current_location_area and current_location_area != 'None':
                        # Find the visitable by name and draw icon at its position
                        for v in visitables:
                            if v.get('name') == current_location_area:
                                pos = v.get('position')
                                if pos and isinstance(pos, (list, tuple)) and len(pos) >= 2:
                                    world_x = map_center_x + float(pos[0])
                                    world_y = map_center_y + float(pos[1])
                                else:
                                    world_x, world_y = map_center_x, map_center_y
                                
                                fleet_screen_x = world_x * zoom + offset.x
                                fleet_screen_y = world_y * zoom + offset.y
                                
                                # Only draw if on screen
                                if -50 < fleet_screen_x < width + 50 and -50 < fleet_screen_y < height + 50:
                                    fleet_icon_scaled = pygame.transform.smoothscale(fleet_icon, (40, 40))
                                    fleet_icon_rect = fleet_icon_scaled.get_rect(center=(int(fleet_screen_x), int(fleet_screen_y)))
                                    screen.blit(fleet_icon_scaled, fleet_icon_rect)
                                break
            except Exception:
                pass

            # Draw simplified compact details rect on the right side if an area is selected
            if selected_area:
                panel_width = 300
                panel_height = 180
                panel_x = width - panel_width - 18
                panel_y = 120

                padding = 12

                # Semi-transparent panel surface
                panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                panel_surf.fill((18, 26, 38, 220))

                # Fonts
                title_font = pygame.font.SysFont(None, 20, bold=True)
                subtitle_font = pygame.font.SysFont(None, 14)
                type_flag_font = pygame.font.SysFont(None, 18, bold=True)

                # Render texts
                name_s = title_font.render(selected_area.get('name', ''), True, (230, 230, 255))

                panel_surf.blit(name_s, (padding, padding))

                # For Asteroids, show ore preview image and type flag
                if selected_area.get('type') == 'Asteroids':
                    ore_type = selected_area.get('ore', 'M')
                    ore_filename = f"RUOre{ore_type}.png"
                    
                    # Load and scale ore preview image
                    try:
                        ore_img_path = os.path.join(PREVIEWS_DIR, ore_filename)
                        if os.path.exists(ore_img_path):
                            ore_img = pygame.image.load(ore_img_path)
                            ore_img_scaled = pygame.transform.smoothscale(ore_img, (50, 50))
                            ore_img_rect = ore_img_scaled.get_rect(center=(padding + 30, padding + 60))
                            panel_surf.blit(ore_img_scaled, ore_img_rect)
                    except Exception:
                        pass
                    
                    # Draw ore type flag rect (similar to bpdetails: "RU" on left, ore letter on right)
                    flag_w = 70
                    flag_h = 24
                    flag_rect = pygame.Rect(padding + 85, padding + 50, flag_w, flag_h)
                    pygame.draw.rect(panel_surf, UI_NAV_LINE_COLOR, flag_rect, 2)
                    oretype_w = 30
                    oretype_h = 24
                    oretype_rect= pygame.Rect(padding + 85, padding + 50, oretype_w, oretype_h)
                    pygame.draw.rect(panel_surf, UI_ICON_BLUE, oretype_rect)
                    
                    
                    # Draw "RU" text on the left side of flag
                    ru_s = type_flag_font.render("RU", True, (220, 230, 255))
                    ru_rect = ru_s.get_rect(centery=flag_rect.centery)
                    ru_rect.left = flag_rect.left + 6
                    panel_surf.blit(ru_s, ru_rect)
                    
                    # Draw ore type letter on the right side of flag
                    ore_letter_s = type_flag_font.render(ore_type, True, (220, 230, 255))
                    ore_letter_rect = ore_letter_s.get_rect(centery=flag_rect.centery)
                    ore_letter_rect.right = flag_rect.right - 15
                    panel_surf.blit(ore_letter_s, ore_letter_rect)

                # JUMP button spanning the bottom of the panel
                btn_h = 32
                btn_w = panel_width - padding * 2
                jump_rect = pygame.Rect(padding, panel_height - padding - btn_h, btn_w, btn_h)
                pygame.draw.rect(panel_surf, (40, 100, 80), jump_rect)
                js = subtitle_font.render("JUMP", True, (170, 210, 240))
                panel_surf.blit(js, (jump_rect.x + (btn_w - js.get_width())//2, jump_rect.y + (btn_h - js.get_height())//2))

                # Blit panel surface to screen
                screen.blit(panel_surf, (panel_x, panel_y))

        # Draw INTERNAL hex button (styled similar to other screens)
        mouse_pos = pygame.mouse.get_pos()
        # hex body
        rect = fleet_btn.rect
        color = (190, 230, 255) if rect.collidepoint(mouse_pos) else (120, 200, 255)
        draw_hex(screen, rect.center, rect.width * 0.9, rect.height * 1.2, color, 3)
        # header text
        label = fleet_btn_font.render("INTERNAL", True, color)
        label_rect = label.get_rect()
        label_rect.bottomleft = (rect.left, rect.top - 10)
        screen.blit(label, label_rect)

        # Draw HUD icons at top-right
        hud_icon_y = 20
        hud_icon_spacing = 140
        hud_start_x = SCREEN_WIDTH - 50
        for i, n in enumerate(hud_icon_names):
            x = hud_start_x - i * hud_icon_spacing
            if i > 0 and hud_separator is not None:
                sep_scaled = pygame.transform.smoothscale(hud_separator, (20, 10))
                sep_rect = sep_scaled.get_rect(center=(x + 70, hud_icon_y + 40))
                screen.blit(sep_scaled, sep_rect)

            is_selected = (i == hud_selected_index)
            icon = load_hud_icon(n, selected=is_selected)
            if icon is not None:
                icon_scaled = pygame.transform.smoothscale(icon, (80, 80))
                icon_rect = icon_scaled.get_rect(topleft=(x - 40, hud_icon_y))
                screen.blit(icon_scaled, icon_rect)

        # screen updated once at end of loop

        # handle panning mouse motion and wheel after drawing (events already processed above)
        for e in pygame.event.get(pygame.MOUSEMOTION):
            if panning and e.buttons[0]:
                mx, my = e.pos
                dx = mx - pan_last[0]
                dy = my - pan_last[1]
                offset.x += dx
                offset.y += dy
                pan_last = (mx, my)
                clamp_offset()

        # Process any mouse wheel events (some backends deliver as separate events)
        for e in pygame.event.get(pygame.MOUSEWHEEL):
            old_zoom = zoom
            if e.y > 0:
                zoom *= 1.12 ** e.y
            else:
                zoom *= 0.9 ** (-e.y)
            zoom = max(min_zoom, min(max_zoom, zoom))
            mx, my = pygame.mouse.get_pos()
            world_x = (mx - offset.x) / old_zoom
            world_y = (my - offset.y) / old_zoom
            offset.x = mx - world_x * zoom
            offset.y = my - world_y * zoom
            clamp_offset()

        # If cinematic bars overlay requested by caller, draw them on top
        try:
            bars = getattr(main_player, '_cinematic_bars', None)
            if bars:
                th = int(bars.get('target_h', SCREEN_HEIGHT * 0.12))
                top_y = int(bars.get('top_y', -th))
                bot_y = int(bars.get('bot_y', SCREEN_HEIGHT))
                pygame.draw.rect(screen, (0, 0, 0), (0, top_y, SCREEN_WIDTH, th))
                pygame.draw.rect(screen, (0, 0, 0), (0, bot_y, SCREEN_WIDTH, th))
        except Exception:
            pass
        pygame.display.flip()