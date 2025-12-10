"""Fleet preview drawing helpers.

Contains small utilities used by fleet-related screens for consistent
visuals (tier icons, section headers and preview layout geometry).
"""

import pygame
from spacegame.config import UI_ICON_BLUE, UI_ICON_WHITE


def tier_to_roman(tier_value: int) -> str:
    """Convert a numeric tier into a short Roman-like label.

    The function returns a compact label used in tier badges. For values
    beyond supported numerals it appends a `+N` suffix (e.g. "III+2").
    """
    if tier_value <= 0:
        return "0"
    numerals = ["", "I", "II", "III"]
    if tier_value < len(numerals):
        return numerals[tier_value]
    return numerals[-1] + f"+{tier_value - (len(numerals) - 1)}"


def draw_tier_icon(surface: pygame.Surface, host_rect: pygame.Rect, tier_value: int) -> None:
    """Draw a small tier badge in the top-right corner of `host_rect`.

    The badge contains a Roman-like numeral produced by `tier_to_roman`.
    This helper ensures the same visual is used across fleet-related UIs.
    """
    large_tier_font = pygame.font.Font(None, 26)

    flag_w = 22
    flag_h = 22
    flag_rect = pygame.Rect(host_rect.right - flag_w - 1, host_rect.top + 1, flag_w, flag_h)

    pygame.draw.rect(surface, UI_ICON_BLUE, flag_rect)

    text = tier_to_roman(int(tier_value))
    tier_text = large_tier_font.render(text, True, UI_ICON_WHITE)
    tier_text_rect = tier_text.get_rect(center=flag_rect.center)
    surface.blit(tier_text, tier_text_rect)


def draw_fleet_section_titles(
    surface: pygame.Surface,
    title_rect: pygame.Rect,
    label_font: pygame.font.Font,
    title_color,
    nav_line_color,
    previews_top: int,
    left_center_x: int,
    circle_col_x: int,
    fr_center_x: int,
    total_slots: int,
    equipped_slots: int,
    frigates_count: int,
    alive_frigates_count: int,
    nav_center_y: int = None,
) -> None:
    """
    Draw the three section headers and their underlines:

      CURRENT LOADOUT   |   SQUADS: x / y   |   ESCORTS: a / b

    This preserves the layout math used in fleet screens so visuals remain
    consistent across `fleet_management.py` and `squad_detail.py`.
    """
    fleet_title_bottom = title_rect.bottom
    label_height = label_font.size("M")[1]

    # If a navigation center Y is provided, align the labels' vertical center
    # to that Y so they sit on the same row as the back/close buttons.
    if nav_center_y is not None:
        labels_y = int(nav_center_y - (label_height // 2))
    else:
        # Fallback: compute labels_y using existing layout proportions.
        labels_y = fleet_title_bottom + (previews_top - fleet_title_bottom - label_height) // 7.1

    # line_margin tuned to visually balance underline spacing with label height
    line_margin = int(label_height * 15 / 19.5)

    # LEFT: CURRENT LOADOUT
    current_surf = label_font.render("CURRENT LOADOUT", True, nav_line_color)
    current_rect = current_surf.get_rect()
    current_rect.centerx = left_center_x
    current_rect.y = labels_y

    pygame.draw.line(
        surface,
        nav_line_color,
        (current_rect.left, current_rect.top - line_margin),
        (current_rect.right * 1.4, current_rect.top - line_margin),
        1,
    )
    pygame.draw.line(
        surface,
        nav_line_color,
        (current_rect.left, current_rect.bottom + line_margin),
        (current_rect.right * 1.4, current_rect.bottom + line_margin),
        1,
    )
    surface.blit(current_surf, current_rect)

    # MIDDLE: SQUADS
    if total_slots > 0:
        squads_text = f"SQUADS: {equipped_slots} / {total_slots}"
    else:
        squads_text = "SQUADS: 0 / 0"

    squads_surf = label_font.render(squads_text, True, title_color)
    squads_rect = squads_surf.get_rect()
    squads_rect.centerx = circle_col_x / 1.2
    squads_rect.y = labels_y

    pygame.draw.line(
        surface,
        nav_line_color,
        (squads_rect.left, squads_rect.top - line_margin),
        (squads_rect.right * 1.45, squads_rect.top - line_margin),
        1,
    )
    pygame.draw.line(
        surface,
        nav_line_color,
        (squads_rect.left, squads_rect.bottom + line_margin),
        (squads_rect.right * 1.45, squads_rect.bottom + line_margin),
        1,
    )
    surface.blit(squads_surf, squads_rect)

    # RIGHT: ESCORTS
    if frigates_count:
        escorts_text = f"ESCORTS: {alive_frigates_count} / {frigates_count}"
    else:
        escorts_text = "ESCORTS: 0 / 0"

    escorts_surf = label_font.render(escorts_text, True, title_color)
    escorts_rect = escorts_surf.get_rect()
    escorts_rect.centerx = fr_center_x / 1.1
    escorts_rect.y = labels_y

    pygame.draw.line(
        surface,
        nav_line_color,
        (escorts_rect.left, escorts_rect.top - line_margin),
        (escorts_rect.right * 1.14, escorts_rect.top - line_margin),
        1,
    )
    pygame.draw.line(
        surface,
        nav_line_color,
        (escorts_rect.left, escorts_rect.bottom + line_margin),
        (escorts_rect.right * 1.14, escorts_rect.bottom + line_margin),
        1,
    )
    surface.blit(escorts_surf, escorts_rect)


def compute_fleet_preview_layout(width, height):
    """Return geometry for expedition ship, interceptor slots and frigate preview.

    This matches the layout used in the fleet-related screens so the visuals
    stay in sync between them.
    """
    ROW_CENTER_Y = height // 2
    COLUMN_SPACING_X = width // 3

    center_x = width // 2
    left_center_x = center_x - COLUMN_SPACING_X
    mid_center_x = center_x
    right_center_x = center_x + COLUMN_SPACING_X

    # Expedition ship (left)
    ms_w, ms_h = 170, 160
    ms_rect = pygame.Rect(0, 0, ms_w, ms_h)
    SHIP_OFFSET_X = 40  # ship offset to the right
    ms_rect.center = (left_center_x + SHIP_OFFSET_X, ROW_CENTER_Y)

    # Light crafts column (middle)
    circle_radius = 30
    # the bottom of a preview image and the title of the next squad
    circle_spacing = 200
    circle_rects = []
    circle_col_x = mid_center_x
    circle_top_y = ROW_CENTER_Y - circle_spacing
    for i in range(3):
        cx = circle_col_x
        cy = circle_top_y + i * circle_spacing
        rect = pygame.Rect(0, 0, circle_radius * 2, circle_radius * 2)
        rect.center = (cx, cy)
        circle_rects.append(rect)

    # Escort frigate preview (right)
    fr_w, fr_h = 140, 70
    fr_rect = pygame.Rect(0, 0, fr_w, fr_h)
    fr_rect.center = (right_center_x, ROW_CENTER_Y)

    previews_top = min(ms_rect.top, circle_rects[0].top, fr_rect.top)

    return {
        "ROW_CENTER_Y": ROW_CENTER_Y,
        "COLUMN_SPACING_X": COLUMN_SPACING_X,
        "left_center_x": left_center_x,
        "mid_center_x": mid_center_x,
        "right_center_x": right_center_x,
        "ms_rect": ms_rect,
        "circle_rects": circle_rects,
        "fr_rect": fr_rect,
        "previews_top": previews_top,
        "circle_radius": circle_radius,
    }

