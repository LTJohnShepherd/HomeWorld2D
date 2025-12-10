"""Screen for selecting / assigning light craft to hangar slots.

This screen renders available light-craft from the player's Hangar and
allows assigning them to a specific slot. It reads hangar state via the
player's `InventoryManager.hangar`.
"""

import pygame
import sys
from spacegame.ui.fleet_management_ui import (
    draw_tier_icon,
    draw_fleet_section_titles,
    compute_fleet_preview_layout,
)
from spacegame.ui.ui import preview_for_unit, scaled_preview_for_unit
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.units.plasma_bomber import PlasmaBomber
from spacegame.models.units.frigate import Frigate
from spacegame.config import (
    FPS,
    UI_BG_COLOR, UI_TITLE_COLOR,
    UI_TOP_BAR_HEIGHT,
    UI_NAV_LINE_COLOR,
    UI_ICON_BLUE,
    UI_TAB_TEXT_SELECTED,
)


def light_craft_selection_screen(main_player, player_fleet, slot_index: int):
    """Display the light-craft list and allow assigning one to `slot_index`.

    Parameters:
    - main_player: the mothership instance (must have `inventory_manager.hangar`).
    - player_fleet: list of current active ships (used for preview/selection).
    - slot_index: index of the hangar slot to assign.

    Returns None on cancel or `"to_game"` to indicate returning to gameplay.
    """
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
    label_font = pygame.font.Font(None, 28)  # CURRENT LOADOUT / SQUADS / ESCORTS

    # ---- NAV / TITLE ----
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

    # ---- FLEET GEOMETRY ----
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
        inv = getattr(main_player, "inventory_manager", None)
        if inv is None or getattr(inv, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        inv.hangar.clear_slot(slot_index)

    def assign_interceptor(icpt_id: int):
        inv = getattr(main_player, "inventory_manager", None)
        if inv is None or getattr(inv, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        inv.hangar.assign_to_slot(slot_index, icpt_id)

    # ---- layout helpers for the cards ----
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

    # ---- smooth scroll state (same behaviour as inventory) ----
    offset_y = 0.0       # what we render with
    offset_y_raw = 0.0   # direct input accumulator
    SCROLL_STEP = 40
    SCROLL_SMOOTH = 0.25

    running = True
    while running:

        # Hangar data: InventoryManager.hangar is required
        inv_mgr = getattr(main_player, "inventory_manager", None)
        if inv_mgr is None or getattr(inv_mgr, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        hangar = inv_mgr.hangar
        alive_entries = hangar.alive_pool_entries()
        selected_ids = hangar.selected_interceptor_ids()

        # Group entries into selected / stored, then sort by unit_type so
        # cards are grouped by ship type rather than by numeric id.
        selected_items = [e for e in alive_entries if e.id in selected_ids]
        stored_items = [e for e in alive_entries if e.id not in selected_ids]

        selected_items = sorted(selected_items, key=lambda e: (getattr(e, 'unit_type', '') or ''))
        stored_items = sorted(stored_items, key=lambda e: (getattr(e, 'unit_type', '') or ''))

        # Caches to avoid expensive per-frame work (unit instantiation and smoothscale)
        if not hasattr(light_craft_selection_screen, "_power_cache"):
            light_craft_selection_screen._power_cache = {}

        # ---- static layout (no offset here) ----
        selected_title_y = UI_TOP_BAR_HEIGHT + 30
        selected_title_x = width // 3.75

        selected_count = 1 + len(selected_items)  # "None" + selected entries
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
        stored_title_x = width // 3.9

        stored_rects = layout_rects(len(stored_items), stored_title_y + 40)

        # ---- EVENTS ----
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

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # hit-test with scrolled rects
                if none_rect is not None:
                    none_draw_rect = none_rect.move(0, offset_y)
                else:
                    none_draw_rect = None

                stored_draw_rects = [r.move(0, offset_y) for r in stored_rects]

                # 1) "None" button
                if none_draw_rect is not None and none_draw_rect.collidepoint(mx, my):
                    clear_slot()
                    return

                # 3) Stored crafts are selectable
                for rect_draw, entry in zip(stored_draw_rects, stored_items):
                    if rect_draw.collidepoint(mx, my):
                        assign_interceptor(entry.id)
                        return

            # Mouse wheel – same as inventory: update raw offset
            if event.type == pygame.MOUSEWHEEL:
                offset_y_raw += event.y * SCROLL_STEP

        # ---- SCROLL LIMITS + SMOOTH RETURN (same logic as inventory) ----
        scroll_area_top = selected_title_y  # content should not scroll above first title

        content_top = selected_title_y
        if stored_rects:
            content_bottom = stored_rects[-1].bottom + 40
        elif selected_rects:
            content_bottom = selected_rects[-1].bottom + 40
        else:
            content_bottom = content_top

        top_limit = 0.0

        total_content_height = content_bottom - content_top
        visible_height = height - scroll_area_top
        if total_content_height <= visible_height:
            bottom_limit = 0.0
        else:
            bottom_limit = scroll_area_top - total_content_height

        target = max(min(offset_y_raw, top_limit), bottom_limit)
        offset_y += (target - offset_y) * SCROLL_SMOOTH
        if abs(target - offset_y) < 0.5:
            offset_y = target
        offset_y_raw = target  # prevent internal drift past limits

        # ---- DRAW ----
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

        # CURRENT LOADOUT / SQUADS / ESCORTS + fleet preview (static, not scrolled)
        assignments = getattr(hangar, 'assignments', []) if hangar is not None else []
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
            nav_center_y,
        )

        # ---- SCROLLABLE AREA CLIP ----
        scroll_clip_rect = pygame.Rect(0, scroll_area_top, width, height - scroll_area_top)
        screen.set_clip(scroll_clip_rect)

        # ---- Selected crafts section ----
        selected_title = section_font.render("SELECTED CRAFTS", True, (220, 220, 255))
        screen.blit(
            selected_title,
            (selected_title_x - selected_title.get_width() // 2, selected_title_y + offset_y),
        )

        if none_rect is not None:
            none_draw_rect = none_rect.move(0, offset_y)
            pygame.draw.rect(screen, (30, 40, 70), none_draw_rect, border_radius=0)
            pygame.draw.rect(screen, (200, 80, 80), none_draw_rect, 2, border_radius=0)

            preview_x = none_draw_rect.x + 40
            preview_y = none_draw_rect.y + none_draw_rect.height // 2

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
            screen.blit(name, (preview_x + 50, none_draw_rect.y + 24))

        for rect, entry in zip(selected_craft_rects, selected_items):
            draw_rect = rect.move(0, offset_y)
            pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

            tier_value = getattr(entry, "tier", 0)
            draw_tier_icon(screen, draw_rect, tier_value)

            preview_x = draw_rect.x + 40
            preview_y = draw_rect.y + draw_rect.height // 2

            # Use cached scaled preview surface to avoid repeated smoothscale()
            img = scaled_preview_for_unit(getattr(entry, "unit_type"), (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            from spacegame.ui.ui import draw_multiline_text, draw_power_icon
            draw_multiline_text(screen, entry.name, name_font, (230, 230, 255), (preview_x + 50, draw_rect.y + 12))

            # Compute a composite "Power" metric for the unit by instantiating
            # a temporary unit of the appropriate type and averaging key stats.
            # Compute/lookup a cached composite power metric for this entry.
            cache_key = (getattr(entry, 'id', None), getattr(entry, 'tier', None))
            power_cache = light_craft_selection_screen._power_cache
            if cache_key in power_cache:
                power_val = power_cache[cache_key]
            else:
                try:
                    ut = getattr(entry, 'unit_type', '')
                    tier = int(getattr(entry, 'tier', 0) or 0)
                    if ut == 'interceptor':
                        unit = Interceptor((0, 0), interceptor_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'plasma_bomber':
                        unit = PlasmaBomber((0, 0), bomber_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'resource_collector':
                        from spacegame.models.units.resource_collector import ResourceCollector
                        unit = ResourceCollector((0, 0), collector_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'frigate':
                        unit = Frigate((0, 0), tier=tier)
                    else:
                        unit = None
                except Exception:
                    unit = None

                if unit is None:
                    power_val = 0
                else:
                    bullet = float(getattr(unit, 'bullet_damage', 0.0))
                    armor = float(getattr(unit, 'armor_damage', 0.0))
                    health = float(getattr(unit, 'max_health', getattr(unit, 'health', 0.0)))
                    mover = getattr(unit, 'mover', None)
                    speed = float(getattr(mover, 'speed', getattr(unit, 'speed', 0.0))) if mover is not None else float(getattr(unit, 'speed', 0.0))
                    try:
                        power = (bullet + armor + speed + (health / 10.0)) / 4.0
                    except Exception:
                        power = 0.0
                    power_val = int(round(power))
                power_cache[cache_key] = power_val

            # Draw icon and numeric label (small, lower than the name)
            icon_size = 12
            icon_x = preview_x + 50
            icon_y = draw_rect.y + 56
            draw_power_icon(screen, (icon_x, icon_y), size=icon_size, color=(200, 200, 220))
            try:
                power_label = dmg_font.render(str(int(power_val)), True, (220, 220, 255))
                label_x = icon_x + icon_size + 8
                icon_h = int(round(icon_size * 1.2))
                label_y = icon_y + (icon_h // 2) - (power_label.get_height() // 2)
                screen.blit(power_label, (label_x, label_y))
            except Exception:
                pass

        # placeholder cards for incomplete selected row
        selected_count_with_none = 1 + len(selected_items)
        if selected_count_with_none > 0:
            items_per_row = 3
            remainder = selected_count_with_none % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(
                    selected_count_with_none + num_placeholders, top_selected_y
                )
                for placeholder_rect in full_row_rects[selected_count_with_none:]:
                    draw_ph = placeholder_rect.move(0, offset_y)
                    pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)

        # ---- Stored crafts section ----
        stored_title = section_font.render("STORED CRAFTS", True, (220, 220, 255))
        screen.blit(
            stored_title,
            (stored_title_x - stored_title.get_width() // 2, stored_title_y + offset_y),
        )

        for rect, entry in zip(stored_rects, stored_items):
            draw_rect = rect.move(0, offset_y)
            pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

            tier_value = getattr(entry, "tier", 0)
            draw_tier_icon(screen, draw_rect, tier_value)

            preview_x = draw_rect.x + 40
            preview_y = draw_rect.y + draw_rect.height // 2

            img = scaled_preview_for_unit(getattr(entry, "unit_type"), (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            from spacegame.ui.ui import draw_multiline_text, draw_power_icon
            draw_multiline_text(screen, entry.name, name_font, (230, 230, 255), (preview_x + 50, draw_rect.y + 12))

            # Use cached power computation if available
            cache_key = (getattr(entry, 'id', None), getattr(entry, 'tier', None))
            power_cache = light_craft_selection_screen._power_cache
            if cache_key in power_cache:
                power_val = power_cache[cache_key]
            else:
                try:
                    ut = getattr(entry, 'unit_type', '')
                    tier = int(getattr(entry, 'tier', 0) or 0)
                    if ut == 'interceptor':
                        unit = Interceptor((0, 0), interceptor_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'plasma_bomber':
                        unit = PlasmaBomber((0, 0), bomber_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'resource_collector':
                        from spacegame.models.units.resource_collector import ResourceCollector
                        unit = ResourceCollector((0, 0), collector_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'frigate':
                        unit = Frigate((0, 0), tier=tier)
                    else:
                        unit = None
                except Exception:
                    unit = None

                if unit is None:
                    power_val = 0
                else:
                    bullet = float(getattr(unit, 'bullet_damage', 0.0))
                    armor = float(getattr(unit, 'armor_damage', 0.0))
                    health = float(getattr(unit, 'max_health', getattr(unit, 'health', 0.0)))
                    mover = getattr(unit, 'mover', None)
                    speed = float(getattr(mover, 'speed', getattr(unit, 'speed', 0.0))) if mover is not None else float(getattr(unit, 'speed', 0.0))
                    try:
                        power = (bullet + armor + speed + (health / 10.0)) / 4.0
                    except Exception:
                        power = 0.0
                    power_val = int(round(power))
                power_cache[cache_key] = power_val

            icon_size = 12
            icon_x = preview_x + 50
            icon_y = draw_rect.y + 56
            draw_power_icon(screen, (icon_x, icon_y), size=icon_size, color=(200, 200, 220))
            try:
                power_label = dmg_font.render(str(int(power_val)), True, (220, 220, 255))
                label_x = icon_x + icon_size + 8
                icon_h = int(round(icon_size * 1.2))
                label_y = icon_y + (icon_h // 2) - (power_label.get_height() // 2)
                screen.blit(power_label, (label_x, label_y))
            except Exception:
                pass

        if len(stored_items) > 0:
            items_per_row = 3
            remainder = len(stored_items) % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(
                    len(stored_items) + num_placeholders, stored_title_y + 40
                )
                for placeholder_rect in full_row_rects[len(stored_items):]:
                    draw_ph = placeholder_rect.move(0, offset_y)
                    pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)

        # reset clip
        screen.set_clip(None)

        pygame.display.flip()
        clock.tick(FPS)