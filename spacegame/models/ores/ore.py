from abc import ABC, abstractmethod


class Ore(ABC):
    """Abstract base class for stackable ores/resources.

    Provides common attributes: `tier` and `stack_size` (max per slot).
    Concrete ores should expose a `name` property and may add quantity.
    """

    def __init__(self, tier: int, stack_size: int = 10000):
        self.tier = int(tier)
        self.stack_size = int(stack_size)

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def max_stack(self) -> int:
        return int(self.stack_size)