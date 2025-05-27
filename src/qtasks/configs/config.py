from dataclasses import dataclass
import logging

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