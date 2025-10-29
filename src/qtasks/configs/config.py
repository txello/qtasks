"""QueueConfig Schema."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from qtasks.enums.task_status import TaskStatusEnum


@dataclass
class QueueConfig:
    """
    Конфигурация очередей задач.

    Attributes:
        max_tasks_process (int): Максимум задач в процессе. По умолчанию: `10`
        running_older_tasks (bool): Запустить прошлые задачи. По умолчанию: `False`
        delete_finished_tasks (bool): Удаление выполненных задач. По умолчанию: `False`

        default_task_priority (int): Приоритет задач по умолчанию. По умолчанию: `0`

        logs_default_level_server (int): Уровень логирования для сервера. По умолчанию: `logging.INFO (20)`
        logs_default_level_client (int | None): Уровень логирования для клиента. По умолчанию: `logging.INFO (20)`
        logs_format (str): Формат логирования. По умолчанию: `%(asctime)s [%(name)s: %(levelname)s] %(message)s`

        result_time_interval (float): Интервал времени для результатов. По умолчанию: `1.0`
        result_statuses_end (list[str]): Статусы завершения результатов. По умолчанию: `["success", "error", "cancel"]`
    """

    max_tasks_process: int = 10
    running_older_tasks: bool = False
    delete_finished_tasks: bool = False

    default_task_priority: int = 0

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

    _callbacks: list[Callable[["QueueConfig", str, Any], None]] = field(
        default_factory=list, init=False, repr=False
    )
    _dynamic_fields: dict[str, Any] = field(
        default_factory=dict, init=False, repr=False
    )

    def subscribe(self, callback: Callable[["QueueConfig", str, Any], None]):
        """Подписка на изменение."""
        self._callbacks.append(callback)

    def _notify(self, key: str, value: Any):
        for callback in self._callbacks:
            callback(self, key, value)

    def __getattr__(self, item):
        """Получение атрибута."""
        # Проверяем динамические поля
        if item in self._dynamic_fields:
            return self._dynamic_fields[item]
        # Вызов стандартного поведения dataclass
        raise AttributeError(f"{type(self).__name__} has no attribute '{item}'")

    def __setattr__(self, key, value):
        """Установка атрибута."""
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
