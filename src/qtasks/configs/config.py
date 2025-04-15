from dataclasses import dataclass

@dataclass
class QueueConfig:
    """
    Конфигурация очередей задач.

    Attributes:
        max_tasks_process (int): Максимум задач в процессе. По умолчанию: 10
        running_older_tasks (bool): Запустить прошлые задачи. По умолчанию: False
        delete_finished_tasks (bool): Удаление выполненных задач. По умолчанию: False
    """
    max_tasks_process: int = 10
    running_older_tasks: bool = False
    delete_finished_tasks: bool = True
