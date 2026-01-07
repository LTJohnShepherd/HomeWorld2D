from spacegame.models.resources.refinedmaterials import Refined

class RURefinedB(Refined):
    def __init__(self, quantity: int = 0):
        super().__init__(quantity=quantity)

    @property
    def name(self) -> str:
        return "RU TYPE B REFINED"

    @property
    def preview_filename(self) -> str:
        return "RUIngotBT1.png"

    def __repr__(self) -> str:
        return f"<RURefinedB qty={self.quantity} / {self.max_stack}>"