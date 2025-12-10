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

    # ---- Inventory ops ----
    def get_amount(self, ore_letter: str) -> int:
        return int(self.inventory.get(str(ore_letter), 0))

    def set_amount(self, ore_letter: str, amount: int) -> None:
        self.inventory[str(ore_letter)] = int(amount)

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

    def consume_resource(self, ore_letter: str, amount: int) -> bool:
        """Attempt to consume `amount` of `ore_letter`. Returns True if successful."""
        if amount <= 0:
            return True
        have = int(self.inventory.get(str(ore_letter), 0))
        if have < amount:
            return False
        self.inventory[str(ore_letter)] = have - int(amount)
        return True

    # ---- Generic item ops (non-ore items) ----
    def add_item(self, key: str, amount: int = 1) -> None:
        """Add a non-ore inventory item keyed by `key` (e.g. blueprint names)."""
        if amount <= 0:
            return
        k = str(key)
        self.inventory[k] = int(self.inventory.get(k, 0)) + int(amount)

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

    def get_hangar_pool(self):
        if self.hangar is None:
            raise RuntimeError("No Hangar registered on InventoryManager")
        return getattr(self.hangar, 'pool', None)
