import functools
from typing import Callable, Union

from qtasks.registries.task_registry import TaskRegistry


def shared_task(func_or_name: Union[Callable, str, None] = None, priority: int = 0):
    if callable(func_or_name):
        # Декоратор без скобок
        return _wrap_function(func_or_name, func_or_name.__name__, priority)
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return _wrap_function(func, func_or_name or func.__name__, priority)
    
    return wrapper

def _wrap_function(func: Callable, name: str, priority: int):
    """Оборачивает функцию и регистрирует её через register"""
    wrapped_func = TaskRegistry.register(name, priority)(func)  # Вызываем register и регистрируем функцию
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return wrapped_func(*args, **kwargs)

    return wrapper