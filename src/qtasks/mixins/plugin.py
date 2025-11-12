"""Миксин для работы с плагинами."""
from __future__ import annotations

import traceback
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    Optional,
    overload,
)

from typing_extensions import Doc

from qtasks.mixins.async_plugin_cache import AsyncPluginCacheMixin
from qtasks.mixins.sync_plugin_cache import SyncPluginCacheMixin

if TYPE_CHECKING:
    from qtasks.logs import Logger
    from qtasks.plugins.base import BasePlugin


class SyncPluginMixin:
    """Миксин для синхронной работы с плагинами."""

    plugins: dict[str, list[BasePlugin]]
    log: Optional[Logger] = None

    plugins_cache = SyncPluginCacheMixin

    @overload
    def _plugin_trigger(
        self,
        name: str,
        *args,
        return_last: bool = True,
        safe: bool = True,
        continue_on_fail: bool = False,
        **kwargs,
    ) -> dict[str, Any]: ...

    @overload
    def _plugin_trigger(
        self,
        name: str,
        *args,
        return_last: bool = False,
        safe: bool = True,
        continue_on_fail: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]: ...

    def _plugin_trigger(
        self,
        name: str,
        *args,
        return_last: bool | None = None,
        safe: bool = True,
        continue_on_fail: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]] | dict[str, Any]:
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
        kwargs_copy = kwargs.copy()

        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            with self.plugins_cache(plugin=plugin) as plugin_cache:
                # cache: start
                if plugin_cache:
                    kwargs_copy.update({"plugin_cache": plugin_cache})
                elif "plugin_cache" in kwargs_copy:
                    del kwargs_copy["plugin_cache"]
                #

                try:
                    result: dict[str, Any] | None = plugin.trigger(
                        name, **kwargs_copy
                    )
                except Exception as e:
                    if safe:
                        tb = "".join(
                            traceback.TracebackException.from_exception(e).format()
                        )
                        msg = f"Плагин {plugin.name} завершился с ошибкой:\n {tb}"
                        if hasattr(self, "log") and self.log:
                            self.log.error(msg)
                        print(msg)
                        if not continue_on_fail:
                            break
                        continue

                if result is not None:
                    # cache: stop
                    if "plugin_cache" in result:
                        if plugin.name:
                            self.plugins_cache.cache[plugin.name] = result["plugin_cache"]
                        del result["plugin_cache"]
                    #

                    results.append(result)
                    if "args" in result:
                        kwargs_copy["args"] = result.get("args", [])
                    if "kw" in result:
                        kwargs_copy["kw"] = result.get("kw", {})

        if return_last and results:
            return {
                **{
                    k: v
                    for r in results
                    for k, v in r.items()
                    if k not in ("args", "kw")
                },
                "args": next((r["args"] for r in results[::-1] if "args" in r), None),
                "kw": next((r["kw"] for r in results[::-1] if "kw" in r), {}),
            }
        return results

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
        ] = None,
    ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return


class AsyncPluginMixin:
    """Миксин для асинхронной работы с плагинами."""

    plugins: dict[str, list[BasePlugin[Literal[True]]]]
    log: Optional[Logger] = None

    plugins_cache = AsyncPluginCacheMixin

    @overload
    async def _plugin_trigger(
        self,
        name: str,
        *args,
        return_last: bool = True,
        safe: bool = True,
        continue_on_fail: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
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
        **kwargs,
    ) -> list[dict[str, Any]]:
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
        *,
        return_last: bool | None = None,
        safe: bool = True,
        continue_on_fail: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]] | dict[str, Any]:
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
        kwargs_copy = kwargs.copy()

        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            async with self.plugins_cache(plugin=plugin) as plugin_cache:
                # cache: start
                if plugin_cache:
                    kwargs_copy.update({"plugin_cache": plugin_cache})
                elif "plugin_cache" in kwargs_copy:
                    del kwargs_copy["plugin_cache"]
                #

                try:
                    result: dict[str, Any] | None = await plugin.trigger(
                        name, **kwargs_copy
                    )
                except Exception as e:
                    if safe:
                        tb = "".join(
                            traceback.TracebackException.from_exception(e).format()
                        )
                        msg = f"Плагин {plugin.name} завершился с ошибкой:\n {tb}"
                        if hasattr(self, "log") and self.log:
                            self.log.error(msg)
                        print(msg)
                        if not continue_on_fail:
                            break
                        continue

                if result is not None:
                    # cache: stop
                    if "plugin_cache" in result:
                        if plugin.name:
                            self.plugins_cache.cache[plugin.name] = result["plugin_cache"]
                        del result["plugin_cache"]
                    #

                    results.append(result)
                    if "args" in result:
                        kwargs_copy["args"] = result.get("args", [])
                    if "kw" in result:
                        kwargs_copy["kw"] = result.get("kw", {})

        if return_last and results:
            return {
                **{
                    k: v
                    for r in results
                    for k, v in r.items()
                    if k not in ("args", "kw")
                },
                "args": next((r["args"] for r in results[::-1] if "args" in r), None),
                "kw": next((r["kw"] for r in results[::-1] if "kw" in r), {}),
            }
        return results

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
        ] = None,
    ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return
