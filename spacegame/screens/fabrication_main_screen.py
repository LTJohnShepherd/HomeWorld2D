import sys
import pygame
from spacegame.config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    UI_BG_COLOR, 
    UI_TAB_HEIGHT, 
    UI_SECTION_TEXT_COLOR,
    UI_TITLE_COLOR,
    UI_TAB_UNDERLINE_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR
    )

from spacegame.models.modules.fabricatormodule import FabricatorModule
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.core.fabrication import get_fabrication_manager
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.fabrication_ui import (
    generate_slot_rects,
    draw_index_square,
    draw_slot_progress,
)
from spacegame.ui.fabrication_ui import make_card_rect, compute_idx_rect_base
from spacegame.ui.ui import draw_plus_circle, drawCornerFrame, UI_BG_IMG


def fabrication_main_screen(main_player, player_fleet):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    section_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)

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

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # ---------- FABRICATOR MODULE SLOTS (01 / 02 / ...) ----------
    manager = get_fabrication_manager(main_player)
    # `fabricator_modules` and `selected_fabricator_index` are computed
    # inside the main loop so the UI updates immediately when modules
    # are installed/removed while this screen is open.

    # Geometry for the left card and index column (01 / 02 / ...)
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
    content_top = nav_bottom_y + 24

    LEFT_SHIFT = 20
    card_rect = make_card_rect(width, height, content_top, left_shift=LEFT_SHIFT)

    idx_size = 96
    idx_rect_base = compute_idx_rect_base(card_rect, idx_size=idx_size)
    IDX_V_SPACING = idx_size + 24
    # Initialize fabricator_modules to a safe default so earlier geometry
    # calculations won't fail before the main loop recomputes them.
    try:
        fabricator_modules = manager.get_modules() or []
    except Exception:
        fabricator_modules = []

    # one rect per equipped fabricator: 01 stays as-is, 02/03/... stacked below it
    idx_rects_modules: list[pygame.Rect] = generate_slot_rects(idx_rect_base, len(fabricator_modules), IDX_V_SPACING)
    # station-only SY slot rect (positioned below module slots)
    sy_rect = pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING * len(idx_rects_modules), idx_size, idx_size)

    # ----- BIG CENTER RECT (AROUND THE PLUS-CIRCLE) -----
    plus_radius = 120
    preview_center = (width // 2, height // 2)
    big_rect_pad = 100
    big_rect = pygame.Rect(
        preview_center[0] - plus_radius - big_rect_pad,
        preview_center[1] - plus_radius - big_rect_pad,
        (plus_radius + big_rect_pad) * 2,
        (plus_radius + big_rect_pad) * 2
    )

    # Selection state for the station-only SY slot
    station_slot_selected = False

    running = True
    while running:
        # Determine whether player is currently at a station (simple name heuristic).
        # This allows the UI to hide the SY slot when the player is not at a station.
        try:
            loc_area = getattr(main_player, 'location_area', '')
            is_at_station = isinstance(loc_area, str) and ('station' in loc_area.lower())
        except Exception:
            is_at_station = False

        # Re-evaluate current fabricator modules and selection each frame so
        # that installations made from other screens (Internal/Module selection)
        # are immediately reflected without needing to re-open the screen.
        try:
            fabricator_modules = manager.get_modules() or []
        except Exception:
            fabricator_modules = []
        try:
            selected_fabricator_index = manager.get_selected_index()
        except Exception:
            selected_fabricator_index = 0

        # one rect per equipped fabricator: 01 stays as-is, 02/03/... stacked below it
        idx_rects_modules: list[pygame.Rect] = generate_slot_rects(idx_rect_base, len(fabricator_modules), IDX_V_SPACING)
        # station-only SY slot rect (positioned below module slots)
        sy_rect = pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING * len(idx_rects_modules), idx_size, idx_size)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return

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
                            selected_tab = 3
                        else:
                            selected_tab = idx
                        break

                # Fabricator slot buttons (01 / 02 / ...)
                for i, rect in enumerate(idx_rects_modules):
                    if rect.collidepoint(mx, my):
                        selected_fabricator_index = i
                        station_slot_selected = False
                        manager.set_selected_index(i)
                        break

                # SY station-only slot: only selectable when player is at a station
                if is_at_station and sy_rect.collidepoint(mx, my):
                    station_slot_selected = True
                    # keep manager selection unchanged; just update UI selection
                    continue

                # BIG CENTER RECT -> OPEN BLUEPRINT SELECT
                if big_rect.collidepoint(mx, my):
                    from spacegame.screens.fabrication_bpselect_screen import fabrication_bpselect_screen
                    res = fabrication_bpselect_screen(main_player, player_fleet, selected_fabricator_index, station_slot=station_slot_selected)
                    if res == "to_game":
                        return "to_game"
                    elif isinstance(res, int):
                        selected_fabricator_index = res
                        manager.set_selected_index(res)

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
        content_top = nav_bottom_y + 24  # same as used when we built card_rect

        # Left detail: index squares (01, 02, ...) with corner-only decoration + progress bar,
        # and transparent details to the right (no border/background).

        # draw all fabricator module slots (01 / 02 / ...)
        for i, rect in enumerate(idx_rects_modules, start=1):
            draw_index_square(
                screen,
                rect,
                f"{i:02d}",
                (i - 1) == selected_fabricator_index and not station_slot_selected,
                UI_TAB_UNDERLINE_COLOR,
                UI_TAB_TEXT_SELECTED,
            )

        # draw the station-only SY slot below modules only if player is at a station
        if is_at_station:
            draw_index_square(
                screen,
                sy_rect,
                "SY",
                station_slot_selected,
                UI_TAB_UNDERLINE_COLOR,
                UI_TAB_TEXT_SELECTED,
            )

        # progress bar inside ALL slot squares (selected or not)
        fabrication_progress = 0.0  # 0 = idle, >0 once fabrication has started
        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X

        for i, rect in enumerate(idx_rects_modules):
            # Always draw slot progress background; manager progress controls fill.
            status = manager.get_status(i)
            fabrication_progress = float(status.get("progress", 0.0))
            draw_slot_progress(screen, rect, fabrication_progress, pb_margin=pb_margin, progress_color=PROGRESS_COLOR)

        # Draw a placeholder progress bar for SY when at a station so visuals match other slots
        if is_at_station:
            draw_slot_progress(screen, sy_rect, 0.0, pb_margin=pb_margin, progress_color=PROGRESS_COLOR)



        # Details to the right of the FIRST 01 square (fixed position)
        if idx_rects_modules:
            base_idx_rect = idx_rects_modules[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        title_font = pygame.font.Font(None, 36)
        module_title = title_font.render("FABRICATOR", True, UI_SECTION_TEXT_COLOR)
        module_title_rect = module_title.get_rect()
        module_title_rect.topleft = (details_x, details_y)
        screen.blit(module_title, module_title_rect)

        # description lines (to the right of the square)
        desc_font = pygame.font.Font(None, 20)
        desc_lines = [
            "A standard fabricator module, used for",
            "on-ship fabrication for weapons and",
            "strike craft.",
        ]
        dy = module_title_rect.bottom + 8
        for line in desc_lines:
            s = desc_font.render(line, True, (180, 200, 220))
            screen.blit(s, (details_x, dy))
            dy += s.get_height() + 2

        # Module stats placed under description — render with connecting underline
        stat_label_font = pygame.font.Font(None, 20)
        stat_value_font = pygame.font.Font(None, 20)
        stat_x = details_x
        stat_y = dy + 12

        # Statistics for the currently selected fabricator module (slot 01 / 02 / ...)
        if 0 <= selected_fabricator_index < len(fabricator_modules):
            fabricator_module = fabricator_modules[selected_fabricator_index] if selected_fabricator_index < len(fabricator_modules) else None
        else:
            fabricator_module = FabricatorModule()

        stat_rows = [
            ("Module Size:", str(fabricator_module.module_size)),
            ("Base Fabrication Time:", str(fabricator_module.base_fabrication_time)),
        ]


        for label_text, value_text in stat_rows:
            lbl = stat_label_font.render(label_text, True, UI_SECTION_TEXT_COLOR)
            val = stat_value_font.render(value_text, True, (200, 230, 200))

            # draw label and value
            screen.blit(lbl, (stat_x, stat_y))
            val_rect = val.get_rect()
            # right-align the value to the card's right padding (match squad_detail)
            val_rect.topright = (card_rect.right - 110, stat_y)
            screen.blit(val, val_rect.topleft)

            # draw a thin line from under the label area to under the value (like squad_detail)
            line_y = stat_y + lbl.get_height() + 4
            line_left = stat_x
            line_right = val_rect.right
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (line_left, line_y), (line_right, line_y), 1)

            stat_y += lbl.get_height() + 12

        # Officer assign box (use style from squad_detail) placed below stats
        officer_box_h = 70
        officer_box_w = 240
        CARD_BG = (12, 26, 50)
        officer_box_rect = pygame.Rect(details_x, stat_y + 36, officer_box_w, officer_box_h)
        pygame.draw.rect(screen, CARD_BG, officer_box_rect)
        pygame.draw.rect(screen, UI_TITLE_COLOR, officer_box_rect, 2)

        # plus-circle inside officer box (left side)
        ocx = officer_box_rect.left + 42
        ocy = officer_box_rect.centery
        inner_radius = int(officer_box_h / 2.8)
        draw_plus_circle(screen, (ocx, ocy), inner_radius, UI_TITLE_COLOR, plus_size=14, circle_thickness=2, plus_thickness=2)

        # Two-line label inside the same square (centered vertically, left-aligned next to plus)
        line1 = stat_label_font.render("ASSIGN", True, UI_SECTION_TEXT_COLOR)
        line2 = stat_label_font.render("OFFICER", True, UI_SECTION_TEXT_COLOR)
        text_x = ocx + inner_radius + 12
        total_text_h = line1.get_height() + line2.get_height() + 4
        start_y = officer_box_rect.centery - total_text_h // 2
        screen.blit(line1, (text_x, start_y))
        screen.blit(line2, (text_x, start_y + line1.get_height() + 4))

        # Center big plus-circle (production slot) — centralized to middle of screen
        plus_radius = 120
        preview_center = (width // 2, height // 2)
        draw_plus_circle(screen, preview_center, plus_radius, (200, 220, 235), plus_size=36, circle_thickness=3, plus_thickness=4)

        # Corner-only rect around big circle (like the 01 square corners)
        big_corner_len = 28
        big_corner_thick = 4
        corner_color = UI_TAB_TEXT_SELECTED
        drawCornerFrame(screen, big_rect, corner_color, corner_len=big_corner_len, corner_thick=big_corner_thick)

        # Bottom green button (centered)
        btn_w = 380
        btn_h = 36
        btn_x = width // 2 - btn_w // 2
        btn_y = height - 100
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        BTN_LIGHT_GREEN = (96, 255, 144)
        pygame.draw.rect(screen, BTN_LIGHT_GREEN, btn_rect, width=2, border_radius=0)
        btn_label = section_font.render("ADD BLUEPRINT FOR PRODUCTION", True, BTN_LIGHT_GREEN)
        btn_label_rect = btn_label.get_rect(center=btn_rect.center)
        screen.blit(btn_label, btn_label_rect)

        pygame.display.flip()