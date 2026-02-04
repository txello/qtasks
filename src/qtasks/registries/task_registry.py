"""Task Registry."""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Annotated

from typing_extensions import Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema


class TaskRegistry:
    """
    Task recorder. Needed for tasks registered via `@shared_task`.
    
        Tasks are registered in `QueueTasks.__init__()`
    """

    _tasks: Annotated[
        dict[str, TaskExecSchema],
        Doc(
            """
            Задачи.

            По умолчанию: `{}`.
            """
        ),
    ] = {}

    @classmethod
    def register(
        cls,
        name: Annotated[
            str | None,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.

                    По умолчанию: `0`.
                    """
            ),
        ] = 0,
        awaiting: Annotated[
            bool,
            Doc(
                """
                    Использовать ли AsyncTask вместо SyncTask

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        echo: Annotated[
            bool,
            Doc(
                """
                    Добавить (A)syncTask первым параметром.

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
    ) -> Callable[[Callable], SyncTask | AsyncTask]:
        """
        Register a task.
        
                Args:
                    name (str, optional): Name of the task. Default: `func.__name__`.
                    priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
                    echo (bool, optional): Add (A)syncTask as the first parameter. Default: `False`.
                    retry (int, optional): Number of attempts to retry the task. Default: `None`.
                    retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
                    decode (Callable, optional): Decoder of the task result. Default: `None`.
                    tags (List[str], optional): Task tags. Default: `None`.
                    description (str, optional): Description of the task. Default: `None`.
                    generate_handler (Callable, optional): Handler generator. Default: `None`.
                    executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `SyncTaskExecutor`.
                    middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
                    middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.
        """

        def wrapper(func: Callable):
            nonlocal middlewares_before, middlewares_after

            task_name = name or func.__name__

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

            cls._tasks[task_name] = model

            method = AsyncTask if awaiting else SyncTask
            return method(
                task_name=model.name,
                priority=model.priority,
                echo=model.echo,
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

    @classmethod
    def get_task(
        cls,
        name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ],
    ) -> TaskExecSchema | None:
        """
        Receiving a task.
        
                Args:
                    name (str): Name of the task.
        
                Returns:
                    TaskExecSchema: Task type `{task_name:qtasks.schemas.TaskExecSchema}`.
        """
        return cls._tasks.get(name)

    @classmethod
    def all_tasks(cls) -> dict[str, TaskExecSchema]:
        """
        Retrieving all tasks.
        
                Returns:
                    Dict[str, TaskExecSchema]: Tasks, type `{task_name:qtasks.schemas.TaskExecSchema}`.
        """
        return cls._tasks
