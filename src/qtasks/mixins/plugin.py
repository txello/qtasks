"""Миксин для работы с плагинами."""

from typing import Any, List


class SyncPluginMixin:
    """Миксин для синхронной работы с плагинами."""

    def _plugin_trigger(self, name: str, *args, **kwargs) -> List[Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.

        Returns:
            List[Any]: Результат выполнения обработчиков.
        """
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results


class AsyncPluginMixin:
    """Миксин для асинхронной работы с плагинами."""

    async def _plugin_trigger(self, name: str, *args, **kwargs) -> List[Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.

        Returns:
            List[Any]: Результат выполнения обработчиков.
        """
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = await plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results
