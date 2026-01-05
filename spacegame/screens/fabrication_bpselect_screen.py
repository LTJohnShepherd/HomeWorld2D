import sys
import math
import pygame
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    UI_BG_COLOR,
    UI_TAB_HEIGHT,
    UI_SECTION_TEXT_COLOR,
    UI_TAB_UNDERLINE_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR,
    UI_ICON_BLUE,
)
from spacegame.config import PREVIEWS_DIR
from spacegame.models.blueprints.interceptorblueprint import BPInterceptor
from spacegame.models.blueprints.resourcecollectorblueprint import BPResourceCollector
from spacegame.models.blueprints.plasmabomberblueprint import BPPlasmaBomber
from spacegame.models.blueprints.refineryblueprint import BPRefinery
from spacegame.models.blueprints.fabricatorblueprint import BPFabricator
from spacegame.models.blueprints.escortfrigateblueprint import BPEscortFrigate
from spacegame.ui.fleet_management_ui import draw_tier_icon_image
from spacegame.core.fabrication import get_fabrication_manager
from spacegame.screens.fabrication_bpdetails_screen import fabrication_bpdetails_screen
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.fabrication_ui import (
    generate_slot_rects,
    draw_index_square,
    draw_slot_progress,
)


def fabrication_bpselect_screen(main_player, player_fleet, selected_fabricator_index=None, station_slot=False):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 22)
    dmg_font = pygame.font.Font(None, 22)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "FABRICATION"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Back arrow (left)
    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, TOP_BAR_HEIGHT // 1.3)

    # Close "X" (right)
    close_surf = close_font.render("X", True, (255, 160, 40))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(16, 16)

    # ---------- TABS ----------
    tab_labels = ["STORAGE", "BRIDGE", "FABRICATION", "REFINING", "INTERNAL MODULES"]
    icon_filenames = ["Nav_Icon_Inventory.png", "Nav_Icon_Bridge.png", "Nav_Icon_Fabricator.png", "Nav_Icon_Refinery.png", "Nav_Icon_InternalModules.png"]
    selected_tab = 2  # FABRICATION selected

    # Use central nav helper to compute tab entries and layout
    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # ---------- FABRICATOR MODULE SLOTS (01 / 02 / ...) ----------
    manager = get_fabrication_manager(main_player)
    fabricator_modules = manager.get_modules() or []
    slot_count = max(1, len(fabricator_modules))

    # Determine selected index: prefer passed value, otherwise use manager persisted index
    if selected_fabricator_index is None:
        selected_fabricator_index = manager.get_selected_index()
    else:
        try:
            selected_fabricator_index = max(0, min(int(selected_fabricator_index), len(fabricator_modules) - 1))
        except Exception:
            selected_fabricator_index = manager.get_selected_index()

    # station slot initial selection state
    station_slot_selected = bool(station_slot)

    # Geometry for the left card and index column (01 / 02 / ...)
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
    content_top = nav_bottom_y + 24

    LEFT_SHIFT = 20
    card_x = 40 - LEFT_SHIFT
    card_y = content_top
    card_w = int(width * 0.38)
    card_h = int(height * 0.64)
    card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

    idx_size = 96
    idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_size, idx_size)
    IDX_V_SPACING = idx_size + 24
    idx_rects = generate_slot_rects(idx_rect_base, slot_count, IDX_V_SPACING)
    # station-only SY slot rect. When opened from SY we place it in the first slot
    # position so there's no empty gap; otherwise position it under module slots.
    if station_slot and idx_rects:
        sy_rect = idx_rects[0].copy()
    else:
        sy_rect = pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING * len(idx_rects), idx_size, idx_size)

    # Layout / card constants reused from inventory screen style
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    # Scroll state (smooth) copied from inventory
    offset_y = 0.0
    offset_y_raw = 0.0
    SCROLL_STEP = 40
    SCROLL_SMOOTH = 0.25

    # Build blueprint categories. If opened from the station-only SY slot, show
    # only large-ship blueprints (Escort Frigate appears first).
    if station_slot:
        categories = [
            ("SHIPS", [BPEscortFrigate()]),
        ]
    else:
        # Default: ships including interceptors, collectors and bombers
        categories = [
            ("SHIPS", [BPInterceptor(), BPPlasmaBomber(), BPResourceCollector(), BPRefinery(), BPFabricator()]),
        ]

    running = True
    while running:
        # Recompute disabled tabs each frame to stay in sync with ModulesManager
        disabled_labels = set()
        if not modules_manager.get_fabricators():
            disabled_labels.add("FABRICATION")
        if not modules_manager.get_refineries():
            disabled_labels.add("REFINING")
        # Determine if player is currently at a station (hide SY when not at a station)
        try:
            loc_area = getattr(main_player, 'location_area', '')
            is_at_station = isinstance(loc_area, str) and ('station' in loc_area.lower())
        except Exception:
            is_at_station = False
        station_visible = bool(station_slot and is_at_station)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return manager.get_selected_index()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return manager.get_selected_index()

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        label = entry["label"]
                        # ignore clicks on disabled tabs
                        if label in disabled_labels:
                            break
                        # Open Storage (Inventory) when STORAGE tab clicked
                        if label == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen

                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to FABRICATION tab after closing inventory
                            selected_tab = 2
                        elif label == "INTERNAL MODULES":
                            from spacegame.screens.internal_modules_screen import internal_modules_screen

                            res = internal_modules_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            if res == "to_internal":
                                return "to_internal"
                            # after closing, go back to FABRICATION tab highlight
                            selected_tab = 2
                        elif label == "REFINING":
                            from spacegame.screens.refining_main_screen import refining_main_screen

                            res = refining_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # after closing, return focus back to FABRICATION tab
                            selected_tab = 2
                        else:
                            selected_tab = idx
                        break

                # Fabricator slot buttons (01 / 02 / ...)
                if not station_visible:
                    for i, rect in enumerate(idx_rects):
                        if rect.collidepoint(mx, my):
                            selected_fabricator_index = i
                            station_slot_selected = False
                            manager.set_selected_index(i)
                            break

                # SY station-only slot (only visible/selectable if this screen was opened from SY and player is at a station)
                if station_visible and sy_rect.collidepoint(mx, my):
                    station_slot_selected = True
                    # keep manager index unchanged for SY selection
                    continue

                # Blueprint card clicks → open DETAILS SCREEN
                for i, rect in enumerate(card_rects):
                    if i >= len(blueprints):
                        continue

                    draw_rect = rect.move(0, offset_y)  # apply scroll offset

                    if draw_rect.collidepoint(mx, my):
                        bp = blueprints[i]

                        # Call the DETAILS screen
                        res = fabrication_bpdetails_screen(
                            main_player,
                            player_fleet,
                            selected_fabricator_index,
                            bp,
                            station_slot=station_slot,
                        )

                        # Sync return value
                        if res == "to_game":
                            return "to_game"
                        elif isinstance(res, int):
                            selected_fabricator_index = res

                        break


            # Mouse wheel support (pygame 2)
            if event.type == pygame.MOUSEWHEEL:
                offset_y_raw += event.y * SCROLL_STEP

        # ---------- DRAW ----------
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
            screen.fill(UI_BG_COLOR)

        # Nav band coordinates
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

        # Brighter strip behind all nav text/buttons
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        # Lines above and below the nav/tab area
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # Title (on top of nav background)
        screen.blit(title_surf, title_rect)

        # Back arrow (on top of nav background) - use image
        back_arrow_img = get_back_arrow_image()
        if back_arrow_img:
            arrow_size = 32
            arrow_scaled = pygame.transform.smoothscale(back_arrow_img, (arrow_size - 4, arrow_size - 4))
            arrow_draw_rect = arrow_scaled.get_rect(center=back_arrow_rect.center)
            screen.blit(arrow_scaled, arrow_draw_rect)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (draw using shared nav helper)
        nav_top_y, nav_bottom_y = draw_tabs(screen, tab_entries, selected_tab, tabs_y, width, tab_font, disabled_labels=disabled_labels)

        # ---------- MAIN CONTENT (fabrication visual) ----------
        content_top = nav_bottom_y + 24

        # Left detail: index squares (01, 02, ...) with corner-only decoration + progress bar.

        # Draw slot squares: either module slots OR the SY station slot depending on how this screen was opened.
        if not station_visible:
            for i, r in enumerate(idx_rects, start=1):
                draw_index_square(
                    screen,
                    r,
                    f"{i:02d}",
                    (i - 1) == selected_fabricator_index and not station_slot_selected,
                    UI_TAB_UNDERLINE_COLOR,
                    UI_TAB_TEXT_SELECTED,
                )
        else:
            # Only draw the station-only SY slot when the screen was opened from SY
            draw_index_square(
                screen,
                sy_rect,
                "SY",
                station_slot_selected,
                UI_TAB_UNDERLINE_COLOR,
                UI_TAB_TEXT_SELECTED,
            )

        # Progress bar inside ALL squares
        fabrication_progress = 0.0  # 0 = idle, >0 once fabrication has started
        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X

        # Draw progress bars for module slots when visible; when in station mode draw a
        # progress bar for the SY slot (station fabrication has no manager timer so show 0).
        if not station_visible:
            for i, r in enumerate(idx_rects):
                status = manager.get_status(i)
                fabrication_progress = float(status.get("progress", 0.0))
                draw_slot_progress(screen, r, fabrication_progress, pb_margin=pb_margin, progress_color=PROGRESS_COLOR)
        else:
            # show an empty/placeholder progress bar for SY so visuals match other slots
            draw_slot_progress(screen, sy_rect, 0.0, pb_margin=pb_margin, progress_color=PROGRESS_COLOR)


        # ---------- Right-hand area: categories + blueprint cards (inventory style)
        # We'll render the first category (SHIPS) for now.
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # Title for the category
        cat_title_font = pygame.font.Font(None, 32)
        cat_title = cat_title_font.render(categories[0][0], True, UI_SECTION_TEXT_COLOR)
        cat_title_rect = cat_title.get_rect()
        cat_title_rect.topleft = (details_x, details_y)
        screen.blit(cat_title, cat_title_rect)

        # Layout for cards: start below title, aligned to the right of the "01" rect
        cards_top_y = cat_title_rect.bottom + 18

        def layout_rects(num_items, top_y, left_start):
            rects = []
            for i in range(num_items):
                row = i // COLS
                col = i % COLS
                x = left_start + col * (BOX_W + MARGIN_X)
                y = top_y + row * (BOX_H + MARGIN_Y)
                rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
            return rects

        # Build blueprint list for display
        blueprints = categories[0][1]

        # displays the cards
        if len(blueprints) == 0:
            display_count = COLS
        else:
            remainder = len(blueprints) % COLS
            if remainder == 0:
                display_count = len(blueprints)
            else:
                display_count = len(blueprints) + (COLS - remainder)

        left_start = details_x
        card_rects = layout_rects(display_count, cards_top_y, left_start)

        # Scroll bounds (same logic as inventory)
        scroll_area_top = nav_bottom_y + 4
        content_top_unscrolled = cards_top_y
        if card_rects:
            content_bottom = card_rects[-1].bottom + 40
        else:
            content_bottom = content_top_unscrolled

        visible_height = SCREEN_HEIGHT - scroll_area_top
        total_content_height = content_bottom - content_top_unscrolled
        if total_content_height <= visible_height:
            bottom_limit = 0.0
        else:
            bottom_limit = scroll_area_top - total_content_height

        # Clamp & smooth scroll
        target = max(min(offset_y_raw, 0.0), bottom_limit)
        offset_y += (target - offset_y) * SCROLL_SMOOTH
        if abs(target - offset_y) < 0.5:
            offset_y = target
        offset_y_raw = target

        # Clip to scroll area
        scroll_clip_rect = pygame.Rect(0, scroll_area_top, width, height - scroll_area_top)
        screen.set_clip(scroll_clip_rect)

        # Draw cards (either blueprints or placeholders)
        for i, rect in enumerate(card_rects):
            draw_rect = rect.move(0, offset_y)
            # If we have a blueprint for this slot, draw it; otherwise placeholder
            if i < len(blueprints):
                bp = blueprints[i]
                # card background + border
                pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
                pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

                # tier icon
                tier_value = getattr(bp, "tier", 0)
                draw_tier_icon_image(screen, draw_rect, tier_value)

                img = pygame.image.load(PREVIEWS_DIR + "/" + bp.preview_filename)
                img = pygame.transform.smoothscale(img, (48, 48))
                img_rect = img.get_rect(
                    center=(draw_rect.x + 40, draw_rect.y + draw_rect.height // 2)
                )
                screen.blit(img, img_rect.topleft)

                # name/title: prefer bp.title (can contain '\n'), fallback to bp.name
                try:
                    title_text = getattr(bp, 'title', None) or getattr(bp, 'name', '')
                    if title_text is None:
                        title_text = ''
                    lines = str(title_text).split('\n')
                except Exception:
                    lines = [getattr(bp, 'name', '')]

                # Render up to two lines, vertically spaced similar to previous layout
                y_offs = 20
                for j, ln in enumerate(lines[:2]):
                    try:
                        line_surf = name_font.render(ln, True, (230, 230, 255))
                        screen.blit(line_surf, (draw_rect.x + 110, draw_rect.y + y_offs + j * 20))
                    except Exception:
                        pass

                # amount
                qty = bp.quantity
                if qty is None or (isinstance(qty, float) and math.isinf(qty)):
                    qty_text = "INF"
                else:
                    qty_text = f"{int(qty):,}"
                qty_surf = dmg_font.render(qty_text, True, (108, 198, 219))
                screen.blit(qty_surf, (draw_rect.x + 60, draw_rect.y + 50))
            else:
                # placeholder card
                pygame.draw.rect(screen, (20, 35, 60), draw_rect, border_radius=0)
                pygame.draw.rect(screen, (60, 100, 150), draw_rect, 1, border_radius=0)

        # reset clip
        screen.set_clip(None)

        pygame.display.flip()