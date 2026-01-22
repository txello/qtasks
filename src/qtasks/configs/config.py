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
    Конфигурация очередей задач.

    Attributes:
        max_tasks_process (int): Максимум задач в процессе. По умолчанию: `10`
        running_older_tasks (bool): Запустить прошлые задачи. По умолчанию: `False`
        delete_finished_tasks (bool): Удаление выполненных задач. По умолчанию: `False`

        task_default_priority (int): Приоритет задач по умолчанию. По умолчанию: `0`
        task_default_decode (Callable | None): Декодер результата задачи по умолчанию. По умолчанию: `None`

        logs_default_level_server (int): Уровень логирования для сервера. По умолчанию: `logging.INFO (20)`
        logs_default_level_client (int | None): Уровень логирования для клиента. По умолчанию: `logging.INFO (20)`
        logs_format (str): Формат логирования. По умолчанию: `%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s`

        result_time_interval (float): Интервал времени для результатов. По умолчанию: `1.0`
        result_statuses_end (list[str]): Статусы завершения результатов. По умолчанию: `["success", "error", "cancel"]`

        environ_prefix (str): Префикс для переменных окружения. По умолчанию: `QTASKS_`
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

    def __post_init__(self):
        """Инициализация после создания."""
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
        """Получение переменных окружения с префиксом."""
        return {k: v for k, v in os.environ.items() if k.startswith(self.environ_prefix)}
