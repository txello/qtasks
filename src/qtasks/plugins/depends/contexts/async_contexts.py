from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple


class AsyncContextPool:
    """
    Stores asynchronous contexts by group (name).
        The key to identify a specific context is id(cm).
    """

    def __init__(self):
        # name -> list[ (cm_id, cm_obj, AsyncExitStack, value) ]
        self._contexts: Dict[str, List[Tuple[int, object, AsyncExitStack, Any]]] = {}

    async def enter(self, name: str, cm: object) -> Any:
        """
        Enter the asynchronous cm context and save it.
                Returns the value obtained from yield in @asynccontextmanager.
        """
        stack = AsyncExitStack()
        value = await stack.enter_async_context(cm) # type: ignore
        entry = (id(cm), cm, stack, value)
        self._contexts.setdefault(name, []).append(entry)
        return value, entry

    async def close_by_cm(self, cm: object) -> bool:
        """
        Close the context on the cm object itself.
                Returns True if found and closed, False otherwise.
        """
        cm_id = id(cm)
        for name, lst in list(self._contexts.items()):
            for i, (stored_id, stored_cm, stack, _) in enumerate(lst):
                if stored_id == cm_id and stored_cm is cm:
                    lst.pop(i)
                    await stack.aclose()
                    if not lst:
                        self._contexts.pop(name, None)
                    return True
        return False

    async def close_by_id(self, cm_id: int) -> bool:
        """Similar to close_by_cm, but by id(cm)."""
        for name, lst in list(self._contexts.items()):
            for i, (stored_id, _, stack, _) in enumerate(lst):
                if stored_id == cm_id:
                    lst.pop(i)
                    await stack.aclose()
                    if not lst:
                        self._contexts.pop(name, None)
                    return True
        return False

    async def close_last(self, name: str) -> bool:
        """Close the last (LIFO) context from the name group."""
        lst = self._contexts.get(name)
        if not lst:
            return False
        _, _, stack, _ = lst.pop()
        await stack.aclose()
        if not lst:
            self._contexts.pop(name, None)
        return True

    async def close_all(self, name: Optional[str] = None) -> None:
        """Close all contexts in a group or all groups."""
        if name is None:
            names = list(self._contexts.keys())
            for n in names:
                await self.close_all(n)
            return
        lst = self._contexts.pop(name, [])
        while lst:
            _, _, stack, _ = lst.pop()
            await stack.aclose()
