try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:
    raise ImportError("Install with `pip install qtasks[kafka]` to use this broker.")

from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from typing import TYPE_CHECKING

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.storages.sync_redis import SyncRedisStorage

from .base import BaseBroker
from qtasks.schemas.task_exec import TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusCancelSchema, TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusProcessSchema

class SyncKafkaBroker(BaseBroker, SyncPluginMixin):
    """
    Брокер, слушающий Kafka и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncKafkaBroker
    
    broker = SyncKafkaBroker(name="QueueTasks", url="localhost:9092")
    
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
                    URL для подключения к Kafka.
                    
                    По умолчанию: `localhost:9092`.
                    """
                )
            ] = None,
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище.
                    
                    По умолчанию: `AsyncRedisStorage`.
                    """
                )
            ] = None,
            topic: Annotated[
                str,
                Doc(
                    """
                    Топик Kafka.
                    
                    По умолчанию: `task_queue`.
                    """
                )
            ] = "task_queue",

            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None,
            config: Annotated[
                Optional[QueueConfig],
                Doc(
                    """
                    Конфиг.
                    
                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
                )
            ] = None
        ):
        super().__init__(name=name, log=log, config=config)
        self.url = url or "localhost:9092"
        self.topic = f"{self.name}_{topic}"
        
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.url,
            group_id=f"{self.name}_group",
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode('utf-8')
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.url,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode('utf-8')
        )
        
        self.storage = storage or SyncRedisStorage(name=self.name, log=self.log, config=config)

        self.running = False
    
    def listen(self, worker: "BaseWorker"):
        """Слушает Kafka и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        self.running = True
        for msg in self.consumer:
            if not self.running:
                break
            task_data = msg.value
            task_name, uuid_str, priority = task_data.split(":")
            uuid = UUID(uuid_str)
            model_get = self.get(uuid=uuid)
            if model_get is None:
                self.log.warning(f"Задача {uuid} не найдена в хранилище.")
                continue
            args, kwargs, created_at = model_get.args or (), model_get.kwargs or {}, model_get.created_at.timestamp()
            self.log.info(f"Получена новая задача: {uuid}")
            worker.add(name=task_name, uuid=uuid, priority=int(priority), args=args, kwargs=kwargs, created_at=created_at)
    
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
            extra: Annotated[
                dict,
                Doc(
                    """
                    Дополнительные параметры задачи.
                    """
                )
            ] = None,
            kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ] = None
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
        args, kwargs = args or (), kwargs or {}
        uuid = uuid4()
        created_at = time()

        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)

        if extra:
            model = self._dynamic_model(model=model, extra=extra)

        self.storage.add(uuid=uuid, task_status=model)

        task_data = f"{task_name}:{uuid}:{priority}"
        self.producer.send(self.topic, task_data)
        self.producer.flush()
        
        return Task(status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
    
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
        return self.storage.update(**kwargs)
    
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
        self.storage.start()

        if self.config.delete_finished_tasks:
            self.storage._delete_finished_tasks()
        
        if self.config.running_older_tasks:
            self.storage._running_older_tasks(worker)
        
        self.listen(worker)
    
    def stop(self):
        """Останавливает брокер."""
        self.running = False
        self.consumer.stop()
        self.producer.stop()
    
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
                Union[TaskStatusProcessSchema|TaskStatusErrorSchema|TaskStatusCancelSchema],
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
    
    def flush_all(self) -> None:
        """Удалить все данные."""
        self.storage.flush_all()