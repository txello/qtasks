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
    """`Task` Cls model.

    Args:
        task_name (str, optional): Task name. Default: `None`.

        priority (int, optional): Task priority. Default: `None`.
        timeout (float, optional): Task timeout. Default: `None`.

        args (Tuple[str]): Arguments of type args. Default: `()`.
        kwargs (Dict[str, Any]): Arguments of type kwargs. Default: `{}`.
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
        """Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Defaults to `()`.
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.

            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.SyncResult` or `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` or `None`.
        """
        pass


class AsyncTaskCls(BaseTaskCls["AsyncTask"]):
    async def add_task(self) -> Union[
        Optional[Task], Task
    ]:
        """Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Defaults to `()`.
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.

            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` or `None`.

        Raises:
            RuntimeError: If `AsyncTask` is not declared.
        """
        if not self._task_deco:
            raise RuntimeError("AsyncTask не объявлен!")

        return await self._task_deco.add_task(*self.args, task_name=self.task_name, priority=self.priority, timeout=self.timeout, **self.kwargs)


class SyncTaskCls(BaseTaskCls["SyncTask"]):
    def add_task(self) -> Union[
        Optional[Task], Task
    ]:
        """Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Defaults to `()`.
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.

            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.SyncResult`.

        Returns:
            Task|None: `schemas.task.Task` or `None`.

        Raises:
            RuntimeError: If `SyncTask` is not declared.
        """
        if not self._task_deco:
            raise RuntimeError("SyncTask не объявлен!")

        return self._task_deco.add_task(*self.args, task_name=self.task_name, priority=self.priority, timeout=self.timeout, **self.kwargs)
