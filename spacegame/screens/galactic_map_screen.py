import pygame
from pygame.math import Vector2
from spacegame.ui.ui import Button, draw_hex
from spacegame.screens.internal_screen import internal_screen
from spacegame.config import PREVIEWS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, UI_ICON_BLUE


# Global caches for fast screen transitions
_GALACTIC_MAP_CACHE = {
    'bg_img': None,
    'small_font': None,
    'fleet_btn_font': None,
    'hud_icons': {},
    'hud_separator': None,
    'tier_icons': {},
    'map_icons': {},
}


def _load_cached_image(filename: str, use_convert_alpha: bool = True) -> pygame.Surface:
    """Load and cache an image."""
    try:
        img = pygame.image.load(filename)
        if use_convert_alpha:
            return img.convert_alpha()
        return img.convert()
    except Exception:
        return None


def _init_galactic_map_cache():
    """Pre-initialize all cached resources for galactic map."""
    global _GALACTIC_MAP_CACHE
    
    # Load galaxy map background (expensive)
    if _GALACTIC_MAP_CACHE['bg_img'] is None:
        _GALACTIC_MAP_CACHE['bg_img'] = _load_cached_image(f"{PREVIEWS_DIR}/GalaxyMap.png", use_convert_alpha=True)
        if _GALACTIC_MAP_CACHE['bg_img'] is None:
            # Fallback placeholder
            _GALACTIC_MAP_CACHE['bg_img'] = pygame.Surface((1024, 768))
            _GALACTIC_MAP_CACHE['bg_img'].fill((10, 10, 30))
    
    # Create fonts (relatively expensive)
    if _GALACTIC_MAP_CACHE['small_font'] is None:
        _GALACTIC_MAP_CACHE['small_font'] = pygame.font.SysFont(None, 20)
    
    if _GALACTIC_MAP_CACHE['fleet_btn_font'] is None:
        _GALACTIC_MAP_CACHE['fleet_btn_font'] = pygame.font.SysFont(None, 19)
    
    # Pre-load HUD icons
    hud_icon_names = ['Map', 'Sys', 'Battle']
    for name in hud_icon_names:
        for selected in [False, True]:
            suffix = "Selected" if selected else "Unselected"
            filename = f"HudIcon_{name}_{suffix}.png"
            key = f"{name}_{suffix}"
            if key not in _GALACTIC_MAP_CACHE['hud_icons']:
                _GALACTIC_MAP_CACHE['hud_icons'][key] = _load_cached_image(f"{PREVIEWS_DIR}/{filename}", use_convert_alpha=True)
    
    # Pre-load separator
    if _GALACTIC_MAP_CACHE['hud_separator'] is None:
        _GALACTIC_MAP_CACHE['hud_separator'] = _load_cached_image(f"{PREVIEWS_DIR}/HudIcon_Separator.png", use_convert_alpha=True)
    
    # Pre-load tier icons
    for tier in range(4):
        tier_key = f"tier{tier}"
        if tier_key not in _GALACTIC_MAP_CACHE['tier_icons']:
            tier_filename = f"UI_icon_tier{tier}.{'jpg' if tier == 0 else 'png'}"
            _GALACTIC_MAP_CACHE['tier_icons'][tier_key] = _load_cached_image(f"{PREVIEWS_DIR}/{tier_filename}", use_convert_alpha=True)
    
    # Pre-load map icons
    map_icon_types = ['Asteroirds', 'Station']
    for icon_type in map_icon_types:
        map_key = f"map_{icon_type}"
        if map_key not in _GALACTIC_MAP_CACHE['map_icons']:
            _GALACTIC_MAP_CACHE['map_icons'][map_key] = _load_cached_image(f"{PREVIEWS_DIR}/UI_Map_{icon_type}.png", use_convert_alpha=True)
    
    # Pre-load fleet icon
    if _GALACTIC_MAP_CACHE.get('fleet_icon') is None:
        _GALACTIC_MAP_CACHE['fleet_icon'] = _load_cached_image(f"{PREVIEWS_DIR}/FleetIcon.png", use_convert_alpha=True)


def preload_map_images():
    """Preload galactic background and all Map_<Name>.png previews from PREVIEWS_DIR.

    Stores results in _GALACTIC_MAP_CACHE['system_previews'] keyed by Titlecase name.
    """
    _init_galactic_map_cache()
    import os
    previews = {}
    try:
        for fn in os.listdir(PREVIEWS_DIR):
            if fn.startswith('Map_') and fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                name = fn[len('Map_'):]
                name = os.path.splitext(name)[0]
                try:
                    img = _load_cached_image(f"{PREVIEWS_DIR}/{fn}", use_convert_alpha=True)
                    if img is not None:
                        previews[name.title()] = img
                except Exception:
                    pass
    except Exception:
        pass

    _GALACTIC_MAP_CACHE['system_previews'] = previews
    return previews


def galactic_map_screen(main_player, player_fleet):
    """Galactic map screen with true-size background, zoom and pan.

    Controls:
    - Scroll wheel to zoom in/out (cursor-centered zoom)
    - Left mouse drag to pan the map
    - ESC to return/back
    - "INTERNAL" hex button (top-left) opens internal_screen
    """
    # Initialize cache on first entry (or reuse if already initialized)
    _init_galactic_map_cache()
    
    # Define selectable map areas (relative offsets; absolute positions computed after background size known)
    # 'rel' is an offset relative to the map center so items stay around center
    map_areas = [
        {'name': 'LAZARUS', 'subtitle': 'Hiigaran', 'position': (-80, 0), 'tier': 0, 'type': 'Station', 'visitables': 5},
        {'name': 'INIIM', 'subtitle': 'Hiigaran', 'position': (90, 40), 'tier': 0, 'type': 'Asteroirds', 'visitables': 2},
        {'name': 'Toasiim', 'subtitle': 'Hiigaran', 'position': (10, -70), 'tier': 0, 'type': 'Asteroirds', 'visitables': 2},
    ]
    
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # --- Use cached resources ---
    fleet_btn_font = _GALACTIC_MAP_CACHE['fleet_btn_font']
    fleet_btn = Button((10, 40, 100, 30), "INTERNAL", fleet_btn_font)

    def draw_hex_button(surface, button, font, base_color, hover_color, header_text):
        rect = button.rect
        mouse_pos = pygame.mouse.get_pos()
        color = hover_color if rect.collidepoint(mouse_pos) else base_color

        # hex body
        draw_hex(surface, rect.center, rect.width * 0.9, rect.height * 1.2, color, 3)

        # header text at top-left of the hex
        label = font.render(header_text, True, color)
        label_rect = label.get_rect()
        label_rect.bottomleft = (rect.left, rect.top - 10)
        surface.blit(label, label_rect)

    # --- HUD Icons (use cached icons) ---
    hud_icon_names = ['Map', 'Sys', 'Battle']
    hud_selected_index = 0
    selected_area = None  # Track selected map area

    # Pre-scaled HUD icons cache (per session)
    hud_icon_scaled_cache = {}
    def get_scaled_icon(name: str, selected: bool):
        cache_key = f"{name}_{selected}"
        if cache_key not in hud_icon_scaled_cache:
            icon_key = f"{name}_{'Selected' if selected else 'Unselected'}"
            icon = _GALACTIC_MAP_CACHE['hud_icons'].get(icon_key)
            if icon:
                scaled = pygame.transform.smoothscale(icon, (80, 80))
                scaled.set_alpha(255)
                hud_icon_scaled_cache[cache_key] = scaled
        return hud_icon_scaled_cache.get(cache_key)

    separator_scaled = None
    def get_scaled_separator():
        nonlocal separator_scaled
        if separator_scaled is None:
            separator = _GALACTIC_MAP_CACHE['hud_separator']
            if separator:
                separator_scaled = pygame.transform.smoothscale(separator, (20, 10))
                separator_scaled.set_alpha(255)
        return separator_scaled

    # --- Galaxy map background (now cached with convert_alpha) ---
    bg_img = _GALACTIC_MAP_CACHE['bg_img']
    bg_w, bg_h = bg_img.get_size()

    # Compute absolute positions for map areas around the center of the map
    map_center_x = bg_w / 2
    map_center_y = bg_h / 2
    for a in map_areas:
        if 'position' in a:
            a['pos'] = (map_center_x + a['position'][0], map_center_y + a['position'][1])
        elif 'pos' not in a:
            a['pos'] = (map_center_x, map_center_y)

    # If a fleet move has been requested (annotated on main_player), animate the fleet icon
    fleet_move = getattr(main_player, '_fleet_move', None)
    if fleet_move:
        try:
            from_name, to_name = fleet_move
            # find map area entries for both names (try variants)
            def find_area_by_name(n):
                if n is None:
                    return None
                for a in map_areas:
                    if a.get('name') and a['name'].lower() == str(n).lower():
                        return a
                    if a.get('name') and a['name'].upper() == str(n).upper():
                        return a
                return None

            a_from = find_area_by_name(from_name)
            a_to = find_area_by_name(to_name)
            if a_from and a_to:
                # compute screen coords for both
                screen_w, screen_h = width, height
                zoom_local = zoom
                off = offset
                from_px = (a_from['pos'][0] * zoom_local + off.x, a_from['pos'][1] * zoom_local + off.y)
                to_px = (a_to['pos'][0] * zoom_local + off.x, a_to['pos'][1] * zoom_local + off.y)
                # simple linear animation over 1.2s
                anim_dur = 1.2
                clock_anim = pygame.time.Clock()
                t = 0.0
                fleet_icon = _GALACTIC_MAP_CACHE.get('fleet_icon')
                while t < anim_dur:
                    dt = clock_anim.tick(60) / 1000.0
                    t += dt
                    alpha = min(1.0, t / anim_dur)
                    ix = from_px[0] + (to_px[0] - from_px[0]) * alpha
                    iy = from_px[1] + (to_px[1] - from_px[1]) * alpha
                    # draw background scaled as usual
                    if cached_bg_scaled is None or cached_zoom != zoom_local:
                        try:
                            cached_bg_scaled = pygame.transform.smoothscale(bg_img, (int(bg_w * zoom_local), int(bg_h * zoom_local)))
                        except Exception:
                            cached_bg_scaled = pygame.transform.scale(bg_img, (int(bg_w * zoom_local), int(bg_h * zoom_local)))
                    screen.blit(cached_bg_scaled, (off.x, off.y))
                    # draw fleet icon
                    if fleet_icon:
                        try:
                            icon = pygame.transform.smoothscale(fleet_icon, (40, 40))
                            icon.set_alpha(255)
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

        except Exception:
            pass
        # Clear annotation so normal interaction resumes
        try:
            delattr(main_player, '_fleet_move')
        except Exception:
            try:
                del main_player._fleet_move
            except Exception:
                pass
        # If caller requested the galactic map to auto-close after the fleet animation,
        # honor that and return immediately so the caller (cinematic) can continue.
        try:
            if getattr(main_player, '_fleet_move_auto', False):
                try:
                    delattr(main_player, '_fleet_move_auto')
                except Exception:
                    try:
                        del main_player._fleet_move_auto
                    except Exception:
                        pass
                return "back"
        except Exception:
            pass

    # View transform - default fully zoomed out so whole map is visible
    fit_zoom = min(width / bg_w, height / bg_h) if bg_w and bg_h else 1.0
    zoom = fit_zoom
    
    # Calculate safe max_zoom to prevent surface size crashes
    # Limit scaled surface to a reasonable max (e.g., 4096 x 4096 pixels max)
    MAX_SCALED_DIMENSION = 8192
    max_zoom = min(4.0, MAX_SCALED_DIMENSION / max(bg_w, bg_h))
    min_zoom, max_zoom = fit_zoom, max_zoom

    # Cache for scaled background - delay initial scaling to first frame to avoid lag on entry
    cached_zoom = None
    cached_bg_scaled = None

    # offset is the top-left of the image in screen coordinates; center image by default
    offset = Vector2((width - bg_w * zoom) / 2, (height - bg_h * zoom) / 2)

    def clamp_offset():
        scaled_w = bg_w * zoom
        scaled_h = bg_h * zoom
        # center when smaller than screen
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

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check fleet button first
                if fleet_btn.handle_event(event):
                    res = internal_screen(main_player, player_fleet)
                    if res == "to_game":
                        pass
                    continue

                # Check for map area clicks
                area_clicked = False
                for area in map_areas:
                    # Convert world coordinates to screen coordinates
                    area_screen_x = area['pos'][0] * zoom + offset.x
                    area_screen_y = area['pos'][1] * zoom + offset.y
                    area_rect = pygame.Rect(area_screen_x - 15, area_screen_y - 15, 30, 30)
                    if area_rect.collidepoint(event.pos):
                        selected_area = area
                        area_clicked = True
                        break

                if area_clicked:
                    continue

                # If a details panel is visible for a selected area, detect clicks on its VIEW button
                if selected_area:
                    panel_width = 260
                    panel_height = 120
                    panel_x = width - panel_width - 18
                    panel_y = 120
                    padding = 12
                    btn_h = 28
                    btn_w = panel_width - padding * 2
                    view_rect_screen = pygame.Rect(panel_x + padding, panel_y + panel_height - padding - btn_h, btn_w, btn_h)
                    if view_rect_screen.collidepoint(event.pos):
                        try:
                            from spacegame.screens.star_system_map import star_system_map as _ssm
                            res = _ssm(main_player, player_fleet, system_name=selected_area.get('name'))
                            if res == 'exit':
                                return 'exit'
                            if res == 'to_game':
                                return 'to_game'
                        except Exception:
                            pass
                        continue

                # Check HUD icon clicks (top-right)
                hud_icon_y = 20
                hud_icon_spacing = 140
                hud_start_x = width - 50
                clicked_ui = False
                for i, hud_name in enumerate(hud_icon_names):
                    x = hud_start_x - i * hud_icon_spacing
                    rect = pygame.Rect(x - 40, hud_icon_y, 80, 80)
                    if rect.collidepoint(event.pos):
                        # Rightmost (i==2) returns to game
                        if i == 2:
                            return "to_game"

                        # Middle (i==1) opens the Star System Map for the currently selected area (or fleet)
                        if i == 1:
                            try:
                                from spacegame.screens.star_system_map import star_system_map as _ssm
                                if selected_area:
                                    res = _ssm(main_player, player_fleet, system_name=selected_area.get('name'))
                                else:
                                    # If no area selected, open current fleet location system
                                    current_system = getattr(main_player, 'location_system', None) or 'Lazarus'
                                    res = _ssm(main_player, player_fleet, system_name=current_system)
                                if res == 'exit':
                                    return 'exit'
                                if res == 'to_game':
                                    return 'to_game'
                            except Exception:
                                pass
                            clicked_ui = True
                            break

                        # Otherwise update selection index
                        hud_selected_index = i
                        clicked_ui = True
                        break

                if not clicked_ui:
                    # start panning only if the scaled map is larger than the screen
                    scaled_w = bg_w * zoom
                    scaled_h = bg_h * zoom
                    if scaled_w > width or scaled_h > height:
                        panning = True
                        pan_last = event.pos
                    else:
                        panning = False

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                panning = False

            elif event.type == pygame.MOUSEMOTION and panning:
                mx, my = event.pos
                dx = mx - pan_last[0]
                dy = my - pan_last[1]
                # move offset by delta (consider zoom so dragging moves map logically)
                offset.x += dx
                offset.y += dy
                pan_last = (mx, my)
                clamp_offset()
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom centered on mouse position
                old_zoom = zoom
                if event.y > 0:
                    zoom *= 1.12 ** event.y
                else:
                    zoom *= 0.9 ** (-event.y)
                zoom = max(min_zoom, min(max_zoom, zoom))

                mx, my = pygame.mouse.get_pos()
                # world coordinates under mouse before zoom
                world_x = (mx - offset.x) / old_zoom
                world_y = (my - offset.y) / old_zoom
                # adjust offset so world point stays at mouse after zoom
                offset.x = mx - world_x * zoom
                offset.y = my - world_y * zoom
                clamp_offset()

        # --- Draw ---
        screen.fill((0, 0, 0))

        # Draw scaled background at offset (use cache, only rescale if zoom changed)
        if zoom != cached_zoom:
            cached_zoom = zoom
            scaled_size = (max(1, int(bg_w * zoom)), max(1, int(bg_h * zoom)))
            # Safety check: ensure scaled size doesn't exceed limits
            if scaled_size[0] > MAX_SCALED_DIMENSION or scaled_size[1] > MAX_SCALED_DIMENSION:
                scale_factor = min(MAX_SCALED_DIMENSION / scaled_size[0], MAX_SCALED_DIMENSION / scaled_size[1])
                scaled_size = (max(1, int(scaled_size[0] * scale_factor)), max(1, int(scaled_size[1] * scale_factor)))
            try:
                cached_bg_scaled = pygame.transform.smoothscale(bg_img, scaled_size)
            except Exception:
                # Fallback to regular scale if smoothscale fails
                try:
                    cached_bg_scaled = pygame.transform.scale(bg_img, scaled_size)
                except Exception:
                    # If both fail, use the original image
                    cached_bg_scaled = bg_img

        if cached_bg_scaled:
            screen.blit(cached_bg_scaled, (int(offset.x), int(offset.y)))

        # Draw map areas (selectable regions)
        for area in map_areas:
            # Convert world coordinates to screen coordinates
            area_screen_x = area['pos'][0] * zoom + offset.x
            area_screen_y = area['pos'][1] * zoom + offset.y
            
            # Only draw if on screen
            if -50 < area_screen_x < width + 50 and -50 < area_screen_y < height + 50:
                # Draw area circle with glow effect
                is_selected = (selected_area == area)
                color = (255, 200, 50) if is_selected else (120, 180, 255)
                glow_color = (255, 220, 100) if is_selected else (150, 200, 255)
                
                # Glow ring
                pygame.draw.circle(screen, glow_color, (int(area_screen_x), int(area_screen_y)), 20, 2)
                # Main circle
                pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 12, 2)
                # Center dot
                pygame.draw.circle(screen, color, (int(area_screen_x), int(area_screen_y)), 4)
                
                # Draw small overlay at top-right of the map icon: title + tier icon + type icon
                try:
                    title_font = _GALACTIC_MAP_CACHE['small_font']
                    title_surf = title_font.render(area['name'], True, (220, 230, 255))
                    icon_size = 18
                    padding = 6

                    # Icons
                    tier_key = f"tier{area.get('tier',0)}"
                    tier_icon = _GALACTIC_MAP_CACHE['tier_icons'].get(tier_key)
                    type_icon = _GALACTIC_MAP_CACHE['map_icons'].get(f"map_{area.get('type','Asteroirds')}")

                    text_w = title_surf.get_width()
                    icons_w = (icon_size + 4) * (1 if tier_icon else 0) + (icon_size + 4) * (1 if type_icon else 0)
                    box_w = text_w + padding + icons_w + padding
                    box_h = max(title_surf.get_height(), icon_size) + padding * 2

                    box_x = int(area_screen_x + 14)
                    box_y = int(area_screen_y - box_h - 8)

                    # Transparent background and no border per request; draw title with shadow for readability
                    text_x = box_x + padding
                    text_y = box_y + padding + (box_h - padding*2 - title_surf.get_height())//2
                    # shadow
                    shadow = _GALACTIC_MAP_CACHE['small_font'].render(area['name'], True, (0, 0, 0))
                    screen.blit(shadow, (text_x + 1, text_y + 1))
                    screen.blit(title_surf, (text_x, text_y))

                    # Blit icons to the right of the text
                    icon_x = box_x + box_w - padding - icon_size
                    icon_y = box_y + padding + (box_h - padding*2 - icon_size)//2
                    if type_icon:
                        t_scaled = pygame.transform.smoothscale(type_icon, (icon_size, icon_size))
                        screen.blit(t_scaled, (icon_x, icon_y))
                        icon_x -= (icon_size + 4)
                    if tier_icon:
                        r_scaled = pygame.transform.smoothscale(tier_icon, (icon_size, icon_size))
                        screen.blit(r_scaled, (icon_x, icon_y))
                except Exception:
                    pass

        # Draw fleet icon at current location
        try:
            current_location = getattr(main_player, 'location_system', None)
            fleet_icon = _GALACTIC_MAP_CACHE.get('fleet_icon')
            if current_location and fleet_icon:
                # Find the area matching current location
                for area in map_areas:
                    if area['name'].upper() == str(current_location).upper():
                        fleet_screen_x = area['pos'][0] * zoom + offset.x
                        fleet_screen_y = area['pos'][1] * zoom + offset.y
                        
                        # Only draw if on screen
                        if -50 < fleet_screen_x < width + 50 and -50 < fleet_screen_y < height + 50:
                            fleet_icon_scaled = pygame.transform.smoothscale(fleet_icon, (40, 40))
                            fleet_icon_rect = fleet_icon_scaled.get_rect(center=(int(fleet_screen_x), int(fleet_screen_y)))
                            screen.blit(fleet_icon_scaled, fleet_icon_rect)
                        break
        except Exception:
            pass
        # Top-left: fleet button (hex style to match game_screen)
        draw_hex_button(screen, fleet_btn, fleet_btn_font, base_color=(120, 200, 255), hover_color=(190, 230, 255), header_text="INTERNAL")

        # Notifications: replicate basic placement and drawing from game_screen
        inv_mgr = getattr(main_player, 'inventory_manager', None)
        notif_list = getattr(inv_mgr, 'notifications', []) if inv_mgr is not None else []
        if notif_list:
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

                preview_fn = n.get('preview')
                try:
                    if preview_fn:
                        icon = pygame.image.load(PREVIEWS_DIR + "/" + preview_fn).convert_alpha()
                    else:
                        icon = None
                    if icon is not None:
                        icon_s = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                        screen.blit(icon_s, (nx + padding, ny + (popup_h - icon_size) // 2))
                except Exception:
                    pass

                title = n.get('title', 'Notification')
                text = n.get('text', title)
                tx = nx + padding + (icon_size + 8 if preview_fn else 0)
                # shadow
                shadow_surf = small_font.render(text, True, (0, 0, 0))
                screen.blit(shadow_surf, (tx + 1, ny + (popup_h - small_font.get_height()) // 2 + 1))
                text_surf = small_font.render(text, True, (108, 198, 219))
                screen.blit(text_surf, (tx, ny + (popup_h - small_font.get_height()) // 2))

        # Top-right HUD icons (use lazy-scaled cache)
        hud_icon_y = 20
        hud_icon_spacing = 140
        hud_start_x = width - 50
        for i, name in enumerate(hud_icon_names):
            x = hud_start_x - i * hud_icon_spacing
            if i > 0:
                sep = get_scaled_separator()
                if sep:
                    sep_rect = sep.get_rect(center=(x + 70, hud_icon_y + 40))
                    screen.blit(sep, sep_rect)

            is_selected = (i == hud_selected_index)
            icon_scaled = get_scaled_icon(name, is_selected)
            if icon_scaled:
                icon_rect = icon_scaled.get_rect(topleft=(x - 40, hud_icon_y))
                screen.blit(icon_scaled, icon_rect)

        # Draw simplified compact details rect on the right side if an area is selected
        if selected_area:
            panel_width = 260
            panel_height = 120
            panel_x = width - panel_width - 18
            panel_y = 120

            padding = 12

            # Create semi-transparent surface so it blends but remains readable
            panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            panel_surf.fill((18, 26, 38, 220))

            # Fonts
            title_font = pygame.font.SysFont(None, 20, bold=True)
            subtitle_font = pygame.font.SysFont(None, 14)
            num_font = pygame.font.SysFont(None, 18, bold=True)

            # Render texts
            name_s = title_font.render(selected_area['name'], True, (230, 230, 255))
            faction_s = subtitle_font.render(selected_area.get('subtitle', ''), True, (160, 200, 240))

            # Top-right group: visitable count, tier icon, type icon (right-aligned)
            visit_count = selected_area.get('visitables', 0)
            visit_s = num_font.render(str(visit_count), True, (180, 240, 180))

            icon_size = 18
            type_icon = _GALACTIC_MAP_CACHE['map_icons'].get(f"map_{selected_area.get('type','Asteroirds')}")
            tier_icon = _GALACTIC_MAP_CACHE['tier_icons'].get(f"tier{selected_area.get('tier',0)}")

            # Blit onto panel surface
            panel_surf.blit(name_s, (padding, padding))
            panel_surf.blit(faction_s, (padding, padding + name_s.get_height() + 2))

            # compute positions for right-aligned icons/text
            # Align the group flush to the panel's top-right (no padding to right/top)
            right_x = panel_width
            top_y = 0

            # visit count with border rect (flush to right edge)
            visit_w = visit_s.get_width()
            visit_border_padding = 6
            visit_rect_x = right_x - (visit_w + 2 * visit_border_padding)
            visit_rect = pygame.Rect(visit_rect_x, top_y, visit_w + 2 * visit_border_padding, icon_size)
            pygame.draw.rect(panel_surf, UI_ICON_BLUE, visit_rect, 2)  # Border only, no fill
            # blit visit text inside the border, vertically centered
            text_x = visit_rect_x + visit_border_padding
            text_y = top_y + (icon_size - visit_s.get_height()) // 2
            panel_surf.blit(visit_s, (text_x, text_y))
            # move right_x to the left edge of the visit rect for placing other icons
            right_x = visit_rect_x

            # tier icon (left of visit count)
            if tier_icon:
                t_scaled = pygame.transform.smoothscale(tier_icon, (icon_size, icon_size))
                panel_surf.blit(t_scaled, (right_x - icon_size, top_y))
                right_x -= (icon_size + 6)

            # type icon (left of tier)
            if type_icon:
                m_scaled = pygame.transform.smoothscale(type_icon, (icon_size, icon_size))
                panel_surf.blit(m_scaled, (right_x - icon_size, top_y))
                right_x -= (icon_size + 6)

            # VIEW Button
            btn_h = 28
            btn_w = panel_width - padding * 2
            # VIEW - spans full width
            view_rect = pygame.Rect(padding, panel_height - padding - btn_h, btn_w, btn_h)
            pygame.draw.rect(panel_surf, (50, 88, 120), view_rect)
            vs = subtitle_font.render("VIEW", True, (170, 210, 240))
            panel_surf.blit(vs, (view_rect.x + (btn_w - vs.get_width())//2, view_rect.y + (btn_h - vs.get_height())//2))

            # Blit panel surface to screen
            screen.blit(panel_surf, (panel_x, panel_y))

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
