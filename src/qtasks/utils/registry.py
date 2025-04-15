import functools
from typing import Callable, Union

from qtasks.registries.task_registry import TaskRegistry


def shared_task(func_or_name: Union[Callable, str, None] = None):
    if callable(func_or_name):
        # Декоратор без скобок
        return _wrap_function(func_or_name, func_or_name.__name__)
    
    # Декоратор со скобками
    def wrapper(func: Callable):
        return _wrap_function(func, func_or_name or func.__name__)
    
    return wrapper

def _wrap_function(func: Callable, name: str):
    """Оборачивает функцию и регистрирует её через register"""
    wrapped_func = TaskRegistry.register(name)(func)  # Вызываем register и регистрируем функцию
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Function '{name}' is called")
        return wrapped_func(*args, **kwargs)

    return wrapper