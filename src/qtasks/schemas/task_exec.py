"""TaskPriority and TaskExec Schema."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from types import FunctionType
from typing import TYPE_CHECKING, Literal
from uuid import UUID

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware


@dataclass(order=True)
class TaskPrioritySchema:
    """
    `TaskPrioritySchema` schema.
    
        Args:
            priority (int): Priority.
            uuid (UUID): UUID.
            name (str): Name.
    
            args (Tuple[str]): Arguments of type args.
            kwargs (Dict[str, str]): Arguments of type kwargs.
    
            created_at (float): Created date in `timestamp` format.
            updated_at (float): Update date in `timestamp` format.
    """

    priority: int
    uuid: UUID = field(compare=False)
    name: str = field(compare=False)

    args: list = field(default_factory=list, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)

    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class TaskExecSchema:
    """
    `TaskExecSchema` schema.
    
        Args:
            priority (int): Priority.
            name (str): Name.
    
            func (FunctionType): Task function.
            awaiting (bool): Asynchronous task. Default: `False`
            generating (str|Literal[False]): Generating a task. Default: `False`
    
            echo (bool): Include the self parameter in the task. Default: `False`
    
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`
    
            retry (int, optional): Number of attempts to retry the task. Default: `None`
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`
    
            decode (Callable, optional): Decoder of the task result. Default: `None`
            tags (List[str], optional): Task tags. Default: `None`
            description (str, optional): Description of the task. Default: `None`.
    
            generate_handler (Callable, optional): Handler generator. Default: `None`
    
            executor (Type[BaseTaskExecutor], optional): Class `BaseTaskExecutor`. Default: `SyncTaskExecutor`|`AsyncTaskExecutor`.
            middlewares_before (List[Type[TaskMiddleware]]): Middleware before the task is executed. Default: `Empty array`.
            middlewares_after (List[Type[TaskMiddleware]]): Middleware after task execution. Default: `Empty array`.
    
            extra (Dict[str, Any]): Additional task parameters. Default: `Empty dictionary`.
    """

    priority: int
    name: str

    func: FunctionType
    awaiting: bool = False
    generating: str | Literal[False] = False

    echo: bool = False

    max_time: float | None = None

    retry: int | None = None
    retry_on_exc: list[type[Exception]] | None = None

    decode: Callable | None = None
    tags: list[str] | None = None
    description: str | None = None

    generate_handler: Callable | None = None

    executor: type[BaseTaskExecutor] | None = None
    middlewares_before: list[type[TaskMiddleware]] = field(default_factory=list)
    middlewares_after: list[type[TaskMiddleware]] = field(default_factory=list)

    extra: dict = field(default_factory=dict)

    def add_middlewares_before(self, middlewares: list[type[TaskMiddleware]]) -> None:
        """
        Adds a middleware to a task.
        
                Args:
                    middlewares (List[Type[TaskMiddleware]]): List of middlewares.
        """
        self.middlewares_before.extend(middlewares)

    def add_middlewares_after(self, middlewares: list[type[TaskMiddleware]]) -> None:
        """
        Adds a middleware to a task.
        
                Args:
                    middlewares (List[Type[TaskMiddleware]]): List of middlewares.
        """
        self.middlewares_after.extend(middlewares)
