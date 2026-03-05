"""Sync Registry class for Plugin system."""

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.classes.registry.base import BasePluginRegistry


class SyncPluginRegistry(BasePluginRegistry):
    def __init__(self, plugin: BasePlugin[True]):
        super().__init__(plugin=plugin)
        pass

    def start(self, *args, **kwargs):
        """Launch the plugin."""
        return self.plugin.start(*args, **kwargs)

    def stop(self, *args, **kwargs):
        """Stopping the plugin."""
        return self.plugin.stop(*args, **kwargs)

    def trigger(self, name, *args, **kwargs):
        return self.plugin.trigger(name, *args, **kwargs)
