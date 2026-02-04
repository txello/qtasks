"""Task status enums."""

from enum import Enum


class TaskStatusEnum(Enum):
    """`TaskStatusEnum` - Task statuses."""

    NEW = "new"
    """New task."""
    PROCESS = "process"
    """Task is being processed."""
    SUCCESS = "success"
    """Task successfully completed."""
    ERROR = "error"
    """Task completed with an error."""
    CANCEL = "cancel"
    """Task cancelled."""
