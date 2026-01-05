import sys
import pygame
from spacegame.ui.fleet_management_ui import draw_tier_icon_image
from spacegame.ui.ui import OREM_PREVIEW_IMG, scaledpreview_for_unit
from spacegame.models.units.interceptor import Interceptor
from spacegame.models.ores.orem import RUOreM
from spacegame.models.ores.orea import RUOreA
from spacegame.models.ores.oreb import RUOreB
from spacegame.models.ores.orec import RUOreC
from spacegame.models.resources.refineda import RURefinedA
from spacegame.models.resources.refinedb import RURefinedB
from spacegame.models.resources.refinedc import RURefinedC
from spacegame.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    UI_BG_COLOR,
    UI_TAB_HEIGHT,
    UI_ICON_BLUE,
    UI_SECTION_TEXT_COLOR,
    UI_TOP_BAR_HEIGHT,
    UI_TAB_TEXT_COLOR,
    UI_NAV_BG_COLOR,
    UI_NAV_LINE_COLOR,
)
from spacegame.config import PREVIEWS_DIR
from spacegame.ui.ui import UI_BG_IMG
from spacegame.ui.nav_ui import create_tab_entries, draw_tabs, get_back_arrow_image
from spacegame.core.modules_manager import manager as modules_manager


def inventory_screen(main_player, player_fleet):
    # Use the existing display surface if present; otherwise create one.
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    width, height = screen.get_size()

    # Inventory constants
    INVENTORY_CAPACITY_LIMIT = 60

    # ---------- FONTS ----------
    title_font = pygame.font.Font(None, 40)
    tab_font = pygame.font.Font(None, 28)
    section_font = pygame.font.Font(None, 32)
    close_font = pygame.font.Font(None, 40)
    name_font = pygame.font.Font(None, 26)
    dmg_font = pygame.font.Font(None, 22)
    capacity_font = pygame.font.Font(None, 24)

    # ---------- TOP BAR ----------
    TOP_BAR_HEIGHT = 96

    # Title in the center of the top bar (moved slightly up to give more room to tabs)
    title_text = "STORAGE"
    title_surf = title_font.render(title_text, True, UI_SECTION_TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 - 22))

    # Capacity display to the right of title (will be updated each frame)
    capacity_rect = pygame.Rect(0, 0, 200, 30)
    capacity_rect.right = width - 80
    capacity_rect.centery = title_rect.centery

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
    tab_labels = ["STORAGE", "BRIDGE", "FABRICATION", "REFINING", "INTERNAL MODULES"]
    icon_filenames = ["Nav_Icon_Inventory.png", "Nav_Icon_Bridge.png", "Nav_Icon_Fabricator.png", "Nav_Icon_Refinery.png", "Nav_Icon_InternalModules.png"]
    selected_tab = 0  # INVENTORY selected

    tab_entries, tabs_y = create_tab_entries(tab_labels, tab_font, width, TOP_BAR_HEIGHT, UI_TAB_HEIGHT, icon_filenames)
    disabled_labels = set()
    if not modules_manager.get_fabricators():
        disabled_labels.add("FABRICATION")
    if not modules_manager.get_refineries():
        disabled_labels.add("REFINING")

    # ---- layout helpers for the cards ----
    BOX_W = 260
    BOX_H = 80
    COLS = 3
    MARGIN_X = 18
    MARGIN_Y = 18

    # precompute left start so titles can align with the first card
    _total_w = COLS * BOX_W + (COLS - 1) * MARGIN_X
    LEFT_START = width // 2 - _total_w // 2

    def layout_rects(num_items, top_y):
        rects = []
        for i in range(num_items):
            row = i // COLS
            col = i % COLS
            x = LEFT_START + col * (BOX_W + MARGIN_X)
            y = top_y + row * (BOX_H + MARGIN_Y)
            rects.append(pygame.Rect(x, y, BOX_W, BOX_H))
        return rects

    running = True

    # Smooth scrolling state
    offset_y = 0.0          # what we actually render with
    offset_y_raw = 0.0      # what the input directly changes
    SCROLL_STEP = 40
    SCROLL_SMOOTH = 0.25    # 0..1, higher = snappier

    while running:
        # Recompute disabled tabs each frame to stay in sync with ModulesManager
        disabled_labels = set()
        if not modules_manager.get_fabricators():
            disabled_labels.add("FABRICATION")
        if not modules_manager.get_refineries():
            disabled_labels.add("REFINING")
        # Recompute alive/selected/stored every frame from the InventoryManager-backed Hangar
        inv_mgr = getattr(main_player, 'inventory_manager', None)
        if inv_mgr is None or getattr(inv_mgr, 'hangar', None) is None:
            raise RuntimeError("Hangar/InventoryManager not available on main_player; migration required")
        hangar = inv_mgr.hangar

        # Inventory modules are sourced directly from the InventoryManager's `get_modules()`.

        alive_entries = hangar.alive_pool_entries()
        selected_ids = hangar.selected_interceptor_ids()

        # Sort stored items by unit_type (ship type) so inventory cards are grouped
        # by type instead of their numeric pool id.
        stored_items = [e for e in alive_entries if e.id not in selected_ids]
        stored_items = sorted(stored_items, key=lambda e: (getattr(e, 'unit_type', '') or ''))
        # Build resources list from main_player inventory if present
        resources_items = []
        inv_mgr = getattr(main_player, 'inventory_manager', None)
        # RU TYPE M mapped to letter 'M'
        m_qty = int(inv_mgr.get_amount('M')) if inv_mgr is not None else 0
        if m_qty > 0:
            resources_items.append(RUOreM(quantity=m_qty))

        # RU TYPE A/B/C mapped to letters 'A','B','C'
        a_qty = int(inv_mgr.get_amount('A')) if inv_mgr is not None else 0
        if a_qty > 0:
            resources_items.append(RUOreA(quantity=a_qty))

        b_qty = int(inv_mgr.get_amount('B')) if inv_mgr is not None else 0
        if b_qty > 0:
            resources_items.append(RUOreB(quantity=b_qty))

        c_qty = int(inv_mgr.get_amount('C')) if inv_mgr is not None else 0
        if c_qty > 0:
            resources_items.append(RUOreC(quantity=c_qty))

        # Refined materials (future acquisition method) mapped to 'RA','RB','RC'
        ra_qty = int(inv_mgr.get_amount('RA')) if inv_mgr is not None else 0
        if ra_qty > 0:
            resources_items.append(RURefinedA(quantity=ra_qty))

        rb_qty = int(inv_mgr.get_amount('RB')) if inv_mgr is not None else 0
        if rb_qty > 0:
            resources_items.append(RURefinedB(quantity=rb_qty))

        rc_qty = int(inv_mgr.get_amount('RC')) if inv_mgr is not None else 0
        if rc_qty > 0:
            resources_items.append(RURefinedC(quantity=rc_qty))

        # ---------- EVENTS ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "to_internal"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if back_arrow_rect.collidepoint(mx, my):
                    return "to_internal"

                if close_hit_rect.collidepoint(mx, my):
                    return "to_game"

                # Tabs
                for idx, entry in enumerate(tab_entries):
                    if entry["rect"].collidepoint(mx, my):
                        label = entry["label"]
                        # ignore clicks on disabled tabs
                        if label in disabled_labels:
                            break
                        # Open Fabrication when FABRICATION tab clicked
                        if label == "FABRICATION":
                            from spacegame.screens.fabrication_main_screen import fabrication_main_screen

                            res = fabrication_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to STORAGE tab after closing fabrication
                            selected_tab = 0
                        elif label == "REFINING":
                            from spacegame.screens.refining_main_screen import refining_main_screen

                            res = refining_main_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            # return focus back to STORAGE tab after closing refining
                            selected_tab = 0
                        elif label == "INTERNAL MODULES":
                            from spacegame.screens.internal_modules_screen import internal_modules_screen

                            res = internal_modules_screen(main_player, player_fleet)
                            if res == "to_game":
                                return "to_game"
                            if res == "to_internal":
                                return "to_internal"
                            # after closing, go back to STORAGE tab highlight
                            selected_tab = 0
                        else:
                            selected_tab = idx
                        break

            # Mouse wheel support (pygame 2)
            if event.type == pygame.MOUSEWHEEL:
                # event.y: 1 for wheel up, -1 for wheel down
                offset_y_raw += event.y * SCROLL_STEP

        # ---------- STATIC LAYOUT (NO OFFSET HERE) ----------
        ships_title_y = UI_TOP_BAR_HEIGHT + 30
        ships_top_y = ships_title_y + 40
        ships_rects = layout_rects(len(stored_items), ships_top_y)

        # Materials
        materials_title_y = (
            ships_rects[-1].bottom + 40
            if ships_rects
            else (ships_top_y + 40)
        )
        materials_top_y = materials_title_y + 40
        materials_rects = layout_rects(3, materials_top_y)

        # Modules (unequipped modules in inventory)
        modules_title_y = materials_top_y + BOX_H + 40
        modules_top_y = modules_title_y + 40
        # Query inventory manager for module instances
        modules_items = []
        if inv_mgr is not None and hasattr(inv_mgr, 'get_modules'):
            try:
                modules_items = inv_mgr.get_modules() or []
            except Exception:
                modules_items = []
        # Reserve space for modules layout (show 3 placeholders if empty)
        modules_count_for_layout = len(modules_items) if len(modules_items) > 0 else 3
        modules_rects = layout_rects(modules_count_for_layout, modules_top_y)

        resources_title_y = modules_top_y + BOX_H + 40
        resources_top_y = resources_title_y + 40
        # If there are no actual resource items, we still reserve space for
        # three placeholder cards so scrolling and layout remain consistent.
        resource_count_for_layout = len(resources_items) if len(resources_items) > 0 else 3
        resource_rects = layout_rects(resource_count_for_layout, resources_top_y)

        # ---------- SCROLL LIMITS + SMOOTH RETURN ----------
        # Area where content is allowed to be visible (below nav bar)
        nav_top_y = tabs_y - 6
        nav_bottom_y = tabs_y + UI_TAB_HEIGHT + 6
        scroll_area_top = nav_bottom_y + 4

        # Content bounds in "unscrolled" space
        content_top = ships_title_y
        # If there are no resource cards, fall back to last materials row or ships
        if resource_rects:
            content_bottom = resource_rects[-1].bottom + 40
        elif materials_rects:
            content_bottom = materials_rects[-1].bottom + 40
        elif ships_rects:
            content_bottom = ships_rects[-1].bottom + 40
        else:
            content_bottom = content_top

        # User cannot scroll above original layout (no going above first title)
        top_limit = 0.0

        # User cannot scroll below last card (bottom edge aligned with scroll area)
        total_content_height = content_bottom - content_top
        visible_height = SCREEN_HEIGHT - scroll_area_top
        if total_content_height <= visible_height:
            # Everything fits; just keep at 0
            bottom_limit = 0.0
        else:
            bottom_limit = scroll_area_top - total_content_height

        # Clamp "target" and ease offset_y towards it (smooth return to bounds)
        target = max(min(offset_y_raw, top_limit), bottom_limit)
        offset_y += (target - offset_y) * SCROLL_SMOOTH

        # Snap if very close, to avoid tiny float drift
        if abs(target - offset_y) < 0.5:
            offset_y = target

        # stop internal scroll value from drifting beyond limits
        offset_y_raw = target

        # ---------- DRAW ----------
        try:
            screen.blit(UI_BG_IMG, (0, 0))
        except Exception:
            screen.fill(UI_BG_COLOR)

        # Nav band coordinates (UI that should clip over the cards)
        pygame.draw.rect(
            screen,
            UI_NAV_BG_COLOR,
            (0, nav_top_y, width, nav_bottom_y - nav_top_y),
        )

        pygame.draw.line(screen, UI_NAV_LINE_COLOR, (0, nav_top_y), (width, nav_top_y), 1)
        pygame.draw.line(
            screen, UI_NAV_LINE_COLOR, (0, nav_bottom_y), (width, nav_bottom_y), 1
        )

        # Title (on top of nav background)
        screen.blit(title_surf, title_rect)

        # Capacity display (dynamically updated each frame)
        current_inventory_count = len(stored_items) + len(resources_items)
        capacity_text = f"CAPACITY: {current_inventory_count} / {INVENTORY_CAPACITY_LIMIT}"
        capacity_surf = capacity_font.render(capacity_text, True, UI_TAB_TEXT_COLOR)
        capacity_display_rect = capacity_surf.get_rect()
        capacity_display_rect.right = width - 80
        capacity_display_rect.centery = title_rect.centery
        screen.blit(capacity_surf, capacity_display_rect)

        # Back arrow (on top of nav background) - use image
        back_arrow_img = get_back_arrow_image()
        if back_arrow_img:
            arrow_size = 32
            arrow_scaled = pygame.transform.smoothscale(back_arrow_img, (arrow_size - 4, arrow_size - 4))
            arrow_draw_rect = arrow_scaled.get_rect(center=back_arrow_rect.center)
            screen.blit(arrow_scaled, arrow_draw_rect)

        # Close X (on top of nav background)
        screen.blit(close_surf, close_rect)

        # Tabs (draw using shared nav helper)
        nav_top_y, nav_bottom_y = draw_tabs(screen, tab_entries, selected_tab, tabs_y, width, tab_font, disabled_labels=disabled_labels)

        # ---- SCROLLABLE AREA CLIP (cards + section titles go under the UI) ----
        scroll_clip_rect = pygame.Rect(0, scroll_area_top, width, height - scroll_area_top)
        screen.set_clip(scroll_clip_rect)

        # ---- Ships section (title + cards) ----
        ships_title = section_font.render("SHIPS", True, (220, 220, 255))
        screen.blit(
            ships_title,
            (LEFT_START, ships_title_y + offset_y),
        )

        # Draw stored ships as cards
        ships_rects = layout_rects(len(stored_items), ships_top_y)
        for rect, entry in zip(ships_rects, stored_items):
            draw_rect = rect.move(0, offset_y)
            pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)

            tier_value = getattr(entry, "tier", 0)
            draw_tier_icon_image(screen, draw_rect, tier_value)

            preview_x = draw_rect.x + 40
            preview_y = draw_rect.y + draw_rect.height // 2

            # preview image (pick by unit_type) — use cached scaled preview
            img = scaledpreview_for_unit(getattr(entry, "unit_type"), (48, 48))
            rect_img = img.get_rect(center=(preview_x, preview_y))
            screen.blit(img, rect_img.topleft)

            from spacegame.ui.ui import draw_multiline_text, draw_power_icon
            draw_multiline_text(screen, entry.name, name_font, (230, 230, 255), (preview_x + 50, draw_rect.y + 12))

            # Cached power computation per-entry to avoid repeated instantiation
            if not hasattr(inventory_screen, '_power_cache'):
                inventory_screen._power_cache = {}
            cache_key = (getattr(entry, 'id', None), getattr(entry, 'tier', None))
            power_cache = inventory_screen._power_cache
            if cache_key in power_cache:
                power_val = power_cache[cache_key]
            else:
                try:
                    ut = getattr(entry, 'unit_type', '')
                    tier = int(getattr(entry, 'tier', 0) or 0)
                    if ut == 'interceptor':
                        unit = Interceptor((0, 0), interceptor_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'resource_collector':
                        from spacegame.models.units.resource_collector import ResourceCollector
                        unit = ResourceCollector((0, 0), collector_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'plasma_bomber':
                        from spacegame.models.units.plasma_bomber import PlasmaBomber
                        unit = PlasmaBomber((0, 0), bomber_id=getattr(entry, 'id', None), tier=tier)
                    elif ut == 'frigate':
                        from spacegame.models.units.frigate import Frigate
                        unit = Frigate((0, 0), tier=tier)
                    else:
                        unit = None
                except Exception:
                    unit = None

                if unit is None:
                    power_val = 0
                else:
                    bullet = float(getattr(unit, 'bullet_damage', 0.0))
                    armor = float(getattr(unit, 'armor_damage', 0.0))
                    health = float(getattr(unit, 'max_health', getattr(unit, 'health', 0.0)))
                    mover = getattr(unit, 'mover', None)
                    speed = float(getattr(mover, 'speed', getattr(unit, 'speed', 0.0))) if mover is not None else float(getattr(unit, 'speed', 0.0))
                    try:
                        power = (bullet + armor + speed + (health / 10.0)) / 4.0
                    except Exception:
                        power = 0.0
                    power_val = int(round(power))
                power_cache[cache_key] = power_val

            # draw small icon and numeric power slightly lower
            icon_size = 12
            icon_x = preview_x + 50
            icon_y = draw_rect.y + 56
            draw_power_icon(screen, (icon_x, icon_y), size=icon_size, color=(200, 200, 220))
            try:
                power_label = dmg_font.render(str(int(power_val)), True, (220, 220, 255))
                icon_h = int(round(icon_size * 1.2))
                label_y = icon_y + (icon_h // 2) - (power_label.get_height() // 2)
                label_x = icon_x + icon_size + 12
                screen.blit(power_label, (label_x, label_y))
            except Exception:
                pass

        # Draw placeholder cards for incomplete rows in ships section
        num_items = len(stored_items)
        if num_items > 0:
            items_per_row = 3
            remainder = num_items % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(num_items + num_placeholders, ships_top_y)
                for placeholder_rect in full_row_rects[num_items:]:
                    draw_ph = placeholder_rect.move(0, offset_y)
                    pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)

        # ---- Materials section (title + placeholder cards) ----
        materials_title = section_font.render("INTERMEDIATE PRODUCTS", True, (220, 220, 255))
        screen.blit(
            materials_title,
            (LEFT_START, materials_title_y + offset_y),
        )

        for rect in materials_rects:
            draw_rect = rect.move(0, offset_y)
            pygame.draw.rect(screen, (20, 35, 60), draw_rect, border_radius=0)
            pygame.draw.rect(screen, (60, 100, 150), draw_rect, 1, border_radius=0)

        # ---- Modules section (unequipped modules from inventory) ----
        modules_title = section_font.render("MODULES", True, (220, 220, 255))
        screen.blit(
            modules_title,
            (LEFT_START, modules_title_y + offset_y),
        )

        # Draw module cards
        for rect, module in zip(modules_rects, modules_items):
            draw_rect = rect.move(0, offset_y)
            pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)
            draw_tier_icon_image(screen, draw_rect, getattr(module, "tier", 0))

            # preview/thumbnail
            try:
                preview_fn = getattr(module, 'preview_filename', None)
                if preview_fn:
                    loaded = pygame.image.load(PREVIEWS_DIR + "/" + preview_fn).convert_alpha()
                    img = pygame.transform.smoothscale(loaded, (48, 48))
                else:
                    img = pygame.transform.smoothscale(OREM_PREVIEW_IMG, (48, 48))
            except Exception:
                img = pygame.transform.smoothscale(OREM_PREVIEW_IMG, (48, 48))

            img_rect = img.get_rect(center=(draw_rect.x + 40, draw_rect.y + draw_rect.height // 2))
            screen.blit(img, img_rect.topleft)

            # Name label
            name_surf = name_font.render(getattr(module, 'name', 'Module'), True, (230, 230, 255))
            screen.blit(name_surf, (draw_rect.x + 96, draw_rect.y + 30))

        # Draw placeholders for modules to fill the last row (match other sections)
        items_per_row = 3
        mod_count = len(modules_items)
        if mod_count == 0:
            # draw three placeholders
            full_row_rects = layout_rects(items_per_row, modules_top_y)
            for placeholder_rect in full_row_rects:
                draw_ph = placeholder_rect.move(0, offset_y)
                pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)
        else:
            remainder = mod_count % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(mod_count + num_placeholders, modules_top_y)
                for placeholder_rect in full_row_rects[mod_count:]:
                    draw_ph = placeholder_rect.move(0, offset_y)
                    pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)

        # ---- Resources section (actual ore cards) ----
        resources_title = section_font.render("RESOURCES", True, (220, 220, 255))
        screen.blit(
            resources_title,
            (LEFT_START, resources_title_y + offset_y),
        )

        for rect, ore in zip(resource_rects, resources_items):
            draw_rect = rect.move(0, offset_y)
            # Card background (match ship card style)
            pygame.draw.rect(screen, (30, 40, 70), draw_rect, border_radius=0)
            pygame.draw.rect(screen, UI_ICON_BLUE, draw_rect, 2, border_radius=0)
            draw_tier_icon_image(screen, draw_rect, getattr(ore, "tier", 0))

            # Preview image: prefer ore-specific preview file if available
            try:
                preview_fn = getattr(ore, 'preview_filename', None)
                if preview_fn:
                    try:
                        loaded = pygame.image.load(PREVIEWS_DIR + "/" + preview_fn).convert_alpha()
                        img = pygame.transform.smoothscale(loaded, (48, 48))
                    except Exception:
                        img = pygame.transform.smoothscale(OREM_PREVIEW_IMG, (48, 48))
                else:
                    img = pygame.transform.smoothscale(OREM_PREVIEW_IMG, (48, 48))
            except Exception:
                img = pygame.transform.smoothscale(OREM_PREVIEW_IMG, (48, 48))
            img_rect = img.get_rect(
                center=(draw_rect.x + 40, draw_rect.y + draw_rect.height // 2)
            )
            screen.blit(img, img_rect.topleft)

            # Name and quantity (current amount only)
            name_surf = name_font.render(ore.name, True, (230, 230, 255))
            screen.blit(name_surf, (draw_rect.x + 96, draw_rect.y + 30))

            qty_text = f"{ore.quantity:,}"
            qty_surf = dmg_font.render(qty_text, True, (108, 198, 219))
            screen.blit(qty_surf, (draw_rect.x + 60, draw_rect.y + 50))

        # Placeholder cards for resource rows. If there are no resource items,
        # show three placeholder cards to match the other sections.
        res_count = len(resources_items)
        items_per_row = 3
        if res_count == 0:
            # draw three placeholders
            full_row_rects = layout_rects(items_per_row, resources_top_y)
            for placeholder_rect in full_row_rects:
                draw_ph = placeholder_rect.move(0, offset_y)
                pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)
        else:
            remainder = res_count % items_per_row
            if remainder != 0:
                num_placeholders = items_per_row - remainder
                full_row_rects = layout_rects(res_count + num_placeholders, resources_top_y)
                for placeholder_rect in full_row_rects[res_count:]:
                    draw_ph = placeholder_rect.move(0, offset_y)
                    pygame.draw.rect(screen, (20, 35, 60), draw_ph, border_radius=0)
                    pygame.draw.rect(screen, (60, 100, 150), draw_ph, 1, border_radius=0)

        # Reset clip so UI is unaffected
        screen.set_clip(None)

        pygame.display.flip()