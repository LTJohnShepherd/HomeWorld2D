"""UI helpers: small widgets, preview image helpers, and simple shape drawers.

This module exposes lightweight utilities used by the game's screens:
- `Button`: simple rectangular button with hover rendering and click detection.
- preview image loaders / scalers used across UI screens.
- small polygon drawing helpers (triangle, diamond, dalton kite, hex).

Keep the helpers minimal and free of game logic; they are intended
to be safe for import from any UI module.
"""

import pygame
from spacegame.config import PREVIEWS_DIR


class Button:
    """A simple rectangular button with hover color and left-click detection.

    The button is responsible for drawing itself and reporting click events.
    It intentionally does not manage callbacks — callers should call
    `handle_event` and react to a True return value.
    """

    def __init__(self, rect, text, font, base_color=(170, 170, 170), hover_color=(220, 220, 220), text_color=(0, 0, 0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color

    def draw(self, surface):
        """Render the button into `surface` and handle hover coloring."""
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        label = self.font.render(self.text, True, self.text_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def handle_event(self, event) -> bool:
        """Return True when the left mouse button is pressed over the button."""
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


# ---------- Shared preview images ----------
# Centralized here so multiple screens can reuse the same loaded surfaces.
EXPEDITION_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Carrier_T1_Preview.png")
FRIGATE_PREVIEW_IMG    = pygame.image.load(PREVIEWS_DIR + "/Frigate_Preview.png")
INTERCEPTOR_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Interceptor_Preview.png")
RESOURCE_COLLECTOR_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Resource_Collector_Preview.png")
OREM_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/RUOreM.png")
BOMBER_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Bomber_Preview.png")

# Map unit type keys to preview surfaces for easy lookup by UI code.
PREVIEW_IMAGE_MAP = {
    "expedition": EXPEDITION_PREVIEW_IMG,
    "frigate": FRIGATE_PREVIEW_IMG,
    "interceptor": INTERCEPTOR_PREVIEW_IMG,
    "resource_collector": RESOURCE_COLLECTOR_PREVIEW_IMG
    ,"plasma_bomber": BOMBER_PREVIEW_IMG
}


def preview_for_unit(unit_type: str, default: str = "interceptor"):
    """Return the preview surface for the given `unit_type` string.

    This centralizes the mapping so screens and UI widgets can simply
    call `preview_for_unit(entry.unit_type)` instead of importing many
    per-unit constants. If `unit_type` is unknown, the `default` key
    is used (defaults to `interceptor`).
    """
    if unit_type is None:
        unit_type = default
    return PREVIEW_IMAGE_MAP.get(unit_type, PREVIEW_IMAGE_MAP.get(default))


# Cache for scaled preview surfaces to avoid repeated smoothscale() calls.
_SCALED_PREVIEW_CACHE: dict = {}

def scaled_preview_for_unit(unit_type: str, size: tuple):
    """Return a scaled preview surface for `unit_type` at `size` (w,h).

    Results are cached in-module to avoid doing `smoothscale` every frame
    which can be a major source of lag when many cards are drawn.
    """
    if unit_type is None:
        unit_type = "interceptor"
    key = (unit_type, int(size[0]), int(size[1]))
    cached = _SCALED_PREVIEW_CACHE.get(key)
    if cached is not None:
        return cached
    base = preview_for_unit(unit_type, default="interceptor")
    try:
        surf = pygame.transform.smoothscale(base, (int(size[0]), int(size[1])))
    except Exception:
        # fallback to base surface
        surf = base.copy()
    _SCALED_PREVIEW_CACHE[key] = surf
    return surf

# ---------- Shape drawing helpers ----------
def draw_triangle(surface, center, size, color, thickness=2):
    cx, cy = int(center[0]), int(center[1])

    h = size * (3 ** 0.5) / 2  # height of an equilateral triangle

    left_tip     = (cx - 2 * h / 3, cy)
    top_right    = (cx + h / 3,     cy - size / 2)
    bottom_right = (cx + h / 3,     cy + size / 2)

    pygame.draw.polygon(surface, color, [top_right, bottom_right, left_tip], thickness)

def draw_diamond(surface, center, width, height, color, thickness=2):
    cx, cy = int(center[0]), int(center[1])
    hw = width * 0.5
    hh = height * 0.5

    points = [
        (cx,      cy - hh),  # top
        (cx + hw, cy),       # right
        (cx,      cy + hh),  # bottom
        (cx - hw, cy)        # left
    ]
    pygame.draw.polygon(surface, color, points, thickness)

def draw_dalton(surface, center, width, height, color, thickness=2):
    """Draw a vertically-oriented diamond (kite) with the long axis vertical.
    The polygon has four points: top, right, bottom, left. Call with a larger
    `height` than `width` to emphasize the downward point as in the reference image.
    """
    cx, cy = int(center[0]), int(center[1])
    hw = float(width) * 0.35

    # We'll make the kite slightly asymmetric: the top point is closer to
    # the center (shorter) and the bottom point extends farther down
    # (longer). These factors control that asymmetry visually.
    top_factor = 0.7   # top is 70% of the half-height above center
    bottom_factor = 1.2  # bottom is 120% of the half-height below center

    hh = float(height) * 0.5

    # Four-point kite: top (closer), right, bottom (longer), left
    points = [
        (cx,            cy - hh * top_factor),    # top (closer to center)
        (cx + hw,       cy),                       # right
        (cx,            cy + hh * bottom_factor),  # bottom (longer, points down)
        (cx - hw,       cy),                       # left
    ]

    # Draw outline (thickness>0) or filled (thickness==0)
    if thickness and thickness > 0:
        pygame.draw.polygon(surface, color, points, int(thickness))
    else:
        pygame.draw.polygon(surface, color, points)

def draw_hex(surface, center, width, height, color, thickness=2):
    cx, cy = int(center[0]), int(center[1])
    hw = width * 0.5
    hh = height * 0.5
    inset = hw * 0.3

    points = [
        (cx - hw + inset, cy - hh),
        (cx + hw - inset, cy - hh),
        (cx + hw,         cy),
        (cx + hw - inset, cy + hh),
        (cx - hw + inset, cy + hh),
        (cx - hw,         cy)
    ]
    pygame.draw.polygon(surface, color, points, thickness)

def draw_health_bar(surface, x, y, w, h, value, max_value):
    """Draw a small rectangular health bar on the given surface."""
    if max_value <= 0:
        return

    pct = max(0.0, min(1.0, float(value) / float(max_value)))

    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (40, 40, 40), bg_rect, border_radius=3)

    fill_w = int(w * pct + 0.5)
    if fill_w > 0:
        fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
        fill_rect = pygame.Rect(x, y, fill_w, h)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=3)

    pygame.draw.rect(surface, (10, 10, 10), bg_rect, 1, border_radius=3)

def draw_armor_bar(surface, x, y, w, h, value, max_value):
    """Draw a small rectangular armor bar (blue) under health bars."""
    if max_value <= 0:
        return

    pct = max(0.0, min(1.0, float(value) / float(max_value)))

    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (20, 40, 70), bg_rect, border_radius=3)

    fill_w = int(w * pct + 0.5)
    if fill_w > 0:
        fill_rect = pygame.Rect(x, y, fill_w, h)
        pygame.draw.rect(surface, (90, 190, 255), fill_rect, border_radius=3)

    pygame.draw.rect(surface, (10, 10, 10), bg_rect, 1, border_radius=3)


def draw_plus_circle(surface, center, radius, color, plus_size: int = 14, circle_thickness: int = 2, plus_thickness: int = 2):
    """Draw a circled plus icon: an outlined circle with a centered plus sign.

    - `center` is (x,y)
    - `radius` is the outer circle radius
    - `plus_size` controls half-length of plus arms
    - `circle_thickness` and `plus_thickness` control stroke widths
    """
    cx, cy = int(center[0]), int(center[1])
    pygame.draw.circle(surface, color, (cx, cy), int(radius), int(circle_thickness))
    # horizontal
    pygame.draw.line(surface, color, (cx - plus_size, cy), (cx + plus_size, cy), int(plus_thickness))
    # vertical
    pygame.draw.line(surface, color, (cx, cy - plus_size), (cx, cy + plus_size), int(plus_thickness))


def draw_corner_frame(surface, rect: pygame.Rect, color, corner_len: int = 18, corner_thick: int = 3, bottom_offset: int = 0):
    """Draw corner-only decorations on `rect`.

    `bottom_offset` moves the bottom corners upward by that many pixels (useful
    when you want the lower corners to sit above some content inside `rect`).
    """
    # top-left
    pygame.draw.line(surface, color, (rect.left, rect.top), (rect.left + corner_len, rect.top), corner_thick)
    pygame.draw.line(surface, color, (rect.left, rect.top), (rect.left, rect.top + corner_len), corner_thick)

    # top-right
    pygame.draw.line(surface, color, (rect.right - corner_len, rect.top), (rect.right, rect.top), corner_thick)
    pygame.draw.line(surface, color, (rect.right, rect.top), (rect.right, rect.top + corner_len), corner_thick)

    # compute adjusted bottom for bottom corners
    adjusted_bottom = rect.bottom - bottom_offset if bottom_offset else rect.bottom

    # bottom-left
    pygame.draw.line(surface, color, (rect.left, adjusted_bottom - corner_len), (rect.left, adjusted_bottom), corner_thick)
    pygame.draw.line(surface, color, (rect.left, adjusted_bottom), (rect.left + corner_len, adjusted_bottom), corner_thick)

    # bottom-right
    pygame.draw.line(surface, color, (rect.right - corner_len, adjusted_bottom), (rect.right, adjusted_bottom), corner_thick)
    pygame.draw.line(surface, color, (rect.right, adjusted_bottom - corner_len), (rect.right, adjusted_bottom), corner_thick)


def draw_multiline_text(surface, text: str, font: pygame.font.Font, color, topleft: tuple, line_spacing: int = 2):
    """Render `text` which may contain '\n' into successive lines starting at `topleft`.

    The first line is drawn at `topleft` (same starting height as previous single-line calls).
    Subsequent lines are drawn below using `font.get_height() + line_spacing` as the step.
    """
    if text is None:
        return
    lines = str(text).split("\n")
    x, y = topleft
    lh = font.get_height()
    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y + i * (lh + line_spacing)))


def draw_power_icon(surface, topleft: tuple, size: int = 20, color=(200, 200, 220)):
    """Draw a small lightning-bolt style power icon inside a box starting at `topleft`.

    The icon is drawn as a filled polygon scaled to `size`.
    """
    x0, y0 = int(topleft[0]), int(topleft[1])
    w = int(size)
    h = int(round(size * 1.2))

    # Normalized bolt shape points (percent of w/h).
    rel = [
        (0.15, 0.00),
        (0.55, 0.00),
        (0.35, 0.48),
        (0.85, 0.48),
        (0.25, 1.00),
        (0.45, 0.52),
        (0.15, 0.52),
    ]

    pts = [(x0 + int(px * w), y0 + int(py * h)) for (px, py) in rel]
    try:
        pygame.draw.polygon(surface, color, pts)
    except Exception:
        # fallback: draw a small circle if polygon failed
        pygame.draw.circle(surface, color, (x0 + w // 2, y0 + h // 2), max(2, w // 3))