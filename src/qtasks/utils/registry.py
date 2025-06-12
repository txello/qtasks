from typing import Callable, List, Literal, Optional, Type, Union, overload

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.async_task_decorator import AsyncTask

def shared_task(
    func_or_name: Union[Callable, str, None] = None,
    *,
    awaiting: bool = False,
    priority: int = 0,
    echo: bool = False,
    retry: Optional[int] = None,
    generate_handler: Optional[Callable] = None,
    executor: Optional[Type[BaseTaskExecutor]] = None,
    middlewares: Optional[List[TaskMiddleware]] = None
) -> Union[Type[SyncTask], Type[AsyncTask]]:
    middlewares = middlewares or []

    if callable(func_or_name):
        # Декоратор без скобок
        return TaskRegistry.register(
            name=func_or_name.__name__,
            priority=priority,
            awaiting=awaiting,
            echo=echo,
            retry=retry,
            generate_handler=generate_handler,
            executor=executor,
            middlewares=middlewares,
        )(func_or_name)

    # Декоратор со скобками
    def wrapper(func: Callable) -> Union[SyncTask, AsyncTask]:
        return TaskRegistry.register(
            name=func_or_name or func.__name__,
            priority=priority,
            awaiting=awaiting,
            echo=echo,
            retry=retry,
            generate_handler=generate_handler,
            executor=executor,
            middlewares=middlewares,
        )(func)

    return wrapper
