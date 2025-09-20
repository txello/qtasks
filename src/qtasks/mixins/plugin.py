"""Миксин для работы с плагинами."""

import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Union, overload
from copy import deepcopy

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class SyncPluginMixin:
    """Миксин для синхронной работы с плагинами."""

    plugins: Dict[str, List["BasePlugin"]]

    @overload
    def _plugin_trigger(
        self,
        name: str,
        *args,

        return_last: bool = True,
        safe: bool = True,
        continue_on_fail: bool = False,

        **kwargs
    ) -> Dict[str, Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            Dict[str, Any]: Последний результат выполнения обработчиков или пустой словарь.
        """
        ...

    @overload
    def _plugin_trigger(
            self,
            name: str,
            *args,

            return_last: bool = False,
            safe: bool = True,
            continue_on_fail: bool = False,

            **kwargs
    ) -> List[Dict[str, Any]]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Dict[str, Any]]: Результаты выполнения обработчиков.
        """
        ...

    def _plugin_trigger(
            self,
            name: str,
            *args,

            return_last: bool = None,
            safe: bool = True,
            continue_on_fail: bool = False,

            **kwargs
    ) -> List[Dict[str, Any]]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Dict[str, Any]]: Результаты выполнения обработчиков.
        """
        results = []
        args_copy = deepcopy(args)
        kwargs_copy = kwargs.copy()
        plugins = self.plugins.get(name, []) + self.plugins.get("Globals", [])
        for plugin in plugins:
            try:
                result: Union[Dict[str, Any], None] = plugin.trigger(name, *args_copy, **kwargs_copy)
            except Exception as e:
                if safe:
                    tb = ''.join(traceback.TracebackException.from_exception(e).format())
                    msg = f"Плагин {plugin.name} завершился с ошибкой:\n {tb}"
                    if hasattr(self, "log"):
                        self.log.error(msg)
                    print(msg)
                    if not continue_on_fail:
                        break
                    continue

            if result is not None:
                results.append(result)
                args_copy = result.get("args", args_copy)
                if result.get("kw"):
                    kwargs_copy["kw"].update(result.get("kw", {}))

        if return_last and results:
            return {
                **{k: v for r in results for k, v in r.items() if k not in ("args", "kw")},
                "args": next((r["args"] for r in results[::-1] if "args" in r), None),
                "kw": next((r["kw"] for r in results[::-1] if "kw" in r), {})
            }
        return results


class AsyncPluginMixin:
    """Миксин для асинхронной работы с плагинами."""

    plugins: Dict[str, List["BasePlugin"]]

    @overload
    async def _plugin_trigger(
        self,
        name: str,
        *args,

        return_last: bool = True,
        safe: bool = True,
        continue_on_fail: bool = False,

        **kwargs
    ) -> Dict[str, Any]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            Dict[str, Any]: Последний результат выполнения обработчиков или пустой словарь.
        """
        ...

    @overload
    async def _plugin_trigger(
        self,
        name: str,
        *args,

        return_last: bool = False,
        safe: bool = True,
        continue_on_fail: bool = False,

        **kwargs
    ) -> List[Dict[str, Any]]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Dict[str, Any]]: Результаты выполнения обработчиков.
        """
        ...

    async def _plugin_trigger(
        self,
        name: str,
        *args,

        return_last: bool = None,
        safe: bool = True,
        continue_on_fail: bool = False,

        **kwargs
    ) -> List[Dict[str, Any]]:
        """Триггер для запуска обработчика плагина.

        Args:
            name (str): Имя обработчика.
            return_last (bool): Если True — вернуть только последний результат, если есть.
            safe (bool): Если True — не игнорировать ошибки плагинов.
            continue_on_fail (bool): Если True — продолжить выполнение других плагинов при ошибке.

        Returns:
            List[Dict[str, Any]]: Результаты выполнения обработчиков.
        """
        results = []
        args_copy = deepcopy(args)
        kwargs_copy = kwargs.copy()
        plugins = self.plugins.get(name, []) + self.plugins.get("Globals", [])
        for plugin in plugins:
            try:
                result: Union[Dict[str, Any], None] = await plugin.trigger(name, *args_copy, **kwargs_copy)
            except Exception as e:
                if safe:
                    tb = ''.join(traceback.TracebackException.from_exception(e).format())
                    msg = f"Плагин {plugin.name} завершился с ошибкой:\n {tb}"
                    if hasattr(self, "log"):
                        self.log.error(msg)
                    print(msg)
                    if not continue_on_fail:
                        break
                    continue

            if result is not None:
                results.append(result)
                args_copy = result.get("args", args_copy)
                if result.get("kw"):
                    kwargs_copy["kw"].update(result.get("kw", {}))

        if return_last and results:
            return {
                **{k: v for r in results for k, v in r.items() if k not in ("args", "kw")},
                "args": next((r["args"] for r in results[::-1] if "args" in r), None),
                "kw": next((r["kw"] for r in results[::-1] if "kw" in r), {})
            }
        return results
