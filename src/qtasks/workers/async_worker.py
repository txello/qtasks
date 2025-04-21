import asyncio
import json
from time import time
import traceback
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID
from typing_extensions import Annotated, Doc

from anyio import Semaphore


from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task

from .base import BaseWorker
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusProcessSchema, TaskStatusSuccessSchema
from qtasks.brokers.async_redis import AsyncRedisBroker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker

class AsyncWorker(BaseWorker):
    """
    Воркер, Получающий из Брокера задачи и обрабатывающий их.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.workers import AsyncWorker

    worker = AsyncWorker()
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
                    
                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
                )
            ] = None,
        ):
        super().__init__(name, broker)
        self.name = name
        self.broker = broker or AsyncRedisBroker(name=self.name)
        self.queue = asyncio.PriorityQueue()
        
        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event = asyncio.Event()
        self.semaphore = asyncio.Semaphore(self.config.max_tasks_process)
        self.condition = asyncio.Condition()
    
    async def worker(self,
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
            await model_init.func(worker=self) if model_init.awaiting else model_init.func(worker=self)

        try:
            while not self._stop_event.is_set():
                async with self.condition:
                    while self.queue.empty():
                        await self.condition.wait()
                
                task_broker: TaskPrioritySchema | None = await self.queue.get()
                if task_broker is None:
                    break
                
                asyncio.create_task(self._execute_task(task_broker))
        finally:
            for model_init in self.init_worker_stoping:
                await model_init.func(worker=self) if model_init.awaiting else model_init.func(worker=self)
            

    async def _execute_task(self,
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
        async with self.semaphore:
            
            model = TaskStatusProcessSchema(task_name=task_broker.name, priority=task_broker.priority, created_at=task_broker.created_at, updated_at=time())
            model.set_json(task_broker.args, task_broker.kwargs)
            
            await self.broker.update(name=f"{self.name}:{task_broker.uuid}", mapping=model.__dict__)

            try:
                task_func = self._tasks[task_broker.name]
            except KeyError as e:
                print(f"[Worker] Задачи {e.args[0]} не существует!")
                trace = traceback.format_exc()
                model = TaskStatusErrorSchema(task_name=task_broker.name, priority=task_broker.priority, traceback=trace, created_at=task_broker.created_at, updated_at=time())
                print(f"[Worker] Задача {task_broker.name} завершена с ошибкой:"), traceback.print_exception(e)

                self.queue.task_done()
                await self.broker.remove_finished_task(task_broker, model)
                return

            try:
                for model_init in self.init_task_running:
                    await model_init.func(task_func=task_func, task_broker=task_broker) if model_init.awaiting else model_init.func(task_func=task_func, task_broker=task_broker)
            except BaseException as e:
                self.queue.task_done()
                raise e

            try:
                print(f"[Worker] Выполняю задачу {task_broker.uuid} ({task_broker.name}), приоритет: {task_broker.priority}")
                
                #########
                
                result = await self._run_task(task_func, *task_broker.args, **task_broker.kwargs)
                
                result = json.dumps(result, ensure_ascii=False)
                model = TaskStatusSuccessSchema(task_name=task_func.name, priority=task_func.priority, returning=result, created_at=task_broker.created_at, updated_at=time())
                model.set_json(task_broker.args, task_broker.kwargs)
                print(f"[Worker] Задача {task_broker.uuid} успешно завершена, результат: {result}")
            except Exception as e:
                trace = traceback.format_exc()
                model = TaskStatusErrorSchema(task_name=task_func.name, priority=task_func.priority, traceback=trace, created_at=task_broker.created_at, updated_at=time())
                model.set_json(task_broker.args, task_broker.kwargs)
                print(f"[Worker] Задача {task_broker.uuid} завершена с ошибкой:"), traceback.print_exception(e)
            finally:
                self.queue.task_done()

            for model_init in self.init_task_stoping:
                await model_init.func(task_func=task_func, task_broker=task_broker, returning=model) if model_init.awaiting else model_init.func(task_func=task_func, task_broker=task_broker, returning=model)

            await self.broker.remove_finished_task(task_broker, model)

    async def add(self,
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
        model = TaskPrioritySchema(priority=priority, uuid=uuid, name=name, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
        async with self.condition:
            await self.queue.put(model)
            self.condition.notify()
        
        model = Task(status=TaskStatusEnum.NEW.value, task_name=name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
        return model

    async def start(self,
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
        self.num_workers = num_workers
        
        # Запускаем несколько воркеров
        workers = [asyncio.create_task(self.worker(number)) for number in range(self.num_workers)]
        await self._stop_event.wait()  # Ожидание сигнала остановки

        # Ожидаем завершения всех воркеров
        for worker_task in workers:
            worker_task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    
    async def stop(self):
        """Останавливает воркеры."""
        self._stop_event.set()

    def update_config(self,
            config: Annotated[
                QueueConfig,
                Doc(
                    """
                    Конфиг.
                    """
                )
            ]
        ) -> None:
        """Обновляет конфиг брокера и семафору.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        self.semaphore = Semaphore(config.max_tasks_process)
        
    async def _run_task(self, task_func: TaskExecSchema, *args, **kwargs) -> Any:
        """Запуск функции задачи.

        Args:
            task_func (TaskExecSchema): Схема `qtasks.schemas.TaskExecSchema`

        Returns:
            Any: Результат функции задачи.
        """
        func = task_func.func
        
        if args and kwargs:
            result = await func(*args, **kwargs) if task_func.awaiting else func(*args, **kwargs)
        elif args:
            result = await func(*args) if task_func.awaiting else func(*args)
        elif kwargs:
            result = await func(**kwargs) if task_func.awaiting else func(**kwargs)
        else:
            result = await func() if task_func.awaiting else func()
        return result
