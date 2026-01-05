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
from spacegame.models.modules.fabricatormodule import FabricatorModule
from spacegame.models.modules.refinerymodule import RefineryModule
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG
from spacegame.ui.ui import draw_plus_circle, drawCornerFrame


def module_details_screen(main_player, player_fleet, initial_section=1, installed_sections=None, selected_module=None, selected_module_index=0):
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
    # Grey-out/selectability: disable FABRICATION/REFINING when none equipped
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # clamp selected_tab to a non-disabled tab if necessary
    if 0 <= selected_tab < len(tab_entries) and tab_entries[selected_tab]["label"] in disabled_labels:
        for i, e in enumerate(tab_entries):
            if e["label"] not in disabled_labels:
                selected_tab = i
                break

    # ---------- MODULE DATA ----------
    # Use the centralised ModulesManager as the source of truth for equipped modules.
    SECTION_MODULES = modules_manager.get_internal_sections()
    # allow caller to override the visible installed sections (caller may pass
    # the live SECTION_MODULES from another screen so navigation persists)
    if installed_sections is not None:
        SECTION_MODULES = installed_sections

    # Fabrication/Refining managers read from ModulesManager dynamically, no sync needed

    selected_section = initial_section  # 0 -> "front", 1 -> "middle", 2 -> "back"

    # simple cache so we only load each preview image once
    preview_cache: dict[str, pygame.Surface] = {}

    running = True
    clock = pygame.time.Clock()

    while running:
        clock.tick(60)

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

        # Base section rect — positions and size identical to fabrication screen
        idx_size = 96
        idx_rect_base = pygame.Rect(card_rect.left + 16, card_rect.top + 16, idx_size, idx_size)

        # Derived section rects stacked vertically
        IDX_V_SPACING = idx_size + 24
        idx_rects = [
            idx_rect_base,
            pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING, idx_size, idx_size),
            pygame.Rect(idx_rect_base.left, idx_rect_base.top + 2 * IDX_V_SPACING, idx_size, idx_size),
        ]

        # determine which module instance to display for the screen
        if selected_module is not None:
            module_instance = selected_module
        else:
                try:
                    module_instance = SECTION_MODULES[selected_section][0]
                except Exception:
                    module_instance = None

        # center big rect (used for plus-circle UI and click actions)
        plus_radius = 120
        preview_center = (width // 2, height // 2)
        big_rect_pad = 100
        big_rect = pygame.Rect(
            preview_center[0] - plus_radius - big_rect_pad,
            preview_center[1] - plus_radius - big_rect_pad,
            (plus_radius + big_rect_pad) * 2,
            (plus_radius + big_rect_pad) * 2,
        )

        # RIGHT PANEL + DISMOUNT BUTTON (copy size/positioning used in
        # fabrication_bpdetails_screen for the build button)
        right_panel_w = 340
        right_rect = pygame.Rect(
            width - right_panel_w - 40,
            card_rect.top,
            right_panel_w,
            140,
        )
        
        dismount_btn_h = 64
        dismount_btn_rect = pygame.Rect(
            right_rect.left,
            height - dismount_btn_h - 40,
            right_panel_w,
            dismount_btn_h,
        )

        # no bottom button in the details screen

        # ---------- EVENT HANDLING ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
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

                # Section selector squares ("01", "02", "03") — clicking
                # any of these should return control to the calling screen with
                # the chosen section so the caller can show that section.
                for i, r in enumerate(idx_rects):
                    if r.collidepoint(mx, my):
                        return i

                # central big rect is non-interactive; handle DISMOUNT button
                if dismount_btn_rect.collidepoint(mx, my):
                    # Only dismount if we have a valid module_instance and it
                    # is currently installed in the selected section.
                        try:
                            if module_instance is None:
                                continue
                        except Exception:
                            continue

                        # remove from central manager
                        try:
                            modules_manager.remove_module(selected_section, module_instance)
                        except Exception:
                            pass

                        # persist compatibility attribute on player
                        try:
                            setattr(main_player, 'installed_internal_modules', modules_manager.get_internal_sections())
                        except Exception:
                            pass

                        # add the module to the unequipped inventory
                        try:
                            inv_mgr = getattr(main_player, 'inventory_manager', None)
                            if inv_mgr is not None and hasattr(inv_mgr, 'add_module'):
                                inv_mgr.add_module(module_instance)
                        except Exception:
                            pass

                        # Return to caller, signalling the selected section so
                        # the caller returns with that section open
                        return selected_section

                # Left-derivered module area: we don't currently display module
                # cards in this details screen, but it is useful if a caller
                # passed a specific `selected_module` and wants to interact
                # with the material. No per-card clicks are handled here.

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

        # Back arrow (on top of nav background)
        arrow_color = (220, 235, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        # back arrow - use image
        back_arrow_img = get_back_arrow_image()
        if back_arrow_img:
            arrow_scaled = pygame.transform.smoothscale(back_arrow_img, (arrow_size - 4, arrow_size - 4))
            arrow_draw_rect = arrow_scaled.get_rect(center=back_arrow_rect.center)
            screen.blit(arrow_scaled, arrow_draw_rect)
        else:
            pygame.draw.polygon(screen, arrow_color, arrow_points)

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

        # Left index column
        for i, rect in enumerate(idx_rects, start=1):
            draw_index_square(rect, f"{i:02d}", selected=(i - 1) == selected_section)

        # ---------- DETAILS PANEL (right of first index square) ----------
        if idx_rects:
            base_idx_rect = idx_rects[0]
        else:
            base_idx_rect = idx_rect_base

        details_x = base_idx_rect.right + 18
        details_y = base_idx_rect.top

        # module_instance determined earlier (before event handling)

        title_font = pygame.font.Font(None, 36)
        module_title_text = (module_instance.name.upper() if module_instance else "EMPTY")
        module_title = title_font.render(module_title_text, True, UI_SECTION_TEXT_COLOR)
        module_title_rect = module_title.get_rect()
        module_title_rect.topleft = (details_x, details_y)
        screen.blit(module_title, module_title_rect)

        # description lines depend on which module type we're showing
        desc_font = pygame.font.Font(None, 20)
        if isinstance(module_instance, RefineryModule):
            desc_lines = [
                "A standard refinery module, used for",
                "on-ship processing of raw ores into",
                "refined materials.",
            ]
        elif isinstance(module_instance, FabricatorModule):
            desc_lines = [
                "A standard fabricator module, used for",
                "on-ship fabrication for weapons and",
                "strike craft.",
            ]
        else:
            desc_lines = ["A ship module."]
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

        # Stats for a RefineryModule (fallback values if missing)
        try:
            module_size = getattr(module_instance, 'module_size', 0)
        except Exception:
            module_size = 0

        # Build stats per module type
        if isinstance(module_instance, RefineryModule):
            base_refinement_time = getattr(module_instance, 'base_refinement_time', 0.0)
            stat_rows = [
                ("Module Size:", str(module_size)),
                ("Base Refinement Time:", str(base_refinement_time)),
            ]
        elif isinstance(module_instance, FabricatorModule):
            base_fabrication_time = getattr(module_instance, 'base_fabrication_time', 0.0)
            stat_rows = [
                ("Module Size:", str(module_size)),
                ("Base Fabrication Time:", str(base_fabrication_time)),
            ]
        else:
            stat_rows = [("Module Size:", str(module_size))]

        for label_text, value_text in stat_rows:
            lbl = stat_label_font.render(label_text, True, UI_SECTION_TEXT_COLOR)
            val = stat_value_font.render(value_text, True, (200, 230, 200))

            screen.blit(lbl, (stat_x, stat_y))
            val_rect = val.get_rect()
            val_rect.topright = (card_rect.right - 110, stat_y)
            screen.blit(val, val_rect.topleft)

            # draw underline from left label to right value
            line_y = stat_y + lbl.get_height() + 4
            line_left = stat_x
            line_right = val_rect.right
            pygame.draw.line(screen, UI_NAV_LINE_COLOR, (line_left, line_y), (line_right, line_y), 1)

            stat_y += lbl.get_height() + 12

        # Officer assign box
        officer_box_h = 70
        officer_box_w = 240
        CARD_BG = (12, 26, 50)
        officer_box_rect = pygame.Rect(details_x, stat_y + 36, officer_box_w, officer_box_h)
        pygame.draw.rect(screen, CARD_BG, officer_box_rect)
        pygame.draw.rect(screen, UI_TITLE_COLOR, officer_box_rect, 2)

        ocx = officer_box_rect.left + 42
        ocy = officer_box_rect.centery
        inner_radius = int(officer_box_h / 2.8)
        draw_plus_circle(screen, (ocx, ocy), inner_radius, UI_TITLE_COLOR, plus_size=14, circle_thickness=2, plus_thickness=2)

        line1 = stat_label_font.render("ASSIGN", True, UI_SECTION_TEXT_COLOR)
        line2 = stat_label_font.render("OPERATOR", True, UI_SECTION_TEXT_COLOR)
        text_x = ocx + inner_radius + 12
        total_text_h = line1.get_height() + line2.get_height() + 4
        start_y = officer_box_rect.centery - total_text_h // 2
        screen.blit(line1, (text_x, start_y))
        screen.blit(line2, (text_x, start_y + line1.get_height() + 4))

        # ----- Center big plus-circle (refinery production) -----
        plus_radius = 120
        preview_center = (width // 2, height // 2)
        big_rect_pad = 100
        big_rect = pygame.Rect(
            preview_center[0] - plus_radius - big_rect_pad,
            preview_center[1] - plus_radius - big_rect_pad,
            (plus_radius + big_rect_pad) * 2,
            (plus_radius + big_rect_pad) * 2,
        )

        # Draw the module preview image centered inside the big rect instead
        filename = getattr(module_instance, 'preview_filename', None)
        preview_surf = None
        if filename:
            preview_surf = preview_cache.get(filename)
            if preview_surf is None:
                try:
                    loaded = pygame.image.load(PREVIEWS_DIR + "/" + filename).convert_alpha()
                    preview_surf = loaded
                except Exception:
                    preview_surf = None
                preview_cache[filename] = preview_surf

        if preview_surf is not None:
            # scale to fit comfortably inside the big rect
            max_w = int(big_rect.width * 0.82)
            max_h = int(big_rect.height * 0.82)
            surf_w, surf_h = preview_surf.get_size()
            scale = min(max_w / surf_w, max_h / surf_h, 1.0)
            target_w = int(surf_w * scale)
            target_h = int(surf_h * scale)
            img = pygame.transform.smoothscale(preview_surf, (target_w, target_h))
            img_rect = img.get_rect(center=preview_center)
            screen.blit(img, img_rect)
        
        big_corner_len = 28
        big_corner_thick = 4
        corner_color = UI_TAB_TEXT_SELECTED
        drawCornerFrame(screen, big_rect, corner_color, corner_len=big_corner_len, corner_thick=big_corner_thick)

        # Draw right panel and DISMOUNT button (red) — informational panel on
        # the right side reusing the same positioning as fabrication details.
        try:
            pygame.draw.rect(screen, (12, 26, 50), right_rect)
            pygame.draw.rect(screen, UI_TITLE_COLOR, right_rect, 2)

            DISMOUNT_COLOR = (210, 60, 60)
            pygame.draw.rect(screen, DISMOUNT_COLOR, dismount_btn_rect, width=2, border_radius=0)
            btn_label = tab_font.render("DISMOUNT", True, DISMOUNT_COLOR)
            btn_label_rect = btn_label.get_rect(center=dismount_btn_rect.center)
            screen.blit(btn_label, btn_label_rect)
        except Exception:
            pass
        pygame.display.flip()