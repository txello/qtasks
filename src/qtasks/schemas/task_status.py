"""Task Status Schema."""

from dataclasses import dataclass, field
from time import time
import json

from qtasks.enums.task_status import TaskStatusEnum


@dataclass
class BaseTaskStatusSchema:
    """`BaseTaskStatusSchema` схема.

    Args:
        status (str): Статус.
        priority (int): Приоритет.
        task_name (str): Название.
        args (tuple[str]): Аргументы типа args.
        kwargs (dict[str, str]): Аргументы типа kwargs.

        created_at (float): Дата создания в формате `timestamp`.
        updated_at (float): Дата обновления в формате `timestamp`.
        returning (str | None): Результат. По умолчанию: `None`.
        traceback (str | None): Трассировка ошибок. По умолчанию: `None`.
    """

    task_name: str = ""
    priority: int = 0

    args: tuple[str] = field(default_factory=lambda: json.dumps(()))
    kwargs: dict[str, str] = field(default_factory=lambda: json.dumps({}))

    created_at: float = 0.0
    updated_at: float = field(default_factory=time)

    def set_json(self, args, kwargs):
        """Установить значения аргументов в формате JSON."""
        if args:
            setattr(self, "args", json.dumps(args))
        if kwargs:
            setattr(self, "kwargs", json.dumps(kwargs))


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
