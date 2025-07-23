"""Task Schema."""

from dataclasses import InitVar, dataclass
from datetime import datetime
from typing import Any, Dict, Tuple, Union
from uuid import UUID


@dataclass
class Task:
    """`Task` модель.

    Args:
        status (str): Статус.
        uuid (UUID): UUID.
        priority (int): Приоритет.
        task_name (str): Название.

        args (Tuple[str]): Аргументы типа args.
        kwargs (Dict[str, Any]): Аргументы типа kwargs.

        created_at (datetime): Дата создания.
        updated_at (datetime): Дата обновления.

        returning (str | None): Результат. По умолчанию: `None`.
        traceback (str | None): Трассировка ошибок. По умолчанию: `None`.
    """

    status: str
    uuid: UUID
    priority: int
    task_name: str

    args: Tuple[str]
    kwargs: Dict[str, Any]

    created_at: datetime
    updated_at: datetime

    returning: InitVar[Union[str, None]] = None
    traceback: InitVar[Union[str, None]] = None
