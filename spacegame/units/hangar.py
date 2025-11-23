from typing import List, Optional
from spacegame.units.interceptor import Interceptor

class Hangar:
    """
    Encapsulates light-craft (interceptor) management for a mothership.

    It keeps track of:
      - slots: which hangar slots currently have a ready interceptor in hangar
      - ships: which live interceptor objects are currently deployed from each slot
      - assignments: which interceptor id from the pool is assigned to each slot
      - pool: the persistent interceptor pool (all possible interceptors, alive/dead)
    """

    def __init__(self, owner, num_slots: int = 3, pool_size: int = 5) -> None:
        self.owner = owner
        self.num_slots = num_slots

        # True = this slot currently has an interceptor ready in hangar.
        self.slots: List[bool] = [False] * num_slots

        # The actual deployed Interceptor objects, indexed by slot.
        self.ships: List[Optional[Interceptor]] = [None] * num_slots

        # Which pool interceptor is assigned to each hangar slot (or None).
        self.assignments: List[Optional[int]] = [None] * num_slots

        # Persistent interceptor pool (data only, not ship instances).
        # Each entry: {"id": int, "name": str, "alive": bool}
        self.pool: List[dict] = [
            {"id": i, "name": f"Interceptor {i+1}", "alive": True}
            for i in range(pool_size)
        ]

        # Track all currently deployed Interceptor ships from this hangar.
        self.deployed: List[Interceptor] = []

        # Default: assign first alive interceptors to slots, up to num_slots.
        alive_ids = [e["id"] for e in self.pool if e.get("alive", False)]
        for slot in range(self.num_slots):
            if slot < len(alive_ids):
                self.assignments[slot] = alive_ids[slot]
                self.slots[slot] = True

    # ---------- Query helpers ----------

    def can_deploy(self, slot: int) -> bool:
        """Return True if the given slot index has a ready interceptor in hangar."""
        return 0 <= slot < self.num_slots and self.slots[slot]

    # ---------- Deployment / recall / death hooks ----------

    def on_deployed(self, slot: int, ship: Interceptor) -> None:
        """
        Called when an interceptor is spawned from a given slot.
        Updates internal bookkeeping so the slot is marked as empty (no ready ship)
        and the ship is tracked as deployed.
        """
        if not (0 <= slot < self.num_slots):
            return

        self.slots[slot] = False
        self.ships[slot] = ship
        if ship not in self.deployed:
            self.deployed.append(ship)

        # remember source slot on the ship itself
        ship.hangar_slot = slot
        ship.recalling = False

    def on_recalled(self, interceptor: Interceptor) -> None:
        """
        Called when a recalling interceptor has successfully docked back
        into the mothership. The corresponding slot becomes 'ready' again.
        """
        slot = getattr(interceptor, "hangar_slot", None)
        if slot is None:
            return
        if 0 <= slot < self.num_slots:
            self.slots[slot] = True
            self.ships[slot] = None

        if interceptor in self.deployed:
            self.deployed.remove(interceptor)

    def on_interceptor_dead(self, interceptor: Interceptor) -> None:
        """
        Called when an interceptor is destroyed.
        Marks its pool entry as not alive and clears any slot / assignment
        that referenced it.
        """
        interceptor_id = getattr(interceptor, "interceptor_id", None)
        if interceptor_id is not None:
            for entry in self.pool:
                if entry.get("id") == interceptor_id:
                    entry["alive"] = False
                    break

        slot = getattr(interceptor, "hangar_slot", None)
        if slot is not None and 0 <= slot < self.num_slots:
            self.slots[slot] = False
            self.ships[slot] = None
            self.assignments[slot] = None

        if interceptor in self.deployed:
            self.deployed.remove(interceptor)

    # ---------- Slot assignment API (used by management UIs) ----------

    def clear_slot(self, slot: int) -> None:
        """Remove any assignment / ship from the given slot."""
        if not (0 <= slot < self.num_slots):
            return

        self.assignments[slot] = None
        self.slots[slot] = False
        self.ships[slot] = None

    def assign_to_slot(self, slot: int, interceptor_id: int) -> None:
        """
        Assign an existing (alive) interceptor from the pool into the given slot.
        The slot becomes 'ready' in hangar.
        """
        if not (0 <= slot < self.num_slots):
            return

        # ensure the id exists and is alive
        exists_alive = any(
            e.get("id") == interceptor_id and e.get("alive", False)
            for e in self.pool
        )
        if not exists_alive:
            return

        self.assignments[slot] = interceptor_id
        self.slots[slot] = True

        ship = self.ships[slot]
        if ship is not None and ship.health <= 0.0:
            self.ships[slot] = None
