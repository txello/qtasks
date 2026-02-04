"""QTasks registry utilities."""
from __future__ import annotations

from collections.abc import Callable
from types import FunctionType
from typing import Annotated, Literal, overload

from typing_extensions import Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.task_registry import TaskRegistry
from qtasks.types.annotations import P, R


@overload
def shared_task(
    name: Annotated[
        str | Callable | None,
        Doc("""
                    Task name.

                    Default: `func.__name__`.
                    """),
    ] = None,
    priority: Annotated[
        int | None,
        Doc("""
                    The task has priority by default.

                    Default: `config.task_default_priority`.
                    """),
    ] = None,
    echo: Annotated[
        bool,
        Doc("""
                    Add (A)syncTask as the first parameter.

                    Default: `False`.
                    """),
    ] = False,
    retry: Annotated[
        int | None,
        Doc("""
                    The number of attempts to retry the task.

                    Default: `None`.
                    """),
    ] = None,
    retry_on_exc: Annotated[
        list[type[Exception]] | None,
        Doc("""
                    Exceptions under which the task will be re-executed.

                    Default: `None`.
                    """),
    ] = None,
    decode: Annotated[
        Callable | None,
        Doc("""
                Task result decoder.

                Default: `None`.
            """),
    ] = None,
    tags: Annotated[
        list[str] | None,
        Doc("""
                Task tags.

                Default: `None`.
            """),
    ] = None,
    description: Annotated[
        str | None,
        Doc("""
                Description of the task.

                Default: `None`.
            """),
    ] = None,
    generate_handler: Annotated[
        Callable | None,
        Doc("""
                    Handler generator.

                    Default: `None`.
                    """),
    ] = None,
    executor: Annotated[
        type[BaseTaskExecutor] | None,
        Doc("""
                    Class `BaseTaskExecutor`.

                    Default: `SyncTaskExecutor`.
                    """),
    ] = None,
    middlewares_before: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed before the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    middlewares_after: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed after the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    awaiting: Annotated[
        Literal[False],
        Doc("""
                    Async version.

                    Default: `None`.
                    """),
    ] = False,
    **kwargs,
) -> SyncTask[P, R] | Callable[[Callable[P, R]], SyncTask[P, R]]: ...


@overload
def shared_task(
    name: Annotated[
        str | Callable[P, R] | None,
        Doc("""
                    Task name.

                    Default: `func.__name__`.
                    """),
    ] = None,
    priority: Annotated[
        int | None,
        Doc("""
                    The task has priority by default.

                    Default: `config.task_default_priority`.
                    """),
    ] = None,
    echo: Annotated[
        bool,
        Doc("""
                    Add (A)syncTask as the first parameter.

                    Default: `False`.
                    """),
    ] = False,
    retry: Annotated[
        int | None,
        Doc("""
                    The number of attempts to retry the task.

                    Default: `None`.
                    """),
    ] = None,
    retry_on_exc: Annotated[
        list[type[Exception]] | None,
        Doc("""
                    Exceptions under which the task will be re-executed.

                    Default: `None`.
                    """),
    ] = None,
    decode: Annotated[
        Callable | None,
        Doc("""
                Task result decoder.

                Default: `None`.
            """),
    ] = None,
    tags: Annotated[
        list[str] | None,
        Doc("""
                Task tags.

                Default: `None`.
            """),
    ] = None,
    description: Annotated[
        str | None,
        Doc("""
                Description of the task.

                Default: `None`.
            """),
    ] = None,
    generate_handler: Annotated[
        Callable | None,
        Doc("""
                    Handler generator.

                    Default: `None`.
                    """),
    ] = None,
    executor: Annotated[
        type[BaseTaskExecutor] | None,
        Doc("""
                    Class `BaseTaskExecutor`.

                    Default: `SyncTaskExecutor`.
                    """),
    ] = None,
    middlewares_before: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed before the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    middlewares_after: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed after the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    awaiting: Annotated[
        Literal[True],
        Doc("""
                    Async version.

                    Default: `False`.
                    """),
    ] = True,
    **kwargs,
) -> AsyncTask[P, R] | Callable[[Callable[P, R]], AsyncTask[P, R]]: ...


def shared_task(
    name: Annotated[
        str | Callable | None,
        Doc("""
                    Task name.

                    Default: `func.__name__`.
                    """),
    ] = None,
    priority: Annotated[
        int | None,
        Doc("""
                    The task has priority by default.

                    Default: `config.task_default_priority`.
                    """),
    ] = None,
    echo: Annotated[
        bool,
        Doc("""
                    Add (A)syncTask as the first parameter.

                    Default: `False`.
                    """),
    ] = False,
    retry: Annotated[
        int | None,
        Doc("""
                    The number of attempts to retry the task.

                    Default: `None`.
                    """),
    ] = None,
    retry_on_exc: Annotated[
        list[type[Exception]] | None,
        Doc("""
                    Exceptions under which the task will be re-executed.

                    Default: `None`.
                    """),
    ] = None,
    decode: Annotated[
        Callable | None,
        Doc("""
                Task result decoder.

                Default: `None`.
            """),
    ] = None,
    tags: Annotated[
        list[str] | None,
        Doc("""
                Task tags.

                Default: `None`.
            """),
    ] = None,
    description: Annotated[
        str | None,
        Doc("""
                Description of the task.

                Default: `None`.
            """),
    ] = None,
    generate_handler: Annotated[
        Callable | None,
        Doc("""
                    Handler generator.

                    Default: `None`.
                    """),
    ] = None,
    executor: Annotated[
        type[BaseTaskExecutor] | None,
        Doc("""
                    Class `BaseTaskExecutor`.

                    Default: `SyncTaskExecutor`.
                    """),
    ] = None,
    middlewares_before: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed before the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    middlewares_after: Annotated[
        list[type[TaskMiddleware]] | None,
        Doc("""
                    Middleware that will be executed after the task.

                    Default: `Empty array`.
                    """),
    ] = None,
    awaiting: Annotated[
        bool | None,
        Doc("""
                    Async version.

                    Default: `False`.
                    """),
    ] = None,
    **kwargs,
) -> SyncTask[P, R] | AsyncTask[P, R] | Callable[[Callable[P, R]], SyncTask[P, R] | AsyncTask[P, R]]:
    """Декоратор для регистрации задач.

    Args:
        name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
        priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.task_default_priority`.
        echo (bool, optional): Добавить (A)syncTask первым параметром. По умолчанию: `False`.
        retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
        retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
        decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
        tags (List[str], optional): Теги задачи. По умолчанию: `None`.
        description (str, optional): Описание задачи. По умолчанию: `None`.
        generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
        executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
        middlewares_before (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены перед задачей. По умолчанию: `Пустой массив`.
        middlewares_after (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.
        awaiting (bool, optional): Использовать ли AsyncTask вместо SyncTask. По умолчанию: `False`.

    Raises:
        ValueError: Если задача с таким именем уже зарегистрирована.
        ValueError: Unknown method {self._method}.

    Returns:
        SyncTask | AsyncTask: Декоратор для регистрации задачи.
    """
    middlewares_before = middlewares_before or []
    middlewares_after = middlewares_after or []

    if not awaiting:
        awaiting = False

    if isinstance(name, FunctionType):
        # Декоратор без скобок
        return TaskRegistry.register(
            name=name.__name__,
            priority=priority or 0,
            awaiting=awaiting,
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
            **kwargs,
        )(
            name
        )  # type: ignore

    # Декоратор со скобками
    def wrapper(func: Callable[P, R]):
        return TaskRegistry.register(
            name=name if isinstance(name, str) else func.__name__,
            priority=priority or 0,
            awaiting=awaiting,
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
            **kwargs,
        )(func)

    return wrapper
