import pygame
from spacegame.config import PREVIEWS_DIR

# ---------- UI helpers ----------
class Button:
    """Simple rectangular button with hover color and click handling."""

    def __init__(self, rect, text, font, base_color=(170,170,170), hover_color=(220,220,220), text_color=(0,0,0)):
        self.rect = pygame.Rect(rect) #pygame.Rect(left, top, width, height) , rect is a tupple with those values, pygame.Rect() create a Rect object for the button (stores position and size)
        self.text = text #text for the button
        self.font = font
        self.base_color = base_color # the color of the button
        self.hover_color = hover_color # the color of the button when you hover on it with the mouse.
        self.text_color = text_color 

    def draw(self, surface):# surface: the screen you want to draw on

        mouse_pos = pygame.mouse.get_pos() #position of the mouse on the screen

        if self.rect.collidepoint(mouse_pos): # set button color depending on mouse hover
            color = self.hover_color
        else:
            color = self.base_color

        pygame.draw.rect(surface, color, self.rect, border_radius=12) # pygame.draw.rect(surface, color, rect (object), width=0, border_radius=0)
        
        label = self.font.render(self.text, True, self.text_color) # render the button text into a new surface (text becomes an image that can be drawn)
        
        label_rect = label.get_rect(center=self.rect.center) # create a Rect for the text surface and center it inside the button's rectangle
        
        surface.blit(label, label_rect) # draw (blit) the rendered text onto the target surface at the calculated position

    # Handle mouse click events: returns True if the left mouse button was pressed
    # while the cursor is positioned over the button; otherwise returns False.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


# ---------- Shared preview images ----------
# Centralized here so multiple screens can reuse the same loaded surfaces.
EXPEDITION_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Carrier_T1_Preview.png")
FRIGATE_PREVIEW_IMG    = pygame.image.load(PREVIEWS_DIR + "/Frigate_Preview.png")
INTERCEPTOR_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Interceptor_Preview.png")
RESOURCE_COLLECTOR_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/Resource_Collector_Preview.png")
OREM_PREVIEW_IMG = pygame.image.load(PREVIEWS_DIR + "/RUOreM.png")

# Map unit type keys to preview surfaces for easy lookup by UI code.
PREVIEW_IMAGE_MAP = {
    "expedition": EXPEDITION_PREVIEW_IMG,
    "frigate": FRIGATE_PREVIEW_IMG,
    "interceptor": INTERCEPTOR_PREVIEW_IMG,
    "resource_collector": RESOURCE_COLLECTOR_PREVIEW_IMG
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