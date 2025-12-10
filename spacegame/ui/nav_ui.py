"""Navigation tab helpers used by UI screens.

Provides `create_tab_entries` for layout metadata and `draw_tabs` for
rendering the tab row. Keep these helpers simple and free of game logic.
"""

import pygame
from typing import List, Tuple
from spacegame.config import (
    UI_TAB_HEIGHT,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_TEXT_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_TAB_UNDERLINE_COLOR,
)


def create_tab_entries(tab_labels: List[str], tab_font: pygame.font.Font, width: int,
                       top_bar_height: int = UI_TOP_BAR_HEIGHT,
                       ui_tab_height: int = UI_TAB_HEIGHT) -> Tuple[List[dict], int]:
    """Create tab entry metadata (text surf, width, rect placeholder).

    Returns (tab_entries, tabs_y).
    """
    tab_spacing = 16
    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    tab_entries = []
    total_tabs_width = -tab_spacing
    for label in tab_labels:
        text_surf = tab_font.render(label, True, UI_TAB_TEXT_COLOR)
        text_width = text_surf.get_width()
        tab_width = icon_size + ICON_MARGIN + text_width + H_PADDING * 2
        tab_entries.append({"label": label, "text_surf": text_surf, "width": tab_width})
        total_tabs_width += tab_width + tab_spacing

    tabs_y = top_bar_height - ui_tab_height - 4
    tabs_left = width // 2 - total_tabs_width // 2

    # assign rects for each computed tab entry
    x = tabs_left
    for entry in tab_entries:
        rect = pygame.Rect(x, tabs_y, entry["width"], ui_tab_height)
        entry["rect"] = rect
        x += entry["width"] + tab_spacing

    return tab_entries, tabs_y


def draw_tabs(screen: pygame.Surface, tab_entries: List[dict], selected_tab: int, tabs_y: int, width: int, tab_font: pygame.font.Font) -> Tuple[int, int]:
    """Draw the tab icons/text and selected underlines.

    Returns (nav_top_y, nav_bottom_y).
    """
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

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

    return nav_top_y, nav_bottom_y
