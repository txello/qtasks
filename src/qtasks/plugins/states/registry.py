"""State Registry."""

from __future__ import annotations

import asyncio
import threading
from typing import Any


class SyncStateRegistry:
    """State registry class."""

    def __init__(self) -> None:
        """Initializing the state register."""
        self._lock = threading.Lock()
        self._buckets: dict[type, dict[str, Any]] = {}

    def _ensure(self, state_cls: type) -> None:
        """
        Ensure that there is a registry for this condition class.
        
                Args:
                    state_cls (Type): State class.
        """
        if state_cls not in self._buckets:
            self._buckets[state_cls] = {}

    def get(self, state_cls: type, key: str, default: Any = None) -> Any:
        """
        Get the status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
                    default (Any, optional): Default value if the state is not found. Defaults to None.
        
                Returns:
                    Any: Status value or default value.
        """
        with self._lock:
            self._ensure(state_cls)
            return self._buckets[state_cls].get(key, default)

    def set(self, state_cls: type, key: str, value: Any) -> None:
        """
        Set the status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
                    value (Any): State value.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls][key] = value

    def update(self, state_cls: type, mapping: dict[str, Any]) -> dict[str, Any]:
        """
        Update status values.
        
                Args:
                    state_cls (Type): State class.
                    mapping (Dict[str, Any]): Dictionary of updated state values.
        
                Returns:
                    Dict[str, Any]: Dictionary of old state values.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].update(mapping)
            # Возвращаем копию «на чтение», чтобы вне не мутировали напрямую
            return dict(self._buckets[state_cls])

    def get_all(self, state_cls: type) -> dict[str, Any]:
        """
        Get all state values.
        
                Args:
                    state_cls (Type): State class.
        
                Returns:
                    Dict[str, Any]: Dictionary of all state values.
        """
        with self._lock:
            self._ensure(state_cls)
            return dict(self._buckets[state_cls])

    def delete(self, state_cls: type, key: str) -> None:
        """
        Remove status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].pop(key, None)

    def clear(self, state_cls: type) -> None:
        """
        Clear all status values.
        
                Args:
                    state_cls (Type): State class.
        """
        with self._lock:
            self._ensure(state_cls)
            self._buckets[state_cls].clear()


class AsyncStateRegistry:
    """State registry class."""

    def __init__(self) -> None:
        """Initializing the state register."""
        self._lock = asyncio.Lock()
        self._buckets: dict[type, dict[str, Any]] = {}

    async def _ensure(self, state_cls: type) -> None:
        """
        Ensure that there is a registry for this condition class.
        
                Args:
                    state_cls (Type): State class.
        """
        if state_cls not in self._buckets:
            self._buckets[state_cls] = {}

    async def get(self, state_cls: type, key: str, default: Any = None) -> Any:
        """
        Get the status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
                    default (Any, optional): Default value if the state is not found. Defaults to None.
        
                Returns:
                    Any: Status value or default value.
        """
        async with self._lock:
            await self._ensure(state_cls)
            return self._buckets[state_cls].get(key, default)

    async def set(self, state_cls: type, key: str, value: Any) -> None:
        """
        Set the status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
                    value (Any): State value.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls][key] = value

    async def update(self, state_cls: type, mapping: dict[str, Any]) -> dict[str, Any]:
        """
        Update status values.
        
                Args:
                    state_cls (Type): State class.
                    mapping (Dict[str, Any]): Dictionary of updated state values.
        
                Returns:
                    Dict[str, Any]: Dictionary of old state values.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].update(mapping)
            return dict(self._buckets[state_cls])

    async def get_all(self, state_cls: type) -> dict[str, Any]:
        """
        Get all state values.
        
                Args:
                    state_cls (Type): State class.
        
                Returns:
                    Dict[str, Any]: Dictionary of all state values.
        """
        async with self._lock:
            await self._ensure(state_cls)
            return dict(self._buckets[state_cls])

    async def delete(self, state_cls: type, key: str) -> None:
        """
        Remove status value.
        
                Args:
                    state_cls (Type): State class.
                    key (str): State key.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].pop(key, None)

    async def clear(self, state_cls: type) -> None:
        """
        Clear all status values.
        
                Args:
                    state_cls (Type): State class.
        """
        async with self._lock:
            await self._ensure(state_cls)
            self._buckets[state_cls].clear()
