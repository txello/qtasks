"""Sync Stats."""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtasks.mixins.plugin import SyncPluginMixin

from .base import BaseStats
from .inspect.inspect import InspectStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.plugins.base import BasePlugin


class SyncStats(BaseStats, SyncPluginMixin):
    """Class for synchronous statistics."""

    def __init__(self, app: QueueTasks, plugins: dict[str, list[BasePlugin]] | None = None):
        """
        Initializing asynchronous statistics.

        Args:
            app (QueueTasks): Application instance.
            plugins (Optional[Dict[str, List[BasePlugin]]]): Plugins. Default: `None`.
        """
        super().__init__(app=app, plugins=plugins)

    def inspect(self):
        """
        Inspection of asynchronous statistics.

        Returns:
            InspectStats: Synchronous statistics schema.
        """
        self._plugin_trigger(
            "stats_inspect",
            stats=self
        )
        return InspectStats(self.app)
