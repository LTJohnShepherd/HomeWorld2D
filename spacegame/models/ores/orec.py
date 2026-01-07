from spacegame.models.ores.ore import Ore


class RUOreC(Ore):
    """
    Concrete ore for the RU TYPE C ORE.
    """

    def __init__(self, quantity: int = 0):
        # Tier 1 and stack up to 10,000 per slot
        super().__init__(tier=1, stack_size=10000)
        self.quantity = int(quantity)

    @property
    def name(self) -> str:
        return "RU TYPE C ORE"

    @property
    def preview_filename(self) -> str:
        if(self.tier == 1):
            return "RUOreCT1.png"
        elif(self.tier == 2):
            return "RUOreCT2.png"
        else:
            return "RUOreCT3.png"

    def __repr__(self) -> str:
        return f"<RUOreC qty={self.quantity} / {self.max_stack}>"
