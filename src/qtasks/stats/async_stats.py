"""Async Stats."""

from typing import TYPE_CHECKING
from .inspect.inspect import InspectStats
from .base import BaseStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class AsyncStats(BaseStats):
    """Класс для асинхронных статистик."""

    def __init__(self, app: "QueueTasks"):
        """Инициализация асинхронной статистики.

        Args:
            app (QueueTasks): Экземпляр приложения.
        """
        super().__init__(app=app)

    def inspect(self):
        """Инспекция асинхронной статистики.

        Returns:
            AsyncStatsSchema: Схема асинхронной статистики.
        """
        return InspectStats(self.app)
