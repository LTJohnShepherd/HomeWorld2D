from spacegame.models.blueprints.blueprint import Blueprint


class BPRefinery(Blueprint):
    """Concrete infinite blueprint for a Tier 1 refinery module.

    Preview image expected at `spacegame/assets/previews/BPRefineryPreview.png`.
    """

    def __init__(self):
        super().__init__(
            tier=1,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="REFINERY\nMODULE",
            description=(
                "An efficient refinery module capable of processing "
                "raw ores into refined materials. Tier 1 version."
            ),
        )

        # Resource costs: 500 refined A, 1000 M ore, 1750 refined C
        self.required_resources = {
            "A": 500,      # Tier 1 Refined A
            "M": 1000,      # M ore
            "C": 1750,     # Tier 1 Refined C
        }
        
        # Base fabrication time in seconds (5 minutes)
        self.base_fabrication_time = 300

    @property
    def name(self) -> str:
        return "Refinery Module Blueprint"

    @property
    def preview_filename(self) -> str:
        return "BPRefineryPreview.png"
