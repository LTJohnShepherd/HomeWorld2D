import sys
import pygame
from fleet_unit import ExpeditionShip, Frigate, Interceptor
from ui import Button


def fleet_management_screen(main_player: ExpeditionShip, player_fleet):
    """
    Fleet management screen:
    - 3 slots in a vertical column.
    - Empty slot: hollow circle with '+'.
    - Assigned slot: interceptor preview triangle drawn instead of the circle.
    - Clicking a slot opens a stored crafts screen:
        * "Clear slot" – frees the slot.
        * Alive interceptors from pool – assigns one to that slot.

    This screen edits:
        main_player.hangar_assignments   (which interceptor is in which slot)
        main_player.hangar[i]            (True = assigned and in hangar, False = no interceptor)
        main_player.hangar_ships[i]      (active deployed interceptor from this slot, if any)
    """
    screen = pygame.display.get_surface()
    if screen is None:
        return

    clock = pygame.time.Clock()
    width, height = screen.get_size()

    title_font = pygame.font.Font(None, 40)
    label_font = pygame.font.Font(None, 28)
    btn_font = pygame.font.Font(None, 24)

    back_btn = Button((10, 10, 100, 32), "Back", btn_font)

    # Ensure interceptor pool & assignments exist
    if not hasattr(main_player, "interceptor_pool"):
        main_player.interceptor_pool = [
            {"id": i, "name": f"Interceptor {i+1}", "alive": True}
            for i in range(5)
        ]
    if not hasattr(main_player, "hangar_assignments"):
        main_player.hangar_assignments = [None, None, None]

    # Layout for previews
    # ExpeditionShip (left) - slightly larger
    ms_w, ms_h = 140, 160
    ms_rect = pygame.Rect(60, height // 2 - ms_h // 2, ms_w, ms_h)

    # Light Crafts column (middle) - more spaced
    circle_radius = 30
    circle_spacing = 120  # increased spacing between slots
    circle_col_x = width // 2
    circle_top_y = height // 2 - circle_spacing
    circle_rects = []
    for i in range(3):
        cx = circle_col_x
        cy = circle_top_y + i * circle_spacing
        rect = pygame.Rect(0, 0, circle_radius * 2, circle_radius * 2)
        rect.center = (cx, cy)
        circle_rects.append(rect)

    # Escort Frigate preview (right) - slightly larger
    fr_w, fr_h = 140, 70
    fr_rect = pygame.Rect(width - 60 - fr_w, height // 2 - fr_h // 2, fr_w, fr_h)

    # Popup state
    selector_open_for = None   # slot index or None
    selector_items = []        # list[(rect, entry)] where entry is dict or None ("clear slot")

    def draw_health_bar(x, y, w, h, current, maximum):
        """Simple horizontal health bar."""
        if maximum <= 0:
            pct = 0.0
        else:
            pct = max(0.0, min(1.0, current / maximum))

        bg_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

        fill_w = int(w * pct + 0.5)
        if fill_w > 0:
            fill_color = (50, 200, 70) if pct >= 0.5 else (220, 70, 70)
            fill_rect = pygame.Rect(x, y, fill_w, h)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)

        pygame.draw.rect(screen, (10, 10, 10), bg_rect, 1, border_radius=3)

    # Previews top for title alignment
    previews_top = min(ms_rect.top, circle_rects[0].top, fr_rect.top)

    running = True
    while running:
        # ------------- EVENTS -------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if back_btn.handle_event(event):
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Handle click on popup list (if open)
                if selector_open_for is not None:
                    clicked_entry = False
                    for item_rect, entry in selector_items:
                        if item_rect.collidepoint(event.pos):
                            slot = selector_open_for

                            # Clear slot
                            if entry is None:
                                main_player.hangar_assignments[slot] = None
                                main_player.hangar[slot] = False
                                if 0 <= slot < len(main_player.hangar_ships):
                                    main_player.hangar_ships[slot] = None

                            # Assign interceptor from pool
                            elif entry.get("alive", False):
                                main_player.hangar_assignments[slot] = entry["id"]
                                main_player.hangar[slot] = True
                                # Ensure no stale reference
                                if 0 <= slot < len(main_player.hangar_ships):
                                    ship = main_player.hangar_ships[slot]
                                    if ship is None or ship.health <= 0.0:
                                        main_player.hangar_ships[slot] = None

                            selector_open_for = None
                            selector_items = []
                            clicked_entry = True
                            break

                    if clicked_entry:
                        continue

                    # Clicked outside list – close it
                    selector_open_for = None
                    selector_items = []

                # Handle click on one of the 3 light-craft slots
                for idx, c_rect in enumerate(circle_rects):
                    if c_rect.collidepoint(event.pos):
                        fighter_ship = (
                            main_player.hangar_ships[idx]
                            if idx < len(main_player.hangar_ships)
                            else None
                        )

                        # Opens the fleet selection screen
                        from light_craft_selection import light_craft_selection_screen
                        light_craft_selection_screen(main_player, idx)
                        selector_open_for = None
                        selector_items = []
                        break

        # ------------- DRAW -------------
        screen.fill((8, 8, 16))

        # Screen title (top center)
        title_surf = title_font.render("Fleet Management", True, (255, 255, 255))
        screen.blit(
            title_surf,
            (width // 2 - title_surf.get_width() // 2, 20),
        )

        back_btn.draw(screen)

        # Common Y for section titles, evenly spaced between main title and previews
        fleet_title_bottom = 20 + title_surf.get_height()
        label_height = label_font.size("M")[1]
        labels_y = fleet_title_bottom + (previews_top - fleet_title_bottom - label_height) // 2

        # ===== LEFT: ExpeditionShip preview =====
        ms_label = label_font.render("ExpeditionShip", True, (220, 220, 220))
        ms_label_x = ms_rect.centerx - ms_label.get_width() // 2
        ms_label_y = labels_y
        screen.blit(ms_label, (ms_label_x, ms_label_y))

        pygame.draw.rect(screen, main_player.color, ms_rect, border_radius=10)

        bar_pad = 6
        bar_h = 6
        bar_w = ms_rect.width
        bar_x = ms_rect.left
        bar_y = ms_rect.bottom + bar_pad
        draw_health_bar(bar_x, bar_y, bar_w, bar_h, main_player.health, main_player.max_health)

        # ===== MIDDLE: Light Crafts column =====
        lc_label = label_font.render("Light Crafts", True, (220, 220, 220))
        lc_label_x = circle_col_x - lc_label.get_width() // 2
        lc_label_y = labels_y
        screen.blit(lc_label, (lc_label_x, lc_label_y))

        for i, c_rect in enumerate(circle_rects):
            cx, cy = c_rect.center

            # Resolve which interceptor (if any) is assigned and still alive
            assigned_id = None
            if 0 <= i < len(main_player.hangar_assignments):
                assigned_id = main_player.hangar_assignments[i]

            assigned_entry = None
            if assigned_id is not None:
                for e in main_player.interceptor_pool:
                    if e.get("id") == assigned_id and e.get("alive", False):
                        assigned_entry = e
                        break

            interceptor_color = Interceptor.DEFAULT_COLOR if hasattr(Interceptor, "DEFAULT_COLOR") else (230, 230, 230)

            if assigned_entry is not None:
                # Triangle preview
                r = circle_radius - 4
                points = [
                    (cx, cy - r),       # top
                    (cx - r, cy + r),   # bottom left
                    (cx + r, cy + r),   # bottom right
                ]
                pygame.draw.polygon(screen, interceptor_color, points)
                pygame.draw.polygon(screen, (15, 15, 15), points, 2)

                # NAME ABOVE craft (always, as long as an alive interceptor is assigned)
                name_surf = label_font.render(assigned_entry.get("name", "Interceptor"), True, (220, 220, 255))
                name_x = cx - name_surf.get_width() // 2
                name_y = c_rect.top - 24
                screen.blit(name_surf, (name_x, name_y))

            else:
                # Empty slot: hollow circle + plus sign
                pygame.draw.circle(screen, (230, 230, 230), (cx, cy), circle_radius, 2)
                pygame.draw.line(
                    screen, (230, 230, 230),
                    (cx - 8, cy), (cx + 8, cy), 2
                )
                pygame.draw.line(
                    screen, (230, 230, 230),
                    (cx, cy - 8), (cx, cy + 8), 2
                )

            # Health bar for deployed interceptor from this slot
            fighter_ship = (
                main_player.hangar_ships[i]
                if i < len(main_player.hangar_ships)
                else None
            )
            fighter_alive = (
                fighter_ship is not None
                and fighter_ship.health > 0.0
                and fighter_ship in player_fleet
            )

            if fighter_alive:
                hb_w = circle_radius * 2
                hb_h = 5
                hb_x = cx - hb_w // 2
                hb_y = cy + circle_radius + 6
                draw_health_bar(hb_x, hb_y, hb_w, hb_h, fighter_ship.health, fighter_ship.max_health)
        # ===== RIGHT: Escort Frigate preview =====
        frigates = [s for s in player_fleet if isinstance(s, Frigate)]

        fr_label = label_font.render("Escort Frigates", True, (220, 220, 220))
        fr_label_x = fr_rect.centerx - fr_label.get_width() // 2
        fr_label_y = labels_y
        screen.blit(fr_label, (fr_label_x, fr_label_y))

        if frigates:
            pygame.draw.rect(screen, frigates[0].color, fr_rect, border_radius=10)

            f = frigates[0]
            bar_pad = 6
            bar_h = 6
            bar_w = fr_rect.width
            bar_x = fr_rect.left
            bar_y = fr_rect.bottom + bar_pad
            draw_health_bar(bar_x, bar_y, bar_w, bar_h, f.health, f.max_health)
        else:
            pygame.draw.rect(screen, (80, 80, 80), fr_rect, border_radius=10)

        pygame.display.flip()
        clock.tick(60)