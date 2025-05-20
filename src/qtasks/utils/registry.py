from typing import Callable, Type, Union

from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask


def shared_task(func_or_name: Union[Callable, str, None] = None, priority: int = 0) -> Type[SyncTask]:
    if callable(func_or_name):
        # Декоратор без скобок
        return _wrap_function(func_or_name, func_or_name.__name__, priority)
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return _wrap_function(func, func_or_name or func.__name__, priority)
    
    return wrapper

def _wrap_function(func: Callable, name: str, priority: int) -> Type[SyncTask]:
    """Оборачивает функцию и регистрирует её через register"""
    return TaskRegistry.register(name, priority)(func)  # Вызываем register и регистрируем функцию