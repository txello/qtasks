import inspect
from typing import TYPE_CHECKING, List, Optional, Type
from typing_extensions import Annotated, Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin

class Router:
    """
    Роутер, который хранит в себе задачи, которые подключает к себе основной `QueueTasks`.

    ## Example

    ```python
    from qtasks import QueueTasks, Router

    app = QueueTasks()
    
    router = Router()
    
    @router.task()
    async def test():
        pass
    
    app.include_router(router)
    ```
    """
    def __init__(self):
        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.
                
                По умолчанию: `Пустой словарь`.
                """
            )
        ] = {}
        
        self.plugins: dict[str, List["BasePlugin"]] = {}
    
    def task(self,
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
            ] = 0,
            executor: Annotated[
                Type["BaseTaskExecutor"],
                Doc(
                    """
                    Класс `BaseTaskExecutor`.
                    
                    По умолчанию: `SyncTaskExecutor`.
                    """
                )
            ] = None,
            middlewares: Annotated[
                List[TaskMiddleware],
                Doc(
                    """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None
        ):
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
        """
        def wrapper(func):
            nonlocal name, priority, executor, middlewares
            task_name = name or func.__name__
            middlewares = middlewares or []
            model = TaskExecSchema(name=task_name, priority=priority, func=func, awaiting=inspect.iscoroutinefunction(func), executor=executor, middlewares=middlewares)
            
            self.tasks[task_name] = model
            
            return SyncTask(task_name=task_name, priority=priority, executor=executor, middlewares=middlewares)
        return wrapper
