"""State Registry."""

from __future__ import annotations

import asyncio
import threading
from typing import Any


class SyncStateRegistry:
    """Класс реестра состояний."""

    def __init__(self) -> None:
        """Инициализация реестра состояний."""
        self._lock = threading.Lock()
        self._buckets: dict[type, dict[str, Any]] = {}

    def _ensure(self, state_cls: type) -> None:
        """Обеспечить наличие реестра для данного класса состояния.

        Args:
            state_cls (Type): Класс состояния.
        """
        if state_cls not in self._buckets:
            self._buckets[state_cls] = {}

    def get(self, state_cls: type, key: str, default: Any = None) -> Any:
        """Получить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
            default (Any, optional): Значение по умолчанию, если состояние не найдено. Defaults to None.

        Returns:
            Any: Значение состояния или значение по умолчанию.
        """
        with self._lock:
            self._ensure(state_cls)
            return self._buckets[state_cls].get(key, default)

    def set(self, state_cls: type, key: str, value: Any) -> None:
        """Установить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
            value (Any): Значение состояния.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls][key] = value

    def update(self, state_cls: type, mapping: dict[str, Any]) -> dict[str, Any]:
        """Обновить значения состояния.

        Args:
            state_cls (Type): Класс состояния.
            mapping (Dict[str, Any]): Словарь обновлённых значений состояния.

        Returns:
            Dict[str, Any]: Словарь старых значений состояния.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].update(mapping)
            # Возвращаем копию «на чтение», чтобы вне не мутировали напрямую
            return dict(self._buckets[state_cls])

    def get_all(self, state_cls: type) -> dict[str, Any]:
        """Получить все значения состояния.

        Args:
            state_cls (Type): Класс состояния.

        Returns:
            Dict[str, Any]: Словарь всех значений состояния.
        """
        with self._lock:
            self._ensure(state_cls)
            return dict(self._buckets[state_cls])

    def delete(self, state_cls: type, key: str) -> None:
        """Удалить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].pop(key, None)

    def clear(self, state_cls: type) -> None:
        """Очистить все значения состояния.

        Args:
            state_cls (Type): Класс состояния.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].clear()


class AsyncStateRegistry:
    """Класс реестра состояний."""

    def __init__(self) -> None:
        """Инициализация реестра состояний."""
        self._lock = asyncio.Lock()
        self._buckets: dict[type, dict[str, Any]] = {}

    async def _ensure(self, state_cls: type) -> None:
        """Обеспечить наличие реестра для данного класса состояния.

        Args:
            state_cls (Type): Класс состояния.
        """
        if state_cls not in self._buckets:
            self._buckets[state_cls] = {}

    async def get(self, state_cls: type, key: str, default: Any = None) -> Any:
        """Получить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
            default (Any, optional): Значение по умолчанию, если состояние не найдено. Defaults to None.

        Returns:
            Any: Значение состояния или значение по умолчанию.
        """
        async with self._lock:
            await self._ensure(state_cls)
            return self._buckets[state_cls].get(key, default)

    async def set(self, state_cls: type, key: str, value: Any) -> None:
        """Установить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
            value (Any): Значение состояния.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls][key] = value

    async def update(self, state_cls: type, mapping: dict[str, Any]) -> dict[str, Any]:
        """Обновить значения состояния.

        Args:
            state_cls (Type): Класс состояния.
            mapping (Dict[str, Any]): Словарь обновлённых значений состояния.

        Returns:
            Dict[str, Any]: Словарь старых значений состояния.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].update(mapping)
            return dict(self._buckets[state_cls])

    async def get_all(self, state_cls: type) -> dict[str, Any]:
        """Получить все значения состояния.

        Args:
            state_cls (Type): Класс состояния.

        Returns:
            Dict[str, Any]: Словарь всех значений состояния.
        """
        async with self._lock:
            await self._ensure(state_cls)
            return dict(self._buckets[state_cls])

    async def delete(self, state_cls: type, key: str) -> None:
        """Удалить значение состояния.

        Args:
            state_cls (Type): Класс состояния.
            key (str): Ключ состояния.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].pop(key, None)

    async def clear(self, state_cls: type) -> None:
        """Очистить все значения состояния.

        Args:
            state_cls (Type): Класс состояния.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].clear()
