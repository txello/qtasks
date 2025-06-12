import inspect
from typing import TYPE_CHECKING, Callable, List, Literal, Optional, Type, Union, overload
from typing_extensions import Annotated, Doc

from qtasks.types.annotations import P, R
from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.async_task_decorator import AsyncTask
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
    @overload
    def __init__(self, method: Literal["sync"] = None) -> None: ...
    @overload
    def __init__(self, method: Literal["async"] = None) -> None: ...

    def __init__(self, method: Literal["sync", "async"] = None):
        self._method = method
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
                Optional[int],
                Doc(
                    """
                    Приоритет у задачи по умолчанию.
                    
                    По умолчанию: `config.default_task_priority`.
                    """
                )
            ] = None,

            echo: bool = False,
            retry: int|None = None,
            retry_on_exc: list[Type[Exception]]|None = None,
            generate_handler: Callable|None = None,

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
                List["TaskMiddleware"],
                Doc(
                    """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None
        ) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Включить вывод в консоль. По умолчанию: `False`.
            retry (int|None, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (list[Type[Exception]]|None, optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            generate_handler (Callable|None, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares (List["TaskMiddleware"], optional): Мидлвари. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            Callable[SyncTask|AsyncTask]: Декоратор для регистрации задачи.
        """
        def wrapper(func):
            nonlocal name, priority, executor, middlewares, echo, retry, retry_on_exc
            
            task_name = name or func.__name__
            if task_name in self.tasks:
                raise ValueError(f"Задача с именем {task_name} уже зарегистрирована!")
            
            if priority is None:
                priority = 0
            
            generating = False
            if inspect.isgeneratorfunction(func): generating = "sync"
            if inspect.isasyncgenfunction(func): generating = "async"

            middlewares = middlewares or []
            
            model = TaskExecSchema(
                name=task_name, priority=priority, func=func,
                awaiting=inspect.iscoroutinefunction(func),
                generating=generating,

                echo=echo,
                retry=retry,
                retry_on_exc=retry_on_exc,
                generate_handler=generate_handler,

                executor=executor, middlewares=middlewares
            )
            
            self.tasks[task_name] = model
            if self._method == "async":
                return AsyncTask(app=self, task_name=task_name, priority=priority, echo=echo, retry=retry, retry_on_exc=retry_on_exc, generate_handler=generate_handler, executor=executor, middlewares=middlewares)
            elif self._method == "sync":
                return SyncTask(app=self, task_name=task_name, priority=priority, echo=echo, retry=retry, retry_on_exc=retry_on_exc, generate_handler=generate_handler, executor=executor, middlewares=middlewares)
            else:
                raise ValueError(f"Неизвестный метод {self._method}")
        return wrapper
