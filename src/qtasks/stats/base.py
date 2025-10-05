"""Base Stats."""

from abc import ABC
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.asyncio import QueueTasks as aioQueueTasks


class BaseStats(ABC):
    """Base класс для всех статистик."""

    def __init__(self, app: Union["QueueTasks", "aioQueueTasks"]):
        """Инициализация базовой статистики."""
        self.app = app
