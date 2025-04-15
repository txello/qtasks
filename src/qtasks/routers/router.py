import inspect
from typing import TYPE_CHECKING, Optional, Type
from typing_extensions import Annotated, Doc

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
        
        self.plugins: dict[str, "BasePlugin"] = {}
    
    def task(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя задачи.
                    
                    По умолчанию: `func.__name__`.
                    """
                )
            ] = None
        ):
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
        """
        def wrapper(func):
            nonlocal name
            task_name = name or func.__name__
            model = TaskExecSchema(name=task_name, priority=0, func=func, awaiting=inspect.iscoroutinefunction(func))
            
            self.tasks[task_name] = model
            
            return func
        return wrapper
