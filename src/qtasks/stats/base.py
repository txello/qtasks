"""Base Stats."""

from abc import ABC
from typing import TYPE_CHECKING, Dict, List, Optional, Union


if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.asyncio import QueueTasks as aioQueueTasks
    from qtasks.plugins.base import BasePlugin


class BaseStats(ABC):
    """Base класс для всех статистик."""

    def __init__(
            self,
            app: Union["QueueTasks", "aioQueueTasks"],
            plugins: Optional[Dict[str, List["BasePlugin"]]] = None
        ):
        """Инициализация базовой статистики."""
        self.app = app

        self.plugins: Dict[str, List["BasePlugin"]] = plugins or {}
