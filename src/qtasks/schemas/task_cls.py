"""Task Cls Schema."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Generic,
    Optional,
    Union,
    overload,
)

from qtasks.schemas.task import Task
from qtasks.types.typing import TTask

if TYPE_CHECKING:
    from qtasks.registries.async_task_decorator import AsyncTask  # noqa: F401
    from qtasks.registries.sync_task_decorator import SyncTask  # noqa: F401


@dataclass
class BaseTaskCls(Generic[TTask], ABC):
    """`Task` Cls модель.

    Args:
        task_name (str, optional): Название задачи. По умолчанию: `None`.

        priority (int, optional): Приоритет задачи. По умолчанию: `None`.
        timeout (float, optional): Таймаут задачи. По умолчанию: `None`.

        args (Tuple[str]): Аргументы типа args. По умолчанию: `()`.
        kwargs (Dict[str, Any]): Аргументы типа kwargs. По умолчанию: `{}`.
    """
    task_name: Optional[str] = None

    priority: Optional[int] = None
    timeout: Optional[float] = None

    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)

    _task_deco: Optional[TTask] = field(default=None, init=False, repr=False, compare=False)

    def bind(self, deco: TTask) -> None:
        self._task_deco = deco

    @overload
    def add_task(self: BaseTaskCls["SyncTask"]) -> Optional[Task]: ...  # noqa: UP037

    @overload
    async def add_task(self: BaseTaskCls["AsyncTask"]) -> Optional[Task]: ...  # noqa: UP037

    @abstractmethod
    def add_task(self) -> Union[
        Optional[Task], Awaitable[Optional[Task]]
    ]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncResult` или `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        pass


class AsyncTaskCls(BaseTaskCls["AsyncTask"]):
    async def add_task(self) -> Union[
        Optional[Task], Task
    ]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.

        Raises:
            RuntimeError: Если `AsyncTask` не объявлен.
        """
        if not self._task_deco:
            raise RuntimeError("AsyncTask не объявлен!")

        return await self._task_deco.add_task(*self.args, task_name=self.task_name, priority=self.priority, timeout=self.timeout, **self.kwargs)


class SyncTaskCls(BaseTaskCls["SyncTask"]):
    def add_task(self) -> Union[
        Optional[Task], Task
    ]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.

        Raises:
            RuntimeError: Если `SyncTask` не объявлен.
        """
        if not self._task_deco:
            raise RuntimeError("SyncTask не объявлен!")

        return self._task_deco.add_task(*self.args, task_name=self.task_name, priority=self.priority, timeout=self.timeout, **self.kwargs)
