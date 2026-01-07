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
from spacegame.ui.fleet_management_ui import draw_tier_icon_image
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG


def internal_modules_screen(main_player, player_fleet):
    """Internal Modules management screen.

    Layout and navigation are intentionally very close to the Fabricator
    blueprint‑select screen so assets and behaviour stay consistent.
    """
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 22)
    small_font = pygame.font.Font(None, 20)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "INTERNAL MODULES"
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
    selected_tab = 4  # INTERNAL MODULES selected

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    try:
        

        if not modules_manager.get_fabricators():
            disabled_labels.add("FABRICATION")
        if not modules_manager.get_refineries():
            disabled_labels.add("REFINING")
    except Exception:
        pass

    if 0 <= selected_tab < len(tab_entries) and tab_entries[selected_tab]["label"] in disabled_labels:
        for i, e in enumerate(tab_entries):
            if e["label"] not in disabled_labels:
                selected_tab = i
                break

    # ---------- MODULE DATA ----------
    # Use the centralised ModulesManager as the source of truth for equipped modules
    SECTION_MODULES = modules_manager.get_internal_sections()

    # Fabrication/Refining managers read from ModulesManager dynamically; no sync required

    # Capacity limits are persisted on the player's ExpeditionShip so they
    # survive navigation between screens. Fall back to sensible defaults
    # if the attribute is missing on older ship objects.
    SECTION_CAPACITY_LIMITS = getattr(main_player, 'internal_section_capacity_limits')
    selected_section = 0  # 0 -> "01", 1 -> "02", 2 -> "03"

    # Layout constants for module cards (inventory style)
    COLS = 2
    BOX_W = int(width * 0.22)
    BOX_H = 110
    MARGIN_X = 22
    MARGIN_Y = 18

    def layout_rects(num_items: int, top_y: int, left_start: int) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        for i in range(num_items):
            row = i // COLS
            col = i % COLS
            x = left_start + col * (BOX_W + MARGIN_X)
            y = top_y + row * (BOX_H + MARGIN_Y)
            rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
        return rects

    # simple cache so we only load each preview image once
    preview_cache: dict[str, pygame.Surface] = {}

    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(60)

        # Recompute disabled tabs and sections each frame so UI stays in sync
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

        # Always read the authoritative sections from the central manager
        SECTION_MODULES = modules_manager.get_internal_sections()

        # ---------- STATIC LAYOUT THAT DEPENDS ON NAV POSITION ----------
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

        # content area begins just under the nav strip, just like fabrication screen
        content_top = nav_bottom_y + 24

        # Left detail placement copied from fabrication_main_screen 01‑square layout
        LEFT_SHIFT = 20
        card_x = 40 - LEFT_SHIFT
        card_y = content_top
        card_w = int(width * 0.38)
        card_h = int(height * 0.64)
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        # Base "01" rect — positions and size identical to fabrication screen
        idx_size = 96
        idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_size, idx_size)

        # Derived "02" and "03" rects stacked vertically under 01
        IDX_V_SPACING = idx_size + 24
        idx_rects = [
            idx_rect_base,
            pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING, idx_size, idx_size),
            pygame.Rect(idx_rect_base.left, idx_rect_base.top + 2 * IDX_V_SPACING, idx_size, idx_size),
        ]

        # Module cards appear to the right of the index column
        cards_left_start = idx_rect_base.right + 80
        cards_top_y = content_top
        current_modules = SECTION_MODULES[selected_section]
        card_rects = layout_rects(len(current_modules), cards_top_y, cards_left_start)

        # Capacity panel on the far right
        capacity_panel_w = 260
        capacity_panel_rect = pygame.Rect(width - capacity_panel_w - 40, content_top, capacity_panel_w, 140)

        # Mount module button (bottom‑right)
        mount_btn_w = 240
        mount_btn_h = 64
        mount_btn_rect = pygame.Rect(
            width - mount_btn_w - 40,
            height - mount_btn_h - 40,
            mount_btn_w,
            mount_btn_h,
        )

        # ---------- EVENT HANDLING ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # If Fabrication/Refining are disabled, signal to skip
                # back to the broader Internal screen instead of returning
                # to a now-inaccessible main screen.
                if "FABRICATION" in disabled_labels or "REFINING" in disabled_labels:
                    return "to_internal"
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    if "FABRICATION" in disabled_labels or "REFINING" in disabled_labels:
                        return "to_internal"
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
                        if label == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen

                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            selected_tab = 0
                        elif label == "FABRICATION":
                            from spacegame.screens.fabrication_main_screen import fabrication_main_screen

                            res = fabrication_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            selected_tab = 2
                        elif label == "REFINING":
                            from spacegame.screens.refining_main_screen import refining_main_screen

                            res = refining_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            selected_tab = 3
                        elif label == "INTERNAL MODULES":
                            selected_tab = 4
                        else:
                            selected_tab = idx
                        break

                # Section selector squares ("01", "02", "03")
                for i, r in enumerate(idx_rects):
                    if r.collidepoint(mx, my):
                        selected_section = i
                        break

                # Mount module button (no gameplay logic yet)
                if mount_btn_rect.collidepoint(mx, my):
                    # Open the module selection screen and allow the player to pick
                    # a module for the currently selected section. If a module is
                    # returned, append it to the SECTION_MODULES for that section.
                    from spacegame.screens.module_selection_screen import module_selection_screen

                    picked = module_selection_screen(main_player, player_fleet, selected_section, installed_sections=SECTION_MODULES)
                    if picked is None:
                        # user cancelled or closed the selection screen
                        pass
                    elif picked == "to_game":
                        return "to_game"
                    else:
                        # `module_selection_screen` returns either a module or
                        # a (module, section_index) tuple. Support both forms
                        # for backwards-compatibility.
                        target_section = selected_section
                        picked_module = picked
                        try:
                            if isinstance(picked, tuple) and len(picked) >= 2:
                                picked_module, target_section = picked[0], int(picked[1])
                        except Exception:
                            picked_module = picked

                        # If the module came from the player's inventory, try to remove
                        # it first from the unequipped modules list so it no longer
                        # appears there.
                        try:
                            inv_mgr = getattr(main_player, 'inventory_manager', None)
                            if inv_mgr is not None and hasattr(inv_mgr, 'remove_module'):
                                try:
                                    inv_mgr.remove_module(picked_module)
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # add the chosen module to the central modules manager
                        try:
                            modules_manager.install_module(target_section, picked_module)
                        except Exception:
                            pass
                        else:
                            # update local view immediately so the UI reflects changes
                            try:
                                SECTION_MODULES = modules_manager.get_internal_sections()
                                current_modules = SECTION_MODULES[selected_section]
                                card_rects = layout_rects(len(current_modules), cards_top_y, cards_left_start)
                            except Exception:
                                pass
                        # Persist compatibility attribute on the player object
                        try:
                            setattr(main_player, 'installed_internal_modules', modules_manager.get_internal_sections())
                        except Exception:
                            pass

                        # Trigger autosave via InventoryManager if available
                        try:
                            inv_mgr = getattr(main_player, 'inventory_manager', None)
                            if inv_mgr is not None and hasattr(inv_mgr, '_trigger_autosave'):
                                try:
                                    inv_mgr._trigger_autosave()
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # No manager sync required; Fabrication/Refining managers
                        # read from the central ModulesManager at runtime.

                # Click on a module card should open the module details screen.
                # The details screen will return a section index when the user
                # clicks one of its section selector buttons; treat that as a
                # navigation hint and set the selected_section accordingly.
                for idx, r in enumerate(card_rects):
                    if r.collidepoint(mx, my):
                        from spacegame.screens.module_details_screen import module_details_screen

                        # Pass the clicked module to the details screen so it can
                        # present module-specific info. If `idx` is out-of-range
                        # for `current_modules`, fall back to None.
                        selected_mod = None
                        try:
                            selected_mod = current_modules[idx]
                        except Exception:
                            selected_mod = None

                        res = module_details_screen(
                            main_player,
                            player_fleet,
                            initial_section=selected_section,
                            installed_sections=SECTION_MODULES,
                            selected_module=selected_mod,
                        )
                        if res == "to_game":
                            return "to_game"
                        try:
                            if isinstance(res, int):
                                selected_section = res
                        except Exception:
                            pass
                        break

        # ---------- CAPACITY CALCULATION FOR CURRENT SECTION ----------
        capacity_used = sum(m.capacity for m in current_modules)
        # read per-section capacity from the ship (fallback to default list)
        capacity_limits = getattr(main_player, 'internal_section_capacity_limits', SECTION_CAPACITY_LIMITS)
        # clamp selected_section index
        if selected_section < 0 or selected_section >= len(capacity_limits):
            capacity_max = SECTION_CAPACITY_LIMITS[0] if capacity_limits else 0
        else:
            capacity_max = capacity_limits[selected_section]
        clamped_used = min(capacity_used, capacity_max)
        capacity_ratio = clamped_used / float(capacity_max) if capacity_max > 0 else 0.0

        # ---------- DRAW ----------
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
            screen.fill(UI_BG_COLOR)

        # Nav band coordinates
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        # Thin separator lines above and below the nav strip
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1
        )
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

        # ---------- MAIN CONTENT ----------

        def draw_index_square(rect: pygame.Rect, label: str, selected: bool):
            """Draw a fabrication-style index square with a three-bar icon replacing the numeric label.

            The interior of the square is filled using the section base/hover colors and
            a small three-vertical-bars icon is drawn in the centre. The filled bar
            corresponds to the section index (left, centre, right).
            """

            corner_color = UI_TAB_UNDERLINE_COLOR if selected else UI_TAB_TEXT_SELECTED
            SOFT_SELECTED_FILL = (255, 200, 140)
            corner_len = 18
            corner_thick = 3

            # corner-only frame (identical pattern to fabrication 01 square)
            if(selected):
                # top-left
                pygame.draw.line(screen, corner_color, (rect.left, rect.top), (rect.left + corner_len, rect.top), corner_thick)
                pygame.draw.line(screen, corner_color, (rect.left, rect.top), (rect.left, rect.top + corner_len), corner_thick)
                # top-right
                pygame.draw.line(screen, corner_color, (rect.right - corner_len, rect.top), (rect.right, rect.top), corner_thick)
                pygame.draw.line(screen, corner_color, (rect.right, rect.top), (rect.right, rect.top + corner_len), corner_thick)
                # bottom-left
                pygame.draw.line(screen, corner_color, (rect.left, rect.bottom - corner_len), (rect.left, rect.bottom), corner_thick)
                pygame.draw.line(screen, corner_color, (rect.left, rect.bottom), (rect.left + corner_len, rect.bottom), corner_thick)
                # bottom-right
                pygame.draw.line(screen, corner_color, (rect.right - corner_len, rect.bottom), (rect.right, rect.bottom), corner_thick)
                pygame.draw.line(screen, corner_color, (rect.right, rect.bottom - corner_len), (rect.right, rect.bottom), corner_thick)

            # Draw a small three-vertical-bars icon in the centre of the rect.
            # Which bar is filled depends on the numeric label ("01","02","03").
            # Map labels to indices: "01"->0 (left), "02"->1 (centre), "03"->2 (right)
            try:
                sel_idx = int(label) - 1
            except Exception:
                sel_idx = 1

            icon_w = int(rect.width * 0.96)
            icon_h = int(rect.height * 0.54)
            icon_top = rect.centery - icon_h // 2

            # Divide icon area into three vertical segments
            bar_w = max(6, icon_w // 7)
            gap = max(6, bar_w // 10)

            bar_widths = [bar_w, bar_w, bar_w]
            bar_widths[sel_idx] = bar_w * 3  # widen only the selected one

            total_width = bar_widths[0] + gap + bar_widths[1] + gap + bar_widths[2]

            # Fixed left boundary (does not change when filled bar width changes)
            left_x = rect.centerx - total_width // 2

            bars = []
            cursor_x = left_x

            for i, bw in enumerate(bar_widths):
                bars.append(pygame.Rect(cursor_x, icon_top, bw, icon_h))
                cursor_x += bw + gap

            # Colors: filled bar uses corner_color (or underline color), outlines use a muted bright
            filled_col = SOFT_SELECTED_FILL if selected else UI_ICON_BLUE

            for i, b in enumerate(bars):
                # draw outline rectangle thin
                pygame.draw.rect(screen, filled_col, b, 2)
                if i == sel_idx:
                    pygame.draw.rect(screen, filled_col, b.inflate(-4, -4))

        # Left index column (01 / 02 / 03)
        for i, rect in enumerate(idx_rects, start=1):
            draw_index_square(rect, f"{i:02d}", selected=(i - 1) == selected_section)

        # Module cards — inventory card style
        for module, rect in zip(current_modules, card_rects):
            # card background + border: match inventory style
            pygame.draw.rect(screen, (30, 40, 70), rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, rect, 2, border_radius=0)

            draw_tier_icon_image(screen, rect, getattr(module, "tier", 0))

            # preview "thumbnail" based on module.preview_filename
            thumb_w, thumb_h = 80, 64
            thumb_x = rect.left + 20
            thumb_y = rect.centery - thumb_h // 2
            thumb_rect = pygame.Rect(thumb_x, thumb_y, thumb_w, thumb_h)

            preview_surf = None
            filename = getattr(module, "preview_filename", None)
            if filename:
                surf = preview_cache.get(filename)
                if surf is None:
                    try:
                        loaded = pygame.image.load(PREVIEWS_DIR + "/" + filename).convert_alpha()
                        surf = loaded
                    except Exception:
                        surf = None
                    preview_cache[filename] = surf
                preview_surf = surf

            if preview_surf is not None:
                thumb_img = pygame.transform.smoothscale(preview_surf, (thumb_w, thumb_h))
                screen.blit(thumb_img, thumb_rect)
            else:
                pygame.draw.rect(screen, (40, 40, 60), thumb_rect)
                pygame.draw.rect(screen, UI_ICON_BLUE, thumb_rect, 1)
            
            # Level / capacity line at the top-right of card (inventory-style meta text)
            level = getattr(module, "level", 1)
            meta_text = f"LVL. {level:02d}"
            meta_surf = small_font.render(meta_text, True, (200, 200, 220))
            meta_rect = meta_surf.get_rect()
            meta_rect.top = rect.top + 8
            # leave some room on the right for the tier flag icon
            meta_rect.right = rect.right - 40
            screen.blit(meta_surf, meta_rect)

            # Module name (two-line if it contains a space)
            name = module.name
            text_x = meta_rect.left - 60

            if " " in name:
                first, second = name.split(" ", 1)
                line1 = name_font.render(first, True, (230, 230, 255))
                line2 = name_font.render(second, True, (230, 230, 255))
                total_h = line1.get_height() + 4 + line2.get_height()
                text_top = rect.centery - total_h // 2 - 4  # slightly above centre
                screen.blit(line1, (text_x, text_top))
                screen.blit(line2, (text_x, text_top + line1.get_height() + 4))
            else:
                line = name_font.render(name, True, (230, 230, 255))
                text_top = rect.centery - line.get_height() - 2  # just above centre line
                screen.blit(line, (text_x, text_top))


        # Capacity panel on the right, per‑section limit
        cap_title = name_font.render("CAPACITY", True, UI_SECTION_TEXT_COLOR)
        cap_title_rect = cap_title.get_rect()
        cap_title_rect.topleft = (capacity_panel_rect.left, capacity_panel_rect.top)
        screen.blit(cap_title, cap_title_rect)

        cap_value_text = f"{clamped_used}/{capacity_max}"
        cap_value_surf = title_font.render(cap_value_text, True, UI_TITLE_COLOR)
        cap_value_rect = cap_value_surf.get_rect()
        # Right-anchor the numeric value so its width changes don't shift layout
        cap_value_rect.right = capacity_panel_rect.right
        cap_value_rect.top = cap_title_rect.bottom + 8
        screen.blit(cap_value_surf, cap_value_rect)

        # Capacity bar
        bar_width = capacity_panel_rect.width - 20
        bar_height = 22
        bar_rect = pygame.Rect(
            capacity_panel_rect.left,
            cap_value_rect.bottom + 12,
            bar_width,
            bar_height,
        )
        pygame.draw.rect(screen, (20, 36, 64), bar_rect)
        # Use rounding to avoid one-pixel truncation flicker when capacity changes
        inner_w = max(2, int(round(bar_width * capacity_ratio)))
        inner_rect = pygame.Rect(bar_rect.left, bar_rect.top, inner_w, bar_rect.height)
        pygame.draw.rect(screen, (80, 200, 120), inner_rect)
        pygame.draw.rect(screen, (40, 90, 140), bar_rect, width=2)

        # Mount module button bottom-right — reuse fabrication big-rect corner style
        # Transparent background: only draw the corner frame.
        big_corner_len = 14
        big_corner_thick = 3
        corner_color = UI_TAB_TEXT_SELECTED
        # top-left
        pygame.draw.line(screen, corner_color, (mount_btn_rect.left, mount_btn_rect.top), (mount_btn_rect.left + big_corner_len, mount_btn_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (mount_btn_rect.left, mount_btn_rect.top), (mount_btn_rect.left, mount_btn_rect.top + big_corner_len), big_corner_thick)
        # top-right
        pygame.draw.line(screen, corner_color, (mount_btn_rect.right - big_corner_len, mount_btn_rect.top), (mount_btn_rect.right, mount_btn_rect.top), big_corner_thick)
        pygame.draw.line(screen, corner_color, (mount_btn_rect.right, mount_btn_rect.top), (mount_btn_rect.right, mount_btn_rect.top + big_corner_len), big_corner_thick)
        # bottom-left
        pygame.draw.line(screen, corner_color, (mount_btn_rect.left, mount_btn_rect.bottom - big_corner_len), (mount_btn_rect.left, mount_btn_rect.bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (mount_btn_rect.left, mount_btn_rect.bottom), (mount_btn_rect.left + big_corner_len, mount_btn_rect.bottom), big_corner_thick)
        # bottom-right
        pygame.draw.line(screen, corner_color, (mount_btn_rect.right - big_corner_len, mount_btn_rect.bottom), (mount_btn_rect.right, mount_btn_rect.bottom), big_corner_thick)
        pygame.draw.line(screen, corner_color, (mount_btn_rect.right, mount_btn_rect.bottom - big_corner_len), (mount_btn_rect.right, mount_btn_rect.bottom), big_corner_thick)

        # "+" icon on the left of the button with a circular outline
        plus_size = 18
        plus_center = (mount_btn_rect.left + 50, mount_btn_rect.centery)
        pygame.draw.line(
            screen,
            corner_color,
            (plus_center[0] - plus_size // 2, plus_center[1]),
            (plus_center[0] + plus_size // 2, plus_center[1]),
            3,
        )
        pygame.draw.line(
            screen,
            corner_color,
            (plus_center[0], plus_center[1] - plus_size // 2),
            (plus_center[0], plus_center[1] + plus_size // 2),
            3,
        )
        # circle around the plus symbol
        circle_radius = plus_size + 8
        pygame.draw.circle(screen, corner_color, plus_center, circle_radius, 2)

        # Two-line label: "MOUNT" on top of "MODULE"
        line1_surf = tab_font.render("MOUNT", True, (200, 230, 255))
        line2_surf = tab_font.render("MODULE", True, (200, 230, 255))

        text_left = plus_center[0] + plus_size * 3
        line1_rect = line1_surf.get_rect()
        line2_rect = line2_surf.get_rect()
        line1_rect.left = text_left
        line2_rect.left = text_left
        # vertically center the two lines relative to the button
        total_text_height = line1_rect.height + 4 + line2_rect.height
        text_top = mount_btn_rect.centery - total_text_height // 2
        line1_rect.top = text_top
        line2_rect.top = text_top + line1_rect.height + 4

        screen.blit(line1_surf, line1_rect)
        screen.blit(line2_surf, line2_rect)

        pygame.display.flip()