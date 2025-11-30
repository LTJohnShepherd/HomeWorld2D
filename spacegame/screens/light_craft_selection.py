import pygame
import sys
from spacegame.ui.fleet_management_ui import (
    draw_tier_icon,
    draw_fleet_section_titles,
    compute_fleet_preview_layout,
)
from spacegame.ui.ui import preview_for_unit
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.frigate import Frigate
from spacegame.config import (
    FPS,
    UI_BG_COLOR, UI_TITLE_COLOR, 
    UI_TOP_BAR_HEIGHT, 
    UI_NAV_LINE_COLOR, 
    UI_ICON_BLUE, 
    UI_TAB_TEXT_SELECTED
    )


def light_craft_selection_screen(main_player, player_fleet, slot_index: int):
    screen = pygame.display.get_surface()
    if screen is None:
        return

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    # fonts
    title_font = pygame.font.Font(None, 40)
    section_font = pygame.font.Font(None, 32)
    name_font = pygame.font.Font(None, 28)
    dmg_font = pygame.font.Font(None, 22)
    label_font = pygame.font.Font(None, 28)  # for CURRENT LOADOUT / SQUADS / ESCORTS

    # ---- NAV / TITLE (match fleet management) ----
    title_text = "FLEET CONFIGURATION"
    title_surf = title_font.render(title_text, True, UI_TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, UI_TOP_BAR_HEIGHT // 2 - 22))

    nav_center_y = UI_TOP_BAR_HEIGHT // 1.3

    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, nav_center_y)
    back_arrow_hit_rect = back_arrow_rect.inflate(20, 20)

    close_font = pygame.font.Font(None, 40)
    close_surf = close_font.render("X", True, (255, 160, 0))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, UI_TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(20, 20)

    
    # ---- FLEET GEOMETRY (shared with fleet_management / squad_detail) ----
    fleet_layout = compute_fleet_preview_layout(width, height)
    left_center_x = fleet_layout["left_center_x"]
    circle_col_x = fleet_layout["mid_center_x"]
    ms_rect = fleet_layout["ms_rect"]
    circle_rects = fleet_layout["circle_rects"]
    fr_rect = fleet_layout["fr_rect"]
    previews_top = fleet_layout["previews_top"]
    previews_top = min(ms_rect.top, circle_rects[0].top, fr_rect.top)

    # ---- helpers to modify assignments ----
    def clear_slot():
        """Clear the current assignment for this slot via the Hangar API."""
        hangar = getattr(main_player, "hangar_system", None)
        if hangar is not None:
            hangar.clear_slot(slot_index)

    def assign_interceptor(icpt_id: int):
        """Assign an interceptor id to this slot via the Hangar API."""
        hangar = getattr(main_player, "hangar_system", None)
        if hangar is not None:
            hangar.assign_to_slot(slot_index, icpt_id)

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
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # nav: back arrow / close X
                if back_arrow_hit_rect.collidepoint(mx, my):
                    return

                # X should act like other screens: go to game screen
                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # card hit-testing
                selected_count = 1 + len(selected_items)   # 1 for "None"
                selected_title_y = UI_TOP_BAR_HEIGHT + 10
                top_selected_y = selected_title_y + 40
                selected_rects = layout_rects(selected_count, top_selected_y)

                if selected_rects:
                    none_rect = selected_rects[0]
                    selected_craft_rects = selected_rects[1:]
                else:
                    none_rect = None
                    selected_craft_rects = []

                stored_title_y = (
                    (selected_rects[-1].bottom + 40)
                    if selected_rects
                    else (top_selected_y + 40)
                )
                stored_rects = layout_rects(len(stored_items), stored_title_y + 40)

                # 1) "None" button (first in selected list)
                if none_rect is not None and none_rect.collidepoint(mx, my):
                    clear_slot()
                    return

                # 2) Selected crafts are NOT selectable (just visual)

                # 3) Stored crafts ARE selectable
                for rect, entry in zip(stored_rects, stored_items):
                    if rect.collidepoint(mx, my):
                        assign_interceptor(entry.id)
                        return

        # background (match fleet management)
        screen.fill(UI_BG_COLOR)

        # nav title
        screen.blit(title_surf, title_rect)

        # back arrow
        arrow_color = UI_TAB_TEXT_SELECTED
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # close X
        screen.blit(close_surf, close_rect)

        # ---- CURRENT LOADOUT / SQUADS / ESCORTS (same geometry as fleet_management) ----
        assignments = hangar.assignments
        total_slots = len(assignments)
        equipped_slots = sum(1 for a in assignments if a is not None)

        frigates = [s for s in player_fleet if isinstance(s, Frigate)]
        alive_frigates = [f for f in frigates if getattr(f, "health", 0) > 0]

        draw_fleet_section_titles(
            screen,
            title_rect,
            label_font,
            UI_TITLE_COLOR,
            UI_NAV_LINE_COLOR,
            previews_top,
            left_center_x,
            circle_col_x,
            fr_rect.centerx,
            total_slots,
            equipped_slots,
            len(frigates),
            len(alive_frigates),
        )

        # ---- Selected crafts section (title + cards) ----
        selected_title = section_font.render("SELECTED CRAFTS", True, (220, 220, 255))
        selected_title_y = UI_TOP_BAR_HEIGHT + 30
        screen.blit(
            selected_title,
            (width // 3.75 - selected_title.get_width() // 2, selected_title_y),
        )

        selected_count = 1 + len(selected_items)   # "None" + selected entries
        top_selected_y = selected_title_y + 40
        selected_rects = layout_rects(selected_count, top_selected_y)

        if selected_rects:
            none_rect = selected_rects[0]
            selected_craft_rects = selected_rects[1:]
        else:
            none_rect = None
            selected_craft_rects = []

        # draw "None" (first selected box) – sharp corners (UNCHANGED)
        if none_rect is not None:
            pygame.draw.rect(screen, (30, 40, 70), none_rect, border_radius=0)
            pygame.draw.rect(screen, (200, 80, 80), none_rect, 2, border_radius=0)

            # circle with X, offset from left
            preview_x = none_rect.x + 40
            preview_y = none_rect.y + none_rect.height // 2

            pygame.draw.circle(screen, (200, 60, 60), (preview_x, preview_y), 22, 3)
            pygame.draw.line(
                screen,
                (200, 60, 60),
                (preview_x - 12, preview_y - 12),
                (preview_x + 12, preview_y + 12),
                3,
            )
            pygame.draw.line(
                screen,
                (200, 60, 60),
                (preview_x + 12, preview_y - 12),
                (preview_x - 12, preview_y + 12),
                3,
            )

            name = name_font.render("None", True, (230, 230, 255))
            screen.blit(name, (preview_x + 50, none_rect.y + 24))

        # draw selected crafts (visual only) – UNCHANGED
        for rect, entry in zip(selected_craft_rects, selected_items):
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

        # Draw placeholder cards for incomplete rows in selected crafts section
        selected_count_with_none = 1 + len(selected_items)
        if selected_count_with_none > 0:
            items_per_row = 3
            remainder = selected_count_with_none % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(selected_count_with_none + num_placeholders, top_selected_y)
                for placeholder_rect in full_row_rects[selected_count_with_none:]:
                    pygame.draw.rect(screen, (20, 35, 60), placeholder_rect, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), placeholder_rect, 1, border_radius=0)

        # ---- Stored crafts section (title + cards) ----
        stored_title_y = (
            (selected_rects[-1].bottom + 40)
            if selected_rects
            else (top_selected_y + 40)
        )

        stored_title = section_font.render("STORED CRAFTS", True, (220, 220, 255))
        screen.blit(
            stored_title,
            (width // 3.9 - stored_title.get_width() // 2, stored_title_y),
        )

        stored_rects = layout_rects(len(stored_items), stored_title_y + 40)

        # stored cards – UNCHANGED
        for rect, entry in zip(stored_rects, stored_items):
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

        # Draw placeholder cards for incomplete rows in stored crafts section
        if len(stored_items) > 0:
            items_per_row = 3
            remainder = len(stored_items) % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(len(stored_items) + num_placeholders, stored_title_y + 40)
                for placeholder_rect in full_row_rects[len(stored_items):]:
                    pygame.draw.rect(screen, (20, 35, 60), placeholder_rect, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), placeholder_rect, 1, border_radius=0)
            screen.blit(dmg_text, (preview_x + 50, rect.y + 44))

        pygame.display.flip()
        clock.tick(FPS)