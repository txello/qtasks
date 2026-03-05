"""Mixin for working with plugins."""
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

from qtasks.plugins.classes.registry.async_registry import AsyncPluginRegistry
from qtasks.plugins.classes.registry.base import BasePluginRegistry
from qtasks.plugins.classes.registry.sync_registry import SyncPluginRegistry
from qtasks.plugins.classes.result import PluginResult

if TYPE_CHECKING:
    from qtasks.logs import Logger
    from qtasks.plugins.base import BasePlugin


class SyncPluginMixin:
    """Mixin for synchronous work with plugins."""

    plugins: dict[str, list[BasePluginRegistry[Literal[False]]]]
    log: Optional[Logger] = None

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
        """
        Trigger to run the plugin handler.

        Args:
            name (str): Handler name.
            return_last (bool): If True, return only the last result, if any.
            safe (bool): If True, do not ignore plugin errors.
            continue_on_fail (bool): If True, continue executing other plugins on error.

        Returns:
            List[Dict[str, Any]]: Results of executing handlers.
        """
        results = []
        kwargs_copy = kwargs.copy()

        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
                try:
                    plugin_result: PluginResult | None = plugin.trigger(
                        name, **kwargs_copy
                    )
                    result = plugin_result.result
                except Exception as e:
                    if safe:
                        tb = "".join(
                            traceback.TracebackException.from_exception(e).format()
                        )
                        msg = f"Plugin {plugin.name} finished with an error:\n {tb}"
                        if hasattr(self, "log") and self.log:
                            self.log.error(msg)
                        print(msg)
                        if not continue_on_fail:
                            break
                        continue
                    continue

                if plugin_result is not None:
                    results.append(result)
                    if plugin_result.args_next:
                        kwargs_copy["args"] = plugin_result.args_next
                    if plugin_result.kwargs_next:
                        kwargs_copy["kw"] = plugin_result.kwargs_next

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
            Doc("""
                    Plugin.
                    """),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc("""
                    The name of the triggers for the plugin.

                    Default: Default: will be added to `Globals`.
                    """),
        ] = None,
    ) -> None:
        """
        Add a plugin to the class.

        Args:
            plugin (BasePlugin): Plugin
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        plugin_registry = SyncPluginRegistry(plugin=plugin)

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin_registry]})
            else:
                self.plugins[name].append(plugin_registry)
        return


class AsyncPluginMixin:
    """Mixin for asynchronous work with plugins."""

    plugins: dict[str, list[BasePluginRegistry[Literal[True]]]]
    log: Optional[Logger] = None

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
        """
        Trigger to run the plugin handler.

        Args:
            name (str): Handler name.
            return_last (bool): If True, return only the last result, if any.
            safe (bool): If True, do not ignore plugin errors.
            continue_on_fail (bool): If True, continue executing other plugins on error.

        Returns:
            Dict[str, Any]: The last result of handler execution or an empty dictionary.
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
        """
        Trigger to run the plugin handler.

        Args:
            name (str): Handler name.
            return_last (bool): If True, return only the last result, if any.
            safe (bool): If True, do not ignore plugin errors.
            continue_on_fail (bool): If True, continue executing other plugins on error.

        Returns:
            List[Dict[str, Any]]: Results of executing handlers.
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
        """
        Trigger to run the plugin handler.

        Args:
            name (str): Handler name.
            return_last (bool): If True, return only the last result, if any.
            safe (bool): If True, do not ignore plugin errors.
            continue_on_fail (bool): If True, continue executing other plugins on error.

        Returns:
            List[Dict[str, Any]]: Results of executing handlers.
        """
        results = []
        kwargs_copy = kwargs.copy()

        for plugin_registry in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            print(plugin_registry.plugin.name)
            # cache: start
            cache = await plugin_registry.get_cache()
            if cache:
                kwargs_copy.update({"plugin_cache": cache})
            elif "plugin_cache" in kwargs_copy:
                del kwargs_copy["plugin_cache"]
            #
            result = None
            try:
                result: PluginResult | None = await plugin_registry.trigger(
                    name, **kwargs_copy
                )
                print(123, result)
            except Exception as e:
                if safe:
                    tb = "".join(
                        traceback.TracebackException.from_exception(e).format()
                    )
                    msg = f"Plugin {plugin_registry.plugin.name} finished with an error:\n {tb}"
                    if hasattr(self, "log") and self.log:
                        self.log.error(msg)
                    print(msg)
                    if not continue_on_fail:
                        break
                    continue

            if result:
                # cache: stop
                print(4444, plugin_registry.plugin.name)
                result_cache = result.cache

                if result_cache is not None:
                    if plugin_registry.plugin.name:
                        plugin_registry.update_cache(result_cache)
                #

                if result.result is not None:
                    results.append(result.result)

                args_next = result.args_next
                kwargs_next = result.kwargs_next

                kwargs_copy["args"] = args_next or ()
                kwargs_copy["kw"] = kwargs_next or {}

        if return_last and results:
            print(111122223333, results, kwargs_copy["args"], kwargs_copy["kw"])
            return {
                **{
                    k: v
                    for r in results
                    for k, v in r.items()
                    if k not in ("args", "kw")
                },
                "args": kwargs_copy["args"],
                "kw": kwargs_copy["kw"],
            }
        return results

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc(
                """
                    Plugin class.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    The name of the triggers for the plugin.

                    Default: will be added to `Globals`.
                    """
            ),
        ] = None,
        component: Annotated[
            str | None,
            Doc(
                """
                    Component name.

                    Default: `None`.
                    """
            ),
        ] = None,
    ) -> None:
        """
        Add a plugin.

        Args:
            plugin (Type[BasePlugin]): Plugin class.
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
            component (str, optional): Component name. Default: `None`.

        Raises:
            KeyError: Unable to get component {component}!
        """
        trigger_names = trigger_names or ["Globals"]

        plugin_registry = AsyncPluginRegistry(plugin=plugin)

        if not component:
            for name in trigger_names:
                if name not in self.plugins:
                    self.plugins.update({name: [plugin_registry]})
                else:
                    self.plugins[name].append(plugin_registry)
            return
