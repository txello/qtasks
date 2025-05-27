from typing import Callable, List, Type, Union

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask


def shared_task(
        func_or_name: Union[Callable, str, None] = None,
        priority: int = 0, executor: Type["BaseTaskExecutor"] = None,
        middlewares: List[TaskMiddleware] = None,
        awaiting: bool = False
    ) -> Type[SyncTask]:
    middlewares = middlewares or []
    if callable(func_or_name):
        # Декоратор без скобок
        return _wrap_function(func_or_name, func_or_name.__name__, priority, executor, middlewares, awaiting)
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return _wrap_function(func, func_or_name or func.__name__, priority, executor, middlewares, awaiting)
    
    return wrapper

def _wrap_function(func: Callable, name: str, priority: int, executor: Type["BaseTaskExecutor"], middlewares: List[TaskMiddleware], awaiting: bool = False) -> Type[SyncTask]:
    """Оборачивает функцию и регистрирует её через register"""
    return TaskRegistry.register(name=name, priority=priority, executor=executor, middlewares=middlewares, awaiting=awaiting)(func)  # Вызываем register и регистрируем функцию