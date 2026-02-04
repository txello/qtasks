"""Task Status Schema."""

import json
from dataclasses import dataclass, field
from time import time
from typing import ClassVar

from qtasks.enums.task_status import TaskStatusEnum


@dataclass
class BaseTaskStatusSchema:
    """
    `BaseTaskStatusSchema` schema.
    
        Args:
            status (str): Status.
            task_name (str): Name.
            priority (int): Priority.
            args (Tuple[str]): Arguments of type args.
            kwargs (Dict[str, str]): Arguments of type kwargs.
    
            created_at (float): Created date in `timestamp` format.
            updated_at (float): Update date in `timestamp` format.
            returning (str | None): Result. Default: `None`.
            traceback (str | None): Trace errors. Default: `None`.
    """

    task_name: str = ""
    priority: int = 0

    args: str = field(default="[]")
    kwargs: str = field(default="{}")

    created_at: float = 0.0
    updated_at: float = field(default_factory=time)

    def __post_init__(self):
        """Convert arguments to JSON format."""
        if not isinstance(self.args, str):
            self.args = json.dumps(self.args)
        if not isinstance(self.kwargs, str):
            self.kwargs = json.dumps(self.kwargs)


@dataclass
class TaskStatusNewSchema(BaseTaskStatusSchema):
    """
    `TaskStatusNewSchema` schema.
    
        Args:
            status (str): Status.
    """

    status: str = TaskStatusEnum.NEW.value


@dataclass
class TaskStatusProcessSchema(BaseTaskStatusSchema):
    """
    `TaskStatusProcessSchema` schema.
    
        Args:
            status (str): Status.
    """

    status: str = TaskStatusEnum.PROCESS.value


@dataclass
class TaskStatusSuccessSchema(BaseTaskStatusSchema):
    """
    `TaskStatusSuccessSchema` schema.
    
        Args:
            status (str): Status.
            returning (str): Result.
    """

    status: str = TaskStatusEnum.SUCCESS.value
    returning: str = ""


@dataclass
class TaskStatusErrorSchema(BaseTaskStatusSchema):
    """
    `TaskStatusErrorSchema` schema.
    
        Args:
            status (str): Status.
            traceback (str): Error tracing.
    """

    status: str = TaskStatusEnum.ERROR.value
    traceback: str = ""

    # plugins
    retry: ClassVar[int | None] = None
    retry_child_uuid: ClassVar[str | None] = None
    retry_parent_uuid: ClassVar[str | None] = None


@dataclass
class TaskStatusCancelSchema(BaseTaskStatusSchema):
    """
    `TaskStatusCancelSchema` schema.
    
        Args:
            status (str): Status.
            cancel_reason (str): Reason for canceling the task.
    """

    status: str = TaskStatusEnum.CANCEL.value
    cancel_reason: str = ""
