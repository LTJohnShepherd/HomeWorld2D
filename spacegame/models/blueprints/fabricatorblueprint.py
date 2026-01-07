from spacegame.models.blueprints.blueprint import Blueprint


class BPFabricator(Blueprint):
    """Concrete infinite blueprint for a Tier 1 fabricator module.

    Preview image expected at `spacegame/assets/previews/BPFabricatorPreview.png`.
    """

    def __init__(self):
        super().__init__(
            tier=1,
            stack_size=9999,
            quantity=float("inf"),
            rarity="COMMON",
            title="FABRICATOR\nMODULE",
            description=(
                "An advanced fabricator module capable of constructing "
                "strike craft and ship components. Tier 1 version."
            ),
        )

        # Copy same resource costs as the refinery blueprint
        self.required_resources = {
            "A": 500,      # Tier 1 Refined A
            "M": 1000,     # M ore
            "C": 1750,     # Tier 1 Refined C
        }

        # Base fabrication time in seconds (same as refinery)
        self.base_fabrication_time = 300

    @property
    def name(self) -> str:
        return "Fabricator Module Blueprint"

    @property
    def preview_filename(self) -> str:
        return "BPFabricatorPreview.png"
