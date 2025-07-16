"""Task Registry."""

import inspect
from typing import Callable, List, Optional, Type, Union
from typing_extensions import Annotated, Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.async_task_decorator import AsyncTask
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
        ),
    ] = {}

    @classmethod
    def register(
        cls,
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
        decode: Annotated[
            Callable | None,
            Doc(
                """
                    Декодер результата задачи.

                    По умолчанию: `None`.
                    """
            )
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                    """
            )
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
        **kwargs
    ) -> Callable[[Callable], Union[SyncTask, AsyncTask]]:
        """Регистрация задачи.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Включить вывод в консоль. По умолчанию: `False`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (list[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (list[str], optional): Теги задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares (List["TaskMiddleware"], optional): Мидлвари. По умолчанию: `Пустой массив`.
        """

        def wrapper(func: Callable):
            nonlocal middlewares

            task_name = name or func.__name__

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
                decode=decode,
                tags=tags,
                generate_handler=generate_handler,
                executor=executor,
                middlewares=middlewares,
                extra=kwargs
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
                generate_handler=model.generate_handler,
                executor=model.executor,
                middlewares=model.middlewares,
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
