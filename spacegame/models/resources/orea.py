from spacegame.models.resources.ore import Ore


class RUOreA(Ore):
    """
    Concrete ore for the RU TYPE A ORE.
    """

    def __init__(self, quantity: int = 0):
        # Tier 1 and stack up to 10,000 per slot
        super().__init__(tier=1, stack_size=10000)
        self.quantity = int(quantity)

    @property
    def name(self) -> str:
        return "RU TYPE A ORE"

    @property
    def preview_filename(self) -> str:
        if(self.tier == 1):
            return "RUOreAT1.png"
        elif(self.tier == 2):
            return "RUOreAT2.png"
        else:
            return "RUOreAT3.png"

    def __repr__(self) -> str:
        return f"<RUOreA qty={self.quantity} / {self.max_stack}>"
