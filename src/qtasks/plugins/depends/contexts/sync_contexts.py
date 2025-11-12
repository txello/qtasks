from contextlib import ExitStack
from typing import Any, Dict, List, Optional, Tuple


class SyncContextPool:
    """
    Хранит асинхронные контексты по группам (name).
    Ключ для идентификации конкретного контекста — id(cm).
    """

    def __init__(self):
        # name -> list[ (cm_id, cm_obj, AsyncExitStack, value) ]
        self._contexts: Dict[str, List[Tuple[int, object, ExitStack, Any]]] = {}

    def enter(self, name: str, cm: object) -> Any:
        """
        Войти в асинхронный контекст cm и сохранить его.
        Возвращает значение, полученное из yield в @contextmanager.
        """
        stack = ExitStack()
        value = stack.enter_context(cm) # type: ignore
        entry = (id(cm), cm, stack, value)
        self._contexts.setdefault(name, []).append(entry)
        return value, entry

    def close_by_cm(self, cm: object) -> bool:
        """
        Закрыть контекст по самому объекту cm.
        Возвращает True если найден и закрыт, иначе False.
        """
        cm_id = id(cm)
        for name, lst in list(self._contexts.items()):
            for i, (stored_id, stored_cm, stack, _) in enumerate(lst):
                if stored_id == cm_id and stored_cm is cm:
                    lst.pop(i)
                    stack.close()
                    if not lst:
                        self._contexts.pop(name, None)
                    return True
        return False

    def close_by_id(self, cm_id: int) -> bool:
        """
        Аналогично close_by_cm, но по id(cm).
        """
        for name, lst in list(self._contexts.items()):
            for i, (stored_id, _, stack, _) in enumerate(lst):
                if stored_id == cm_id:
                    lst.pop(i)
                    stack.close()
                    if not lst:
                        self._contexts.pop(name, None)
                    return True
        return False

    def close_last(self, name: str) -> bool:
        """Закрыть последний (LIFO) контекст из группы name."""
        lst = self._contexts.get(name)
        if not lst:
            return False
        _, _, stack, _ = lst.pop()
        stack.close()
        if not lst:
            self._contexts.pop(name, None)
        return True

    def close_all(self, name: Optional[str] = None) -> None:
        """Закрыть все контексты в группе или все группы."""
        if name is None:
            names = list(self._contexts.keys())
            for n in names:
                self.close_all(n)
            return
        lst = self._contexts.pop(name, [])
        while lst:
            _, _, stack, _ = lst.pop()
            stack.close()
