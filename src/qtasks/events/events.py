"""Events."""

import inspect
from abc import ABC
from collections.abc import Awaitable, Callable

from qtasks.schemas.inits import InitsExecSchema


class BaseOnEvents(ABC):  # noqa: B024
    """Базовый класс для событий."""

    def __init__(self):
        """Инициализация базового класса событий."""
        self._events: dict[str, list[Callable[..., Awaitable | None]]] = {}

    def _make_decorator(self, event_name: str):
        """Создание декоратора для события."""

        def decorator(func: Callable):
            self._events.setdefault(event_name, []).append(func)
            return InitsExecSchema(
                name=event_name, func=func, awaiting=inspect.iscoroutinefunction(func)
            )

        return decorator


class OnEvents(BaseOnEvents):
    """Класс для обработки событий."""

    def __init__(self):
        """Инициализация класса для обработки событий."""
        super().__init__()

    def starting(self):
        """Событие запуска."""
        return self._make_decorator("starting")

    def stopping(self):
        """Событие остановки."""
        return self._make_decorator("stopping")

    def worker_running(self):
        """Событие работы воркера."""
        return self._make_decorator("worker_running")

    def worker_stopping(self):
        """Событие остановки воркера."""
        return self._make_decorator("worker_stopping")

    def task_running(self):
        """Событие выполнения задачи."""
        return self._make_decorator("task_running")

    def task_success(self):
        """Событие успешного завершения задачи."""
        return self._make_decorator("task_success")

    def task_error(self):
        """Событие неуспешного завершения задачи."""
        return self._make_decorator("task_error")

    def task_cancel(self):
        """Событие отмены задачи."""
        return self._make_decorator("task_cancel")

    def task_stopping(self):
        """Событие остановки задачи."""
        return self._make_decorator("task_stopping")
