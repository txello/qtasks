"""Sync Stats."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.plugins.classes.registry.base import BasePluginRegistry

from .base import BaseStats
from .inspect.inspect import InspectStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class SyncStats(BaseStats, SyncPluginMixin):
    """Class for synchronous statistics."""

    def __init__(self, app: QueueTasks, plugins: dict[str, list[BasePluginRegistry[Literal[False]]]] | None = None):
        """
        Initializing asynchronous statistics.

        Args:
            app (QueueTasks): Application instance.
            plugins (Optional[Dict[str, List[BasePluginRegistry[Literal[False]]]]]): Plugins. Default: `None`.
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
