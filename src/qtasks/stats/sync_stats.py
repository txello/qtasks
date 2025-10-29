"""Sync Stats."""

from typing import TYPE_CHECKING, Dict, List, Optional

from qtasks.mixins.plugin import SyncPluginMixin
from .inspect.inspect import InspectStats
from .base import BaseStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.plugins.base import BasePlugin


class SyncStats(BaseStats, SyncPluginMixin):
    """Класс для синхронных статистик."""

    def __init__(self, app: "QueueTasks", plugins: Optional[Dict[str, List["BasePlugin"]]] = None):
        """Инициализация асинхронной статистики.

        Args:
            app (QueueTasks): Экземпляр приложения.
            plugins (Optional[Dict[str, List[BasePlugin]]]): Плагины. По умолчанию: `None`.
        """
        super().__init__(app=app, plugins=plugins)

    def inspect(self):
        """Инспекция асинхронной статистики.

        Returns:
            AsyncStatsSchema: Схема асинхронной статистики.
        """
        self._plugin_trigger(
            "stats_inspect",
            stats=self
        )
        return InspectStats(self.app)
