from spacegame.models.blueprints.blueprint import Blueprint
from spacegame.models.units.frigate import Frigate


class BPEscortFrigate(Blueprint):
    """Concrete infinite blueprint for a Tier-0 Escort Frigate.

    Uses the Resource Collector preview temporarily as requested.
    """

    def __init__(self):
        super().__init__(
            tier=0,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="ESCORT\nFRIGATE",
            description=(
                "A small escort frigate used for fleet defense and escort duties."
            ),
        )

        self.unit_class = Frigate
        self.required_ore_letter = "M"
        self.required_ore_tier = self.tier
        # Cost as requested: 1125 M-type ore
        self.required_ore_amount = 1125
        self.base_fabrication_time = 20

    @property
    def name(self) -> str:
        return "Escort Frigate Blueprint"

    @property
    def preview_filename(self) -> str:
        # use resource collector BP image temporarily
        return "BPResourceCollectorPreview.png"
