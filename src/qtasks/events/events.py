"""Events."""

import inspect
from abc import ABC
from collections.abc import Awaitable, Callable

from qtasks.schemas.inits import InitsExecSchema


class BaseOnEvents(ABC):  # noqa: B024
    """Base class for events."""

    def __init__(self):
        """Initialize the base event class."""
        self._events: dict[str, list[Callable[..., Awaitable | None]]] = {}

    def _make_decorator(self, event_name: str):
        """Creating a decorator for an event."""

        def decorator(func: Callable):
            self._events.setdefault(event_name, []).append(func)
            return InitsExecSchema(
                name=event_name, func=func, awaiting=inspect.iscoroutinefunction(func)
            )

        return decorator


class OnEvents(BaseOnEvents):
    """Class for handling events."""

    def __init__(self):
        """Initializing a class to handle events."""
        super().__init__()

    def starting(self):
        """Start event."""
        return self._make_decorator("starting")

    def stopping(self):
        """Stop event."""
        return self._make_decorator("stopping")

    def worker_running(self):
        """Worker work event."""
        return self._make_decorator("worker_running")

    def worker_stopping(self):
        """Worker stop event."""
        return self._make_decorator("worker_stopping")

    def task_running(self):
        """Task completion event."""
        return self._make_decorator("task_running")

    def task_success(self):
        """Event of successful completion of a task."""
        return self._make_decorator("task_success")

    def task_error(self):
        """Event of unsuccessful completion of a task."""
        return self._make_decorator("task_error")

    def task_cancel(self):
        """Task cancellation event."""
        return self._make_decorator("task_cancel")

    def task_stopping(self):
        """Task stop event."""
        return self._make_decorator("task_stopping")
