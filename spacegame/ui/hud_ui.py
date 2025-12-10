"""HUD helpers: small widget that draws the in-game HUD previews.

`HudUI` prepares pre-scaled previews for quick drawing in the game loop
and provides input handling for small deploy/recall buttons.
"""

import pygame
from spacegame.models.units.frigate import Frigate
from spacegame.ui.ui import preview_for_unit, draw_triangle, draw_diamond, draw_dalton, draw_hex, draw_health_bar, draw_armor_bar
from spacegame.config import UI_TAB_TEXT_SELECTED


class HudUI:
    """Draws the bottom-row HUD previews and handles simple clicks.

    This class caches scaled preview images to avoid expensive per-frame
    smoothscale calls and exposes `handle_mouse_button_down` to let callers
    react to HUD clicks.
    """

    def __init__(self, font, preview_size=40):
        self.font = font
        self.preview_size = preview_size

        # pre-scaled light craft preview sprites for hangar icons
        self.interceptor_preview_img = pygame.transform.smoothscale(
            preview_for_unit("interceptor"), (preview_size, preview_size)
        )
        self.resource_collector_preview_img = pygame.transform.smoothscale(
            preview_for_unit("resource_collector"), (preview_size, preview_size)
        )
        self.bomber_preview_img = pygame.transform.smoothscale(
            preview_for_unit("plasma_bomber"), (preview_size, preview_size)
        )

        # --- Unified preview row layout ---
        row_y = 630

        # --- ExpeditionShip preview (bigger, on the left) ---
        self.expeditionship_preview = {
            'preview_position': pygame.Vector2(80, row_y),
            'width': 90,
            'height': 60,
        }

        # --- Frigate preview (between ExpeditionShip and interceptors) ---
        self.frigate_preview = {
            'preview_position': pygame.Vector2(190, row_y),
            'width': 60,
            'height': 35,
        }

        # --- 3 interceptor previews, evenly spaced to the right of the ExpeditionShip ---
        self.hangar_slots = [
            {'preview_position': pygame.Vector2(280, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(380, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
            {'preview_position': pygame.Vector2(480, row_y), 'show_button': False, 'button_rect': pygame.Rect(0, 0, 80, 25)},
        ]

    def handle_mouse_button_down(self, mouse_pos, main_player, player_shapes):
        """Process a left mouse button click. Returns True if the click was consumed by the hangar UI."""
        clicked_ui = False

        # InventoryManager-backed hangar is required
        inv = getattr(main_player, 'inventory_manager', None)
        if inv is None or getattr(inv, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        hangar = inv.hangar

        # Check deploy / recall buttons
        for i, hangar_slot in enumerate(self.hangar_slots):
            if hangar_slot['show_button'] and hangar_slot['button_rect'].collidepoint(mouse_pos):
                # Deploy if slot currently has a craft in hangar
                if hangar.slots[i]:
                    # Use hangar.deploy (created on Hangar) to spawn the craft.
                    new_fighter = None
                    if hasattr(hangar, 'deploy'):
                        new_fighter = hangar.deploy(i)
                    if new_fighter:
                        player_shapes.append(new_fighter)
                else:
                    # RECALL: check deployed ships tracked by hangar
                    icpts = getattr(hangar, 'ships', [None, None, None])
                    fighter_ship = icpts[i] if i < len(icpts) else None
                    if fighter_ship is not None and fighter_ship in player_shapes and fighter_ship.health > 0.0:
                        fighter_ship.recalling = True
                        fighter_ship.selected = False  # stop being commanded by the player

                hangar_slot['show_button'] = False  # hide button after click
                clicked_ui = True
                break

        # Check ExpeditionShip preview click: select the mothership if clicked
        if not clicked_ui:
            ms_center = self.expeditionship_preview['preview_position']
            ms_w = self.expeditionship_preview['width']
            ms_h = self.expeditionship_preview['height']
            ms_rect = pygame.Rect(int(ms_center.x - ms_w / 2), int(ms_center.y - ms_h / 2), int(ms_w), int(ms_h))
            if ms_rect.collidepoint(mouse_pos):
                # select mothership and deselect others
                for s in player_shapes:
                    s.selected = False
                main_player.selected = True
                clicked_ui = True

        # Check Frigate preview click: select the first Frigate found in player_shapes
        if not clicked_ui:
            fr_center = self.frigate_preview['preview_position']
            fr_w = self.frigate_preview['width'] * 2
            fr_h = self.frigate_preview['height'] * 2
            fr_rect = pygame.Rect(int(fr_center.x - fr_w / 2), int(fr_center.y - fr_h / 2), int(fr_w), int(fr_h))
            if fr_rect.collidepoint(mouse_pos):
                frigate = None
                for s in player_shapes:
                    if isinstance(s, Frigate):
                        frigate = s
                        break
                if frigate is not None and frigate.health > 0.0:
                    for s in player_shapes:
                        s.selected = False
                    frigate.selected = True
                    clicked_ui = True

        # Check mini previews
        if not clicked_ui:
            for i, hangar_slot in enumerate(self.hangar_slots):
                preview_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - self.preview_size // 2,
                    hangar_slot['preview_position'].y - self.preview_size // 2,
                    self.preview_size, self.preview_size,
                )
                if preview_rect.collidepoint(mouse_pos):
                    # If the craft is deployed and alive, select it; otherwise toggle the deploy/recall button
                    icpts = getattr(hangar, 'ships', [None, None, None])
                    fighter_ship = icpts[i] if i < len(icpts) else None
                    fighter_alive = (
                        fighter_ship is not None and
                        fighter_ship in player_shapes and
                        fighter_ship.health > 0.0
                    )
                    if fighter_alive:
                        # Deselect all other ships and select this one
                        for s in player_shapes:
                            s.selected = False
                        fighter_ship.selected = True
                        # Also show the deploy/recall button for this deployed ship
                        hangar_slot['show_button'] = True
                    else:
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
        # Require InventoryManager.hangar
        inv = getattr(main_player, 'inventory_manager', None)
        if inv is None or getattr(inv, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        hangar = inv.hangar
        
        # --- Draw ExpeditionShip preview (sprite + hex overlay) ---
        ms_center = self.expeditionship_preview['preview_position']
        ms_w = self.expeditionship_preview['width']
        ms_h = self.expeditionship_preview['height']

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

        ms_surf = pygame.transform.smoothscale(preview_for_unit("expedition"), (ms_w, ms_h))
        ms_x = int(ms_center.x - ms_w / 2)
        ms_y = int(ms_center.y - ms_h / 2)
        screen.blit(ms_surf, (ms_x, ms_y))

        # --- ExpeditionShip health bar BELOW the preview ---
        bar_w = ms_w
        bar_h = 5
        pad = 4
        bar_x = ms_x
        bar_y = ms_y + ms_h + pad

        draw_health_bar(screen, bar_x, bar_y, bar_w, bar_h, main_player.health, main_player.max_health)
        # Armor bar directly under health, if the ship has armor
        if getattr(main_player, 'max_armor', 0) > 0:
            armor_y = bar_y + bar_h + 2
            draw_armor_bar(screen, bar_x, armor_y, bar_w, bar_h, getattr(main_player, 'armor', 0), getattr(main_player, 'max_armor', 0))

        # ---------------------------------------------------------
        # --- Frigate preview (sprite + diamond overlay) ---
        frigate = None
        for s in player_shapes:
            if isinstance(s, Frigate):
                frigate = s
                break

        if frigate is not None and frigate.health > 0.0:
            fr_center = self.frigate_preview['preview_position']
            fr_w = self.frigate_preview['width'] * 2
            fr_h = self.frigate_preview['height'] * 2

            # Diamond overlay, scaled with same proportions as in gameScreen
            draw_diamond(
                screen,
                (fr_center.x, fr_center.y),
                fr_w * 0.3,
                fr_h * 0.75,
                (80, 255, 190),
                2
            )

            # use frigate preview image
            fr_img = pygame.transform.smoothscale(
                preview_for_unit("frigate"),
                (int(fr_w), int(fr_h))
            )
            fr_x = int(fr_center.x - fr_w / 2)
            fr_y = int(fr_center.y - fr_h / 2)
            screen.blit(fr_img, (fr_x, fr_y))

            # Frigate health bar BELOW the preview
            bar_w = fr_w * 0.6
            bar_h = 5
            pad = -1.1
            bar_x = int(fr_x + (fr_w - bar_w) / 2)
            bar_y = fr_y + fr_h + pad

            draw_health_bar(screen, bar_x, bar_y, bar_w, bar_h, frigate.health, frigate.max_health)
            # Armor bar directly under health, if frigate has armor
            if getattr(frigate, 'max_armor', 0) > 0:
                armor_y = bar_y + bar_h + 2
                draw_armor_bar(screen, bar_x, armor_y, bar_w, bar_h, getattr(frigate, 'armor', 0), getattr(frigate, 'max_armor', 0))


        # ---------------------------------------------------------
        # --- Draw hangar previews & deploy/recall buttons ---
        for i, hangar_slot in enumerate(self.hangar_slots):
            # figure out which light craft (if any) is linked to this slot
            icpts = getattr(hangar, 'ships', [None, None, None])
            fighter_ship = icpts[i] if i < len(icpts) else None

            # If this slot has neither a craft in hangar nor a live one deployed,
            # do not show a preview at all (this lets you have 0/1/2/3 previews).
            fighter_alive = (
                fighter_ship is not None and
                fighter_ship in player_shapes and
                fighter_ship.health > 0.0
            )
            if not hangar.slots[i] and not fighter_alive:
                hangar_slot['show_button'] = False
                continue

            # Get the unit type from hangar entry to determine which preview and shape to use
            unit_type = "interceptor"  # default
            if fighter_ship is not None:
                unit_type = getattr(fighter_ship, 'shape_id', lambda: "interceptor")()
            else:
                # Check the pool entry for the assigned unit
                entry_id = hangar.assignments[i] if i < len(hangar.assignments) else None
                if entry_id is not None:
                    entry = hangar.get_entry_by_id(entry_id)
                    if entry is not None:
                        unit_type = entry.unit_type

            # Select the appropriate preview image based on unit type
            if unit_type == "resource_collector":
                craft_preview_img = self.resource_collector_preview_img.copy()
            elif unit_type == "plasma_bomber":
                craft_preview_img = self.bomber_preview_img.copy()
            else:
                # default to interceptor
                craft_preview_img = self.interceptor_preview_img.copy()

            # if it's still in hangar, darken the ship sprite itself (no dark box)
            if hangar.slots[i]:
                dim = pygame.Surface(craft_preview_img.get_size(), pygame.SRCALPHA)
                dim.fill((128, 128, 128, 255))  # < 255 => darker
                craft_preview_img.blit(dim, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Draw the appropriate shape overlay based on unit type
            craft_center = (
                hangar_slot['preview_position'].x,
                hangar_slot['preview_position'].y
            )
            
            if unit_type == "resource_collector":
                # Draw dalton shape for resource collector (long end pointing down)
                draw_dalton(
                    screen,
                    craft_center,
                    preview_size * 1.2,
                    preview_size * 1.5,  # make it taller to emphasize the downward point
                    (80, 255, 190),
                    2
                )
            else:
                # Draw triangle for interceptor
                draw_triangle(
                    screen,
                    craft_center,
                    preview_size * 1.2,
                    (80, 255, 190),
                    2
                )
            
            preview_x = hangar_slot['preview_position'].x - preview_size // 2
            preview_y = hangar_slot['preview_position'].y - preview_size // 2
            screen.blit(craft_preview_img, (preview_x, preview_y))

            # Health bar under preview when deployed and alive
            if fighter_alive:
                bar_w = preview_size
                bar_h = 5
                pad = 12
                bar_x = preview_x
                bar_y = preview_y + preview_size + pad

                draw_health_bar(screen, bar_x, bar_y, bar_w, bar_h, fighter_ship.health, fighter_ship.max_health)
                # Armor bar directly under health, if craft has armor
                if getattr(fighter_ship, 'max_armor', 0) > 0:
                    armor_y = bar_y + bar_h + 2
                    draw_armor_bar(screen, bar_x, armor_y, bar_w, bar_h, getattr(fighter_ship, 'armor', 0), getattr(fighter_ship, 'max_armor', 0))
                # (Removed: mining meter above preview)


            # Draw deploy/recall button above preview if active
            if hangar_slot['show_button']:
                btn_rect = pygame.Rect(
                    hangar_slot['preview_position'].x - 40,
                    hangar_slot['preview_position'].y - 65,
                    80, 25,
                )
                hangar_slot['button_rect'] = btn_rect

                if hangar.slots[i]:
                    # light craft still in hangar
                    btn_color = (40, 160, 40)
                    label = 'Deploy'
                else:
                    # light craft already deployed
                    btn_color = (180, 40, 40)
                    label = 'Recall'

                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=6)
                pygame.draw.rect(screen, (0, 0, 0), btn_rect, 2, border_radius=6)
                text = font.render(label, True, UI_TAB_TEXT_SELECTED)
                screen.blit(text, (btn_rect.x + 10, btn_rect.y + 3))