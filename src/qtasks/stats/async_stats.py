"""Async Stats."""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtasks.mixins.plugin import AsyncPluginMixin

from .base import BaseStats
from .inspect.inspect import InspectStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.plugins.base import BasePlugin


class AsyncStats(BaseStats, AsyncPluginMixin):
    """Класс для асинхронных статистик."""

    def __init__(self, app: QueueTasks, plugins: dict[str, list[BasePlugin]] | None = None):
        """Инициализация асинхронной статистики.

        Args:
            app (QueueTasks): Экземпляр приложения. z
            plugins (Optional[Dict[str, List[BasePlugin]]]): Плагины. По умолчанию: `None`.
        """
        super().__init__(app=app, plugins=plugins)

    async def inspect(self):
        """Инспекция асинхронной статистики.

        Returns:
            AsyncStatsSchema: Схема асинхронной статистики.
        """
        await self._plugin_trigger(
            "stats_inspect",
            stats=self
        )
        return InspectStats(self.app)
