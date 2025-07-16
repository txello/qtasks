"""TaskPriority and TaskExec Schema."""

from dataclasses import dataclass, field
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Literal, Type
from uuid import UUID


if TYPE_CHECKING:
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.executors.base import BaseTaskExecutor


@dataclass(order=True)
class TaskPrioritySchema:
    """`TaskPrioritySchema` схема.

    Args:
        priority (int): Приоритет.
        uuid (UUID): UUID.
        name (str): Название.

        args (tuple[str]): Аргументы типа args.
        kwargs (dict[str, str]): Аргументы типа kwargs.

        created_at (float): Дата создания в формате `timestamp`.
        updated_at (float): Дата обновления в формате `timestamp`.
    """

    priority: int
    uuid: UUID = field(compare=False)
    name: str = field(compare=False)

    args: list = field(default_factory=list, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)

    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class TaskExecSchema:
    """`TaskExecSchema` схема.

    Args:
        priority (int): Приоритет.
        name (str): Название.

        func (FunctionType): Функция задачи.
        awaiting (bool): Асинхронность задачи. По умолчанию: False
        generating (str|Literal[False]): Генерация задачи. По умолчанию: False

        echo (bool): Включить параметр self в задачу. По умолчанию: False
        retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: None
        retry_on_exc (list[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: None

        decode (Callable, optional): Декодер результата задачи. По умолчанию: None
        tags (list[str], optional): Теги задачи. По умолчанию: None

        generate_handler (Callable, optional): Генератор обработчика. По умолчанию: None

        executor (Type[BaseTaskExecutor], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`|`AsyncTaskExecutor`.
        middlewares (list[Type[TaskMiddleware]]): Мидлвари. По умолчанию: `Пустой массив`.

    """

    priority: int
    name: str

    func: FunctionType
    awaiting: bool = False
    generating: str | Literal[False] = False

    echo: bool = False
    retry: int | None = None
    retry_on_exc: list[Type[Exception]] | None = None

    decode: Callable | None = None
    tags: list[str] | None = None

    generate_handler: Callable | None = None

    executor: Type["BaseTaskExecutor"] = None
    middlewares: list[Type["TaskMiddleware"]] = field(default_factory=list)

    extra: dict[str, Any] = field(default_factory=dict)
