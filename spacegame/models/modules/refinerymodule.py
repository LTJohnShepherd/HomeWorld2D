from spacegame.models.modules.module import ShipModule


class RefineryModule(ShipModule):
    """
    Concrete implementation of a ship Refinery module.

    Mirrors FabricatorModule structure but exposes `base_refinement_time`.
    """

    def __init__(
        self,
        *,
        tier: int = 1,
        module_size: int = 72,
        base_refinement_time: float = 1.0,
        # standard time in seconds for one conversion (200 -> 100)
        standard_refinement_time_s: float = 75.0,
    ):
        # In this game, "module size" is also the capacity this module uses.
        super().__init__(tier=tier, capacity=module_size)
        self.module_size: int = int(module_size)
        # Refinery modules are intended for the middle internal section by default
        # (index 1). This value controls where the UI will allow them to be mounted.
        self.allowed_sections = [1]
        # Measured in "refinement time units" (could be minutes / turns etc.)
        self.base_refinement_time: float = float(base_refinement_time)
        # Standard time (seconds) for converting 200 raw ore -> 100 refined output
        self.standard_refinement_time_s: float = float(standard_refinement_time_s)

    @property
    def name(self) -> str:
        return "Refinery"

    @property
    def preview_filename(self) -> str:
        return "RefineryModule.png"


def get_refinery_modules_for_ship():
    """
    Return the list of Refinery modules installed in the ship's
    middle internal section.

    This is used by the internal-modules screen and Refinery
    screens so that the number of slots (01, 02, ...) stays in sync.
    """
    # Prefer the centralised ModulesManager as the source of truth when available.
    try:
        from spacegame.core.modules_manager import manager

        return manager.get_refineries() or []
    except Exception:
        # backward-compatible default for legacy callers
        return [RefineryModule(tier=1, module_size=72, base_refinement_time=1.0)]
