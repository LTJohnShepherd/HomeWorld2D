from abc import ABC, abstractmethod


class Blueprint(ABC):
    """Abstract base for blueprint-like inventory items.

    Blueprints are stackable in principle, but some may be infinite
    (represented by quantity=float('inf')). Concrete blueprints should
    provide `name`, `tier`, and `preview_filename` properties.
    """

    def __init__(self, tier: int = 0, stack_size: int = 9999, quantity=None, rarity: str = "COMMON", title: str | None = None, description: str = "",):
        self.tier = int(tier)
        self.stack_size = int(stack_size)
        self.quantity = quantity if quantity is not None else 0
        self.rarity = str(rarity).upper()
        self.title = title          # UI title (can be multi-line with '\n')
        self.description = description  # long description text

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def preview_filename(self) -> str:
        raise NotImplementedError()