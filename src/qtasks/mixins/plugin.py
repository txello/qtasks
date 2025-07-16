"""Миксин для работы с плагинами."""

from typing import Any, List


class SyncPluginMixin:
    """Миксин для синхронной работы с плагинами."""

    def _plugin_trigger(
            self,
            name: str,
            *args,

            return_last: bool = False,
            safe: bool = True,
            continue_on_fail: bool = False,

            **kwargs
    ) -> List[Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Any] | Any: Результаты выполнения обработчиков или последний.
        """
        results = []
        plugins = self.plugins.get(name, []) + self.plugins.get("Globals", [])
        for plugin in plugins:
            try:
                result = plugin.trigger(name=name, *args, **kwargs)
            except Exception as e:
                if safe:
                    msg = f"Плагин {plugin.name} завершился с ошибкой: {e}"
                    if hasattr(self, "log"):
                        self.log.error(msg)
                    print(msg)
                    if not continue_on_fail:
                        return results
                    continue
            if result is not None:
                results.append(result)
                if isinstance(result, dict):
                    kwargs.update(result)

        if return_last and results:
            return results[-1]
        return results


class AsyncPluginMixin:
    """Миксин для асинхронной работы с плагинами."""

    async def _plugin_trigger(
        self,
        name: str,
        *args,

        return_last: bool = False,
        safe: bool = True,
        continue_on_fail: bool = False,

        **kwargs
    ) -> List[Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Any] | Any: Результаты выполнения обработчиков или последний.
        """
        results = []
        plugins = self.plugins.get(name, []) + self.plugins.get("Globals", [])
        for plugin in plugins:
            try:
                result = await plugin.trigger(name=name, *args, **kwargs)
            except Exception as e:
                if safe:
                    msg = f"Плагин {plugin.name} завершился с ошибкой: {e}"
                    if hasattr(self, "log"):
                        self.log.error(msg)
                    print(msg)
                    if not continue_on_fail:
                        return results
                    continue
            if result is not None:
                results.append(result)
                if isinstance(result, dict):
                    kwargs.update(result)

        if return_last and results:
            return results[-1]
        return results
