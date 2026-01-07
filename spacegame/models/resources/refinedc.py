from spacegame.models.resources.refinedmaterials import Refined

class RURefinedC(Refined):
    def __init__(self, quantity: int = 0):
        super().__init__(quantity=quantity)

    @property
    def name(self) -> str:
        return "RU TYPE C REFINED"

    @property
    def preview_filename(self) -> str:
        return "RUIngotCT1.png"

    def __repr__(self) -> str:
        return f"<RURefinedC qty={self.quantity} / {self.max_stack}>"