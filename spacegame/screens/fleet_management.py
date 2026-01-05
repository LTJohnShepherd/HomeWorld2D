"""Fleet management screen and helpers.

This module provides the in-game fleet management UI which reads hangar
state from `main_player.inventory_manager.hangar` and allows inspecting
and assigning light-craft to slots.
"""

import sys
import pygame
from spacegame.ui.fleet_management_ui import (
    draw_fleet_section_titles,
    compute_fleet_preview_layout,
    draw_tier_icon_image,
)
from spacegame.models.units.expedition_ship import ExpeditionShip
from spacegame.models.units.frigate import Frigate
from spacegame.ui.ui import preview_for_unit, draw_hex, draw_triangle, draw_dalton, draw_diamond, UI_BG_IMG
from spacegame.ui.nav_ui import get_back_arrow_image
from spacegame.config import (
    FPS,
    UI_BG_COLOR, 
    UI_NAV_LINE_COLOR, 
    UI_TITLE_COLOR,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_TEXT_SELECTED
    )
from spacegame.config import UI_ICON_BLUE, UI_ICON_WHITE


def _build_hangar_snapshot(main_player):
    """Return the current hangar snapshot from the player's registered Hangar.

    Returns a tuple (assignments, ships, pool_by_id). Raises a RuntimeError
    if `inventory_manager.hangar` is not present on `main_player`.
    """
    inv = getattr(main_player, 'inventory_manager', None)
    if inv is None or getattr(inv, 'hangar', None) is None:
        raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
    hangar = inv.hangar
    if not hasattr(hangar, "snapshot"):
        return [], [], {}
    return hangar.snapshot()


def _entry_is_alive(entry) -> bool:
    """Return True if the given pool entry exists and is marked alive."""
    return bool(getattr(entry, "alive", False))


def _entry_name(entry) -> str:
    """Return the display name for a hangar pool entry, with a safe fallback."""
    name = getattr(entry, "name", None)
    return name if name is not None else ""


def fleet_management_screen(main_player: ExpeditionShip, player_fleet):
    """Main fleet management UI.

    Displays the mothership preview, squad slots and an escort preview. The
    function renders a live view of the hangar (queried each frame) and
    returns `"to_game"` if the user requests returning to gameplay; otherwise
    it exits normally (None).
    """
    screen = pygame.display.get_surface()
    if screen is None:
        return

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    # ---------- COLORS / CONSTANTS TO MATCH INTERNAL SCREEN ----------
    # Fonts
    title_font = pygame.font.Font(None, 40)
    label_font = pygame.font.Font(None, 28)

    # ----------------- TITLE + NAV LAYOUT -----------------
    title_text = "FLEET CONFIGURATION"
    title_surf = title_font.render(title_text, True, UI_TITLE_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, UI_TOP_BAR_HEIGHT // 2 - 22))

    # Back arrow and close "X" at same height as in internal screen
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

    
    # ----------------- LAYOUT CONSTANTS (shared fleet preview geometry) -----------------
    fleet_layout = compute_fleet_preview_layout(width, height)
    left_center_x = fleet_layout["left_center_x"]
    mid_center_x = fleet_layout["mid_center_x"]
    ms_rect = fleet_layout["ms_rect"]
    circle_rects = fleet_layout["circle_rects"]
    fr_rect = fleet_layout["fr_rect"]
    previews_top = fleet_layout["previews_top"]
    circle_radius = fleet_layout.get("circle_radius", 30)
    circle_col_x = mid_center_x

    # vertical offset (pixels) to lower preview shapes and preview images
    PREVIEW_OFFSET_Y = 60

    # compute a reference Y for ship titles based on the first squad slot
    # (we'll align expedition and frigate titles to this Y so heights match)
    first_slot_name_height = label_font.size("M")[1]
    if fleet_layout.get("circle_rects"):
        ref_name_y = fleet_layout["circle_rects"][0].top - (first_slot_name_height + 6)
    else:
        ref_name_y = ms_rect.top - (first_slot_name_height + 6)

    running = True
    while running:
        # ------------- EVENTS -------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_arrow_hit_rect.collidepoint(event.pos):
                    running = False
                    continue
                if close_hit_rect.collidepoint(event.pos):
                    return "to_game"

                for idx, c_rect in enumerate(circle_rects):
                    # Create a hit rectangle that spans the title area above
                    # the slot and the lowered preview area below. This allows
                    # clicking anywhere in the visual squad card to open details.
                    name_height = label_font.size("M")[1]
                    # title is drawn at: title_y = c_rect.top - (name_height + 6)
                    title_y = c_rect.top - (name_height + 6)
                    preview_bottom = c_rect.bottom + PREVIEW_OFFSET_Y

                    # pad a few pixels above the title and below the preview
                    pad = 8
                    card_top = title_y - pad
                    card_bottom = preview_bottom + pad

                    card_left = c_rect.left - 140
                    card_right = c_rect.right + 140
                    card_rect = pygame.Rect(card_left, card_top, card_right - card_left, card_bottom - card_top)

                    if card_rect.collidepoint(event.pos):
                        # Open detailed squad card for this hangar slot.
                        from spacegame.screens.squad_detail import squad_detail_screen

                        res = squad_detail_screen(main_player, player_fleet, idx)
                        if res == "to_game":
                            return "to_game"
                        break

        # Rebuild a fresh snapshot of hangar state each frame (authoritative)
        assignments, ships, pool_by_id = _build_hangar_snapshot(main_player)

        # ------------- DRAW -------------
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
            screen.fill(UI_BG_COLOR)

        # Title
        screen.blit(title_surf, title_rect)

        # Back arrow - use image
        back_arrow_img = get_back_arrow_image()
        if back_arrow_img:
            arrow_size = 32
            arrow_scaled = pygame.transform.smoothscale(back_arrow_img, (arrow_size - 4, arrow_size - 4))
            arrow_draw_rect = arrow_scaled.get_rect(center=back_arrow_rect.center)
            screen.blit(arrow_scaled, arrow_draw_rect)

        # Close X
        screen.blit(close_surf, close_rect)

        # -------- Section titles + lines (CURRENT LOADOUT / SQUADS / ESCORTS) --------
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

        # LEFT: expedition ship preview and HP
        # Draw geometric hex behind the expedition preview (lowered)
        ms_center = (ms_rect.centerx, ms_rect.centery - 125)
        draw_hex(screen, ms_center, ms_rect.width * 0.9, ms_rect.height * 0.5, (80, 255, 190), 3)
        ms_surf = pygame.transform.smoothscale(preview_for_unit("expedition"), (ms_rect.width, ms_rect.height))
        ms_img_rect = ms_surf.get_rect(center=ms_center)
        screen.blit(ms_surf, ms_img_rect.topleft)
        # Expedition ship name: left-align above the preview, vertically aligned
        # to the first squad title (do not change squad title positions)
        ms_name = getattr(main_player, 'name', 'EXPEDITION SHIP')
        name_surf = label_font.render(ms_name, True, (220, 220, 255))
        name_x = ms_rect.left / 1.45
        name_y = ref_name_y
        screen.blit(name_surf, (name_x, name_y))
        # Tier icon drawn to the right of the ship name (same height)
        try:
            tier_val = int(main_player.get_tier())
        except Exception:
            tier_val = 0
        flag_w = 22
        flag_h = 22
        flag_x = name_x * 3.58
        flag_y = name_y + (name_surf.get_height() - flag_h) // 2
        flag_rect = pygame.Rect(flag_x, flag_y, flag_w, flag_h)
        draw_tier_icon_image(screen, flag_rect, tier_val)

        # MIDDLE: squad circles (assigned interceptors or empty)
        for i, c_rect in enumerate(circle_rects):
            cx, cy = c_rect.center
            # reset per-slot name variables so flags align to the correct name
            name_surf = None
            name_x = None
            name_y = None

            assigned_id = assignments[i] if 0 <= i < len(assignments) else None
            assigned_entry = (
                pool_by_id.get(assigned_id) if assigned_id is not None else None
            )
            if assigned_entry is not None and not _entry_is_alive(assigned_entry):
                assigned_entry = None

            if assigned_entry is not None:
                r = circle_radius - 4
                size = int(r * 2)
                # scale squad previews similarly to the frigate preview
                scale = 1.35
                scaled = int(size * scale)
                # choose preview image by unit_type
                unit_type = getattr(assigned_entry, "unit_type")
                # Draw geometric shape behind the preview depending on unit type (lowered, using scaled dims)
                slot_center = (cx, cy + PREVIEW_OFFSET_Y - 20)
                if unit_type == 'resource_collector':
                    # Slightly increase the dalton shape so collectors feel more
                    # visually prominent behind their preview image.
                    draw_dalton(screen, slot_center, scaled * 1.25, scaled * 1.65, (80, 255, 190), 2)
                elif unit_type == 'interceptor':
                    draw_triangle(screen, slot_center, scaled * 1.2, (80, 255, 190), 2)
                else:
                    draw_diamond(screen, slot_center, scaled * 1.2, scaled * 1.2, (80, 255, 190), 2)

                preview_img = preview_for_unit(unit_type)
                icpt_img = pygame.transform.smoothscale(preview_img, (scaled, scaled))
                img_rect = icpt_img.get_rect(center=slot_center)
                screen.blit(icpt_img, img_rect.topleft)

                # Ship name: left-align above the slot. Render single-line
                # even if the stored name contains newlines (replace with space).
                single_name = _entry_name(assigned_entry).replace("\n", " ")
                name_surf = label_font.render(single_name, True, (220, 220, 255))
                name_x = c_rect.left - 140
                name_y = c_rect.top - (name_surf.get_height() + 6)
                screen.blit(name_surf, (name_x, name_y))

                # Tier icon to the right of the name (same height)
                tier_val = int(getattr(assigned_entry, 'tier', 0))
                flag_w = 22
                flag_h = 22
                flag_x = name_x * 1.8
                flag_y = name_y + (name_surf.get_height() - flag_h) // 2
                flag_rect = pygame.Rect(flag_x, flag_y, flag_w, flag_h)
                draw_tier_icon_image(screen, flag_rect, tier_val)
            else:
                pygame.draw.circle(
                    screen, (230, 230, 230), (cx, cy), circle_radius, 2
                )
                pygame.draw.line(
                    screen, (230, 230, 230), (cx - 8, cy), (cx + 8, cy), 2
                )
                pygame.draw.line(
                    screen, (230, 230, 230), (cx, cy - 8), (cx, cy + 8), 2
                )

        if frigates:
            f = frigates[0]
            # Draw larger diamond behind frigate preview (rotated) and scale up preview image (lowered)
            scale = 1.35  # scale factor to make the frigate preview larger
            fr_center = (fr_rect.centerx, fr_rect.centery - 125)
            draw_diamond(screen, fr_center, fr_rect.height * scale, fr_rect.width / 1.2 * scale, (80, 255, 190), 3)
            fr_w = int(fr_rect.width * scale)
            fr_h = int(fr_rect.height * scale)
            fr_img = pygame.transform.smoothscale(preview_for_unit("frigate"), (fr_w, fr_h))
            # center the scaled preview on the lowered center so name/flag positions remain unchanged
            img_rect = fr_img.get_rect(center=fr_center)
            screen.blit(fr_img, img_rect.topleft)

            # Frigate name: left-align above the preview and match the first squad title height
            fr_name = getattr(f, 'name', 'SCOUTING FRIGATE')
            name_surf = label_font.render(fr_name, True, (220, 220, 255))
            name_x = fr_rect.left - 98
            name_y = ref_name_y
            screen.blit(name_surf, (name_x, name_y))

            # Tier icon to the right of the frigate name (same height)
            try:
                tier_val = int(f.get_tier())
            except Exception:
                tier_val = 0
            flag_w = 22
            flag_h = 22
            flag_x = name_x * 1.297
            flag_y = name_y + (name_surf.get_height() - flag_h) // 2
            flag_rect = pygame.Rect(flag_x, flag_y, flag_w, flag_h)
            draw_tier_icon_image(screen, flag_rect, tier_val)
        else:
            pygame.draw.rect(screen, (80, 80, 80), fr_rect, border_radius=10)

        pygame.display.flip()
        clock.tick(FPS)