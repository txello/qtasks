"""QueueConfig Schema."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from qtasks.enums.task_status import TaskStatusEnum


@dataclass
class QueueConfig:
    """
    Configuration of task queues.
    
        Attributes:
            max_tasks_process (int): Maximum tasks in process. Default: `10`
            running_older_tasks (bool): Run past tasks. Default: `False`
            delete_finished_tasks (bool): Deleting completed tasks. Default: `False`
    
            task_default_priority (int): Default task priority. Default: `0`
            task_default_decode (Callable | None): Default task result decoder. Default: `None`
    
            logs_default_level_server (int): Logging level for the server. Default: `logging.INFO(20)`
            logs_default_level_client (int | None): Logging level for the client. Default: `logging.INFO(20)`
            logs_format (str): Logging format. Default: `%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s`
    
            result_time_interval (float): Time interval for results. Default: `1.0`
            result_statuses_end (list[str]): Results end statuses. Default: `["success", "error", "cancel"]`
    
            environ_prefix (str): Prefix for environment variables. Default: `QTASKS_`
    """

    max_tasks_process: int = 10
    running_older_tasks: bool = False
    delete_finished_tasks: bool = False

    task_default_priority: int = 0
    task_default_decode: Optional[Callable] = None

    global_config_status_ttl = 20
    global_config_status_set_periodic = 17

    logs_default_level_server: int = logging.INFO
    logs_default_level_client: int = logging.INFO
    logs_format: str = "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s"

    result_time_interval: float = 1.0
    result_statuses_end: list[str] = field(
        default_factory=lambda: [
            TaskStatusEnum.SUCCESS.value,
            TaskStatusEnum.ERROR.value,
            TaskStatusEnum.CANCEL.value,
        ]
    )

    environ_prefix: str = "QTASKS_"

    _callbacks: list[Callable[["QueueConfig", str, Any], None]] = field(
        default_factory=list, init=False, repr=False
    )
    _dynamic_fields: dict[str, Any] = field(
        default_factory=dict, init=False, repr=False
    )

    def subscribe(self, callback: Callable[["QueueConfig", str, Any], None]):
        """Subscribe to change."""
        self._callbacks.append(callback)

    def _notify(self, key: str, value: Any):
        for callback in self._callbacks:
            callback(self, key, value)

    def __getattr__(self, item):
        """Getting an attribute."""
        # Проверяем динамические поля
        if item in self._dynamic_fields:
            return self._dynamic_fields[item]
        # Вызов стандартного поведения dataclass
        raise AttributeError(f"{type(self).__name__} has no attribute '{item}'")

    def __setattr__(self, key, value):
        """Setting the attribute."""
        # Для полей dataclass
        if key in self.__annotations__:
            object.__setattr__(self, key, value)
            if (
                "_callbacks" in self.__dict__
            ):  # Проверяем наличие для избежания рекурсии
                self._notify(key, value)
        # Для внутренних атрибутов
        elif key.startswith("_"):
            object.__setattr__(self, key, value)
        # Для динамических полей
        else:
            dynamic_fields = object.__getattribute__(self, "_dynamic_fields")
            dynamic_fields[key] = value
            self._notify(key, value)

    def __post_init__(self):
        """Initialization after creation."""
        env_vars = self._get_env_all()
        for key, value in env_vars.items():
            attr_key = key[len(self.environ_prefix) :].lower()
            if hasattr(self, attr_key):
                attr_type = type(getattr(self, attr_key))
                try:
                    if attr_type is bool:
                        casted_value = value.lower() in ("1", "true", "yes", "on")
                    else:
                        casted_value = attr_type(value)
                    setattr(self, attr_key, casted_value)
                except (ValueError, TypeError):
                    pass


    def _get_env_all(self) -> dict[str, Any]:
        """Getting environment variables with prefix."""
        return {k: v for k, v in os.environ.items() if k.startswith(self.environ_prefix)}
