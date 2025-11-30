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