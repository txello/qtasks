from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class AsyncPluginCacheMixin:

    cache: Dict[str, Any] = {}

    def __init__(self, plugin: BasePlugin) -> None:
        self.plugin = plugin
        pass

    async def __aenter__(self) -> Any | None:
        if self.plugin.name and self.plugin.name in self.cache:
            return self.cache[self.plugin.name]

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return
