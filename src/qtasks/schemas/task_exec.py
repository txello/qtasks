"""TaskPriority and TaskExec Schema."""

from collections.abc import Callable
from dataclasses import dataclass, field
from types import FunctionType
from typing import TYPE_CHECKING, Literal
from uuid import UUID

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware


@dataclass(order=True)
class TaskPrioritySchema:
    """`TaskPrioritySchema` схема.

    Args:
        priority (int): Приоритет.
        uuid (UUID): UUID.
        name (str): Название.

        args (Tuple[str]): Аргументы типа args.
        kwargs (Dict[str, str]): Аргументы типа kwargs.

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
        awaiting (bool): Асинхронность задачи. По умолчанию: `False`
        generating (str|Literal[False]): Генерация задачи. По умолчанию: `False`

        echo (bool): Включить параметр self в задачу. По умолчанию: `False`

        max_time (float, optional): Максимальное время выполнения задачи в секундах. По умолчанию: `None`

        retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`
        retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`

        decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`
        tags (List[str], optional): Теги задачи. По умолчанию: `None`
        description (str, optional): Описание задачи. По умолчанию: `None`.

        generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`

        executor (Type[BaseTaskExecutor], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`|`AsyncTaskExecutor`.
        middlewares_before (List[Type[TaskMiddleware]]): Мидлвари до выполнения задачи. По умолчанию: `Пустой массив`.
        middlewares_after (List[Type[TaskMiddleware]]): Мидлвари после выполнения задачи. По умолчанию: `Пустой массив`.

        extra (Dict[str, Any]): Дополнительные параметры задачи. По умолчанию: `Пустой словарь`.

    """

    priority: int
    name: str

    func: FunctionType
    awaiting: bool = False
    generating: str | Literal[False] = False

    echo: bool = False

    max_time: float | None = None

    retry: int | None = None
    retry_on_exc: list[type[Exception]] | None = None

    decode: Callable | None = None
    tags: list[str] | None = None
    description: str | None = None

    generate_handler: Callable | None = None

    executor: type["BaseTaskExecutor"] | None = None
    middlewares_before: list[type["TaskMiddleware"]] = field(default_factory=list)
    middlewares_after: list[type["TaskMiddleware"]] = field(default_factory=list)

    extra: dict = field(default_factory=dict)

    def add_middlewares_before(self, middlewares: list[type["TaskMiddleware"]]) -> None:
        """Добавляет мидлвари к задаче.

        Args:
            middlewares (List[Type[TaskMiddleware]]): Список мидлварей.
        """
        self.middlewares_before.extend(middlewares)

    def add_middlewares_after(self, middlewares: list[type["TaskMiddleware"]]) -> None:
        """Добавляет мидлвари к задаче.

        Args:
            middlewares (List[Type[TaskMiddleware]]): Список мидлварей.
        """
        self.middlewares_after.extend(middlewares)
