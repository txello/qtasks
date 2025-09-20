"""State Machine (FSM)."""

from __future__ import annotations
from typing import Any, Dict, Type

from .registry import SyncStateRegistry, AsyncStateRegistry


class SyncState:
    """Базовый синхронный State."""

    def __init__(self, registry: SyncStateRegistry, state_cls: Type["SyncState"]) -> None:
        """Инициализация состояния."""
        self._registry = registry
        self._cls = state_cls

    def get(self, key: str | None = None, default: Any = None) -> Any:
        """Получить значение состояния.

        Args:
            key (str, optional): Ключ состояния. По умолчанию: `None`.
            default (Any, optional): Значение по умолчанию, если состояние не найдено. По умолчанию: `None`.

        Returns:
            Any: Значение состояния или значение по умолчанию.
        """
        if key is None:
            return self._registry.get_all(self._cls)
        return self._registry.get(self._cls, key, default)

    def get_all(self) -> Dict[str, Any]:
        """Получить все значения состояния.

        Returns:
            Dict[str, Any]: Словарь всех значений состояния.
        """
        return self._registry.get_all(self._cls)

    def set(self, key: str, value: Any) -> None:
        """Установить значение состояния.

        Args:
            key (str): Ключ состояния.
            value (Any): Значение состояния.
        """
        self._registry.set(self._cls, key, value)

    def update(self, **kwargs: Any) -> Dict[str, Any]:
        """Обновить значения состояния.

        Returns:
            Dict[str, Any]: Словарь обновлённых значений состояния.
        """
        return self._registry.update(self._cls, kwargs)

    def delete(self, key: str) -> None:
        """Удалить значение состояния.

        Args:
            key (str): Ключ состояния.
        """
        self._registry.delete(self._cls, key)

    def clear(self) -> None:
        """Очистить все значения состояния."""
        self._registry.clear(self._cls)



class AsyncState:
    """Базовый асинхронный State."""

    def __init__(self, registry: AsyncStateRegistry, state_cls: Type["AsyncState"]) -> None:
        """Инициализация состояния."""
        self._registry = registry
        self._cls = state_cls

    async def get(self, key: str | None = None, default: Any = None) -> Any:
        """Получить значение состояния.

        Args:
            key (str, optional): Ключ состояния. По умолчанию: `None`.
            default (Any, optional): Значение по умолчанию, если состояние не найдено. По умолчанию: `None`.

        Returns:
            Any: Значение состояния или значение по умолчанию.
        """
        if key is None:
            return await self._registry.get_all(self._cls)
        return await self._registry.get(self._cls, key, default)

    async def get_all(self) -> Dict[str, Any]:
        """Получить все значения состояния.

        Returns:
            Dict[str, Any]: Словарь всех значений состояния.
        """
        return await self._registry.get_all(self._cls)

    async def set(self, key: str, value: Any) -> None:
        """Установить значение состояния.

        Args:
            key (str): Ключ состояния.
            value (Any): Значение состояния.
        """
        await self._registry.set(self._cls, key, value)

    async def update(self, **kwargs: Any) -> Dict[str, Any]:
        """Обновить значения состояния.

        Returns:
            Dict[str, Any]: Словарь обновлённых значений состояния.
        """
        return await self._registry.update(self._cls, kwargs)

    async def delete(self, key: str) -> None:
        """Удалить значение состояния.

        Args:
            key (str): Ключ состояния.
        """
        await self._registry.delete(self._cls, key)

    async def clear(self) -> None:
        """Очистить все значения состояния."""
        await self._registry.clear(self._cls)
