import sys
import pygame
from spacegame.ui.fleet_management_ui import (
    draw_tier_icon
)
from spacegame.ui.ui import preview_for_unit
from spacegame.models.units.interceptor import Interceptor
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    UI_BG_COLOR,
    UI_TAB_HEIGHT,
    UI_ICON_BLUE,
    UI_SECTION_TEXT_COLOR,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_UNDERLINE_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_TAB_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR
    )

def inventory_screen(main_player, player_fleet):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()
    
    # Inventory constants
    INVENTORY_CAPACITY_LIMIT = 60

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    section_font = pygame.font.Font(None, 32)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 28)
    dmg_font = pygame.font.Font(None, 22)
    capacity_font = pygame.font.Font(None, 24)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "STORAGE"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))
    
    # Capacity display to the right of title (will be updated each frame)
    capacity_rect = pygame.Rect(0, 0, 200, 30)
    capacity_rect.right = width - 80
    capacity_rect.centery = title_rect.centery

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
    tab_labels = ["STORAGE", "FABRICATION", "REFINING", "BRIDGE"]
    selected_tab = 0  # INVENTORY selected
    tab_spacing = 16

    tab_entries = []
    total_tabs_width = -tab_spacing
    # Measure and compute widths (icon + text + padding)
    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    for label in tab_labels:
        text_surf = tab_font.render(label, True, UI_TAB_TEXT_COLOR)
        text_width = text_surf.get_width()
        tab_width = icon_size + ICON_MARGIN + text_width + H_PADDING * 2
        tab_entries.append({"label": label, "text_surf": text_surf, "width": tab_width})
        total_tabs_width += tab_width + tab_spacing

    # Move tabs slightly lower so they are not too close to the title text
    tabs_y = TOP_BAR_HEIGHT - UI_TAB_HEIGHT - 4
    tabs_left = width // 2 - total_tabs_width // 2

    # Create rects for tabs
    x = tabs_left
    for entry in tab_entries:
        rect = pygame.Rect(x, tabs_y, entry["width"], UI_TAB_HEIGHT)
        entry["rect"] = rect
        x += entry["width"] + tab_spacing

    # ---- layout helpers for the cards (unchanged visually) ----
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    def layout_rects(num_items, top_y):
        total_w = COLS * BOX_W + (COLS - 1) * MARGIN_X
        left_start = width // 2 - total_w // 2
        rects = []
        for i in range(num_items):
            row = i // COLS
            col = i % COLS
            x = left_start + col * (BOX_W + MARGIN_X)
            y = top_y + row * (BOX_H + MARGIN_Y)
            rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
        return rects

    running = True
    while running:

        # recompute alive/selected/stored every frame from the Hangar system
        hangar = getattr(main_player, "hangar_system", None)
        if hangar is None:
            return

        alive_entries = hangar.alive_pool_entries()
        selected_ids = hangar.selected_interceptor_ids()

        selected_items = [e for e in alive_entries if e.id in selected_ids]
        stored_items = [e for e in alive_entries if e.id not in selected_ids]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "to_internal"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return "to_internal"

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        if entry["label"] == "FLEET CONFIGURATION":
                            from spacegame.screens.fleet_management import (
                                fleet_management_screen,
                            )

                            res = fleet_management_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # reset highlight back to INTERNAL after returning
                            selected_tab = 1
                        else:
                            selected_tab = idx
                        break

                # card hit-testing
                selected_count = len(selected_items)
                selected_title_y = UI_TOP_BAR_HEIGHT + 10
                top_selected_y = selected_title_y + 40
                selected_rects = layout_rects(selected_count, top_selected_y)

                if selected_rects:
                    selected_craft_rects = selected_rects[0:]
                else:
                    selected_craft_rects = []
                

        # ---------- DRAW ----------
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
        
        # Capacity display (dynamically updated each frame)
        current_inventory_count = len(stored_items)
        capacity_text = f"CAPACITY: {current_inventory_count} / {INVENTORY_CAPACITY_LIMIT}"
        capacity_surf = capacity_font.render(capacity_text, True, UI_TAB_TEXT_COLOR)
        capacity_display_rect = capacity_surf.get_rect()
        capacity_display_rect.right = width - 80
        capacity_display_rect.centery = title_rect.centery
        screen.blit(capacity_surf, capacity_display_rect)

        # Back arrow (on top of nav background)
        arrow_color = (220, 235, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (transparent background: only icon, text, highlight on nav lines)
        for idx, entry in enumerate(tab_entries):
            rect = entry["rect"]
            is_selected = idx == selected_tab

            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.centery = rect.centery
            icon_rect.left = rect.left + H_PADDING
            pygame.draw.rect(
                screen,
                (210, 220, 235) if is_selected else (170, 190, 210),
                icon_rect,
                border_radius=4,
                width=2,
            )

            text_color = UI_TAB_TEXT_SELECTED if is_selected else UI_TAB_TEXT_COLOR
            label_surf = tab_font.render(entry["label"], True, text_color)
            label_rect = label_surf.get_rect()
            label_rect.centery = rect.centery
            label_rect.left = icon_rect.right + ICON_MARGIN
            screen.blit(label_surf, label_rect)

            if is_selected:
                # highlight segments exactly on the top/bottom nav lines
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_top_y),
                    (rect.right - 6, nav_top_y),
                    2,
                )
                pygame.draw.line(
                    screen,
                    UI_TAB_UNDERLINE_COLOR,
                    (rect.left + 6, nav_bottom_y),
                    (rect.right - 6, nav_bottom_y),
                    2,
                )
        
    # ---- Ships section (title + cards) ----
        ships_title = section_font.render("SHIPS", True, (220, 220, 255))
        ships_title_y = UI_TOP_BAR_HEIGHT + 30
        screen.blit(
            ships_title,
            (width // 4.8 - ships_title.get_width() // 2, ships_title_y),
        )

        ships_top_y = ships_title_y + 40
        ships_rects = layout_rects(len(stored_items), ships_top_y)

        # Draw only stored (unused) ships as cards (matching light_craft_selection layout)
        for rect, entry in zip(ships_rects, stored_items):
            pygame.draw.rect(screen, (30, 40, 70), rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, rect, 2, border_radius=0)

            tier_value = getattr(entry, "tier", 0)
            draw_tier_icon(screen, rect, tier_value)

            preview_x = rect.x + 40
            preview_y = rect.y + rect.height // 2

            # preview image (pick by unit_type)
            preview_img = preview_for_unit(getattr(entry, "unit_type"))
            img = pygame.transform.smoothscale(preview_img, (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            name = name_font.render(entry.name, True, (230, 230, 255))
            screen.blit(name, (preview_x + 50, rect.y + 12))

            # show damage (resource collectors have 0 damage)
            if getattr(entry, "unit_type") == "resource_collector":
                dmg = 0
            elif getattr(entry, "unit_type") == "interceptor":
                dmg = Interceptor.DEFAULT_BULLET_DAMAGE
            dmg_text = dmg_font.render(f"Damage: {int(dmg)}", True, (200, 200, 220))
            screen.blit(dmg_text, (preview_x + 50, rect.y + 44))

        # Draw placeholder cards for incomplete rows in ships section
        num_items = len(stored_items)
        if num_items > 0:
            items_per_row = 3
            remainder = num_items % items_per_row
            if remainder != 0:
                # Calculate how many placeholders are needed to complete the row
                num_placeholders = items_per_row - remainder
                # Create rects for the full row to get placeholder positions
                full_row_rects = layout_rects(num_items + num_placeholders, ships_top_y)
                # Draw placeholder cards starting after the last actual item
                for placeholder_rect in full_row_rects[num_items:]:
                    pygame.draw.rect(screen, (20, 35, 60), placeholder_rect, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), placeholder_rect, 1, border_radius=0)

        # ---- Materials section (title + placeholder cards) ----
        materials_title_y = (
            (ships_rects[-1].bottom + 40)
            if ships_rects
            else (ships_top_y + 40)
        )
        
        materials_title = section_font.render("MATERIALS", True, (220, 220, 255))
        screen.blit(
            materials_title,
            (width // 4.3 - materials_title.get_width() // 2, materials_title_y),
        )

        # Display 3 placeholder cards for materials section
        materials_top_y = materials_title_y + 40
        materials_rects = layout_rects(3, materials_top_y)

        for rect in materials_rects:
            # Draw lightly highlighted placeholder box
            pygame.draw.rect(screen, (20, 35, 60), rect, border_radius=0)
            pygame.draw.rect(screen, (60, 100, 150), rect, 1, border_radius=0)

        pygame.display.flip()