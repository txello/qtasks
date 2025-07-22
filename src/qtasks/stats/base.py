"""Base Stats."""


from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class BaseStats(ABC):
    """Base класс для всех статистик."""

    def __init__(
        self,
        app: "QueueTasks"
    ):
        """Инициализация базовой статистики."""
        self.app = app
