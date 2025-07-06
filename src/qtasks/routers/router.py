"""Router for task execution."""

import inspect
from typing import (
    TYPE_CHECKING,
    Callable,
    List,
    Literal,
    Optional,
    Type,
    Union,
    overload,
)
from typing_extensions import Annotated, Doc

from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.types.annotations import P, R
from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class Router(SyncPluginMixin):
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
    def __init__(self, method: Literal["sync"] = None) -> None:
        """Инициализация роутера для синхронных задач."""
        ...

    @overload
    def __init__(self, method: Literal["async"] = None) -> None:
        """Инициализация роутера для асинхронных задач."""
        ...

    def __init__(self, method: Literal["sync", "async"] = None):
        """Инициализация роутера.

        Args:
            method (Literal["sync", "async"], optional): Метод выполнения задач. По умолчанию: `None`.
        """
        self._method = method
        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.plugins: dict[str, List["BasePlugin"]] = {}

    def task(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc(
                """
                    Приоритет у задачи по умолчанию.

                    По умолчанию: `config.default_task_priority`.
                    """
            ),
        ] = None,
        echo: Annotated[
            bool,
            Doc(
                """
                    Включить вывод в консоль.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        retry: Annotated[
            int | None,
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            list[Type[Exception]] | None,
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        generate_handler: Annotated[
            Callable | None,
            Doc(
                """
                    Генератор обработчика.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            Type["BaseTaskExecutor"],
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
    ) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Включить вывод в консоль. По умолчанию: `False`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (list[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares (List["TaskMiddleware"], optional): Мидлвари. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            Callable[SyncTask|AsyncTask]: Декоратор для регистрации задачи.
        """

        def wrapper(func):
            nonlocal priority, middlewares

            task_name = name or func.__name__
            if task_name in self.tasks:
                raise ValueError(f"Задача с именем {task_name} уже зарегистрирована!")

            if priority is None:
                priority = 0

            generating = False
            if inspect.isgeneratorfunction(func):
                generating = "sync"
            if inspect.isasyncgenfunction(func):
                generating = "async"

            middlewares = middlewares or []

            model = TaskExecSchema(
                name=task_name,
                priority=priority,
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
                generating=generating,
                echo=echo,
                retry=retry,
                retry_on_exc=retry_on_exc,
                generate_handler=generate_handler,
                executor=executor,
                middlewares=middlewares,
            )

            self.tasks[task_name] = model
            if self._method == "async":
                return AsyncTask(
                    app=self,
                    task_name=task_name,
                    priority=priority,
                    echo=echo,
                    retry=retry,
                    retry_on_exc=retry_on_exc,
                    generate_handler=generate_handler,
                    executor=executor,
                    middlewares=middlewares,
                )
            elif self._method == "sync":
                return SyncTask(
                    app=self,
                    task_name=task_name,
                    priority=priority,
                    echo=echo,
                    retry=retry,
                    retry_on_exc=retry_on_exc,
                    generate_handler=generate_handler,
                    executor=executor,
                    middlewares=middlewares,
                )
            else:
                raise ValueError(f"Неизвестный метод {self._method}")

        return wrapper
