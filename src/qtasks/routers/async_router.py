"""Router for task execution."""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Annotated,
)

from typing_extensions import Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.types.annotations import P, R

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class AsyncRouter(AsyncPluginMixin):
    """
    A router that stores tasks that the main `QueueTasks` connects to itself.

    ## Example

    ```python
    from qtasks import QueueTasks, AsyncRouter

    app = QueueTasks()

    router = AsyncRouter()

    @router.task()
    async def test():
        pass

    app.include_router(router)
    ```
    """

    def __init__(self) -> None:
        """Initializing the router."""
        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.plugins: dict[str, list[BasePlugin]] = {}

    def task(
        self,
        name: Annotated[
            str | Callable | None,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        *,
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи по умолчанию.

                    По умолчанию: `config.task_default_priority`.
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
            float | None,
            Doc(
                """
                    Максимальное время выполнения задачи в секундах.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
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
            list[type[Exception]] | None,
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Callable | None,
            Doc(
                """
                    Декодер результата задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                    Описание задачи.

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
            type[BaseTaskExecutor] | None,
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares_before: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        **kwargs,
    ) -> AsyncTask[P, R] | Callable[[Callable[P, R]], AsyncTask[P, R]]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add (A)syncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.

        Returns:
            SyncTask: Decorator for registering a task.
        """

        def wrapper(func: Callable[P, R]):
            nonlocal priority, middlewares_before, middlewares_after

            task_name = name or func.__name__ if not callable(name) else name.__name__
            if task_name in self.tasks:
                raise ValueError(f"Task with name {task_name} is already registered!")

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
                extra=kwargs,
            )

            self.tasks[task_name] = model

            return AsyncTask(
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
