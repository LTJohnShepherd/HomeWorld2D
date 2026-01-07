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
    UI_NAV_LINE_COLOR,
    UI_ICON_BLUE,
    PREVIEWS_DIR,
)
from spacegame.core.refining import get_refinery_manager
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.fabrication_ui import (
    generate_slot_rects,
    draw_index_square,
    draw_slot_progress,
    make_card_rect,
    compute_idx_rect_base,
)
from spacegame.ui.ui import draw_plus_circle, drawCornerFrame
from spacegame.ui.fleet_management_ui import draw_tier_icon_image
from spacegame.models.ores.orem import RUOreM
from spacegame.models.ores.orea import RUOreA
from spacegame.models.ores.oreb import RUOreB
from spacegame.models.ores.orec import RUOreC


def refining_oredetails_screen(main_player, player_fleet, selected_refinery_index, ore_letter):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 26)   # ore & REQUIREMENTS
    desc_font = pygame.font.Font(None, 20)   # data
    stat_font = pygame.font.Font(None, 20)   # ore
    btn_font = pygame.font.Font(None, 28)    # REFINE
    meta_font = pygame.font.Font(None, 20)   # DETAILS / REFINEMENT DETAILS

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar
    title_text = "REFINING"
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
    selected_tab = 3  # REFINING selected

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # ---------- REFINERY MODULE SLOTS (01 / 02 / ...) ----------
    manager = get_refinery_manager(main_player)
    refinery_modules = manager.get_modules() or []
    selected_refinery_index = manager.get_selected_index()  # which refinery slot is currently selected

    # Geometry for the left card and index column (01 / 02 / ...)
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
    content_top = nav_bottom_y + 24

    LEFT_SHIFT = 20
    card_rect = make_card_rect(width, height, content_top, left_shift=LEFT_SHIFT)

    idx_size = 96
    idx_rect_base = compute_idx_rect_base(card_rect, idx_size=idx_size)
    IDX_V_SPACING = idx_size + 24
    # one rect per equipped refinery: 01 stays as-is, 02/03/... stacked below it
    slot_count = max(1, len(refinery_modules))
    idx_rects: list[pygame.Rect] = generate_slot_rects(idx_rect_base, slot_count, IDX_V_SPACING)

    # ----- BIG CENTER RECT -----
    plus_radius = 120
    preview_center = (width // 2, height // 2)
    big_rect_pad = 100
    big_rect = pygame.Rect(
        preview_center[0] - plus_radius - big_rect_pad,
        preview_center[1] - plus_radius - big_rect_pad,
        (plus_radius + big_rect_pad) * 2,
        (plus_radius + big_rect_pad) * 2
    )

    # ---------- REQUIREMENTS PANEL (RIGHT) ----------
    right_panel_w = 340
    right_rect = pygame.Rect(
        width - right_panel_w - 40,
        card_rect.top,
        right_panel_w,
        140,
    )

    # ---------- REFINE BUTTON (BIG GREEN) ----------
    refine_btn_h = 64
    refine_btn_rect = pygame.Rect(
        right_rect.left,
        height - refine_btn_h - 40,
        right_panel_w,
        refine_btn_h,
    )

    # "SPEED UP" button (used only while refining)
    speed_btn_h = 64
    speed_btn_rect = pygame.Rect(
        right_rect.left,
        right_rect.bottom + 40,
        right_panel_w,
        speed_btn_h,
    )

    # Map ore letter to ore class and get ore object
    ore_classes = {
        'M': RUOreM,
        'A': RUOreA,
        'B': RUOreB,
        'C': RUOreC,
    }

    ore_class = ore_classes.get(ore_letter, RUOreM)
    inv_mgr = getattr(main_player, 'inventory_manager', None)
    # initial amount (will be refreshed each frame)
    available_ore = int(inv_mgr.get_amount(ore_letter)) if inv_mgr is not None else 0
    ore = ore_class(quantity=available_ore)

    ore_preview_img = None
    try:
        from spacegame.ui.ui import OREM_PREVIEW_IMG
        ore_preview_img = OREM_PREVIEW_IMG
    except Exception:
        pass

    # mapping from ore letter to refined preview (show refined ingot in center)
    refined_preview_map = {
        'A': 'RUIngotAT1.png',
        'B': 'RUIngotBT1.png',
        'C': 'RUIngotCT1.png',
        'M': 'RUIngotAT1.png',
    }

    running = True
    while running:
        # Recompute disabled tabs each frame to stay in sync with ModulesManager
        disabled_labels = set()
        if not modules_manager.get_fabricators():
            disabled_labels.add("FABRICATION")
        if not modules_manager.get_refineries():
            disabled_labels.add("REFINING")
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
                            # return focus back to REFINING tab after closing inventory
                            selected_tab = 3
                        elif label == "FABRICATION":
                            from spacegame.screens.fabrication_main_screen import fabrication_main_screen
                            res = fabrication_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to REFINING tab after closing fabrication
                            selected_tab = 3
                        elif label == "INTERNAL MODULES":
                            from spacegame.screens.internal_modules_screen import internal_modules_screen
                            res = internal_modules_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            if res == "to_internal":
                                return "to_internal"
                            # after closing, go back to REFINING tab highlight
                            selected_tab = 3
                        else:
                            selected_tab = idx
                        break
                
                # Refinery slot buttons (01 / 02 / ...)
                for i, rect in enumerate(idx_rects):
                    if rect.collidepoint(mx, my):
                        selected_refinery_index = i
                        manager.set_selected_index(i)
                        break

                # ----- REFINE / SPEED UP / CANCEL -----
                refinery_module = manager.get_module(selected_refinery_index)
                status = manager.get_status(selected_refinery_index)
                total_ms = int(status.get("total_ms", 0))
                start_ticks = int(status.get("start_ticks", 0))
                is_refining = bool(status.get("is_refining", False))

                # CANCEL (bottom red button while refining)
                if is_refining and refine_btn_rect.collidepoint(mx, my):
                    manager.cancel_refinement(selected_refinery_index)
                    continue

                # SPEED UP (grey button)
                if is_refining and speed_btn_rect.collidepoint(mx, my):
                    manager.speed_up(selected_refinery_index)
                    continue

                # REFINE (start refinement)
                # recompute availability to avoid stale values during rapid clicks
                available_ore = int(inv_mgr.get_amount(ore_letter)) if inv_mgr is not None else 0
                required_input = 200
                insufficient_resources = available_ore < required_input
                if (not is_refining) and refinery_module is not None and refine_btn_rect.collidepoint(mx, my):
                    if not insufficient_resources:
                        manager.start_refinement(selected_refinery_index, ore_letter, 100, main_player)
                    # if insufficient, clicking does nothing (visual banner is shown below)
                    continue


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

        # ---------- MAIN CONTENT (refining visual) ----------
        content_top = nav_bottom_y + 24

        # draw all refinery slots (01 / 02 / ...)
        # use the horizontal-line style for refinery indexes (top+bottom lines)
        for i, rect in enumerate(idx_rects, start=1):
            try:
                from spacegame.ui.fabrication_ui import draw_index_lines

                draw_index_lines(
                    screen,
                    rect,
                    f"{i:02d}",
                    (i - 1) == selected_refinery_index,
                    UI_TAB_UNDERLINE_COLOR,
                    UI_TAB_TEXT_SELECTED,
                )
            except Exception:
                # fallback to corner-style if helper is unavailable
                draw_index_square(
                    screen,
                    rect,
                    f"{i:02d}",
                    (i - 1) == selected_refinery_index,
                    UI_TAB_UNDERLINE_COLOR,
                    UI_TAB_TEXT_SELECTED,
                )

        # ----- shared refinement timer/progress (per refinery module) -----
        refinery_module = refinery_modules[selected_refinery_index]
        # Compute true refinement time in seconds using the module's
        # `standard_refinement_time_s` (seconds for one conversion of 200->100)
        # multiplied by any module factor and scaled by ore tier.
        module_standard_s = float(getattr(refinery_module, 'standard_refinement_time_s', 75.0))
        module_factor = float(getattr(refinery_module, "base_refinement_time", 1.0))
        ore_tier = int(getattr(ore, 'tier', 1) or 1)
        base_time_s = int(module_standard_s * module_factor * ore_tier)

        # Use manager API to retrieve authoritative refinement status for this slot
        status = manager.get_status(selected_refinery_index)
        total_ms = int(status.get("total_ms", 0))
        start_ticks = int(status.get("start_ticks", 0))
        refinement_progress = float(status.get("progress", 0.0))
        # If the slot is not currently refining, prefer to display the
        # computed ore time (ore * module factor) rather than
        # any module-default value (which may be the module factor like 1).
        if not bool(status.get("is_refining", False)):
            remaining_s = int(base_time_s)
        else:
            remaining_s = int(status.get("remaining_s", base_time_s))

        # Keep module fields in sync for UI code
        try:
            refinery_module.refinement_progress = refinement_progress
            refinery_module.refinement_remaining_s = remaining_s
        except Exception:
            pass

        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X


        for i, rect in enumerate(idx_rects):
            # Always draw the progress bar background; fill when manager reports progress.
            status = manager.get_status(i)
            progress = float(status.get("progress", 0.0))
            draw_slot_progress(screen, rect, progress, pb_margin=pb_margin, progress_color=PROGRESS_COLOR)



        # Details to the right of the FIRST 01 square (fixed position)
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # small row: "DETAILS" on the left, tier on the right
        details_label = meta_font.render("DETAILS", True, (160, 180, 210))
        screen.blit(details_label, (details_x, details_y))

        tier_text = f"TIER {ore.tier}"
        tier_surf = meta_font.render(tier_text, True, (160, 180, 210))
        tier_rect = tier_surf.get_rect()
        tier_rect.topright = (card_rect.right - 110, details_y)
        screen.blit(tier_surf, tier_rect.topleft)

        # now place the ore name a bit lower, under the DETAILS row
        title_font = pygame.font.Font(None, 26)

        # title from ore
        title_text = getattr(ore, "name", "ORE")

        title_lines = str(title_text).split("\n")
        module_title_rect = None
        ty = details_y + details_label.get_height() + 6
        for i, line in enumerate(title_lines[:2]):
            module_title = title_font.render(line, True, UI_SECTION_TEXT_COLOR)
            r = module_title.get_rect()
            r.topleft = (details_x, ty + i * (title_font.get_height() + 2))
            screen.blit(module_title, r.topleft)
            module_title_rect = r

        if module_title_rect is None:
            module_title_rect = pygame.Rect(details_x, details_y, 0, title_font.get_height())

        # description lines
        desc_font = pygame.font.Font(None, 20)
        desc_text = f"Refining {ore.name} into refined materials."

        desc_lines = []
        words = desc_text.split()
        line = ""
        max_width = card_rect.right - details_x - 100
        for w in words:
            test = (line + " " + w).strip()
            if desc_font.size(test)[0] > max_width and line:
                desc_lines.append(line)
                line = w
            else:
                line = test
        if line:
            desc_lines.append(line)

        dy = module_title_rect.bottom + 8
        for line in desc_lines:
            s = desc_font.render(line, True, (180, 200, 220))
            screen.blit(s, (details_x, dy))
            dy += s.get_height() + 2

        # (Simplified) we do not show Ore Tier / Ore Quantity here per design
        stat_label_font = pygame.font.Font(None, 20)
        stat_value_font = pygame.font.Font(None, 20)
        stat_x = details_x
        stat_y = dy + 12

        # Officer assign box
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

        # Corner-only rect around big circle
        big_corner_len = 28
        big_corner_thick = 4
        corner_color = UI_TAB_TEXT_SELECTED
        bottom_offset = 80
        drawCornerFrame(screen, big_rect, corner_color, corner_len=big_corner_len, corner_thick=big_corner_thick, bottom_offset=bottom_offset)

        # --- preview in the center of the big rect ---
        img = None
        try:
            # show the REFINED preview in the big rect (ingot), not the raw ore preview
            refined_name = refined_preview_map.get(ore_letter, getattr(ore, 'preview_filename', None))
            if refined_name:
                img = pygame.image.load(PREVIEWS_DIR + "/" + refined_name).convert_alpha()

            if img is not None:
                # reduce inner margin so the preview appears larger in the big rect
                inner_margin = 20
                adjusted_bottom = big_rect.bottom - bottom_offset
                avail_height = adjusted_bottom - big_rect.top
                max_w = big_rect.width - inner_margin * 2
                max_h = avail_height - inner_margin * 2

                if max_w > 0 and max_h > 0:
                    try:
                        scale = min(max_w / img.get_width(), max_h / img.get_height(), 1.0)
                        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                        img = pygame.transform.smoothscale(img, new_size)
                    except Exception:
                        pass

                    center_x = big_rect.centerx
                    center_y = (big_rect.top + adjusted_bottom) // 2
                    img_rect = img.get_rect(center=(center_x, center_y))
                    screen.blit(img, img_rect.topleft)
        except Exception:
            pass

        # ---------- REQUIREMENTS (RIGHT) ----------
        # header
        ref_surf = meta_font.render("REQUIREMENTS", True, (160, 180, 210))
        ref_rect = ref_surf.get_rect()
        ref_rect.left = right_rect.left + 16
        ref_rect.centery = details_y
        screen.blit(ref_surf, ref_rect)

        is_refining = (total_ms > 0 and start_ticks > 0 and refinement_progress < 1.0)
        # idle vs refining UI
        # refresh available_ore each frame so UI reflects inventory changes immediately
        available_ore = int(inv_mgr.get_amount(ore_letter)) if inv_mgr is not None else 0
        insufficient_resources = available_ore < 200

        # ----- IDLE: REQUIREMENTS + TIME + REFINE / INSUFFICIENT -----
        if not is_refining:
            # ore preview image
            row_y = ref_rect.bottom + 22
            ore_size = 40
            if ore_preview_img is not None:
                try:
                    ore_surf = pygame.transform.smoothscale(ore_preview_img, (ore_size, ore_size))
                except Exception:
                    ore_surf = None
            else:
                ore_surf = None

            if ore_surf is not None:
                ore_rect = ore_surf.get_rect()
                ore_rect.left = right_rect.left + 16
                ore_rect.centery = row_y
                screen.blit(ore_surf, ore_rect)
            else:
                ore_rect = pygame.Rect(right_rect.left + 16, row_y - ore_size // 2, ore_size, ore_size)

            # ore tier icon (keep small)
            flag_w = 70
            flag_h = 24
            flag_rect = pygame.Rect(0, 0, flag_w, flag_h)
            flag_rect.left = ore_rect.right + 12
            flag_rect.centery = ore_rect.centery
            draw_tier_icon_image(screen, flag_rect, ore.tier)
            pygame.draw.rect(screen, UI_NAV_LINE_COLOR, flag_rect, width=2)

            flag_text = f"{ore_letter}"
            flag_surf = stat_font.render(flag_text, True, UI_SECTION_TEXT_COLOR)
            flag_text_rect = flag_surf.get_rect(center=flag_rect.center)
            flag_text_rect.x -= 11
            screen.blit(flag_surf, flag_text_rect)

            # AVAILABLE / REQUIRED (live)
            required_input = 200
            refined_output = 100
            avail_text = f"{available_ore} / {required_input}"
            avail_color = UI_SECTION_TEXT_COLOR if available_ore >= required_input else (220, 60, 60)
            avail_surf = stat_font.render(avail_text, True, avail_color)
            avail_rect = avail_surf.get_rect()
            avail_rect.right = right_rect.right - 20
            avail_rect.centery = ore_rect.centery
            screen.blit(avail_surf, avail_rect)

            # underline
            line_y = ore_rect.bottom + 8
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (ore_rect.left, line_y), (avail_rect.right, line_y), 1)

            # --- TIME ROW ---
            time_row_y = line_y + 26

            # clock icon
            clock_radius = 16
            clock_cx = ore_rect.left + clock_radius
            clock_cy = time_row_y
            pygame.draw.circle(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy), clock_radius, 3)
            pygame.draw.line(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy),
                             (clock_cx, clock_cy - clock_radius // 2), 2)
            pygame.draw.line(screen, UI_TAB_TEXT_SELECTED, (clock_cx, clock_cy),
                             (clock_cx + clock_radius // 2, clock_cy), 2)

            # TIME rect aligned with ore flag
            time_box_w = 56
            time_box_h = 24
            time_box_rect = pygame.Rect(0, 0, time_box_w, time_box_h)
            time_box_rect.left = flag_rect.left
            time_box_rect.centery = time_row_y
            pygame.draw.rect(screen, UI_ICON_BLUE, time_box_rect)
            time_label_surf = stat_font.render("TIME", True, UI_SECTION_TEXT_COLOR)
            time_label_rect = time_label_surf.get_rect(center=time_box_rect.center)
            screen.blit(time_label_surf, time_label_rect)

            # text: total/remaining time formatted as MM:SS (use base_time_s when idle)
            def fmt_mmss(sec: int) -> str:
                if sec is None:
                    return "0:00"
                m = sec // 60
                s = sec % 60
                return f"{m}m:{s:02d}s"

            # show total expected time when idle, otherwise remaining time
            display_sec = remaining_s if bool(status.get("is_refining", False)) else int(base_time_s)
            time_text = fmt_mmss(display_sec)
            time_surf = stat_font.render(time_text, True, UI_SECTION_TEXT_COLOR)
            time_rect = time_surf.get_rect()
            time_rect.centery = time_row_y
            time_rect.right = avail_rect.right
            screen.blit(time_surf, time_rect)

            # underline below time row
            line_y = time_box_rect.bottom + 16
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (ore_rect.left, line_y), (time_rect.right, line_y), 1)
            # CONVERSION row: draw an icon (matching TIME icon style) and a blue label box aligned with TIME
            conv_row_y = line_y + 26

            # conversion icon (circle like TIME icon, with left-right arrows)
            conv_radius = 16
            conv_cx = ore_rect.left + conv_radius
            conv_cy = conv_row_y
            pygame.draw.circle(screen, UI_TAB_TEXT_SELECTED, (conv_cx, conv_cy), conv_radius, 3)
            # draw left and right small triangles (arrows) inside the circle
            tri_w = conv_radius * 0.5
            tri_h = conv_radius * 0.4
            # left arrow
            lx = conv_cx - tri_w * 0.6
            ly = conv_cy
            left_pts = [
                (lx - tri_w / 2, ly),
                (lx + tri_w / 2, ly - tri_h / 2),
                (lx + tri_w / 2, ly + tri_h / 2),
            ]
            # right arrow
            rx = conv_cx + tri_w * 0.6
            ry = conv_cy
            right_pts = [
                (rx + tri_w / 2, ry),
                (rx - tri_w / 2, ry - tri_h / 2),
                (rx - tri_w / 2, ry + tri_h / 2),
            ]
            try:
                pygame.draw.polygon(screen, UI_TAB_TEXT_SELECTED, left_pts)
                pygame.draw.polygon(screen, UI_TAB_TEXT_SELECTED, right_pts)
            except Exception:
                pass

            # CONVERSION blue label box (aligned X with TIME box)
            conv_box_w = 110
            conv_box_h = 24
            conv_box_rect = pygame.Rect(0, 0, conv_box_w, conv_box_h)
            conv_box_rect.left = flag_rect.left
            conv_box_rect.centery = conv_row_y
            pygame.draw.rect(screen, UI_ICON_BLUE, conv_box_rect)
            conv_label = stat_font.render("CONVERSION", True, UI_SECTION_TEXT_COLOR)
            conv_label_rect = conv_label.get_rect(center=conv_box_rect.center)
            screen.blit(conv_label, conv_label_rect)

            # conversion values (available/produced)
            conv_vals = f"{required_input}/{refined_output}"
            conv_val_surf = stat_font.render(conv_vals, True, UI_SECTION_TEXT_COLOR)
            conv_val_rect = conv_val_surf.get_rect()
            conv_val_rect.right = right_rect.right - 20
            conv_val_rect.centery = conv_row_y
            screen.blit(conv_val_surf, conv_val_rect)

            # REFINE button or INSUFFICIENT banner
            WARNING_ORANGE = (255, 160, 40)
            if not insufficient_resources:
                refine_color = (60, 200, 90)
                pygame.draw.rect(screen, refine_color, refine_btn_rect)
                refine_text_surf = btn_font.render("REFINE", True, (10, 20, 10))
                refine_text_rect = refine_text_surf.get_rect(center=refine_btn_rect.center)
                screen.blit(refine_text_surf, refine_text_rect)
            else:
                outer_bg = (8, 18, 40)
                pygame.draw.rect(screen, outer_bg, refine_btn_rect)
                pygame.draw.rect(screen, WARNING_ORANGE, refine_btn_rect, 2)

                icon_rect = refine_btn_rect.copy()
                icon_rect.width = icon_rect.height
                icon_bg = (40, 22, 10)
                pygame.draw.rect(screen, icon_bg, icon_rect)
                pygame.draw.rect(screen, WARNING_ORANGE, icon_rect, 1)

                # Load and scale warning icon image
                warning_icon_path = f"{PREVIEWS_DIR}/WarningIcon_TriangleNoGlow.png"
                warning_icon = pygame.image.load(warning_icon_path)
                icon_size = int(icon_rect.width * 0.75)
                warning_icon = pygame.transform.scale(warning_icon, (icon_size, icon_size))
                warning_icon_rect = warning_icon.get_rect(center=icon_rect.center)
                screen.blit(warning_icon, warning_icon_rect)

                warn_text = "INSUFFICIENT RESOURCES"
                warn_surf = btn_font.render(warn_text, True, (255, 230, 120))
                warn_rect = warn_surf.get_rect()
                warn_rect.midleft = (icon_rect.right + 5, refine_btn_rect.centery)
                screen.blit(warn_surf, warn_rect)

        else:
            # ----- REFINING: progress bar + timers + SPEED UP + CANCEL -----

            # timer at top-left (mm:ss)
            minutes = remaining_s // 60
            seconds = remaining_s % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            time_font = pygame.font.Font(None, 42)
            time_surf = time_font.render(time_str, True, UI_SECTION_TEXT_COLOR)
            time_rect = time_surf.get_rect()
            time_rect.topleft = (right_rect.left + 10, ref_rect.bottom + 6)
            screen.blit(time_surf, time_rect)

            # percent at top-right
            pct = int(refinement_progress * 100)
            pct_text = f"{pct} %"
            pct_surf = time_font.render(pct_text, True, UI_SECTION_TEXT_COLOR)
            pct_rect = pct_surf.get_rect()
            pct_rect.topright = (right_rect.right - 10, time_rect.top)
            screen.blit(pct_surf, pct_rect)

            # long horizontal progress bar
            bar_y = time_rect.bottom + 24
            bar_h = 18
            bar_rect = pygame.Rect(
                right_rect.left + 10,
                bar_y,
                right_panel_w - 20,
                bar_h,
            )
            pygame.draw.rect(screen, (15, 45, 70), bar_rect)
            inner_w = int(bar_rect.width * refinement_progress)
            if inner_w > 0:
                inner_rect = pygame.Rect(bar_rect.left, bar_rect.top, inner_w, bar_h)
                pygame.draw.rect(screen, (0, 220, 180), inner_rect)

            # SPEED UP button
            pygame.draw.rect(screen, (40, 60, 90), speed_btn_rect)
            pygame.draw.rect(screen, UI_NAV_LINE_COLOR, speed_btn_rect, 2)
            speed_surf = btn_font.render("SPEED UP", True, UI_SECTION_TEXT_COLOR)
            speed_rect = speed_surf.get_rect(center=speed_btn_rect.center)
            screen.blit(speed_surf, speed_rect)

            # CANCEL button
            cancel_bg = (210, 40, 40)
            pygame.draw.rect(screen, cancel_bg, refine_btn_rect)
            cancel_surf = btn_font.render("CANCEL", True, UI_SECTION_TEXT_COLOR)
            cancel_rect = cancel_surf.get_rect(center=refine_btn_rect.center)
            screen.blit(cancel_surf, cancel_rect)

        pygame.display.flip()
