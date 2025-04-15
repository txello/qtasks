from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class Task:
    """`Task` модель.

    Args:
        status (str): Статус.
        uuid (UUID): UUID.
        priority (int): Приоритет.
        task_name (str): Название.
        
        args (tuple[str]): Аргументы типа args.
        kwargs (dict[str, Any]): Аргументы типа kwargs.
        
        created_at (datetime): Дата создания.
        updated_at (datetime): Дата обновления.
        
        returning (str | None): Результат. По умолчанию: `None`.
        traceback (str | None): Трассировка ошибок. По умолчанию: `None`.
    """
    status: str
    uuid: UUID
    priority: int
    task_name: str
    
    args: tuple[str]
    kwargs: dict[str, Any]
    
    created_at: datetime
    updated_at: datetime
    
    returning: str|None = None
    traceback: str|None = None