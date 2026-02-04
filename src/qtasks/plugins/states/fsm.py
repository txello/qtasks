"""State Machine (FSM)."""

from __future__ import annotations

from typing import Any

from .registry import AsyncStateRegistry, SyncStateRegistry


class SyncState:
    """Basic synchronous State."""

    def __init__(
        self, registry: SyncStateRegistry, state_cls: type[SyncState]
    ) -> None:
        """Initializing the state."""
        self._registry = registry
        self._cls = state_cls

    def get(self, key: str | None = None, default: Any = None) -> Any:
        """
        Get the status value.

        Args:
            key (str, optional): State key. Default: `None`.
            default (Any, optional): Default value if the state is not found. Default: `None`.

        Returns:
            Any: Status value or default value.
        """
        if key is None:
            return self._registry.get_all(self._cls)
        return self._registry.get(self._cls, key, default)

    def get_all(self) -> dict[str, Any]:
        """
        Get all state values.

        Returns:
            Dict[str, Any]: Dictionary of all state values.
        """
        return self._registry.get_all(self._cls)

    def set(self, key: str, value: Any) -> None:
        """
        Set the status value.

        Args:
            key (str): State key.
            value (Any): State value.
        """
        self._registry.set(self._cls, key, value)

    def update(self, **kwargs: Any) -> dict[str, Any]:
        """
        Update status values.

        Returns:
            Dict[str, Any]: Dictionary of updated state values.
        """
        return self._registry.update(self._cls, kwargs)

    def delete(self, key: str) -> None:
        """
        Remove status value.

        Args:
            key (str): State key.
        """
        self._registry.delete(self._cls, key)

    def clear(self) -> None:
        """Clear all status values."""
        self._registry.clear(self._cls)


class AsyncState:
    """Basic asynchronous State."""

    def __init__(
        self, registry: AsyncStateRegistry, state_cls: type[AsyncState]
    ) -> None:
        """Initializing the state."""
        self._registry = registry
        self._cls = state_cls

    async def get(self, key: str | None = None, default: Any = None) -> Any:
        """
        Get the status value.

        Args:
            key (str, optional): State key. Default: `None`.
            default (Any, optional): Default value if the state is not found. Default: `None`.

        Returns:
            Any: Status value or default value.
        """
        if key is None:
            return await self._registry.get_all(self._cls)
        return await self._registry.get(self._cls, key, default)

    async def get_all(self) -> dict[str, Any]:
        """
        Get all state values.

        Returns:
            Dict[str, Any]: Dictionary of all state values.
        """
        return await self._registry.get_all(self._cls)

    async def set(self, key: str, value: Any) -> None:
        """
        Set the status value.

        Args:
            key (str): State key.
            value (Any): State value.
        """
        await self._registry.set(self._cls, key, value)

    async def update(self, **kwargs: Any) -> dict[str, Any]:
        """
        Update status values.

        Returns:
            Dict[str, Any]: Dictionary of updated state values.
        """
        return await self._registry.update(self._cls, kwargs)

    async def delete(self, key: str) -> None:
        """
        Remove status value.

        Args:
            key (str): State key.
        """
        await self._registry.delete(self._cls, key)

    async def clear(self) -> None:
        """Clear all status values."""
        await self._registry.clear(self._cls)
