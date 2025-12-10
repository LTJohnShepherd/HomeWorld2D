from spacegame.models.blueprints.blueprint import Blueprint
from spacegame.models.units.plasma_bomber import PlasmaBomber


class BPPlasmaBomber(Blueprint):
    """Concrete infinite blueprint for the Tier-0 Plasma Bomber.

    Preview image expected at `spacegame/assets/previews/BPPlasmaBomberPreview.png`.
    """

    def __init__(self):
        super().__init__(
            tier=0,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="PLASMA\nBOMBER",
            description=(
                "A heavy light-craft specialized for anti-armor strikes. "
                "Trades maneuverability for increased damage and durability."
            ),
        )

        self.unit_class = PlasmaBomber
        self.required_ore_letter = "M"
        self.required_ore_tier = self.tier
        # Cost chosen to be larger than a single interceptor squadron
        self.required_ore_amount = 625
        self.base_fabrication_time = 12

    @property
    def name(self) -> str:
        return "Plasma Bomber Blueprint"

    @property
    def preview_filename(self) -> str:
        return "BPBomberPreview.png"
