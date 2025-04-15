import datetime
import json
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import redis
from typing import TYPE_CHECKING

from .base import BaseStorage
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker

class SyncRedisStorage(BaseStorage):
    """
    Хранилище, работающий с Redis, сохраняя информацию о задачах.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRedisBroker
    from qtasks.storages import SyncRedisStorage
    
    storage = SyncRedisBroker(name="QueueTasks")
    broker = SyncRedisBroker(name="QueueTasks", storage=storage)
    
    app = QueueTasks(broker=broker)
    ```
    """
    
    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется брокером.
                    
                    По умолчанию: `QueueTasks`.
                    """
                )
            ] = "QueueTasks",
            url: Annotated[
                str,
                Doc(
                    """
                    URL для подключения к Redis.
                    
                    По умолчанию: `redis://localhost:6379/0`.
                    """
                )
            ] = "redis://localhost:6379/0",
            redis_connect: Annotated[
                Optional[redis.Redis],
                Doc(
                    """
                    Внешний класс подключения к Redis.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            queue_process: Annotated[
                str,
                Doc(
                    """
                    Имя канала для задач в процессе.
                    
                    По умолчанию: `task_process`.
                    """
                )
            ] = "task_process"
        ):
        super().__init__(name=name)
        self.url = url
        self._queue_process = queue_process
        self.queue_process = f"{self.name}:{queue_process}"
        self.client = redis_connect or redis.Redis.from_url(self.url, decode_responses=True, encoding='utf-8')
        
    def add(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ],
            task_status: Annotated[
                TaskStatusNewSchema,
                Doc(
                    """
                    Схема статуса новой задачи.
                    """
                )
            ]
        ) -> None:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        uuid = str(uuid)
        self.client.hset(f"{self.name}:{uuid}", mapping=task_status.__dict__)
    
    def get(self,
            uuid: UUID|str
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        key = f"{self.name}:{uuid}"
        result = self.client.hgetall(key)
        if not result:
            return None
        
        return Task(
            status=result["status"],
            uuid=uuid,
            priority=int(result["priority"]),
            task_name=result["task_name"],
            args=json.loads(result["args"]),
            kwargs=json.loads(result["kwargs"]),
            created_at=datetime.datetime.fromtimestamp(float(result["created_at"])),
            updated_at=datetime.datetime.fromtimestamp(float(result["updated_at"]))
        )
    
    def get_all(self) -> list[Task]:
        """Получить все задачи.

        Returns:
            list[Task]: Массив задач.
        """
        pattern = f"{self.name}:*"
        result = []
        for key in self.client.scan_iter(pattern):
            _, uuid = key.split(":")
            if uuid in [self._queue_process, "task_queue"]:
                continue
            task = self.get(uuid=uuid)
            if task:
                result.append(task)
        return result
    
    def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        self.client.hset(kwargs["name"], mapping=kwargs["mapping"])
    
    def remove_finished_task(self,
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    Схема приоритетной задачи.
                    """
                )
            ],
            model: Annotated[
                Union[TaskStatusNewSchema|TaskStatusErrorSchema],
                Doc(
                    """
                    Модель результата задачи.
                    """
                )
            ]
        ) -> None:
        """Обновляет данные задачи.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        self.client.hset(f"{self.name}:{task_broker.uuid}", mapping=model.__dict__)
        self.client.zrem(self.queue_process, f"{task_broker.name}:{task_broker.uuid}:{task_broker.priority}")
    
    def start(self):
        """Запускает хранилище."""
        pass
    
    def stop(self) -> None:
        """Останавливает хранилище."""
        self.client.close()
    
    def add_process(self,
            task_data: Annotated[
                str,
                Doc(
                    """
                    Данные задачи из брокера.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    """
                )
            ]
        ) -> None:
        """Добавляет задачу в список задач в процессе.

        Args:
            task_data (str): Данные задачи из брокера.
            priority (int): Приоритет задачи.
        """
        self.client.zadd(self.queue_process, {task_data: priority})
    
    def _running_older_tasks(self, worker: "BaseWorker") -> None:
        tasks = self.client.zrange(self.queue_process, 0, -1)
        for task_data in tasks:
            task_name, uuid, priority = task_data.split(":")
            name_ = f"{self.name}:{uuid}"
            args, kwargs, created_at = self.client.hget(name_, "args"), self.client.hget(name_, "kwargs"), self.client.hget(name_, "created_at")
            args, kwargs, created_at = json.loads(args) or (), json.loads(kwargs) or {}, float(created_at)
            
            worker.add(name=task_name, uuid=uuid, priority=int(priority), created_at=created_at, args=args, kwargs=kwargs)
