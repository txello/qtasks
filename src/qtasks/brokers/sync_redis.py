import redis
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time, sleep
from typing import TYPE_CHECKING

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.storages import SyncRedisStorage

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.storages.base import BaseStorage

from .base import BaseBroker
from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema

class SyncRedisBroker(BaseBroker):
    """
    Брокер, слушающий Redis и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRedisBroker
    
    broker = SyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")
    
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
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище.
                    
                    По умолчанию: `AsyncRedisStorage`.
                    """
                )
            ] = None,
            queue_name: Annotated[
                str,
                Doc(
                    """
                    Имя массива очереди задач для Redis. Название обновляется на: `name:queue_name`
                    
                    По умолчанию: `task_queue`.
                    """
                )
            ] = "task_queue"
        ):
        super().__init__(name=name)
        self.url = url
        self.queue_name = f"{self.name}:{queue_name}"
        
        self.client = redis.Redis.from_url(self.url, decode_responses=True, encoding='utf-8')
        self.storage = storage or SyncRedisStorage(name=name, url=self.url, redis_connect=self.client)
        
        self.running = False

    def listen(self,
            worker: Annotated[
                "BaseWorker",
                Doc(
                    """
                    Класс воркера.
                    """
                )
            ]
        ):
        """Слушает очередь Redis и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        self.running = True

        while self.running:
            task_data = self.client.lpop(self.queue_name)
            
            if task_data:
                task_name, uuid, priority = task_data.split(':')
                
                self.storage.add_process(task_data, priority)
                
                model_get = self.get(uuid=uuid)
                args, kwargs, created_at = model_get.args or (), model_get.kwargs or {}, model_get.created_at.timestamp()
                
                print(f"[Broker] Получена новая задача: {uuid}")
                worker.add(name=task_name, uuid=uuid, priority=int(priority), args=args, kwargs=kwargs, created_at=created_at)
            else:
                sleep(1)
    
    def add(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0,
            *args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ],
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ]
        ) -> Task:
        """Добавляет задачу в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            args (tuple, optional): Аргументы задачи типа args.
            kwargs (dict, optional): Аргументы задачи типа kwargs.

        Returns:
            Task: `schemas.task.Task`
        """
        uuid = uuid4()
        created_at = time()
        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)
        
        self.storage.add(uuid=uuid, task_status=model)
        self.client.rpush(self.queue_name, f"{task_name}:{uuid}:{priority}")
        
        model = Task(status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
        return model
    
    def get(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        if isinstance(uuid, str): uuid = UUID(uuid)
        return self.storage.get(uuid=uuid)
    
    def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления для хранилища типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        self.storage.update(**kwargs)
    
    def start(self,
            worker: Annotated[
                "BaseWorker",
                Doc(
                    """
                    Класс Воркера.
                    """
                )
            ]
        ) -> None:
        """Запускает брокер.

        Args:
            worker (BaseWorker): Класс Воркера.
        """
        if self.config.running_older_tasks:
            self.storage._running_older_tasks(worker)
        
        self.listen(worker)

    def stop(self):
        """Останавливает брокер."""
        self.running = False
        self.client.close()
    
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
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        self.storage.remove_finished_task(task_broker, model)
