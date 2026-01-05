import sys
import math
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
)
from spacegame.config import PREVIEWS_DIR
from spacegame.models.ores.orea import RUOreA
from spacegame.models.ores.oreb import RUOreB
from spacegame.models.ores.orec import RUOreC
from spacegame.ui.fleet_management_ui import draw_tier_icon_image
from spacegame.core.refining import get_refinery_manager
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.fabrication_ui import (
    generate_slot_rects,
    draw_slot_progress,
)
from spacegame.ui.ui import drawCornerFrame, draw_plus_circle


def refining_main_screen(main_player, player_fleet):
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

    # Use central nav helper to compute tab entries and layout
    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")
    # ensure selected_tab isn't disabled
    if 0 <= selected_tab < len(tab_entries) and tab_entries[selected_tab]["label"] in disabled_labels:
        for i, e in enumerate(tab_entries):
            if e["label"] not in disabled_labels:
                selected_tab = i
                break

    # ---------- REFINERY MODULE SLOTS (01 / 02 / ...) ----------
    manager = get_refinery_manager(main_player)
    refinery_modules = manager.get_modules() or []
    slot_count = max(1, len(refinery_modules))

    # use manager's persisted selected index and clamp to valid range
    selected_refinery_index = manager.get_selected_index()

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

    # make slot rectangles wider and taller to add officer card below.
    # Keep `old_idx_h` as the original visual height so existing
    # elements (top line, label, icon) remain at the same coordinates.
    idx_w = 240
    old_idx_h = 160  # baseline used for existing element positions
    officer_box_h = 70
    # new height extends below by the officer card + some padding
    idx_h = old_idx_h + officer_box_h + 24
    idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_w, idx_h)
    IDX_V_SPACING = idx_h + 32
    idx_rects = generate_slot_rects(idx_rect_base, slot_count, IDX_V_SPACING)

    # Layout / card constants reused from inventory screen style
    BOX_W = 360
    BOX_H = 80
    COLS = 2
    MARGIN_X = 18
    MARGIN_Y = 18

    # Scroll state (smooth)
    offset_y = 0.0
    offset_y_raw = 0.0
    SCROLL_STEP = 40
    SCROLL_SMOOTH = 0.25

    # Build ores category from player's inventory
    running = True
    while running:
        # Precompute the right-hand card layout and mapping so event handling
        # (mouse clicks) can reference `card_rects` and `display_items`.
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # Title area height approximation
        cat_title_font = pygame.font.Font(None, 32)
        cards_top_y = details_y + 32 + 18

        def layout_rects(num_items, top_y, left_start):
            rects = []
            for i in range(num_items):
                row = i // COLS
                col = i % COLS
                x = left_start + col * (BOX_W + MARGIN_X)
                y = top_y + row * (BOX_H + MARGIN_Y)
                rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
            return rects

        # (Grouping and layout for display_items/card_rects handled below)
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

                # Ore/refined card clicks → open DETAILS screen for the
                # corresponding ore letter. We map display_items (item, ore_letter)
                # to the card_rects computed earlier.
                for i, rect in enumerate(card_rects):
                    draw_rect = rect.move(0, offset_y)  # apply scroll offset
                    if draw_rect.collidepoint(mx, my):
                        if i < len(display_items):
                            ore_letter = display_items[i][1]
                            from spacegame.screens.refining_oredetails_screen import refining_oredetails_screen

                            res = refining_oredetails_screen(
                                main_player,
                                player_fleet,
                                manager.get_selected_index(),
                                ore_letter,
                            )
                            if res == "to_game":
                                return "to_game"
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

        # ---------- MAIN CONTENT (refining visual) ----------
        content_top = nav_bottom_y + 24

        # Left detail: index squares (01, 02, ...) with corner-only decoration + progress bar.

        # Draw all slot squares (01 / 02 / ...) in the custom refinery style.
        pb_margin = 12
        PROGRESS_COLOR = (255, 160, 40)  # same orange as nav X
        roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
        index_font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 18)
        status_font = pygame.font.Font(None, 22)

        for idx, rect in enumerate(idx_rects):
            # slot visual state
            status = manager.get_status(idx)
            recipe = status.get('recipe')
            is_refining = bool(status.get('is_refining', False))
            progress = float(status.get('progress', 0.0))

            # color based on selected
            sel = (idx == selected_refinery_index)
            color = UI_TAB_UNDERLINE_COLOR if sel else UI_TAB_TEXT_SELECTED

            # top horizontal line across the rect
            top_line_y = rect.top + 10
            pygame.draw.line(screen, color, (rect.left + 2, top_line_y), (rect.right - 2, top_line_y), 3)

            # tier roman numeral on the right under the line
            module = refinery_modules[idx] if idx < len(refinery_modules) else None
            tier_val = getattr(module, 'tier', 1) if module is not None else 1
            roman = roman_map.get(tier_val, str(tier_val))
            roman_surf = small_font.render(roman, True, color)
            roman_rect = roman_surf.get_rect()
            roman_rect.top = top_line_y + 6
            roman_rect.right = rect.right - 12
            screen.blit(roman_surf, roman_rect.topleft)

            # compute a larger corner preview rect that extends leftwards
            # and drops down to just above the READY/REFINING text.
            icon_left_gap = 12
            icon_w = 161
            # icon top is below the roman numeral
            icon_top = top_line_y + 6 + roman_rect.height + 6
            # target bottom anchored to the original baseline so extending
            # the rect below doesn't move the corner preview down.
            icon_bottom_target = rect.top + old_idx_h - 44
            icon_h = max(40, int(icon_bottom_target - icon_top))
            icon_rect = pygame.Rect(rect.right - icon_w - icon_left_gap, int(icon_top), icon_w, int(icon_h))
            drawCornerFrame(screen, icon_rect, color, corner_len=10, corner_thick=2)

            # "01" label on the left aligned vertically with the corner preview top
            label = f"{idx+1:02d}"
            label_surf = index_font.render(label, True, color)
            label_rect = label_surf.get_rect()
            label_rect.left = rect.left + 12
            # align label top to icon_rect top so it starts at same height
            label_rect.top = icon_rect.top
            screen.blit(label_surf, label_rect.topleft)

            # If there's an active recipe for this slot, draw its preview inside the corner frame
            try:
                if recipe is not None:
                    preview_name = getattr(recipe, 'preview_filename', None)
                    if preview_name:
                        img = pygame.image.load(PREVIEWS_DIR + "/" + preview_name).convert_alpha()
                        # scale to fit icon rect with small padding
                        pad = 6
                        max_w = max(4, icon_rect.width - pad * 2)
                        max_h = max(4, icon_rect.height - pad * 2)
                        scale = min(max_w / img.get_width(), max_h / img.get_height(), 1.0)
                        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                        try:
                            img = pygame.transform.smoothscale(img, new_size)
                        except Exception:
                            pass
                        img_rect = img.get_rect(center=icon_rect.center)
                        screen.blit(img, img_rect.topleft)
            except Exception:
                pass

            # READY / timer text under the label towards bottom-left
            # Anchor this text to the original baseline (old_idx_h) so that
            # increasing the rect height below does not move these elements.
            if is_refining:
                # Show remaining time in MM:SS format
                remaining_s = int(status.get('remaining_s', 0))
                minutes = remaining_s // 60
                seconds = remaining_s % 60
                status_text = f"{minutes}:{seconds:02d}"
                status_color = (200, 220, 255)
            else:
                status_text = "READY"
                status_color = (220, 200, 120)
            status_surf = status_font.render(status_text, True, status_color)
            status_rect = status_surf.get_rect()
            status_rect.left = rect.left + 12
            status_rect.top = rect.top + (old_idx_h - 38)
            screen.blit(status_surf, status_rect.topleft)

            # progress bar anchored to the original baseline area as well.
            progress_anchor_rect = pygame.Rect(rect.left, rect.top, rect.width, old_idx_h)
            draw_slot_progress(screen, progress_anchor_rect, progress, pb_margin=12, progress_color=PROGRESS_COLOR)

            # --- Officer select card placed in the extended lower area ---
            try:
                CARD_BG = (12, 26, 50)
                officer_box_w = 70
                ob_left = rect.left + 8
                ob_top = rect.top + old_idx_h + 12
                officer_box_rect = pygame.Rect(ob_left, ob_top, officer_box_w, officer_box_h)
                pygame.draw.rect(screen, CARD_BG, officer_box_rect)
                pygame.draw.rect(screen, UI_TITLE_COLOR, officer_box_rect, 2)

                # plus-circle inside officer box (left side)
                ocx = officer_box_rect.left + 36
                ocy = officer_box_rect.centery
                inner_radius = int(officer_box_h / 2.8)
                draw_plus_circle(screen, (ocx, ocy), inner_radius, UI_TITLE_COLOR, plus_size=14, circle_thickness=2, plus_thickness=2)

                # One-line label
                line = small_font.render("ASSIGN OFFICER", True, UI_SECTION_TEXT_COLOR)
                text_x = ocx + inner_radius + 16
                total_text_h = line.get_height()
                start_y = officer_box_rect.centery - total_text_h // 2
                screen.blit(line, (text_x, start_y))
            except Exception:
                pass


        # ---------- Right-hand area: ores + cards (inventory style)
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # Layout for cards: start near details_y (we intentionally omit a
        # top-level "ORES" title per design; block headers will show tiers)
        cat_title_font = pygame.font.Font(None, 32)
        cards_top_y = details_y + 8

        def layout_rects(num_items, top_y, left_start):
            rects = []
            for i in range(num_items):
                row = i // COLS
                col = i % COLS
                x = left_start + col * (BOX_W + MARGIN_X)
                y = top_y + row * (BOX_H + MARGIN_Y)
                rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
            return rects


        # Build refined-materials list for display from player's inventory and
        # group by availability (available >0) and insufficient (==0).
        inv_mgr = getattr(main_player, 'inventory_manager', None)
        from spacegame.models.resources.refineda import RURefinedA
        from spacegame.models.resources.refinedb import RURefinedB
        from spacegame.models.resources.refinedc import RURefinedC

        refined_map = [
            (RURefinedA, RUOreA, 'A', 'RA'),
            (RURefinedB, RUOreB, 'B', 'RB'),
            (RURefinedC, RUOreC, 'C', 'RC'),
        ]

        available_groups = {}  # tier -> [ (refined_item_obj, ore_letter, ore_qty) ]
        insufficient_items = []  # list of (refined_item_obj, ore_letter, 0)

        for r_cls, ore_cls, ore_letter, refined_key in refined_map:
            ore_qty = int(inv_mgr.get_amount(ore_letter)) if inv_mgr is not None else 0
            # refined item instance used for preview/name (quantity shown separately)
            refined_item = r_cls(quantity=0)
            # get tier from the raw ore class
            try:
                ore_obj = ore_cls(quantity=ore_qty)
                tier = getattr(ore_obj, 'tier', 1)
            except Exception:
                tier = 1

            if ore_qty > 0:
                available_groups.setdefault(tier, []).append((refined_item, ore_letter, ore_qty))
            else:
                insufficient_items.append((refined_item, ore_letter, 0))

        # Build ordered blocks: tiers (ascending) then insufficient block
        blocks = []
        if available_groups:
            for tier in sorted(available_groups.keys()):
                blocks.append({
                    'header': f"TIER {tier}",
                    'items': available_groups.get(tier, []),
                })

        # Insufficient block always after available blocks if any, or alone
        if insufficient_items:
            blocks.append({
                'header': "INSUFFICIENT RESOURCES",
                'items': insufficient_items,
            })

        # Flatten blocks into master lists and compute rects per block
        display_items = []  # list of tuples (refined_item, ore_letter, ore_qty)
        card_rects = []
        left_start = details_x
        top_y = cards_top_y
        HEADER_SPACING = 18
        for b in blocks:
            items = b['items']
            if not items:
                continue
            # header height
            hdr_h = cat_title_font.get_height() + 8
            # compute rects for this block
            block_rects = layout_rects(len(items), top_y + hdr_h, left_start)
            # append
            for rr in block_rects:
                card_rects.append(rr)
            for it in items:
                display_items.append(it)
            # advance top_y past this block
            if block_rects:
                top_y = block_rects[-1].bottom + HEADER_SPACING
            else:
                top_y = top_y + hdr_h + HEADER_SPACING

        # displays the cards (precomputed into `card_rects` and `display_items` above)

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

        # Draw grouped blocks: tier headers and their cards, then an
        # "INSUFFICIENT RESOURCES" block if present
        top_y = cards_top_y
        left_start = details_x
        HEADER_SPACING = 18
        for b in blocks:
            items = b['items']
            if not items:
                continue

            # draw header
            hdr = b['header']
            hdr_surf = cat_title_font.render(hdr, True, UI_SECTION_TEXT_COLOR)
            hdr_rect = hdr_surf.get_rect()
            hdr_rect.topleft = (details_x, top_y)
            screen.blit(hdr_surf, hdr_rect.topleft)

            hdr_h = hdr_rect.height + 8
            # compute rects for this block
            block_rects = layout_rects(len(items), top_y + hdr_h, left_start)

            for j, rr in enumerate(block_rects):
                draw_rect = rr.move(0, offset_y)
                refined_item, ore_letter, ore_qty = items[j]

                # card background + border
                pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
                pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

                # tier icon (use the refined_item's tier if available)
                tier_value = getattr(refined_item, "tier", 0)
                draw_tier_icon_image(screen, draw_rect, tier_value)

                try:
                    img = pygame.image.load(PREVIEWS_DIR + "/" + refined_item.preview_filename)
                    img = pygame.transform.smoothscale(img, (48, 48))
                    img_rect = img.get_rect(center=(draw_rect.x + 40, draw_rect.y + draw_rect.height // 2))
                    screen.blit(img, img_rect.topleft)
                except Exception:
                    pass

                # name/title
                try:
                    title_text = getattr(refined_item, 'name', '')
                    lines = str(title_text).split('\n')
                except Exception:
                    lines = ['']

                y_offs = 20
                for k, ln in enumerate(lines[:2]):
                    try:
                        line_surf = name_font.render(ln, True, (230, 230, 255))
                        screen.blit(line_surf, (draw_rect.x + 110, draw_rect.y + y_offs + k * 20))
                    except Exception:
                        pass

                # amount: show quantity of the RAW ore in inventory
                qty = ore_qty
                if qty is None or (isinstance(qty, float) and math.isinf(qty)):
                    qty_text = "INF"
                else:
                    qty_text = f"{int(qty):,}"
                qty_surf = dmg_font.render(qty_text, True, (108, 198, 219))
                screen.blit(qty_surf, (draw_rect.x + 60, draw_rect.y + 50))

            # advance past this block
            if block_rects:
                top_y = block_rects[-1].bottom + HEADER_SPACING
            else:
                top_y = top_y + hdr_h + HEADER_SPACING

        # reset clip
        screen.set_clip(None)

        pygame.display.flip()
