from dataclasses import dataclass
from typing import Any


@dataclass
class HangarEntry:
    """Represents a single light-craft in the persistent hangar pool."""
    id: int
    name: str
    unit_type: str = ""
    alive: bool = True
    tier: int = 0
    rarity: str = ""


class Hangar:
    """Encapsulates light-craft management for a mothership.

    It keeps track of:
      - slots: which hangar slots currently have a ready craft in hangar
      - ships: which live unit objects are currently deployed from each slot
      - assignments: which pool entry id is assigned to each slot
      - pool: the persistent pool (all possible crafts, alive/dead, any unit_type)
    """

    def __init__(self, owner, num_slots: int = 3, interceptor_pool_size: int = 5, collector_pool_size: int = 0) -> None:
        self.owner = owner
        self.num_slots = num_slots

        # True = this slot currently has a craft ready in hangar.
        self.slots = [False] * num_slots

        # The actual deployed unit objects, indexed by slot.
        self.ships = [None] * num_slots  # type: list[Any | None]

        # Which pool entry is assigned to each hangar slot (or None).
        self.assignments = [None] * num_slots  # type: list[int | None]

        # Persistent pool (data only, not ship instances).
        # Initialized with both interceptors and resource collectors at game start.
        self.pool = self._initialize_pool(interceptor_pool_size, collector_pool_size)

        # Track all currently deployed ships from this hangar.
        self.deployed = []

        # Default: assign first alive entries to slots, up to num_slots.
        self._assign_default_slots()


    # ---------- Pool initialization ----------

    def _initialize_pool(self, interceptor_count: int, collector_count: int) -> list[HangarEntry]:
        """Create and return the initial hangar pool with interceptors and collectors.
        
        This method is called once at Hangar initialization to set up all beginner
        crafts. It creates `interceptor_count` interceptors followed by `collector_count`
        resource collectors, assigning them unique sequential IDs.
        
        Args:
            interceptor_count: Number of interceptor entries to create.
            collector_count: Number of resource collector entries to create.
        
        Returns:
            List of HangarEntry objects with unique IDs.
        """
        pool = []
        entry_id = 0

        # Create interceptor entries (IDs 0 to interceptor_count-1)
        for i in range(interceptor_count):
            pool.append(HangarEntry(
                id=entry_id,
                name=f"Interceptor {i+1}",
                unit_type="interceptor"
            ))
            entry_id += 1

        # Create resource collector entries (IDs starting after interceptors)
        for j in range(collector_count):
            pool.append(HangarEntry(
                id=entry_id,
                name=f"Collector {j+1}",
                unit_type="resource_collector"
            ))
            entry_id += 1

        return pool

    def _assign_default_slots(self) -> None:
        """Assign the first alive pool entries to available hangar slots.
        Called during initialization to populate slots with default assignments.
        """
        alive_ids = [e.id for e in self.pool if e.alive]
        for slot in range(self.num_slots):
            if slot < len(alive_ids):
                self.assignments[slot] = alive_ids[slot]
                self.slots[slot] = True

    # ---------- Query helpers ----------

    def can_deploy(self, slot: int) -> bool:
        """Return True if the given slot index has a ready interceptor in hangar."""
        return 0 <= slot < self.num_slots and self.slots[slot]

    def get_entry_by_id(self, entry_id: int) -> HangarEntry | None:
        """Return the pool entry with the given id, or None if not found."""
        for entry in self.pool:
            if entry.id == entry_id:
                return entry
        return None

    def get_entry_for_slot(self, slot: int) -> HangarEntry | None:
        """Return the pool entry assigned to a given slot, if any and alive."""
        if not (0 <= slot < self.num_slots):
            return None
        entry_id = self.assignments[slot]
        if entry_id is None:
            return None
        entry = self.get_entry_by_id(entry_id)
        if entry is None or not entry.alive:
            return None
        return entry


    # ---------- Deployment / recall / death hooks ----------
    def on_deployed(self, slot: int, ship: Any) -> None:
        """
        Called when a craft is spawned from a given slot.
        Updates internal bookkeeping so the slot is marked as empty (no ready ship)
        and the ship is tracked as deployed.
        """
        if not (0 <= slot < self.num_slots):
            return

        self.slots[slot] = False
        self.ships[slot] = ship
        if ship not in self.deployed:
            self.deployed.append(ship)

        # Apply per-ship tier from the pool for this assignment (if available)
        entry = self.get_entry_for_slot(slot)
        if entry is not None and hasattr(ship, "tier"):
            ship.tier = entry.tier

        # remember source slot on the ship itself
        setattr(ship, "hangar_slot", slot)
        setattr(ship, "recalling", False)
        # remember mothership reference so craft can return to offload resources
        try:
            setattr(ship, "mothership", self.owner)
        except Exception:
            pass

    def on_recalled(self, ship: Any) -> None:
        """
        Called when a recalling craft has successfully docked back
        into the mothership. The corresponding slot becomes 'ready' again.
        """
        slot = getattr(ship, "hangar_slot", None)
        if slot is None:
            return
        if 0 <= slot < self.num_slots:
            self.slots[slot] = True
            self.ships[slot] = None

        if ship in self.deployed:
            self.deployed.remove(ship)

    def on_interceptor_dead(self, ship: Any) -> None:
        """
        Called when a craft (currently interceptor) is destroyed.
        Marks its pool entry as not alive and clears any slot / assignment
        that referenced it.

        Note: still uses 'interceptor_id' attribute for backwards compatibility.
        """
        entry_id = getattr(ship, "interceptor_id", None)
        if entry_id is not None:
            entry = self.get_entry_by_id(entry_id)
            if entry is not None:
                entry.alive = False

        slot = getattr(ship, "hangar_slot", None)
        if slot is not None and 0 <= slot < self.num_slots:
            self.slots[slot] = False
            self.ships[slot] = None
            self.assignments[slot] = None

        if ship in self.deployed:
            self.deployed.remove(ship)


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

        entry = self.get_entry_by_id(interceptor_id)
        if entry is None or not entry.alive:
            return

        self.assignments[slot] = interceptor_id
        self.slots[slot] = True

        ship = self.ships[slot]
        if ship is not None and ship.health <= 0.0:
            self.ships[slot] = None

    # ---------- Query helpers for UI screens ----------

    def alive_pool_entries(self):
        """Return a list of pool entries that are still marked as alive."""
        return [e for e in self.pool if e.alive]

    def selected_interceptor_ids(self):
        """Return a set of interceptor IDs that are assigned to any slot and still alive."""
        alive_ids = {e.id for e in self.pool if e.alive}
        result = set()
        for interceptor_id in self.assignments:
            if interceptor_id is None:
                continue
            if interceptor_id in alive_ids:
                result.add(interceptor_id)
        return result


    def snapshot(self):
        """Return a simple snapshot of the current hangar state.

        Returns (assignments, ships, pool_by_id) where:
          - assignments: list of interceptor ids per slot
          - ships: list of Interceptor (or None) per slot
          - pool_by_id: dict[id] -> InterceptorEntry
        """
        assignments = list(self.assignments)
        ships = list(self.ships)
        pool_by_id = {entry.id: entry for entry in self.pool}
        return assignments, ships, pool_by_id


    def iter_slot_infos(self):
        """Yield dictionaries describing the state of each hangar slot."""
        for idx in range(self.num_slots):
            ship = self.ships[idx]
            ship_alive = bool(ship is not None and getattr(ship, "health", 0.0) > 0.0)
            yield {
                "index": idx,
                "assigned_id": self.assignments[idx],
                "ready_in_hangar": self.slots[idx],
                "ship": ship,
                "ship_alive": ship_alive,
            }
