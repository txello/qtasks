from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class SyncPluginCacheMixin:

    cache: Dict[str, Any] = {}

    def __init__(self, plugin: BasePlugin) -> None:
        self.plugin = plugin
        pass

    def __enter__(self) -> Any | None:
        if self.plugin.name and self.plugin.name in self.cache:
            return self.cache[self.plugin.name]

    def __exit__(self, exc_type, exc_val, exc_tb):
        return
