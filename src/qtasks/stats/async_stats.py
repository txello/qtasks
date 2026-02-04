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
    """Class for asynchronous statistics."""

    def __init__(self, app: QueueTasks, plugins: dict[str, list[BasePlugin]] | None = None):
        """
        Initializing asynchronous statistics.

        Args:
            app (QueueTasks): Application instance. z
            plugins (Optional[Dict[str, List[BasePlugin]]]): Plugins. Default: `None`.
        """
        super().__init__(app=app, plugins=plugins)

    async def inspect(self):
        """
        Inspection of asynchronous statistics.

        Returns:
            InspectStats: Asynchronous statistics schema.
        """
        await self._plugin_trigger(
            "stats_inspect",
            stats=self
        )
        return InspectStats(self.app)
