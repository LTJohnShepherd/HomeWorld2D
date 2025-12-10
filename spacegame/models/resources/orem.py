from spacegame.models.resources.ore import Ore


class RUOreM(Ore):
    """
    Concrete ore for the RU TYPE M ORE.
    """

    def __init__(self, quantity: int = 0):
        # Tier 0 and stack up to 10,000 per slot
        super().__init__(tier=0, stack_size=10000)
        self.quantity = int(quantity)

    @property
    def name(self) -> str:
        return "RU TYPE M ORE"

    @property
    def preview_filename(self) -> str:
        return "RUOreM.png"

    def __repr__(self) -> str:
        return f"<RUOreM qty={self.quantity} / {self.max_stack}>"
