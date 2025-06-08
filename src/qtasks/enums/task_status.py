from enum import Enum
from pydoc import Doc
from typing_extensions import Annotated


class TaskStatusEnum(Enum):
    """ `TaskStatusEnum` - Статусы задач."""
    NEW = "new"
    """Новая задача"""
    PROCESS = "process"
    """Задача в процессе"""
    SUCCESS = "success"
    """Задача успешно выполнена"""
    ERROR = "error"
    """Задача выполнена с ошибкой"""
    CANCEL = 'cancel'
    """Задача отменена"""
