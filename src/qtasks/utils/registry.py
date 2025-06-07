from typing import Callable, List, Type, Union

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask


def shared_task(
        func_or_name: Union[Callable, str, None] = None,
        priority: int = 0, executor: Type["BaseTaskExecutor"] = None,
        middlewares: List[TaskMiddleware] = None,
        awaiting: bool = False,
        echo: bool = False,
        retry: int|None = None

    ) -> Type[SyncTask]:
    middlewares = middlewares or []
    if callable(func_or_name):
        # Декоратор без скобок
        return _wrap_function(
            func=func_or_name, name=func_or_name.__name__, priority=priority,
            awaiting=awaiting, echo=echo, retry=retry,
            executor=executor, middlewares=middlewares
        )
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return _wrap_function(
            func=func, name=func_or_name or func.__name__, priority=priority, 
            awaiting=awaiting, echo=echo, retry=retry,
            executor=executor, middlewares=middlewares
        )
    
    return wrapper

def _wrap_function(func: Callable,
        name: str, priority: int, 
        
        awaiting: bool,
        echo: bool,
        retry: int|None,
        
        executor: Type["BaseTaskExecutor"], middlewares: List[TaskMiddleware]
    ) -> Type[SyncTask]:
    """Оборачивает функцию и регистрирует её через register"""
    return TaskRegistry.register(name=name, priority=priority,
        awaiting=awaiting, echo=echo, retry=retry,
        executor=executor, middlewares=middlewares
    )(func)  # Вызываем register и регистрируем функцию
