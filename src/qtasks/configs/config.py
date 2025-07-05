from dataclasses import dataclass, field
import logging
from typing import Any, Callable, Dict, List


@dataclass
class QueueConfig:
    """
    Конфигурация очередей задач.

    Attributes:
        max_tasks_process (int): Максимум задач в процессе. По умолчанию: 10
        running_older_tasks (bool): Запустить прошлые задачи. По умолчанию: False
        delete_finished_tasks (bool): Удаление выполненных задач. По умолчанию: False

        default_task_priority (int): Приоритет задач по умолчанию. По умолчанию: 0

        logs_default_level (int): Уровень логирования. По умолчанию: logging.INFO (20)
        logs_format (str): Формат логирования. По умолчанию: "%(asctime)s [%(name)s: %(levelname)s] %(message)s"
    """

    max_tasks_process: int = 10
    running_older_tasks: bool = False
    delete_finished_tasks: bool = True

    default_task_priority: int = 0

    global_config_status_ttl = 20
    global_config_status_set_periodic = 17

    logs_default_level: int = logging.INFO
    logs_format: str = "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s"

    _callbacks: List[Callable[["QueueConfig", str, Any], None]] = field(
        default_factory=list, init=False, repr=False
    )
    _dynamic_fields: Dict[str, Any] = field(
        default_factory=dict, init=False, repr=False
    )

    def subscribe(self, callback: Callable[["QueueConfig", str, Any], None]):
        """Подписка на изменение."""
        self._callbacks.append(callback)

    def _notify(self, key: str, value: Any):
        for callback in self._callbacks:
            callback(self, key, value)

    def __getattr__(self, item):
        # Проверяем динамические поля
        if item in self._dynamic_fields:
            return self._dynamic_fields[item]
        # Вызов стандартного поведения dataclass
        raise AttributeError(f"{type(self).__name__} has no attribute '{item}'")

    def __setattr__(self, key, value):
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
