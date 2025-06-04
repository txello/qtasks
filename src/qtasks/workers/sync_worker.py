from threading import Event, Lock, Semaphore, Thread
import json
from time import time, sleep
import traceback
from queue import PriorityQueue
from typing import Optional
from uuid import UUID
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.executors.sync_task_executor import SyncTaskExecutor
from qtasks.logs import Logger
from qtasks.schemas.task import Task

from .base import BaseWorker
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusProcessSchema, TaskStatusSuccessSchema
from qtasks.brokers.base import BaseBroker
from qtasks.brokers import SyncRedisBroker

class SyncThreadWorker(BaseWorker):
    """
    Воркер, Получающий из Брокера задачи и обрабатывающий их.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.workers import SyncThreadWorker

    worker = SyncThreadWorker()
    app = QueueTasks(worker=worker)
    ```
    """
    
    def __init__(self, 
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется воркером.
                    
                    По умолчанию: `QueueTasks`.
                    """
                )
            ] = "QueueTasks",
            broker: Annotated[
                Optional["BaseBroker"],
                Doc(
                    """
                    Брокер.
                    
                    По умолчанию: `qtasks.brokers.SyncRedisBroker`.
                    """
                )
            ] = None,

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
        super().__init__(name=name, broker=broker, log=log, config=config)
        self.name = name
        self.broker = broker or SyncRedisBroker(name=self.name, log=self.log, config=self.config)
        self.queue = PriorityQueue()
        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event = Event()
        self.lock = Lock()
        self.threads: list[Thread] = []
        self.semaphore = Semaphore(self.config.max_tasks_process)

    def worker(self,
            number: Annotated[
                int,
                Doc(
                    """
                    Номер Воркера.
                    """
                )
            ]
        ) -> None:
        """Обработчик задач.

        Args:
            number (int): Номер Воркера.
        """
        for model_init in self.init_worker_running:
            model_init.func(worker=self)

        try:
            while not self._stop_event.is_set():
                with self.lock:
                    if self.queue.empty():
                        sleep(0.1)
                        continue
                    task_broker: TaskPrioritySchema = self.queue.get()
                
                if task_broker is None:
                    break
                Thread(target=self._execute_task, args=(task_broker,), daemon=True).start()
        
        finally:
            for model_init in self.init_worker_stoping:
                model_init.func(worker=self) if model_init.awaiting else model_init.func(worker=self)

    def _execute_task(self,
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    Схема приоритетной задачи.
                    """
                )
            ]
        ) -> None:
        """Выполняет задачу независимо.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
        """
        with self.semaphore:
            model = TaskStatusProcessSchema(task_name=task_broker.name, priority=task_broker.priority, created_at=task_broker.created_at, updated_at=time())
            model.set_json(task_broker.args, task_broker.kwargs)
            self.broker.update(name=f"{self.name}:{task_broker.uuid}", mapping=model.__dict__)
            
            task_func = self._task_exists(task_broker=task_broker)
            if not task_func:
                self.queue.task_done()
                return

            self._init_task_running()
            
            model = self._run_task(task_func=task_func, task_broker=task_broker)

            self._init_task_stoping(task_func=task_func, task_broker=task_broker, model=model)

            self.broker.remove_finished_task(task_broker, model)
            
            self.queue.task_done()

    def add(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            uuid: Annotated[
                UUID,
                Doc(
                    """
                    UUID задачи.
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
            ],
            created_at: Annotated[
                float,
                Doc(
                    """
                    Создание задачи в формате timestamp.
                    """
                )
            ],
            args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ],
            kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ]
        ) -> Task:
        """Добавление задачи в очередь.

        Args:
            name (str): Имя задачи.
            uuid (UUID): UUID задачи.
            priority (int): Приоритет задачи.
            created_at (float): Создание задачи в формате timestamp.
            args (tuple): Аргументы задачи типа args.
            kwargs (dict): Аргументы задачи типа kwargs.
        """
        model = TaskPrioritySchema(priority=priority, uuid=uuid, name=name, args=list(args), kwargs=kwargs, created_at=created_at, updated_at=created_at)
        with self.lock:
            self.queue.put(model)
        
        return Task(status=TaskStatusEnum.NEW.value, task_name=name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)

    def start(self,
            num_workers: Annotated[
                int,
                Doc(
                    """
                    Количество воркеров.
                    
                    По умолчанию: `4`.
                    """
                )
            ] = 4
        ) -> None:
        """Запускает несколько обработчиков задач.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        for number in range(num_workers):
            thread = Thread(target=self.worker, args=(number, ), daemon=True)
            thread.start()
            self.threads.append(thread)
    
    def stop(self):
        """Останавливает воркеры."""
        self._stop_event.set()
        for thread in self.threads:
            thread.join()

    def update_config(self, config: QueueConfig):
        """Обновляет конфиг."""
        self.config = config
        self.semaphore = Semaphore(config.max_tasks_process)

    def _run_task(self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema) -> TaskStatusSuccessSchema|TaskStatusErrorSchema:
        """Запуск функции задачи.

        Args:
            task_func (TaskExecSchema): Схема `qtasks.schemas.TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `qtasks.schemas.TaskPrioritySchema`.
        
        Returns:
            Any: Результат функции задачи.
        """
        self.log.info(f"Выполняю задачу {task_broker.uuid} ({task_broker.name}), приоритет: {task_broker.priority}")

        middlewares = self.task_middlewares[:]
        if task_func.middlewares:
            middlewares.extend(task_func.middlewares)
        
        if task_func.executor is not None:
            executor = task_func.executor(task_func=task_func, task_broker=task_broker, middlewares=middlewares, log=self.log)
        else:
            executor = SyncTaskExecutor(task_func=task_func, task_broker=task_broker, middlewares=middlewares, log=self.log)
        try:
            result = executor.execute()

            model = TaskStatusSuccessSchema(task_name=task_func.name, priority=task_func.priority, returning=result, created_at=task_broker.created_at, updated_at=time())
            model.set_json(task_broker.args, task_broker.kwargs)
            self.log.info(f"Задача {task_broker.uuid} успешно завершена, результат: {result}")
            return model
        except BaseException:
            trace = traceback.format_exc()
            model = TaskStatusErrorSchema(task_name=task_func.name, priority=task_func.priority, traceback=trace, created_at=task_broker.created_at, updated_at=time())
            self.log.warning(f"Задача {task_broker.uuid} завершена с ошибкой:\n{trace}")
            return model
        
    def _task_exists(self, task_broker: TaskPrioritySchema) -> TaskExecSchema|None:
        """Проверка существования задачи.

        Args:
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.

        Returns:
            TaskExecSchema|None: Схема `TaskExecSchema` или `None`.
        """
        
        try:
            return self._tasks[task_broker.name]
        except KeyError as e:
            self.log.warning(f"Задачи {e.args[0]} не существует!")
            trace = traceback.format_exc()
            model = TaskStatusErrorSchema(task_name=task_broker.name, priority=task_broker.priority, traceback=trace, created_at=task_broker.created_at, updated_at=time())
            self.broker.remove_finished_task(task_broker, model)
            self.log.warning(f"Задача {task_broker.name} завершена с ошибкой:\n{trace}")
            return None
        
    def _init_task_running(self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema) -> None:
        """Вызов задач `init_task_running`.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
        """
        for model_init in self.init_task_running:
            try:
                model_init.func(task_func=task_func, task_broker=task_broker)
            except BaseException:
                pass
        return
    
    def _init_task_stoping(self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema, model: TaskStatusSuccessSchema|TaskStatusErrorSchema) -> None:
        """Вызов задач `init_task_stoping`.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Модель `TaskStatusSuccessSchema` или `TaskStatusSuccessSchema`.
        """
        for model_init in self.init_task_stoping:
            try:
                model_init.func(task_func=task_func, task_broker=task_broker, returning=model)
            except BaseException:
                pass
        return
