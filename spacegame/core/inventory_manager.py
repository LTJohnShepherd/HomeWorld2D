"""Inventory manager: single source of truth for resources and notifications.

This module centralizes inventory and notifications. All systems must use
the `InventoryManager` APIs on the player (e.g. `player.inventory_manager`).
Hangar operations are forwarded to a registered `Hangar` instance and are
strict: the hangar must be registered before modifying its pool.
"""
from typing import Dict, List, Optional


class InventoryManager:
    """Manage a simple inventory mapping ore_letter -> int and notifications.

    This class is the authoritative storage for player resources and in-game
    notifications.
    """

    def __init__(self, owner=None):
        self.owner = owner
        self.inventory: Dict[str, int] = {}
        # notifications are dicts: {'ore_letter','amount','elapsed','duration','preview'(opt)}
        self.notifications: List[Dict] = []

        # Placeholder for hangar integration; hangar instance can register itself
        # and the inventory manager will forward hangar modifications directly.
        self.hangar = None
        # Non-ore items stored as objects (e.g. unequipped modules)
        # Stored as a simple list of module instances.
        self.modules: List[object] = []

    def _trigger_autosave(self) -> None:
        """Post a custom SAVE_GAME event so the running screen loop performs the save.

        This replaces the previous direct save call. The event contains an
        `owner` attribute with the object to save.
        """
        # Avoid module-level cycles by importing here.
        try:
            import pygame
            from spacegame.core import events as _events

            ev = _events.make_save_game_event(self.owner)
            try:
                pygame.event.post(ev)
            except Exception:
                # If posting to the event queue fails (unlikely), fall back
                # to performing a direct save below.
                pass
        except Exception:
            # If events/pygame cannot be imported for any reason, continue
            # and attempt a direct save below.
            pass

        # Also perform a direct save immediately to ensure persistence even
        # when the current screen's event loop doesn't handle the custom event.
        try:
            from spacegame.core import save as _save

            try:
                _save.save_game(self.owner)
            except Exception:
                pass
        except Exception:
            pass

    # ---- Inventory ops ----
    def get_amount(self, ore_letter: str) -> int:
        return int(self.inventory.get(str(ore_letter), 0))

    def set_amount(self, ore_letter: str, amount: int) -> None:
        self.inventory[str(ore_letter)] = int(amount)
        try:
            self._trigger_autosave()
        except Exception:
            pass

    def add_resource(self, ore_letter: str, amount: int, preview: Optional[str] = None) -> None:
        """Add `amount` of resource `ore_letter` to inventory and emit a notification.

        Keeps behavior consistent with previous `ExpeditionShip.add_resource`.
        """
        if amount <= 0:
            return
        ore_letter = str(ore_letter)
        current = int(self.inventory.get(ore_letter, 0))
        self.inventory[ore_letter] = current + int(amount)

        # build notification dict (kept light)
        notif = {
            'ore_letter': ore_letter,
            'amount': int(amount),
            'elapsed': 0.0,
            'duration': 3.0,
        }
        if preview:
            notif['preview'] = preview
        self.notifications.append(notif)
        try:
            self._trigger_autosave()
        except Exception:
            pass

    def consume_resource(self, ore_letter: str, amount: int) -> bool:
        """Attempt to consume `amount` of `ore_letter`. Returns True if successful."""
        if amount <= 0:
            return True
        have = int(self.inventory.get(str(ore_letter), 0))
        if have < amount:
            return False
        self.inventory[str(ore_letter)] = have - int(amount)
        try:
            self._trigger_autosave()
        except Exception:
            pass
        return True

    # ---- Generic item ops (non-ore items) ----
    def add_item(self, key: str, amount: int = 1) -> None:
        """Add a non-ore inventory item keyed by `key` (e.g. blueprint names)."""
        if amount <= 0:
            return
        k = str(key)
        self.inventory[k] = int(self.inventory.get(k, 0)) + int(amount)
        try:
            self._trigger_autosave()
        except Exception:
            pass

    # ---- Module list ops ----
    def add_module(self, module_obj) -> None:
        """Add a module instance to the unequipped modules list."""
        if module_obj is None:
            return
        self.modules.append(module_obj)
        try:
            self._trigger_autosave()
        except Exception:
            pass

    def remove_module(self, module_obj) -> bool:
        """Remove a module instance from the unequipped modules list. Returns True if removed."""
        # Prefer exact identity removal
        try:
            self.modules.remove(module_obj)
            try:
                self._trigger_autosave()
            except Exception:
                pass
            return True
        except ValueError:
            # Fallback: try to remove a module that matches by type and a set
            # of likely identifying attributes (name, tier, capacity/module_size).
            try:
                for m in list(self.modules):
                    try:
                        if type(m) is type(module_obj):
                            # compare a number of common attributes if present
                            same_tier = getattr(m, 'tier', None) == getattr(module_obj, 'tier', None)
                            same_capacity = (
                                getattr(m, 'capacity', None) == getattr(module_obj, 'capacity', None)
                                or getattr(m, 'module_size', None) == getattr(module_obj, 'module_size', None)
                            )
                            same_name = False
                            try:
                                name_m = getattr(m, 'name', None)
                                name_o = getattr(module_obj, 'name', None)
                                if name_m is not None and name_o is not None:
                                    same_name = str(name_m) == str(name_o)
                            except Exception:
                                same_name = False

                            # Accept a match if name and tier match, or tier+capacity match
                            if (same_name and same_tier) or (same_tier and same_capacity):
                                self.modules.remove(m)
                                try:
                                    self._trigger_autosave()
                                except Exception:
                                    pass
                                return True
                    except Exception:
                        continue
            except Exception:
                pass
            return False

    def get_modules(self) -> List[object]:
        """Return a shallow copy of unequipped module instances."""
        return list(self.modules)

    # ---- Notifications ----
    def add_notification(self, notif: Dict) -> None:
        """Append a prepared notification dict to the active notifications list."""
        if not isinstance(notif, dict):
            return
        # Ensure minimal fields
        notif.setdefault('elapsed', 0.0)
        notif.setdefault('duration', notif.get('duration', 3.0))
        self.notifications.append(notif)

    def update(self, dt: float) -> None:
        """Advance notification timers and drop expired entries.

        Removes notifications whose elapsed time exceeds their duration.
        """
        if not self.notifications:
            return
        remaining = []
        for n in self.notifications:
            n['elapsed'] = n.get('elapsed', 0.0) + float(dt)
            if n['elapsed'] < n.get('duration', 3.0):
                remaining.append(n)
        self.notifications = remaining

    # ---- Hangar integration hooks (optional) ----
    def register_hangar(self, hangar):
        """Register a `Hangar` instance for optional inventory-backed hangar persistence."""
        # Strict registration: simply keep a reference to the hangar instance.
        # No fallback initialization from prior saved state is supported.
        self.hangar = hangar

    def add_hangar_entry(self, entry) -> None:
        """Add a `HangarEntry` to the registered hangar pool.

        This centralizes hangar pool modifications. Registration of a `Hangar`
        instance via `register_hangar()` is required before calling this
        method; otherwise a `RuntimeError` is raised.
        """
        if self.hangar is None:
            raise RuntimeError("No Hangar registered on InventoryManager; cannot add hangar entry")
        # Append directly to the hangar pool; let any higher-level persistence
        # be handled by the owning systems.
        self.hangar.pool.append(entry)
        try:
            self._trigger_autosave()
        except Exception:
            pass

    def get_hangar_pool(self):
        if self.hangar is None:
            raise RuntimeError("No Hangar registered on InventoryManager")
        return getattr(self.hangar, 'pool', None)
