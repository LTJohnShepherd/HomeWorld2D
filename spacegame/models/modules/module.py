from abc import ABC, abstractmethod


class ShipModule(ABC):
    """
    Abstract base class for ship internal modules.

    Every module consumes some capacity in the internal–modules screen.
    The three core properties that all modules share are:
    - name: display name of the module
    - tier: tech / upgrade level (integer)
    - capacity: how many capacity points the module occupies

    Concrete modules should also expose a `preview_filename` property
    so UI screens can render a consistent preview icon, similar to the
    Blueprint and Ore models.
    """

    def __init__(self, *, tier: int, capacity: int):
        self.tier = int(tier)
        self.capacity = int(capacity)

        # Which internal sections this module can be mounted into.
        # Sections use indices: 0=left, 1=middle, 2=right.
        # By default modules are allowed on any section unless overridden.
        self.allowed_sections = [0, 1, 2]

    def is_mountable_on(self, section_index: int) -> bool:
        """Return True if this module can be mounted on the given section index."""
        try:
            return int(section_index) in list(self.allowed_sections)
        except Exception:
            return False

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable module name used in the UI."""

    @property
    @abstractmethod
    def preview_filename(self) -> str:
        """Filename (inside PREVIEWS_DIR) for this module's preview image."""