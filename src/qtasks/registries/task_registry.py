import inspect
from typing import Callable, Optional
from typing_extensions import Annotated, Doc

from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema


class TaskRegistry:
    """Регистратор задач. Нужен для задач, зарегистрированных через `@shared_task`.
    
    Задачи регистрируются в `QueueTasks.__init__()`
    """
    
    _tasks: Annotated[
        dict[str, TaskExecSchema],
        Doc(
            """
            Задачи.
            
            По умолчанию: `{}`.
            """
        )
    ] = {}

    @classmethod
    def register(cls, 
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя задачи.
                    
                    По умолчанию: `func.__name__`.
                    """
                )
            ] = None,
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0
        ) -> None:
        """Регистрация задачи.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int): Приоритет задачи. По умолчанию: `0`.
        """
        def wrapper(func: Callable):
            nonlocal name, priority
            
            task_name = name or func.__name__
            model = TaskExecSchema(name=task_name, priority=priority, func=func, awaiting=inspect.iscoroutinefunction(func))
            cls._tasks[task_name] = model
            return SyncTask(task_name=task_name, priority=priority)
        return wrapper

    @classmethod
    def get_task(cls, 
            name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    
                    По умолчанию: `func.__name__`.
                    """
                )
            ]
        ) -> TaskExecSchema:
        """Получение задачи.

        Args:
            name (str): Имя задачи.

        Returns:
            TaskExecSchema: Задача, тип `{task_name:qtasks.schemas.TaskExecSchema}`.
        """
        return cls._tasks.get(name)

    @classmethod
    def all_tasks(cls) -> dict[str, TaskExecSchema]:
        """Получение всех задач.

        Returns:
            dict[str, TaskExecSchema]: Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.
        """
        return cls._tasks