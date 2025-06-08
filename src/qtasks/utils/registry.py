from typing import Callable, List, Type, Union

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.async_task_decorator import AsyncTask


def shared_task(
        func_or_name: Union[Callable, str, None] = None,
        priority: int = 0,

        echo: bool = False,
        retry: int|None = None,
        awaiting: bool = False,

        generate_handler: Callable|None = None,
        executor: Type["BaseTaskExecutor"] = None,
        middlewares: List[TaskMiddleware] = None


    ) -> Type[SyncTask]|Type[AsyncTask]:
    middlewares = middlewares or []
    if callable(func_or_name):
        # Декоратор без скобок
        return TaskRegistry.register(name=func_or_name.__name__, priority=priority,
        awaiting=awaiting, echo=echo, retry=retry,


        executor=executor, middlewares=middlewares
        )(func_or_name)
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return TaskRegistry.register(name=func_or_name or func.__name__, priority=priority,
        awaiting=awaiting, echo=echo, retry=retry,
        generate_handler=generate_handler,
        executor=executor, middlewares=middlewares
        )(func)
    
    return wrapper
