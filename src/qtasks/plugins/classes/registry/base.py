"""Base Registry class for Plugin system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Dict, Generic, Literal, Optional, overload

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.classes.result import PluginResult
from qtasks.types.typing import TAsyncFlag


class BasePluginRegistry(Generic[TAsyncFlag], ABC):
    def __init__(self, plugin: BasePlugin[TAsyncFlag], name: Optional[str] = None):
        self.name: Optional[str] = name
        self.plugin: BasePlugin[TAsyncFlag] = plugin

        self.enabled: bool = True
        self.priority: int = 1

        self.cache: Dict[str, Any] = {}

    @overload
    def start(
        self: BasePluginRegistry[Literal[False]],
    ) -> None: ...

    @overload
    async def start(
        self: BasePluginRegistry[Literal[True]],
    ) -> None: ...

    @abstractmethod
    def start(self) -> None | Awaitable[None]:
        pass


    @overload
    def stop(
        self: BasePluginRegistry[Literal[False]],
    ) -> None: ...

    @overload
    async def stop(
        self: BasePluginRegistry[Literal[True]],
    ) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        pass


    @overload
    def trigger(
        self: BasePluginRegistry[Literal[False]], name: str, *args, **kwargs
    ) -> PluginResult | None: ...

    @overload
    async def trigger(
        self: BasePluginRegistry[Literal[True]], name: str, *args, **kwargs
    ) -> PluginResult | None: ...

    @abstractmethod
    def trigger(
        self, name: str, *args, **kwargs
    ) -> PluginResult | None:
        pass


    @overload
    def get_cache(
        self: BasePluginRegistry[Literal[False]]
    ) -> dict[str, Any] | None: ...

    @overload
    async def get_cache(
        self: BasePluginRegistry[Literal[True]]
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    def get_cache(
        self
    ) -> dict[str, Any] | None:
        pass


    @overload
    def update_cache(
        self: BasePluginRegistry[Literal[False]], **kwargs
    ) -> None: ...

    @overload
    async def update_cache(
        self: BasePluginRegistry[Literal[True]], **kwargs
    ) -> None: ...

    @abstractmethod
    def update_cache(
        self, **kwargs
    ) -> None:
        pass
