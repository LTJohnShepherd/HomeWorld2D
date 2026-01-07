import pygame
from typing import List
from spacegame.models.modules.fabricatormodule import FabricatorModule
from spacegame.core.modules_manager import manager as modules_manager
from spacegame.core.hangar import HangarEntry
from spacegame.core.sound_manager import get_sound_manager


class FabricationManager:
    """Manage fabricator modules and fabrication timers for a player/ship.

    The manager holds module instances and exposes helper methods to start,
    cancel, and speed-up fabrications. It also computes progress so UI
    screens can read consistent, persistent values.
    """

    def __init__(self):
        # FabricationManager no longer owns module persistence; modules are
        # provided by the central ModulesManager. Keep only UI selection state.
        self.selected_index: int = 0
        # owner/player reference (set by get_fabrication_manager)
        self.player = None

    def get_modules(self) -> List[FabricatorModule]:
        return modules_manager.get_fabricators()

    def get_module(self, index: int) -> FabricatorModule:
        mods = self.get_modules() or []
        if 0 <= index < len(mods):
            return mods[index]
        return None

    def start_fabrication(self, index: int, blueprint, player) -> bool:
        """Start fabricating `blueprint` in module `index` if resources exist.

        Consumes required ore from the player's `InventoryManager` (`player.inventory_manager`).
        Returns True if fabrication started, False otherwise.
        """
        module = self.get_module(index)
        if blueprint is None:
            return False

        ore_letter = getattr(blueprint, "required_ore_letter", None)
        ore_amount = int(getattr(blueprint, "required_ore_amount", 0))
        # Use InventoryManager API for resource checks/consumption
        inv_mgr = getattr(player, 'inventory_manager', None)
        # Require InventoryManager to be present for resource checks
        if inv_mgr is None and ore_letter is not None:
            return False
        available = inv_mgr.get_amount(ore_letter) if ore_letter is not None else 0

        if available < ore_amount:
            return False

        # Compute true fabrication time as: blueprint base time * module factor
        # Blueprint `base_fabrication_time` is typically expressed in seconds.
        # Module `base_fabrication_time` is a multiplier (e.g. 1.0).
        blueprint_time = float(getattr(blueprint, "base_fabrication_time", 0))
        if module is None:
            return False

        module_factor = float(getattr(module, "base_fabrication_time", 1.0))
        total_seconds = blueprint_time * module_factor
        total_ms = max(1, int(total_seconds * 1000))
        module.fabrication_total_ms = int(total_ms)
        module.fabrication_start_ticks = int(pygame.time.get_ticks())
        module.fabrication_blueprint = blueprint
        module.fabrication_progress = 0.0

        # consume ore from player inventory (if applicable)
        if ore_letter is not None:
            # InventoryManager is required here (we returned False earlier if missing),
            # consume via the manager and raise if it's unexpectedly absent.
            if inv_mgr is None:
                raise RuntimeError("InventoryManager required to consume fabrication resources")
            inv_mgr.consume_resource(ore_letter, ore_amount)

        # attach owner reference so manager can finalize on completion
        try:
            self.player = player
        except Exception:
            pass

        return True

    def cancel_fabrication(self, index: int) -> None:
        module = self.get_module(index)
        if module is None:
            return
        module.fabrication_total_ms = 0
        module.fabrication_start_ticks = 0
        module.fabrication_progress = 0.0
        module.fabrication_blueprint = None

    def speed_up(self, index: int) -> None:
        module = self.get_module(index)
        if module is None:
            return
        total_ms = int(getattr(module, "fabrication_total_ms", 0))
        if total_ms > 0:
            # set start_ticks so that elapsed >= total_ms (complete instantly)
            module.fabrication_start_ticks = int(pygame.time.get_ticks()) - int(total_ms)

    def get_status(self, index: int):
        """Compute and return status info for module `index`.

        Returns a dict with keys: total_ms, start_ticks, progress (0.0-1.0), remaining_s,
        is_fabricating (bool), blueprint
        """
        module = self.get_module(index)
        # If the module has no assigned blueprint, consider it idle regardless
        # of any lingering timer fields.
        blueprint = getattr(module, "fabrication_blueprint", None) if module is not None else None
        if blueprint is None:
            # No active fabrication assigned to this module. Return idle status.
            # Do not expose the module's internal `base_fabrication_time` here
            # (it's a multiplier), because UIs that display blueprint times
            # should compute blueprint_time * module_factor themselves.
            progress = 0.0
            remaining_s = 0
            if module is not None:
                try:
                    module.fabrication_progress = progress
                    module.fabrication_remaining_s = remaining_s
                except Exception:
                    pass
            return {
                "total_ms": 0,
                "start_ticks": 0,
                "progress": progress,
                "remaining_s": remaining_s,
                "is_fabricating": False,
                "blueprint": None,
            }

        total_ms = int(getattr(module, "fabrication_total_ms", 0)) if module is not None else 0
        start_ticks = int(getattr(module, "fabrication_start_ticks", 0)) if module is not None else 0
        now_ticks = int(pygame.time.get_ticks())

        if total_ms > 0 and start_ticks > 0:
            elapsed = max(0, now_ticks - start_ticks)
            progress = min(1.0, elapsed / float(total_ms))
            remaining_ms = max(0, total_ms - elapsed)
            remaining_s = remaining_ms // 1000
            is_fabricating = progress < 1.0
            # If fabrication completed, finalize result and clear module
            if progress >= 1.0:
                try:
                    self._finalize_module(index)
                except Exception:
                    # don't let finalization errors break UI; report idle instead
                    pass
        else:
            progress = 0.0
            remaining_s = int(getattr(module, "base_fabrication_time", 0)) if module is not None else 0
            is_fabricating = False

        # keep module fields in sync for UI code
        if module is not None:
            module.fabrication_progress = progress
            module.fabrication_remaining_s = remaining_s

        return {
            "total_ms": total_ms,
            "start_ticks": start_ticks,
            "progress": progress,
            "remaining_s": remaining_s,
            "is_fabricating": is_fabricating,
            "blueprint": getattr(module, "fabrication_blueprint", None),
        }

    def _finalize_module(self, index: int) -> None:
        """Finalize a completed fabrication.

        Creates a new `HangarEntry` for the completed blueprint and adds it to
        the owner's registered `Hangar` via the owner's `InventoryManager`.
        This method requires the player to have a registered `InventoryManager`
        with a `hangar` and will raise if those contracts are not met.

        Clears the module fabrication state after successful finalization.
        """
        module = self.get_module(index)
        bp = getattr(module, "fabrication_blueprint", None)
        if bp is None:
            return

        # Add the produced unit to the player's Hangar via InventoryManager.
        player = getattr(self, "player", None)
        if player is None:
            raise RuntimeError("No player associated with FabricationManager during finalization")

        inv_mgr = getattr(player, 'inventory_manager', None)
        if inv_mgr is None or getattr(inv_mgr, 'hangar', None) is None:
            raise RuntimeError("Player missing InventoryManager.hangar; cannot finalize fabrication without hangar")

        hangar = inv_mgr.hangar
        # choose unit_type from blueprint.unit_class if present
        unit_cls = getattr(bp, "unit_class", None)
        unit_type = ""
        if unit_cls is not None:
            name = getattr(unit_cls, "__name__", "Unit")
            if "Interceptor" in name:
                unit_type = "interceptor"
            elif "Collector" in name or "ResourceCollector" in name:
                unit_type = "resource_collector"
            elif "Bomber" in name or "Plasma" in name:
                unit_type = "plasma_bomber"

        # generate new pool id
        existing_ids = [e.id for e in hangar.pool] if hangar.pool else []
        next_id = max(existing_ids) + 1 if existing_ids else 0
        entry_name = getattr(bp, "title", getattr(bp, "name", "Craft"))
        entry = HangarEntry(id=next_id, name=entry_name, unit_type=unit_type, alive=True, tier=getattr(bp, "tier", 0), rarity=getattr(bp, "rarity", ""))
        # Add via InventoryManager (strict)
        inv_mgr.add_hangar_entry(entry)

        # Notify player (if present) so gameplay HUD can show a popup
        try:
            if player is not None:
                notif = {
                    'type': 'fabrication',
                    'title': entry_name,
                    'elapsed': 0.0,
                    'duration': 3.5,
                }
                # include preview filename when blueprint supplies one
                try:
                    preview = getattr(bp, 'preview_filename', None)
                    if preview:
                        notif['preview'] = preview
                except Exception:
                    pass

                # Use InventoryManager to add notification if available
                try:
                    inv_mgr = getattr(player, 'inventory_manager', None)
                    if inv_mgr is not None:
                        inv_mgr.add_notification(notif)
                except Exception:
                    pass
        except Exception:
            pass

        # Play fabrication complete sound
        try:
            sound_manager = get_sound_manager()
            sound_manager.on_fabrication_complete()
        except Exception:
            pass

        # Clear module fabrication state
        module.fabrication_total_ms = 0
        module.fabrication_start_ticks = 0
        module.fabrication_progress = 0.0
        module.fabrication_blueprint = None
        module.fabrication_remaining_s = 0

    def get_selected_index(self) -> int:
        # clamp to valid range
        mods = self.get_modules() or []
        if not mods:
            return 0
        return max(0, min(self.selected_index, len(mods) - 1))

    def set_selected_index(self, index: int) -> None:
        mods = self.get_modules() or []
        if not mods:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(int(index), len(mods) - 1))

    def update(self) -> None:
        """Perform a passive per-frame update: check all modules and finalize
        any fabrications that reached completion. This should be called from
        the game's main loop so completions are processed even when no
        fabrication UI is open.
        """
        # iterate modules and call get_status which will internally finalize
        # completed modules (get_status already contains the finalize call).
        try:
            mods = self.get_modules() or []
            for i in range(len(mods)):
                # ignore returned status; get_status has side-effects we rely on
                self.get_status(i)
        except Exception:
            # swallow exceptions to avoid interrupting the game loop
            pass


def get_fabrication_manager(player) -> FabricationManager:
    """Return a FabricationManager attached to `player`, creating one if needed."""
    if player is None:
        # fallback global manager
        if not hasattr(get_fabrication_manager, "_global"):
            get_fabrication_manager._global = FabricationManager()
        return get_fabrication_manager._global

    if not hasattr(player, "_fabrication_manager"):
        player._fabrication_manager = FabricationManager()
    return player._fabrication_manager
