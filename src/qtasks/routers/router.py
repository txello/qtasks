"""Router for task execution."""

import inspect
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
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
            Dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.plugins: Dict[str, List["BasePlugin"]] = {}

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
        *,
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
                    Добавить (A)syncTask первым параметром.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        max_time: Annotated[
            Union[float, None],
            Doc(
                """
                    Максимальное время выполнения задачи в секундах.

                    По умолчанию: `None`.
                    """
            )
        ] = None,
        retry: Annotated[
            Union[int, None],
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            Union[List[Type[Exception]], None],
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Union[Callable, None],
            Doc(
                """
                    Декодер результата задачи.

                    По умолчанию: `None`.
                """
            )
        ] = None,
        tags: Annotated[
            Union[List[str], None],
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                """
            )
        ] = None,
        description: Annotated[
            Union[str, None],
            Doc(
                """
                    Описание задачи.

                    По умолчанию: `None`.
                """
            )
        ] = None,
        generate_handler: Annotated[
            Union[Callable, None],
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
        middlewares_before: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        **kwargs
    ) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Добавить (A)syncTask первым параметром. По умолчанию: `False`.
            max_time (float, optional): Максимальное время выполнения задачи в секундах. По умолчанию: `None`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares_before (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены перед задачей. По умолчанию: `Пустой массив`.
            middlewares_after (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            SyncTask | AsyncTask: Декоратор для регистрации задачи.
        """

        def wrapper(func):
            nonlocal priority, middlewares_before, middlewares_after

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

            middlewares_before = middlewares_before or []
            middlewares_after = middlewares_after or []

            model = TaskExecSchema(
                name=task_name,
                priority=priority,
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
                generating=generating,
                echo=echo,
                max_time=max_time,
                retry=retry,
                retry_on_exc=retry_on_exc,
                decode=decode,
                tags=tags,
                description=description,
                generate_handler=generate_handler,
                executor=executor,
                middlewares_before=middlewares_before,
                middlewares_after=middlewares_after,
                extra=kwargs
            )

            self.tasks[task_name] = model
            if self._method not in ["async", "sync"]:
                raise ValueError(f"Неизвестный метод {self._method}")

            method = AsyncTask if self._method == "async" else SyncTask
            return method(
                app=self,
                task_name=model.name,
                priority=model.priority,
                echo=model.echo,
                max_time=model.max_time,
                retry=model.retry,
                retry_on_exc=model.retry_on_exc,
                decode=model.decode,
                tags=model.tags,
                description=model.description,
                generate_handler=model.generate_handler,
                executor=model.executor,
                middlewares_before=model.middlewares_before,
                middlewares_after=model.middlewares_after,
            )

        return wrapper
