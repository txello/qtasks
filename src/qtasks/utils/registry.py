"""QTasks registry utilities."""

from types import FunctionType
from typing import Callable, List, Literal, Optional, Type, Union, overload
from typing_extensions import Annotated, Doc

from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.task_registry import TaskRegistry
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.types.annotations import P, R


@overload
def shared_task(
    func_or_name: Annotated[
        Union[str, Callable[P, R], None],
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
        ),
    ] = None,
    tags: Annotated[
        Union[List[str], None],
        Doc(
            """
                Теги задачи.

                По умолчанию: `None`.
            """
        ),
    ] = None,
    description: Annotated[
        Union[str, None],
        Doc(
            """
                Описание задачи.

                По умолчанию: `None`.
            """
        ),
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
        Optional[Type["BaseTaskExecutor"]],
        Doc(
            """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
        ),
    ] = None,
    middlewares_before: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    middlewares_after: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    awaiting: Annotated[
        Literal[False],
        Doc(
            """
                    Async версия.

                    По умолчанию: `None`.
                    """
        ),
    ] = False,
    **kwargs,
) -> Callable[[Callable[P, R]], SyncTask[P, R]]: ...


@overload
def shared_task(
    func_or_name: Annotated[
        Union[str, Callable[P, R], None],
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
        ),
    ] = None,
    tags: Annotated[
        Union[List[str], None],
        Doc(
            """
                Теги задачи.

                По умолчанию: `None`.
            """
        ),
    ] = None,
    description: Annotated[
        Union[str, None],
        Doc(
            """
                Описание задачи.

                По умолчанию: `None`.
            """
        ),
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
        Optional[Type["BaseTaskExecutor"]],
        Doc(
            """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
        ),
    ] = None,
    middlewares_before: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    middlewares_after: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    awaiting: Annotated[
        Literal[True],
        Doc(
            """
                    Async версия.

                    По умолчанию: `False`.
                    """
        ),
    ] = True,
    **kwargs,
) -> Callable[[Callable[P, R]], AsyncTask[P, R]]: ...


def shared_task(
    func_or_name: Annotated[
        Union[str, Callable[P, R], None],
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
        ),
    ] = None,
    tags: Annotated[
        Union[List[str], None],
        Doc(
            """
                Теги задачи.

                По умолчанию: `None`.
            """
        ),
    ] = None,
    description: Annotated[
        Union[str, None],
        Doc(
            """
                Описание задачи.

                По умолчанию: `None`.
            """
        ),
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
        Optional[Type["BaseTaskExecutor"]],
        Doc(
            """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
        ),
    ] = None,
    middlewares_before: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    middlewares_after: Annotated[
        Optional[List[Type["TaskMiddleware"]]],
        Doc(
            """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
        ),
    ] = None,
    awaiting: Annotated[
        Optional[bool],
        Doc(
            """
                    Async версия.

                    По умолчанию: `False`.
                    """
        ),
    ] = None,
    **kwargs,
) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
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
        middlewares_before (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены перед задачей. По умолчанию: `Пустой массив`.
        middlewares_after (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.
        awaiting (bool, optional): Использовать ли AsyncTask вместо SyncTask. По умолчанию: `False`.

    Raises:
        ValueError: Если задача с таким именем уже зарегистрирована.
        ValueError: Неизвестный метод {self._method}.

    Returns:
        SyncTask | AsyncTask: Декоратор для регистрации задачи.
    """
    middlewares_before = middlewares_before or []
    middlewares_after = middlewares_after or []

    if not awaiting:
        awaiting = False

    if isinstance(func_or_name, FunctionType):
        # Декоратор без скобок
        return TaskRegistry.register(
            name=func_or_name.__name__,
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
            func_or_name
        )  # type: ignore

    # Декоратор со скобками
    def wrapper(func: Callable):
        return TaskRegistry.register(
            name=func_or_name if isinstance(func_or_name, str) else func.__name__,
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
