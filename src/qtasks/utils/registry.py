"""QTasks registry utilities."""

from typing import Callable, List, Optional, Type, Union
from typing_extensions import Annotated, Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.async_task_decorator import AsyncTask


def shared_task(
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
                    Добавить (A)syncTask первым параметром.

                    По умолчанию: `False`.
                    """
        ),
    ] = False,
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
    awaiting: Annotated[
        bool,
        Doc(
            """
                    Async версия.

                    По умолчанию: `False`.
                    """
        ),
    ] = False,
    **kwargs
) -> Union[Type[SyncTask], Type[AsyncTask]]:
    """Декоратор для регистрации задач.

    Args:
        name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
        priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
        echo (bool, optional): Добавить (A)syncTask первым параметром. По умолчанию: `False`.
        retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
        retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
        decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
        tags (List[str], optional): Теги задачи. По умолчанию: `None`.
        description (str, optional): Описание задачи. По умолчанию: `None`.
        generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
        executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
        middlewares_before (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены перед задачей. По умолчанию: `Пустой массив`.
        middlewares_after (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.
        awaiting (bool, optional): Использовать ли AsyncTask вместо SyncTask. По умолчанию: `False`.

    Raises:
        ValueError: Если задача с таким именем уже зарегистрирована.
        ValueError: Неизвестный метод {self._method}.

    Returns:
        SyncTask | AsyncTask: Декоратор для регистрации задачи.
    """
    middlewares_before = middlewares_before or []
    middlewares_after = middlewares_after or []

    if callable(name):
        # Декоратор без скобок
        return TaskRegistry.register(
            name=name.__name__,
            priority=priority,
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
            **kwargs
        )(name)

    # Декоратор со скобками
    def wrapper(func: Callable) -> Union[SyncTask, AsyncTask]:
        return TaskRegistry.register(
            name=name or func.__name__,
            priority=priority,
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
            **kwargs
        )(func)

    return wrapper
