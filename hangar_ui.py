import pygame
from fleet_unit import Frigate


def draw_triangle(surface, center, width, height, color, thickness=2):
    # Same helper as in gameScreen.py
    size = width
    cx, cy = int(center[0]), int(center[1])

    h = size * (3 ** 0.5) / 2

    left_tip     = (cx - 2 * h / 3, cy)
    top_right    = (cx + h / 3,     cy - size / 2)
    bottom_right = (cx + h / 3,     cy + size / 2)

    pygame.draw.polygon(surface, color, [top_right, bottom_right, left_tip], thickness)


def draw_diamond(surface, center, width, height, color, thickness=2):
    # Same shape logic as in gameScreen (just scaled)
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
    # Same helper as in gameScreen.py
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


class HangarUI:
    """Manages hangar light craft previews and deploy/recall buttons for the main ship."""

    def __init__(self, font, preview_size=40):
        self.font = font
        self.preview_size = preview_size

        # --- Unified preview row layout ---
        row_y = 565

        # --- ExpeditionShip preview (bigger, on the left) ---
        self.expeditionship_preview = {
            'preview_position': pygame.Vector2(60, row_y),
            'width': 80,
            'height': 50,
        }

        # --- Frigate preview (between ExpeditionShip and interceptors) ---
        self.frigate_preview = {
            'preview_position': pygame.Vector2(170, row_y),
            'width': 60,
            'height': 35,
        }

        # --- 3 interceptor previews, evenly spaced to the right of the ExpeditionShip ---
        self.hangar_slots = [
            {'preview_position': pygame.Vector2(260, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(360, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(460, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
        ]

    def handle_mouse_button_down(self, mouse_pos, main_player, player_shapes):
        """Process a left mouse button click. Returns True if the click was consumed by the hangar UI."""
        clicked_ui = False

        # Check deploy / recall buttons
        for i, hangar_slot in enumerate(self.hangar_slots):
            if hangar_slot['show_button'] and hangar_slot['button_rect'].collidepoint(mouse_pos):
                if main_player.hangar[i]:
                    # DEPLOY
                    if main_player.can_deploy(i):
                        new_fighter = main_player.deploy(i)
                        if new_fighter:
                            player_shapes.append(new_fighter)
                else:
                    # RECALL
                    icpts = getattr(main_player, 'hangar_ships', [None, None, None])
                    fighter_ship = icpts[i] if i < len(icpts) else None
                    if fighter_ship is not None and fighter_ship in player_shapes and fighter_ship.health > 0.0:
                        fighter_ship.recalling = True
                        fighter_ship.selected = False  # stop being commanded by the player

                hangar_slot['show_button'] = False  # hide button after click
                clicked_ui = True
                break

        # Check mini previews
        if not clicked_ui:
            for i, hangar_slot in enumerate(self.hangar_slots):
                preview_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - self.preview_size // 2,
                    hangar_slot['preview_position'].y - self.preview_size // 2,
                    self.preview_size, self.preview_size,
                )
                if preview_rect.collidepoint(mouse_pos):
                    # Toggle deploy/recall button visibility above this preview
                    hangar_slot['show_button'] = not hangar_slot['show_button']
                    clicked_ui = True
                    break

        return clicked_ui

    def close_all_previews(self):
        for slot in self.hangar_slots:
            slot['show_button'] = False

    def draw(self, screen, main_player, player_shapes):
        """Draw hangar previews, health bars, and active deploy/recall buttons."""
        preview_size = self.preview_size
        font = self.font
        
        # --- Draw ExpeditionShip preview (rectangle + hex overlay) ---
        ms_center = self.expeditionship_preview['preview_position']
        ms_w = self.expeditionship_preview['width']
        ms_h = self.expeditionship_preview['height']

        ms_surf = pygame.Surface((ms_w, ms_h), pygame.SRCALPHA)
        pygame.draw.rect(ms_surf, main_player.color, pygame.Rect(0, 0, ms_w, ms_h), border_radius=4)

        ms_x = int(ms_center.x - ms_w / 2)
        ms_y = int(ms_center.y - ms_h / 2)
        screen.blit(ms_surf, (ms_x, ms_y))

        # Hex overlay, scaled similarly to gameScreen (relative to ship size)
        hex_w = ms_w * 0.875   # 70/80 like in gameScreen
        hex_h = ms_h * 0.8     # 32/40
        draw_hex(
            screen,
            (ms_center.x, ms_center.y),
            hex_w,
            hex_h,
            (80, 255, 190),
            3
        )

        # --- ExpeditionShip health bar BELOW the preview ---
        bar_w = ms_w
        bar_h = 5
        pad = 4
        bar_x = ms_x
        bar_y = ms_y + ms_h + pad

        pct = 0.0
        if main_player.max_health > 0:
            pct = max(0.0, min(1.0, main_player.health / main_player.max_health))

        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

        fill_w = int(bar_w * pct + 0.5)
        if fill_w > 0:
            fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)

        pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1, border_radius=3)

        # ---------------------------------------------------------
        # --- Frigate preview (rectangle + diamond overlay) ---
        frigate = None
        for s in player_shapes:
            if isinstance(s, Frigate):
                frigate = s
                break

        if frigate is not None and frigate.health > 0.0:
            fr_center = self.frigate_preview['preview_position']
            fr_w = self.frigate_preview['width']
            fr_h = self.frigate_preview['height']

            fr_surf = pygame.Surface((fr_w, fr_h), pygame.SRCALPHA)
            pygame.draw.rect(fr_surf, frigate.color, pygame.Rect(0, 0, fr_w, fr_h), border_radius=4)

            fr_x = int(fr_center.x - fr_w / 2)
            fr_y = int(fr_center.y - fr_h / 2)
            screen.blit(fr_surf, (fr_x, fr_y))

            # Diamond overlay, scaled with same proportions as in gameScreen
            draw_diamond(
                screen,
                (fr_center.x, fr_center.y),
                fr_w * 0.6,
                fr_h * 1.4,
                (80, 255, 190),
                2
            )

            # Frigate health bar BELOW the preview
            bar_w = fr_w
            bar_h = 5
            pad = 10
            bar_x = fr_x
            bar_y = fr_y + fr_h + pad

            pct = 0.0
            if frigate.max_health > 0:
                pct = max(0.0, min(1.0, frigate.health / frigate.max_health))

            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

            fill_w = int(bar_w * pct + 0.5)
            if fill_w > 0:
                fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
                fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
                pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)

            pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1, border_radius=3)

        # ---------------------------------------------------------
        # --- Draw hangar previews & deploy/recall buttons ---
        for i, hangar_slot in enumerate(self.hangar_slots):
            icpt_surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)

            # figure out which light craft (if any) is linked to this slot
            icpts = getattr(main_player, 'hangar_ships', [None, None, None])
            fighter_ship = icpts[i] if i < len(icpts) else None

            # If this slot has neither an interceptor in hangar nor a live one deployed,
            # do not show a preview at all (this lets you have 0/1/2/3 previews).
            fighter_alive = (
                fighter_ship is not None and
                fighter_ship in player_shapes and
                fighter_ship.health > 0.0
            )
            if not main_player.hangar[i] and not fighter_alive:
                hangar_slot['show_button'] = False
                continue

            if main_player.hangar[i]:
                # In hangar: show grey light craft (available for deployment)
                color = (120, 120, 120)
            else:
                # Deployed: show real color while alive
                color = fighter_ship.color if fighter_alive else (60, 60, 60)

            pygame.draw.polygon(
                icpt_surf,
                color,
                [(preview_size // 2, 0), (0, preview_size), (preview_size, preview_size)],
            )

            preview_x = hangar_slot['preview_position'].x - preview_size // 2
            preview_y = hangar_slot['preview_position'].y - preview_size // 2
            screen.blit(icpt_surf, (preview_x, preview_y))

            # Triangle overlay over interceptor preview, like in gameScreen
            icpt_center = (
                hangar_slot['preview_position'].x,
                hangar_slot['preview_position'].y
            )
            draw_triangle(
                screen,
                icpt_center,
                preview_size * 1.2,
                preview_size * 1.0,
                (80, 255, 190),
                2
            )

            # Health bar under preview when deployed and alive
            if fighter_alive:
                bar_w = preview_size
                bar_h = 5
                pad = 4
                bar_x = preview_x
                bar_y = preview_y + preview_size + pad

                pct = fighter_ship.health / fighter_ship.max_health if fighter_ship.max_health > 0 else 0.0
                pct = max(0.0, min(1.0, pct))
                fill_w = int(bar_w * pct + 0.5)

                bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
                pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

                if fill_w > 0:
                    fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
                    fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
                    pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)

                pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1, border_radius=3)

            # Draw deploy/recall button above preview if active
            if hangar_slot['show_button']:
                btn_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - 40,
                    hangar_slot['preview_position'].y - 65,
                    80, 25,
                )
                hangar_slot['button_rect'] = btn_rect

                if main_player.hangar[i]:
                    # light craft still in hangar
                    btn_color = (40, 160, 40)
                    label = 'Deploy'
                else:
                    # light craft already deployed
                    btn_color = (180, 40, 40)
                    label = 'Recall'

                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)
                pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=6)
                text = font.render(label, True, (255, 255, 255))
                screen.blit(text, (btn_rect.x + 10, btn_rect.y + 3))