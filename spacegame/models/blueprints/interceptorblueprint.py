from spacegame.models.blueprints.blueprint import Blueprint
from spacegame.models.units.interceptor import Interceptor

class BPInterceptor(Blueprint):
    """Concrete infinite blueprint for a Tier-0 interceptor.

    Preview image expected at `spacegame/assets/previews/BPInterceptorPreview.png`.
    """

    def __init__(self):
        super().__init__(
            tier=0,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="INTERCEPTOR\nSQUADRON",
            description=(
                "The Interceptor is a fast, maneuverable "
                "and versatile craft designed for patrol "
                "escort, and Capital Ship defense"
            ),
        )

        self.unit_class = Interceptor
        self.required_ore_letter = "M"
        self.required_ore_tier = self.tier
        self.required_ore_amount = 625
        self.base_fabrication_time = 9

    @property
    def name(self) -> str:
        return "Interceptor Blueprint"

    @property
    def preview_filename(self) -> str:
        return "BPInterceptorPreview.png"
