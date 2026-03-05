"""Async Registry class for Plugin system."""

from typing import Literal

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.classes.registry.base import BasePluginRegistry
from qtasks.plugins.classes.result import PluginResult


class AsyncPluginRegistry(BasePluginRegistry):
    def __init__(self, plugin: BasePlugin[Literal[True]]):
        super().__init__(plugin=plugin)
        pass

    async def start(self, *args, **kwargs):
        """Launch the plugin."""
        return await self.plugin.start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        """Stopping the plugin."""
        return await self.plugin.stop(*args, **kwargs)

    async def trigger(self, name, *args, **kwargs) -> PluginResult | None:
        return await self.plugin.trigger(name, *args, **kwargs)

    async def get_cache(self):
        return self.cache

    async def update_cache(self, **kwargs):
        return self.cache.update(kwargs)
