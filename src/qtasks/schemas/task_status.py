"""Task Status Schema."""

from dataclasses import dataclass, field
from time import time
import json
from typing import Dict, Tuple

from qtasks.enums.task_status import TaskStatusEnum


@dataclass
class BaseTaskStatusSchema:
    """`BaseTaskStatusSchema` схема.

    Args:
        status (str): Статус.
        task_name (str): Название.
        priority (int): Приоритет.
        args (Tuple[str]): Аргументы типа args.
        kwargs (Dict[str, str]): Аргументы типа kwargs.

        created_at (float): Дата создания в формате `timestamp`.
        updated_at (float): Дата обновления в формате `timestamp`.
        returning (str | None): Результат. По умолчанию: `None`.
        traceback (str | None): Трассировка ошибок. По умолчанию: `None`.
    """

    task_name: str = ""
    priority: int = 0

    args: Tuple[str] = field(default="()")
    kwargs: Dict[str, str] = field(default="{}")

    created_at: float = 0.0
    updated_at: float = field(default_factory=time)

    def __post_init__(self):
        """Преобразовать аргументы в формат JSON."""
        if not isinstance(self.args, str):
            self.args = json.dumps(self.args)
        if not isinstance(self.kwargs, str):
            self.kwargs = json.dumps(self.kwargs)


@dataclass
class TaskStatusNewSchema(BaseTaskStatusSchema):
    """`TaskStatusNewSchema` схема.

    Args:
        status (str): Статус.
    """

    status: str = TaskStatusEnum.NEW.value


@dataclass
class TaskStatusProcessSchema(BaseTaskStatusSchema):
    """`TaskStatusProcessSchema` схема.

    Args:
        status (str): Статус.
    """

    status: str = TaskStatusEnum.PROCESS.value


@dataclass
class TaskStatusSuccessSchema(BaseTaskStatusSchema):
    """`TaskStatusSuccessSchema` схема.

    Args:
        status (str): Статус.
        returning (str): Результат.
    """

    status: str = TaskStatusEnum.SUCCESS.value
    returning: str = ""


@dataclass
class TaskStatusErrorSchema(BaseTaskStatusSchema):
    """`TaskStatusErrorSchema` схема.

    Args:
        status (str): Статус.
        traceback (str): Трассировка ошибок.
    """

    status: str = TaskStatusEnum.ERROR.value
    traceback: str = ""


@dataclass
class TaskStatusCancelSchema(BaseTaskStatusSchema):
    """`TaskStatusCancelSchema` схема.

    Args:
        status (str): Статус.
        cancel_reason (str): Причина отмены задачи.
    """

    status: str = TaskStatusEnum.CANCEL.value
    cancel_reason: str = ""
