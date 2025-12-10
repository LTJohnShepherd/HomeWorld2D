import pygame
from typing import List


def generate_slot_rects(idx_rect_base: pygame.Rect, count: int, v_spacing: int) -> List[pygame.Rect]:
    """Return a list of rects stacked vertically starting from idx_rect_base.

    Keeps the same width/height as idx_rect_base and stacks each subsequent
    rect by `v_spacing` pixels.
    """
    if count <= 0:
        return [idx_rect_base]
    rects = [pygame.Rect(idx_rect_base.left, idx_rect_base.top + i * v_spacing, idx_rect_base.width, idx_rect_base.height) for i in range(count)]
    return rects


def draw_index_square(screen: pygame.Surface, rect: pygame.Rect, label: str, selected: bool,
                      underline_color, text_selected_color, corner_len: int = 18, corner_thick: int = 3,
                      index_font: pygame.font.Font | None = None) -> None:
    """Draw the corner-only index square with centered index label.

    Colors are provided so callers can use their UI constants.
    """
    corner_color = underline_color if selected else text_selected_color

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

    if index_font is None:
        index_font = pygame.font.Font(None, 36)
    idx_text = index_font.render(label, True, corner_color)
    it_rect = idx_text.get_rect(center=rect.center)
    screen.blit(idx_text, it_rect)


def draw_slot_progress(screen: pygame.Surface, rect: pygame.Rect, progress: float,
                       pb_margin: int = 12, progress_color=(255, 160, 40), bg_color=(40, 50, 70)) -> None:
    """Draw a thin progress bar anchored to the bottom of `rect`.

    Progress is a float in [0.0, 1.0]. If <= 0, only the background bar is drawn.
    """
    pb_rect = pygame.Rect(
        rect.left + pb_margin,
        rect.bottom - 22,
        rect.width - pb_margin * 2,
        12,
    )
    pygame.draw.rect(screen, bg_color, pb_rect)
    if progress is None:
        return
    p = float(progress)
    if p <= 0.0:
        return
    inner_w = max(2, int(pb_rect.width * max(0.0, min(1.0, p))))
    inner_rect = pygame.Rect(pb_rect.left, pb_rect.top, inner_w, pb_rect.height)
    pygame.draw.rect(screen, progress_color, inner_rect)


def make_card_rect(width: int, height: int, content_top: int, left_shift: int = 20, left_margin: int = 40, frac: float = 0.38, height_frac: float = 0.64) -> pygame.Rect:
    """Compute a left-side card rect used across fabrication screens.

    - `frac` controls the width fraction of the card relative to `width`.
    - `height_frac` controls the card height relative to `height`.
    Returns a pygame.Rect.
    """
    card_x = left_margin - left_shift
    card_y = content_top
    card_w = int(width * frac)
    card_h = int(height * height_frac)
    return pygame.Rect(card_x, card_y, card_w, card_h)


def compute_idx_rect_base(card_rect: pygame.Rect, idx_size: int = 96, left_offset: int = 16, top_offset: int = 16) -> pygame.Rect:
    """Return the base index-rect placed inside `card_rect` with given padding."""
    return pygame.Rect(card_rect.left + left_offset, card_rect.top + top_offset, idx_size, idx_size)
