import sys
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
    PREVIEWS_DIR,
)
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.ui.ui import UI_BG_IMG
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.ui.fleet_management_ui import draw_tier_icon_image


def module_selection_screen(main_player, player_fleet, start_section: int = 1, installed_sections=None):
    """Screen that allows the player to pick a module to mount into a section.

    - Reuses the same nav/tabs as other screens.
    - Shows the three index squares on the left so the player can switch section.
    - Shows an inventory/grid in the middle filtered to modules that declare
      they can be mounted on the selected section.

    Returns the chosen module instance and the section index as a tuple
    `(module, section)` if the user selects one, otherwise None. The
    `section` value reflects the section selected within this screen and may
    differ from `start_section` if the player switched sections before
    choosing a module.
    """
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # fonts
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    name_font = pygame.font.Font(None, 22)
    small_font = pygame.font.Font(None, 20)

    # top bar / tabs
    TOP_BAR_HEIGHT = 96
    title_text = "MODULE SELECTION"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    tab_labels = ["STORAGE", "BRIDGE", "FABRICATION", "REFINING", "INTERNAL MODULES"]
    icon_filenames = ["Nav_Icon_Inventory.png", "Nav_Icon_Bridge.png", "Nav_Icon_Fabricator.png", "Nav_Icon_Refinery.png", "Nav_Icon_InternalModules.png"]
    selected_tab = 4
    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # ensure start tab is not disabled
    if 0 <= selected_tab < len(tab_entries) and tab_entries[selected_tab]["label"] in disabled_labels:
        for i, e in enumerate(tab_entries):
            if e["label"] not in disabled_labels:
                selected_tab = i
                break

    # Back arrow (left)
    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, TOP_BAR_HEIGHT // 1.3)

    # Close "X" (right)
    close_font = pygame.font.Font(None, 40)
    close_surf = close_font.render("X", True, (255, 160, 40))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(16, 16)

    # left index column geometry (match internal_modules_screen)
    LEFT_SHIFT = 20
    card_x = 40 - LEFT_SHIFT
    content_top = tabs_y + UI_TAB_HEIGHT + 6 + 24
    idx_size = 96
    idx_rect_base = pygame.Rect(card_x + 16, content_top + 16, idx_size, idx_size)
    IDX_V_SPACING = idx_size + 24
    idx_rects = [
        idx_rect_base,
        pygame.Rect(idx_rect_base.left, idx_rect_base.top + IDX_V_SPACING, idx_size, idx_size),
        pygame.Rect(idx_rect_base.left, idx_rect_base.top + 2 * IDX_V_SPACING, idx_size, idx_size),
    ]

    # module inventory area in the middle (use same centered layout as other screens)
    cards_top_y = content_top

    # card geometry (match `inventory_screen` / `light_craft_selection_screen`)
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    def layout_rects(num_items: int, top_y: int) -> list[pygame.Rect]:
        total_w = COLS * BOX_W + (COLS - 1) * MARGIN_X
        left_start = width // 2 - total_w // 2
        rects: list[pygame.Rect] = []
        for i in range(num_items):
            row = i // COLS
            col = i % COLS
            x = left_start + col * (BOX_W + MARGIN_X)
            y = top_y + row * (BOX_H + MARGIN_Y)
            rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
        return rects

    # Prepare a live list of candidate modules sourced from the player's InventoryManager
    inv_mgr = getattr(main_player, 'inventory_manager', None)
    all_candidates = []
    if inv_mgr is not None and hasattr(inv_mgr, 'get_modules'):
        try:
            # Use the player's unequipped modules as candidates.
            mods = list(inv_mgr.get_modules() or [])
            all_candidates = mods
        except Exception:
            all_candidates = []

    selected_section = int(start_section)

    clock = pygame.time.Clock()
    running = True

    def draw_index_square(rect: pygame.Rect, label: str, selected: bool):
        """Copy of the index-drawing logic from `internal_modules_screen` to ensure
        identical visuals between screens.
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
        # widen only the selected one
        if 0 <= sel_idx < 3:
            bar_widths[sel_idx] = bar_w * 3

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

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # if corresponding main tabs are disabled, bubble up to Internal
                if "FABRICATION" in disabled_labels or "REFINING" in disabled_labels:
                    return "to_internal"
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # back / close buttons
                if back_arrow_rect.collidepoint(mx, my):
                    if "FABRICATION" in disabled_labels or "REFINING" in disabled_labels:
                        return "to_internal"
                    return None

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        label = entry["label"]
                        # ignore disabled tabs
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

                # index squares
                for i, r in enumerate(idx_rects):
                    if r.collidepoint(mx, my):
                        selected_section = i
                        break

                # click on module card: check middle grid area
                # filter candidates by allowed_sections and exclude already-equipped module instances
                installed_objs = set()
                if isinstance(installed_sections, (list, tuple)):
                    for sec in installed_sections:
                        try:
                            for im in sec:
                                if im is not None:
                                    installed_objs.add(im)
                        except Exception:
                            pass

                filtered = [m for m in all_candidates if m.is_mountable_on(selected_section) and m not in installed_objs]


                # compute rows and card rects using the shared layout helper
                rows = max((len(filtered) + COLS - 1) // COLS, 1)
                total_slots = rows * COLS
                card_rects = layout_rects(total_slots, cards_top_y)

                for idx, rect in enumerate(card_rects):
                    if idx < len(filtered):
                        module = filtered[idx]
                        if rect.collidepoint(mx, my):
                            return (module, selected_section)
                    else:
                        # placeholder card click does nothing
                        pass

        # draw background and nav
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
            screen.fill(UI_BG_COLOR)
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
        pygame.draw.rect(screen, UI_NAV_BG_COLOR, (0, nav_top_y, width, nav_bottom_y - nav_top_y))
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1)
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

        nav_top_y, nav_bottom_y = draw_tabs(screen, tab_entries, selected_tab, tabs_y, width, tab_font, disabled_labels=disabled_labels)

        # left index column
        for i, rect in enumerate(idx_rects, start=1):
            draw_index_square(rect, f"{i:02d}", selected=(i - 1) == selected_section)

        # middle inventory grid: 3 columns and placeholders to fill rows
        # build set of installed module instances to filter them out (compare by identity)
        installed_objs = set()
        if isinstance(installed_sections, (list, tuple)):
            for sec in installed_sections:
                try:
                    for im in sec:
                        if im is not None:
                            installed_objs.add(im)
                except Exception:
                    pass

        filtered = [m for m in all_candidates if m.is_mountable_on(selected_section) and m not in installed_objs]

        # grid layout: use shared constants and centered layout helper
        rows = max((len(filtered) + COLS - 1) // COLS, 1)
        total_slots = rows * COLS
        card_rects = layout_rects(total_slots, cards_top_y)

        # draw filled module cards then placeholders for remaining slots
        for idx, rect in enumerate(card_rects):
            if idx < len(filtered):
                module = filtered[idx]
                pygame.draw.rect(screen, (30, 40, 70), rect, border_radius=0)
                pygame.draw.rect(screen, UI_ICON_BLUE, rect, 2, border_radius=0)
                draw_tier_icon_image(screen, rect, getattr(module, "tier", 0))

                thumb_w, thumb_h = 80, 64
                thumb_x = rect.left + 20
                thumb_y = rect.centery - thumb_h // 2
                thumb_rect = pygame.Rect(thumb_x, thumb_y, thumb_w, thumb_h)
                try:
                    loaded = pygame.image.load(PREVIEWS_DIR + "/" + module.preview_filename).convert_alpha()
                    thumb_img = pygame.transform.smoothscale(loaded, (thumb_w, thumb_h))
                    screen.blit(thumb_img, thumb_rect)
                except Exception:
                    pygame.draw.rect(screen, (40, 40, 60), thumb_rect)
                    pygame.draw.rect(screen, UI_ICON_BLUE, thumb_rect, 1)

                # name
                name = module.name
                name_surf = name_font.render(name, True, (230, 230, 255))
                name_rect = name_surf.get_rect()
                name_rect.left = rect.left + 120
                name_rect.centery = rect.centery
                screen.blit(name_surf, name_rect)
            else:
                # placeholder card (match inventory / light craft visuals)
                pygame.draw.rect(screen, (20, 35, 60), rect, border_radius=0)
                pygame.draw.rect(screen, (60, 100, 150), rect, 1, border_radius=0)

        pygame.display.flip()

    return None
