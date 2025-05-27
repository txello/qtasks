import json
from typing import TYPE_CHECKING, Optional, Union

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskPrioritySchema
try:
    import pika
except ImportError:
    raise ImportError("Install with `pip install qtasks[rabbitmq]` to use this broker.")

from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from .base import BaseBroker
from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusSuccessSchema
from qtasks.storages import SyncRedisStorage

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

class SyncRabbitMQBroker(BaseBroker):
    """
    Брокер, слушающий RabbitMQ и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRabbitMQBroker
    
    broker = SyncRabbitMQBroker(name="QueueTasks", url="amqp://guest:guest@localhost/")
    
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
                    URL для подключения к RabbitMQ.
                    
                    По умолчанию: `amqp://guest:guest@localhost/`.
                    """
                )
            ] = None,
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище.
                    
                    По умолчанию: `SyncRedisStorage`.
                    """
                )
            ] = None,
            queue_name: Annotated[
                str,
                Doc(
                    """
                    Имя очереди задач для RabbitMQ. Название обновляется на: `name:queue_name`
                    
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
            ] = None
        ):
        super().__init__(name=name, log=log)
        self.url = url or "amqp://guest:guest@localhost/"
        self.queue_name = f"{self.name}:{queue_name}"
        self.storage = storage or SyncRedisStorage(name=self.name, log=self.log)
        
        self.connection = None
        self.channel = None
        self.running = False

    def connect(self):
        """Подключение к RabbitMQ синхронно."""
        self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        
        self.queue = self.channel.queue_declare(self.queue_name, durable=True)

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
        """Слушает очередь RabbitMQ и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        if not self.channel:
            self.connect()
        
        def callback(ch, method, properties, body):
            task_data = json.loads(body)
            self.storage.add_process(f'{task_data["task_name"]}:{task_data["uuid"]}:{task_data["priority"]}', task_data["priority"])
            self.log.info(f"Получена новая задача: {task_data['uuid']}")
            
            worker.add(
                name=task_data["task_name"],
                uuid=task_data["uuid"],
                priority=task_data["priority"],
                args=task_data["args"],
                kwargs=task_data["kwargs"],
                created_at=task_data["created_at"]
            )
        
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
        self.running = True
        self.channel.start_consuming()

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
        if not self.channel:
            self.connect()

        uuid = str(uuid4())
        created_at = time()
        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)
        
        self.storage.add(uuid=uuid, task_status=model)
        
        task_data = {
            "uuid": uuid,
            "task_name": task_name,
            "priority": priority,
            "args": args,
            "kwargs": kwargs,
            "created_at": created_at
        }
        
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=json.dumps(task_data).encode(),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Поставить задачу в очередь как persistent
            )
        )

        return Task(
            status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid,
            priority=priority, args=args, kwargs=kwargs,
            created_at=created_at, updated_at=created_at
        )

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
        if self.connection:
            self.connection.close()
            self.connection = None
            self.channel = None
        self.storage.stop()

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
                Union[TaskStatusSuccessSchema|TaskStatusErrorSchema],
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
        return self.storage.remove_finished_task(task_broker, model)
    
    def _running_older_tasks(self, worker):
        return self.storage._running_older_tasks(worker)
