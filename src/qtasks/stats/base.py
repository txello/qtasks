"""Base Stats."""

from abc import ABC
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks as aioQueueTasks
    from qtasks.plugins.base import BasePlugin
    from qtasks.qtasks import QueueTasks


class BaseStats(ABC): # noqa: B024
    """Base класс для всех статистик."""

    def __init__(
            self,
            app: Union["QueueTasks", "aioQueueTasks"],
            plugins: dict[str, list["BasePlugin"]] | None = None
        ):
        """Инициализация базовой статистики."""
        self.app = app

        self.plugins: dict[str, list[BasePlugin]] = plugins or {}
