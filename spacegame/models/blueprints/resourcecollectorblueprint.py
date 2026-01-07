from spacegame.models.blueprints.blueprint import Blueprint
from spacegame.models.units.resource_collector import ResourceCollector


class BPResourceCollector(Blueprint):
    """Concrete infinite blueprint for a Tier-0 Resource Collector.

    Preview image expected at `spacegame/assets/previews/BPResourceCollectorPreview.png`.
    """

    def __init__(self):
        super().__init__(
            tier=0,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="RESOURCE\nCOLLECTOR",
            description=(
                "Small deployable resource collectors. "
                "Used to mine asteroids and transfer resources back to the mothership."
            ),
        )

        self.unit_class = ResourceCollector
        self.required_ore_letter = "M"
        self.required_ore_tier = self.tier
        # Fabrication cost: 75 M-type ore
        self.required_ore_amount = 75
        self.base_fabrication_time = 6

    @property
    def name(self) -> str:
        return "Resource Collector Blueprint"

    @property
    def preview_filename(self) -> str:
        return "BPResourceCollectorPreview.png"
