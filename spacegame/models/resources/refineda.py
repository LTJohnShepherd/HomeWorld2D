from spacegame.models.resources.refinedmaterials import Refined

class RURefinedA(Refined):
    def __init__(self, quantity: int = 0):
        super().__init__(quantity=quantity)

    @property
    def name(self) -> str:
        return "RU TYPE A REFINED"

    @property
    def preview_filename(self) -> str:
        return "RUIngotAT1.png"

    def __repr__(self) -> str:
        return f"<RURefinedA qty={self.quantity} / {self.max_stack}>"