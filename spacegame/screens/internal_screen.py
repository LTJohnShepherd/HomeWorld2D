import sys
import pygame
from spacegame.ui.ui import Button, draw_health_bar, draw_armor_bar, UI_BG_IMG
from spacegame.config import (
    SCREEN_WIDTH, 
    SCREEN_HEIGHT, 
    UI_BG_COLOR, 
    UI_TAB_HEIGHT, 
    UI_SECTION_BASE_COLOR, 
    UI_SECTION_HOVER_COLOR,
    UI_SECTION_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR,
    PREVIEWS_DIR,
    )
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.core.modules_manager import manager as modules_manager


def _load_icon(filename: str) -> pygame.Surface | None:
    """Load icon from previews folder."""
    try:
        return pygame.image.load(f"{PREVIEWS_DIR}/{filename}").convert_alpha()
    except Exception:
        return None


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
    icon_filenames = ["Nav_Icon_External.png", "Nav_Icon_Internal.png", "Nav_Icon_Loadout.png"]
    selected_tab = 1  # INTERNAL initially selected

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

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
        ("STORAGE", storage_btn, "Nav_Icon_Inventory.png"),
        ("BRIDGE", bridge_btn, "Nav_Icon_Bridge.png"),
        ("FABRICATION", fabrication_btn, "Nav_Icon_Fabricator.png"),
        ("REFINING", refining_btn, "Nav_Icon_Refinery.png"),
    ]
    
    # Preload icons
    icon_cache = {}
    for name, btn, icon_file in section_buttons:
        icon_cache[name] = _load_icon(icon_file)

    # ---------- HEALTH BAR ----------
    health_bar_width = int(width * 0.80)
    health_bar_height = 14
    health_bar_x = (width - health_bar_width) // 2
    health_bar_y = height - 46

    running = True
    while running:
        # Recompute disabled tabs each frame to stay in sync with ModulesManager
        disabled_labels = set()
        if not modules_manager.get_fabricators():
            disabled_labels.add("FABRICATION")
        if not modules_manager.get_refineries():
            disabled_labels.add("REFINING")
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
                        label = entry["label"]
                        if label in disabled_labels:
                            break
                        if label == "FLEET CONFIGURATION":
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

                for name, btn, icon_file in section_buttons:
                    if btn.handle_event(event):
                        if name == "STORAGE":
                            from spacegame.screens.inventory import inventory_screen
                            res = inventory_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # "to_internal" or None: stay in internal screen loop, don't return
                        if name == "FABRICATION":
                            # ignore if disabled
                            if "FABRICATION" in disabled_labels:
                                continue
                            from spacegame.screens.fabrication_main_screen import fabrication_main_screen
                            res = fabrication_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                        if name == "REFINING":
                            # ignore if disabled
                            if "REFINING" in disabled_labels:
                                continue
                            from spacegame.screens.refining_main_screen import refining_main_screen
                            res = refining_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"

        # ---------- DRAW ----------
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
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

        # Back arrow (on top of nav background) - use image
        back_arrow_img = get_back_arrow_image()
        if back_arrow_img:
            arrow_scaled = pygame.transform.smoothscale(back_arrow_img, (arrow_size - 4, arrow_size - 4))
            arrow_draw_rect = arrow_scaled.get_rect(center=back_arrow_rect.center)
            screen.blit(arrow_scaled, arrow_draw_rect)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (draw using shared nav helper)
        nav_top_y, nav_bottom_y = draw_tabs(screen, tab_entries, selected_tab, tabs_y, width, tab_font, disabled_labels=disabled_labels)

        # Section buttons + icon images
        ICON_BOX_SIZE = 34
        for name, btn, icon_file in section_buttons:
            # visually disable buttons when corresponding modules are not equipped
            if name == "FABRICATION" and "FABRICATION" in disabled_labels:
                btn.text_color = (140, 140, 140)
            elif name == "REFINING" and "REFINING" in disabled_labels:
                btn.text_color = (140, 140, 140)
            else:
                btn.text_color = UI_SECTION_TEXT_COLOR
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

            # Draw icon image
            icon_surf = icon_cache.get(name)
            if icon_surf:
                icon_scaled = pygame.transform.smoothscale(icon_surf, (ICON_BOX_SIZE - 8, ICON_BOX_SIZE - 8))
                icon_draw_rect = icon_scaled.get_rect(center=icon_box_rect.center)
                screen.blit(icon_scaled, icon_draw_rect)

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