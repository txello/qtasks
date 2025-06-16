class SyncPluginMixin:
    def _plugin_trigger(self, name: str, *args, **kwargs):
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results
    
class AsyncPluginMixin:
    async def _plugin_trigger(self, name: str, *args, **kwargs):
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = await plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results
