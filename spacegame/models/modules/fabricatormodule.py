from spacegame.models.modules.module import ShipModule


class FabricatorModule(ShipModule):
    """
    Concrete implementation of a ship Fabricator module.

    The numbers here mirror the values shown in the Fabrication main screen,
    but are stored as real numbers so they can be used in calculations
    instead of hard-coded strings in the UI.
    """

    def __init__(
        self,
        *,
        tier: int = 1,
        module_size: int = 72,
        base_fabrication_time: float = 1.0,
    ):
        # In this game, "module size" is also the capacity this module uses.
        super().__init__(tier=tier, capacity=module_size)
        self.module_size: int = int(module_size)
        # Fabricator modules are intended for the middle internal section by default
        # (index 1). This value controls where the UI will allow them to be mounted.
        self.allowed_sections = [1]
        # Measured in "fabrication time units" (could be minutes / turns etc.)
        self.base_fabrication_time: float = float(base_fabrication_time)

    @property
    def name(self) -> str:
        return "Fabricator"

    @property
    def preview_filename(self) -> str:
        # Temporary: reuse the RU TYPE M ORE preview art
        # until a dedicated Fabricator module icon exists.
        return "FabricatorModule.png"
    
def get_fabricator_modules_for_ship():
    """
    Return the list of Fabricator modules installed in the ship's
    middle internal section.

    This is used by the internal-modules screen and both Fabricator
    screens so that the number of slots (01, 02, ...) stays in sync.
    """
    # Prefer the centralised ModulesManager as the source of truth when available.
    try:
        from spacegame.core.modules_manager import manager

        return manager.get_fabricators() or []
    except Exception:
        # backward-compatible default for legacy callers
        return [FabricatorModule(tier=1, module_size=72, base_fabrication_time=1.0)]