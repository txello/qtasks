"""Init module for async worker."""

import asyncio
from dataclasses import asdict
from time import time
import traceback
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID
from typing_extensions import Annotated, Doc

from anyio import Semaphore

from qtasks.plugins.pydantic import AsyncPydanticWrapperPlugin


from .base import BaseWorker
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.exc.task import TaskCancelError
from qtasks.executors.async_task_executor import AsyncTaskExecutor
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.task import Task
from qtasks.plugins.retries import AsyncRetryPlugin

from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)
from qtasks.brokers.async_redis import AsyncRedisBroker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker


class AsyncWorker(BaseWorker, AsyncPluginMixin):
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

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется воркером.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker: Annotated[
            Optional["BaseBroker"],
            Doc(
                """
                    Брокер.

                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
            ),
        ] = None,
        log: Annotated[
            Optional[Logger],
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            Optional[QueueConfig],
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
            ),
        ] = None,
    ):
        """Инициализация асинхронного воркера.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            broker (BaseBroker, optional): Брокер. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
        """
        super().__init__(name=name, broker=broker, log=log, config=config)
        self.name = name
        self.broker = broker or AsyncRedisBroker(
            name=self.name, log=self.log, config=self.config
        )
        self.queue = asyncio.PriorityQueue()

        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event = asyncio.Event()
        self.semaphore = asyncio.Semaphore(self.config.max_tasks_process)
        self.condition = asyncio.Condition()

        self.task_executor = AsyncTaskExecutor

    async def worker(
        self,
        number: Annotated[
            int,
            Doc(
                """
                    Номер Воркера.
                    """
            ),
        ],
    ) -> None:
        """Обработчик задач.

        Args:
            number (int): Номер Воркера.
        """
        for model_init in self.init_worker_running:
            (
                await model_init.func(worker=self)
                if model_init.awaiting
                else model_init.func(worker=self)
            )

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
                (
                    await model_init.func(worker=self)
                    if model_init.awaiting
                    else model_init.func(worker=self)
                )

    async def _execute_task(
        self,
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
    ) -> None:
        """Выполняет задачу независимо.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
        """
        async with self.semaphore:
            model = TaskStatusProcessSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                created_at=task_broker.created_at,
                updated_at=time(),
            )
            model.set_json(task_broker.args, task_broker.kwargs)

            task_func = await self._task_exists(task_broker=task_broker)
            if not task_func:
                self.queue.task_done()
                return

            new_model = await self._plugin_trigger(
                "worker_execute_before",
                worker=self,
                task_broker=task_broker,
                task_func=task_func,
                model=model,
                return_last=True
            )
            if new_model:
                model = new_model

            await self.broker.update(
                name=f"{self.name}:{task_broker.uuid}", mapping=asdict(model)
            )

            await self._init_task_running(task_func=task_func, task_broker=task_broker)

            model = await self._run_task(task_func, task_broker)

            await self._init_task_stoping(
                task_func=task_func, task_broker=task_broker, model=model
            )
            await self.remove_finished_task(task_func=task_func, task_broker=task_broker, model=model)

            await self._plugin_trigger("worker_execute_after", task_func=task_func, task_broker=task_broker, model=model)

            self.queue.task_done()

    async def add(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        uuid: Annotated[
            UUID,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.
                    """
            ),
        ],
        created_at: Annotated[
            float,
            Doc(
                """
                    Создание задачи в формате timestamp.
                    """
            ),
        ],
        args: Annotated[
            tuple,
            Doc(
                """
                    Аргументы задачи типа args.
                    """
            ),
        ],
        kwargs: Annotated[
            dict,
            Doc(
                """
                    Аргументы задачи типа kwargs.
                    """
            ),
        ],
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
        new_data = await self._plugin_trigger(
            "worker_add",
            worker=self,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=created_at,
            return_last=True
        )
        if new_data:
            name = new_data.get("name", name)
            uuid = new_data.get("uuid", uuid)
            priority = new_data.get("priority", priority)
            args = new_data.get("args", args)
            kwargs = new_data.get("kwargs", kwargs)
            created_at = new_data.get("created_at", created_at)

        model = TaskPrioritySchema(
            priority=priority,
            uuid=uuid,
            name=name,
            args=list(args),
            kwargs=kwargs,
            created_at=created_at,
            updated_at=created_at,
        )
        async with self.condition:
            await self.queue.put(model)
            self.condition.notify()

        return Task(
            status=TaskStatusEnum.NEW.value,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=created_at,
            updated_at=created_at,
        )

    async def start(
        self,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
    ) -> None:
        """Запускает несколько обработчиков задач.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        self.num_workers = num_workers
        await self._plugin_trigger("worker_start", worker=self)

        # Запускаем несколько воркеров
        workers = [
            asyncio.create_task(self.worker(number))
            for number in range(self.num_workers)
        ]
        await self._stop_event.wait()  # Ожидание сигнала остановки

        # Ожидаем завершения всех воркеров
        for worker_task in workers:
            worker_task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    async def stop(self):
        """Останавливает воркеры."""
        await self._plugin_trigger("worker_stop", worker=self)
        self._stop_event.set()

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc(
                """
                    Конфиг.
                    """
            ),
        ],
    ) -> None:
        """Обновляет конфиг брокера и семафору.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        self.semaphore = Semaphore(config.max_tasks_process)

    async def _run_task(
        self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema:
        """Запуск функции задачи.

        Args:
            task_func (TaskExecSchema): Схема `qtasks.schemas.TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `qtasks.schemas.TaskPrioritySchema`.

        Returns:
            Any: Результат функции задачи.
        """
        self.log.info(
            f"Выполняю задачу {task_broker.uuid} ({task_broker.name}), приоритет: {task_broker.priority}"
        )

        new_data = await self._plugin_trigger(
            "worker_run_task_before",
            worker=self,
            task_func=task_func,
            task_broker=task_broker,
            return_last=True
        )
        if new_data:
            task_func = new_data.get("task_func", task_func)
            task_broker = new_data.get("task_broker", task_broker)

        middlewares = self.task_middlewares[:]
        if task_func.middlewares:
            middlewares.extend(task_func.middlewares)

        executor = task_func.executor if task_func.executor is not None else self.task_executor
        executor = executor(
            task_func=task_func,
            task_broker=task_broker,
            middlewares=middlewares,
            log=self.log,
            plugins=self.plugins,
        )

        try:
            result = await executor.execute()
            return await self._task_success(result, task_func, task_broker)
        except TaskCancelError as e:
            return await self._task_cancel(e, task_func, task_broker)
        except BaseException as e:
            return await self._task_error(e, task_func, task_broker)

    async def _task_success(self, result: Any, task_func: TaskExecSchema, task_broker: TaskPrioritySchema) -> None:
        """Событие успешного завершения задачи."""
        model = TaskStatusSuccessSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            returning=result,
            created_at=task_broker.created_at,
            updated_at=time(),
        )
        model.set_json(task_broker.args, task_broker.kwargs)
        self.log.info(
            f"Задача {task_broker.uuid} успешно завершена, результат: {result}"
        )
        return model

    async def _task_error(self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema) -> None:
        """Событие завершения задачи с ошибкой."""
        trace = traceback.format_exc()

        # plugin: retry
        plugin_result = None

        should_retry = (
            task_func.retry and (
                not task_func.retry_on_exc or type(e) in task_func.retry_on_exc
            )
        )
        if should_retry:
            if task_func.retry:
                plugin_result = await self._plugin_trigger(
                    "worker_task_error_retry",
                    broker=self.broker,
                    task_func=task_func,
                    task_broker=task_broker,
                    trace=trace,
                )

        if not plugin_result:
            model = TaskStatusErrorSchema(
                task_name=task_func.name,
                priority=task_func.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time(),
            )
            model.set_json(args=task_broker.args, kwargs=task_broker.kwargs)
        else:
            model: TaskStatusErrorSchema = plugin_result[-1]
        #

        if plugin_result and model.retry != 0:
            self.log.warning(f"Задача {task_broker.uuid} завершена с ошибкой и будет повторена.")
        else:
            self.log.warning(f"Задача {task_broker.uuid} завершена с ошибкой:\n{trace}")
        return model

    async def _task_cancel(self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema) -> None:
        """Событие отмены задачи."""
        model = TaskStatusCancelSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            cancel_reason=str(e),
            created_at=task_broker.created_at,
            updated_at=time(),
        )
        self.log.info(f"Задача {task_broker.uuid} была отменена по причине: {e}")
        return model

    async def _task_exists(
        self, task_broker: TaskPrioritySchema
    ) -> TaskExecSchema | None:
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
            model = TaskStatusErrorSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time(),
            )
            await self.remove_finished_task(task_func=None, task_broker=task_broker, model=model)
            self.log.warning(f"Задача {task_broker.name} завершена с ошибкой:\n{trace}")
            return None

    async def _init_task_running(
        self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> None:
        """Вызов задач `init_task_running`.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
        """
        for model_init in self.init_task_running:
            try:
                (
                    await model_init.func(task_func=task_func, task_broker=task_broker)
                    if model_init.awaiting
                    else model_init.func(task_func=task_func, task_broker=task_broker)
                )
            except BaseException:
                pass
        return

    async def _init_task_stoping(
        self,
        task_func: TaskExecSchema,
        task_broker: TaskPrioritySchema,
        model: TaskStatusSuccessSchema | TaskStatusErrorSchema,
    ) -> None:
        """Вызов задач `init_task_stoping`.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Модель `TaskStatusSuccessSchema` или `TaskStatusSuccessSchema`.
        """
        for model_init in self.init_task_stoping:
            try:
                (
                    await model_init.func(
                        task_func=task_func, task_broker=task_broker, returning=model
                    )
                    if model_init.awaiting
                    else model_init.func(
                        task_func=task_func, task_broker=task_broker, returning=model
                    )
                )
            except BaseException:
                pass
        return

    async def remove_finished_task(
        self,
        task_func: Annotated[
            Optional[TaskExecSchema],
            Doc(
                """
                    Схема функции задачи.
                    """
            )
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
        model: Annotated[
            Union[
                TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema
            ],
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
        ],
    ) -> None:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_func (TaskExecSchema, optional): Схема функции задачи. По умолчанию: `None`.
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Модель результата задачи.
        """
        new_data = await self._plugin_trigger(
            "worker_remove_finished_task",
            worker=self,
            broker=self.broker,
            task_func=task_func,
            task_broker=task_broker,
            model=model,
            return_last=True
        )
        if new_data:
            task_broker, model = new_data
        await self.broker.remove_finished_task(task_broker, model)

    def init_plugins(self):
        """Инициализация плагинов."""
        self.add_plugin(AsyncRetryPlugin(), trigger_names=["worker_task_error_retry"])
        self.add_plugin(AsyncPydanticWrapperPlugin(), trigger_names=["task_executor_args_replace", "task_executor_after_execute_result_replace"])
