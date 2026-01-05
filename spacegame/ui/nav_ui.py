"""Navigation tab helpers used by UI screens.

Provides `create_tab_entries` for layout metadata and `draw_tabs` for
rendering the tab row with icons. Keep these helpers simple and free of game logic.
"""

import pygame
from typing import List, Tuple, Dict, Optional
from spacegame.config import (
    UI_TAB_HEIGHT,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_TEXT_COLOR,
    UI_TAB_TEXT_SELECTED,
    UI_TAB_UNDERLINE_COLOR,
    PREVIEWS_DIR,
)

_icon_cache: Dict[str, pygame.Surface] = {}
_back_arrow_img: Optional[pygame.Surface] = None


def _load_icon(icon_filename: str) -> Optional[pygame.Surface]:
    """Load and cache an icon image from the previews folder."""
    if icon_filename not in _icon_cache:
        try:
            path = f"{PREVIEWS_DIR}/{icon_filename}"
            img = pygame.image.load(path).convert_alpha()
            _icon_cache[icon_filename] = img
        except Exception:
            return None
    return _icon_cache.get(icon_filename)


def get_back_arrow_image() -> Optional[pygame.Surface]:
    """Load and cache the back arrow image."""
    global _back_arrow_img
    if _back_arrow_img is None:
        _back_arrow_img = _load_icon("BackArrow.png")
    return _back_arrow_img


def create_tab_entries(tab_labels: List[str], tab_font: pygame.font.Font, width: int,
                       top_bar_height: int = UI_TOP_BAR_HEIGHT,
                       ui_tab_height: int = UI_TAB_HEIGHT,
                       icon_filenames: Optional[List[str]] = None) -> Tuple[List[dict], int]:
    """Create tab entry metadata (text surf, width, rect placeholder).

    icon_filenames: optional list of icon filenames to display next to each tab.
    Returns (tab_entries, tabs_y).
    """
    tab_spacing = 16
    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    tab_entries = []
    total_tabs_width = -tab_spacing
    for idx, label in enumerate(tab_labels):
        text_surf = tab_font.render(label, True, UI_TAB_TEXT_COLOR)
        text_width = text_surf.get_width()
        tab_width = icon_size + ICON_MARGIN + text_width + H_PADDING * 2
        
        icon_filename = None
        icon_surf = None
        if icon_filenames and idx < len(icon_filenames):
            icon_filename = icon_filenames[idx]
            icon_surf = _load_icon(icon_filename)
        
        tab_entries.append({
            "label": label,
            "text_surf": text_surf,
            "width": tab_width,
            "icon_filename": icon_filename,
            "icon_surf": icon_surf,
        })
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


def draw_tabs(screen: pygame.Surface, tab_entries: List[dict], selected_tab: int, tabs_y: int, width: int, tab_font: pygame.font.Font, disabled_labels: set | None = None) -> Tuple[int, int]:
    """Draw the tab icons/text and selected underlines.

    Returns (nav_top_y, nav_bottom_y).
    """
    nav_top_y = tabs_y - 6
    nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

    icon_size = 24
    ICON_MARGIN = 10
    H_PADDING = 24

    disabled_labels = disabled_labels or set()
    for idx, entry in enumerate(tab_entries):
        rect = entry["rect"]
        is_selected = idx == selected_tab
        is_disabled = entry.get("label") in disabled_labels

        icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
        icon_rect.centery = rect.centery
        icon_rect.left = rect.left + H_PADDING
        # Icon background: selected / normal / disabled
        icon_bg = (210, 220, 235) if is_selected else ((150, 165, 180) if is_disabled else (170, 190, 210))
        pygame.draw.rect(
            screen,
            icon_bg,
            icon_rect,
            border_radius=4,
            width=2,
        )

        # Draw icon if available
        icon_surf = entry.get("icon_surf")
        if icon_surf:
            icon_scaled = pygame.transform.smoothscale(icon_surf, (icon_size - 8, icon_size - 8))
            icon_draw_rect = icon_scaled.get_rect(center=icon_rect.center)
            screen.blit(icon_scaled, icon_draw_rect)

        # Disabled tabs use a muted text color
        if is_disabled:
            text_color = (140, 150, 160)
        else:
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
