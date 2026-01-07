from spacegame.models.ores.ore import Ore


class RUOreB(Ore):
    """
    Concrete ore for the RU TYPE B ORE.
    """

    def __init__(self, quantity: int = 0):
        # Tier 1 and stack up to 10,000 per slot
        super().__init__(tier=1, stack_size=10000)
        self.quantity = int(quantity)

    @property
    def name(self) -> str:
        return "RU TYPE B ORE"

    @property
    def preview_filename(self) -> str:
        if(self.tier == 1):
            return "RUOreBT1.png"
        elif(self.tier == 2):
            return "RUOreBT2.png"
        else:
            return "RUOreBT3.png"

    def __repr__(self) -> str:
        return f"<RUOreB qty={self.quantity} / {self.max_stack}>"
