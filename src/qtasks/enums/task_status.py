from enum import Enum
from pydoc import Doc
from typing_extensions import Annotated


class TaskStatusEnum(Enum):
    """ `TaskStatusEnum` - Статусы задач.

    Args:
        NEW("new") - Новая задача.
        PROCESS("process") - Задача в процессе.
        SUCCESS("success") - Задача успешно выполнена.
        ERROR("error") - Задача выполнена с ошибкой.
    """
    NEW: Annotated[str, Doc("Новая задача")] = "new"
    """Новая задача"""
    PROCESS: Annotated[str, Doc("Задача в процессе")] = "process"
    """Задача в процессе"""
    
    SUCCESS: Annotated[str, Doc("Задача успешно выполнена")] = "success"
    """Задача успешно выполнена"""
    ERROR: Annotated[str, Doc("Задача выполнена с ошибкой")] = "error"
    """Задача выполнена с ошибкой"""