import sys
import pygame
from spacegame.ui.ui import Button, draw_health_bar, draw_armor_bar
from spacegame.config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    UI_BG_COLOR, 
    UI_TAB_HEIGHT, 
    UI_SECTION_BASE_COLOR, 
    UI_SECTION_HOVER_COLOR,
    UI_SECTION_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR
    )
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs


def internal_screen(main_player, player_fleet):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    section_font = pygame.font.Font(None, 26)
    close_font = pygame.font.Font(None, 40)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "INTERNAL"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Back arrow (left)
    arrow_size = 32
    back_arrow_rect = pygame.Rect(0, 0, arrow_size, arrow_size)
    back_arrow_rect.center = (40, TOP_BAR_HEIGHT // 1.3)

    # Close "X" (right)
    close_surf = close_font.render("X", True, (255, 160, 40))
    close_rect = close_surf.get_rect()
    close_rect.center = (width - 40, TOP_BAR_HEIGHT // 1.25)
    close_hit_rect = close_rect.inflate(16, 16)

    # ---------- TABS ----------
    tab_labels = ["EXTERNAL", "INTERNAL", "FLEET CONFIGURATION"]
    selected_tab = 1  # INTERNAL initially selected

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT)

    # ---------- SECTION BUTTONS ----------
    section_width = int(width * 0.32)
    section_height = 56

    def centered_rect(cx, cy):
        return pygame.Rect(
            cx - section_width // 2,
            cy - section_height // 2,
            section_width,
            section_height,
        )

    # Positions adjusted
    row1_y = int(height * 0.38)
    row2_y = int(height * 0.66)
    left_x = int(width * 0.26)
    right_x = int(width * 0.70)

    storage_center = (left_x, row1_y)
    bridge_center = (right_x, row1_y)
    fabrication_center = (left_x, row2_y)
    refining_center = (right_x, row2_y)

    storage_btn = Button(
        centered_rect(*storage_center),
        "STORAGE",
        section_font,
        base_color=UI_SECTION_BASE_COLOR,
        hover_color=UI_SECTION_HOVER_COLOR,
        text_color=UI_SECTION_TEXT_COLOR,
    )
    bridge_btn = Button(
        centered_rect(*bridge_center),
        "BRIDGE",
        section_font,
        base_color=UI_SECTION_BASE_COLOR,
        hover_color=UI_SECTION_HOVER_COLOR,
        text_color=UI_SECTION_TEXT_COLOR,
    )
    fabrication_btn = Button(
        centered_rect(*fabrication_center),
        "FABRICATION",
        section_font,
        base_color=UI_SECTION_BASE_COLOR,
        hover_color=UI_SECTION_HOVER_COLOR,
        text_color=UI_SECTION_TEXT_COLOR,
    )
    refining_btn = Button(
        centered_rect(*refining_center),
        "REFINING",
        section_font,
        base_color=UI_SECTION_BASE_COLOR,
        hover_color=UI_SECTION_HOVER_COLOR,
        text_color=UI_SECTION_TEXT_COLOR,
    )

    section_buttons = [
        ("STORAGE", storage_btn),
        ("BRIDGE", bridge_btn),
        ("FABRICATION", fabrication_btn),
        ("REFINING", refining_btn),
    ]

    # ---------- HEALTH BAR ----------
    health_bar_width = int(width * 0.80)
    health_bar_height = 14
    health_bar_x = (width - health_bar_width) // 2
    health_bar_y = height - 46

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        if entry["label"] == "FLEET CONFIGURATION":
                            from spacegame.screens.fleet_management import (
                                fleet_management_screen
                            )

                            res = fleet_management_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # reset highlight back to INTERNAL after returning
                            selected_tab = 1
                        else:
                            selected_tab = idx
                        break

                for name, btn in section_buttons:
                    if btn.handle_event(event):
                        if name == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen
                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # "to_internal" or None: stay in internal screen loop, don't return
                        if name == "FABRICATION":
                            from spacegame.screens.fabrication_main_screen import fabrication_main_screen
                            res = fabrication_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"

        # ---------- DRAW ----------
        screen.fill(UI_BG_COLOR)

        # Nav band coordinates
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6

        # Brighter strip behind all nav text/buttons
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        # Lines above and below the nav/tab area
        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # Title (on top of nav background)
        screen.blit(title_surf, title_rect)

        # Back arrow (on top of nav background)
        arrow_color = (220, 235, 255)
        arrow_points = [
            (back_arrow_rect.left, back_arrow_rect.centery),
            (back_arrow_rect.right, back_arrow_rect.top),
            (back_arrow_rect.right, back_arrow_rect.bottom),
        ]
        pygame.draw.polygon(screen, arrow_color, arrow_points)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (draw using shared nav helper)
        nav_top_y, nav_bottom_y = draw_tabs(screen, tab_entries, selected_tab, tabs_y, width, tab_font)

        # Section buttons + larger icon squares with internal geometry
        ICON_BOX_SIZE = 34
        for name, btn in section_buttons:
            btn.draw(screen)

            icon_box_rect = pygame.Rect(
                btn.rect.left + 22,
                btn.rect.centery - ICON_BOX_SIZE // 2,
                ICON_BOX_SIZE,
                ICON_BOX_SIZE,
            )
            pygame.draw.rect(
                screen,
                UI_SECTION_TEXT_COLOR,
                icon_box_rect,
                width=2,
                border_radius=4,
            )

            cx, cy = icon_box_rect.center

            if name == "STORAGE":
                r = 3
                offset = 7
                for dx in (-offset, offset):
                    for dy in (-offset, offset):
                        pygame.draw.circle(screen, UI_SECTION_TEXT_COLOR, (cx + dx, cy + dy), r)
            elif name == "BRIDGE":
                star_r_outer = 10
                star_r_inner = 4
                points = []
                for i in range(10):
                    ang = i * 3.14159 / 5.0
                    r = star_r_outer if i % 2 == 0 else star_r_inner
                    v = pygame.math.Vector2(1, 0).rotate_rad(ang)
                    px = cx + int(r * v.x)
                    py = cy + int(r * v.y)
                    points.append((px, py))
                pygame.draw.polygon(screen, UI_SECTION_TEXT_COLOR, points, width=1)
            elif name == "FABRICATION":
                p1 = (icon_box_rect.left + 5, icon_box_rect.bottom - 5)
                p2 = (icon_box_rect.left + 5, icon_box_rect.top + 5)
                p3 = (icon_box_rect.right - 5, icon_box_rect.bottom - 5)
                pygame.draw.polygon(screen, UI_SECTION_TEXT_COLOR, [p1, p2, p3], width=1)
            elif name == "REFINING":
                bar_w = 4
                gap = 3
                start_x = cx - (bar_w * 3 + gap * 2) // 2
                for i in range(3):
                    bx = start_x + i * (bar_w + gap)
                    pygame.draw.rect(
                        screen,
                        UI_SECTION_TEXT_COLOR,
                        (bx, cy - 8, bar_w, 16),
                        width=1,
                    )

        # Health bar at the bottom
        if hasattr(main_player, "max_health") and main_player.max_health > 0:
            draw_health_bar(
                screen,
                health_bar_x,
                health_bar_y,
                health_bar_width,
                health_bar_height,
                getattr(main_player, "health", 0),
                main_player.max_health,
            )
            # Armor bar underneath health, if the main ship has armor
            if hasattr(main_player, "max_armor") and main_player.max_armor > 0:
                armor_y = health_bar_y + health_bar_height + 4
                draw_armor_bar(
                    screen,
                    health_bar_x,
                    armor_y,
                    health_bar_width,
                    health_bar_height,
                    getattr(main_player, "armor", 0),
                    main_player.max_armor,
                )


            segment_count = 10
            segment_w = health_bar_width / float(segment_count)
            for i in range(1, segment_count):
                x_pos = int(health_bar_x + i * segment_w)
                pygame.draw.line(
                    screen,
                    (10, 10, 10),
                    (x_pos, health_bar_y + 2),
                    (x_pos, health_bar_y + health_bar_height - 2),
                    1,
                )

        pygame.display.flip()