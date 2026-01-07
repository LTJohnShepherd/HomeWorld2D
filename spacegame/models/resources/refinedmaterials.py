from abc import ABC, abstractmethod
from spacegame.models.ores.ore import Ore


class Refined(Ore, ABC):
    """Abstract base class for refined materials.

    Refined materials are stackable resources derived from ores. They default
    to tier 1 and a large stack size (10,000).
    """

    def __init__(self, quantity: int = 0):
        super().__init__(tier=1, stack_size=10000)
        self.quantity = int(quantity)

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def preview_filename(self) -> str:
        raise NotImplementedError()