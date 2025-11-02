"""Init module for async worker."""
from __future__ import annotations

import asyncio
import json
import traceback
from dataclasses import asdict
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID

from anyio import Semaphore
from typing_extensions import Doc

from qtasks.brokers.async_redis import AsyncRedisBroker
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.exc.task import TaskCancelError
from qtasks.executors.async_task_executor import AsyncTaskExecutor
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.plugins.depends.async_depends import AsyncDependsPlugin
from qtasks.plugins.pydantic import AsyncPydanticWrapperPlugin
from qtasks.plugins.retries import AsyncRetryPlugin
from qtasks.plugins.states.async_state import AsyncStatePlugin
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)

from .base import BaseWorker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.executors.base import BaseTaskExecutor


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
            Optional[BaseBroker],
            Doc(
                """
                    Брокер.

                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
            ),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация асинхронного воркера.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            broker (BaseBroker, optional): Брокер. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `None`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `None`.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        super().__init__(
            name=name, broker=broker, log=log, config=config, events=events
        )

        self.events = self.events or AsyncEvents()
        self.events: BaseEvents[Literal[True]]

        self.broker = broker or AsyncRedisBroker(
            name=self.name, log=self.log, config=self.config
        )
        self.broker: BaseBroker[Literal[True]]

        self.queue = asyncio.PriorityQueue()

        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event: asyncio.Event | None = None
        self.semaphore = asyncio.Semaphore(self.config.max_tasks_process)
        self.condition: asyncio.Condition | None = None

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

        Raises:
            RuntimeError: Воркер не запущен.
        """
        if not self._stop_event or not self.condition:
            raise RuntimeError("Воркер не запущен")

        await self.events.fire("worker_running", worker=self, number=number)

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
            await self.events.fire("worker_stopping", worker=self, number=number)

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
                args=json.dumps(task_broker.args),
                kwargs=json.dumps(task_broker.kwargs),
            )

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
                return_last=True,
            )
            if new_model:
                model = new_model.get("model", model)

            await self.broker.update(
                name=f"{self.name}:{task_broker.uuid}", mapping=asdict(model)
            )

            await self.events.fire(
                "task_running",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
            )
            model = await self._run_task(task_func, task_broker)
            await self.events.fire(
                "task_stopping",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

            await self.remove_finished_task(
                task_func=task_func, task_broker=task_broker, model=model
            )

            await self._plugin_trigger(
                "worker_execute_after",
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

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

            Raises:
                RuntimeError: Воркер не запущен.
        """
        if not self.condition:
            raise RuntimeError("Воркер не запущен.")

        new_data = await self._plugin_trigger(
            "worker_add",
            worker=self,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kw=kwargs,
            created_at=created_at,
            return_last=True,
        )
        if new_data:
            name = new_data.get("name", name)
            uuid = new_data.get("uuid", uuid)
            priority = new_data.get("priority", priority)
            args = new_data.get("args", args)
            kwargs = new_data.get("kw", kwargs)
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
            self.condition.notify_all()
        return Task(
            status=TaskStatusEnum.NEW.value,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=datetime.fromtimestamp(created_at),
            updated_at=datetime.fromtimestamp(created_at),
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

        if self.condition is None:
            self.condition = asyncio.Condition()
        if self._stop_event is None:
            self._stop_event = asyncio.Event()
        await self._plugin_trigger("worker_start", worker=self)

        # Запускаем несколько воркеров
        loop = asyncio.get_event_loop()
        workers = [
            loop.create_task(self.worker(number)) for number in range(self.num_workers)
        ]
        await self._stop_event.wait()  # Ожидание сигнала остановки

        # Ожидаем завершения всех воркеров
        for worker_task in workers:
            worker_task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    async def stop(self):
        """Останавливает воркеры."""
        await self._plugin_trigger("worker_stop", worker=self)
        if self._stop_event:
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

        Raises:
            RuntimeError: task_executor не определен.
        """
        if not self.task_executor:
            raise RuntimeError("task_executor не определен.")

        if self.log:
            self.log.info(
                f"Выполняю задачу {task_broker.uuid} ({task_broker.name}), приоритет: {task_broker.priority}"
            )
            self.log.info(f"Аргументы задачи: {task_broker.args}, {task_broker.kwargs}")
        new_data = await self._plugin_trigger(
            "worker_run_task_before",
            worker=self,
            task_func=task_func,
            task_broker=task_broker,
            return_last=True,
        )
        if new_data:
            task_func = new_data.get("task_func", task_func)
            task_broker = new_data.get("task_broker", task_broker)

        if self.task_middlewares_before:
            task_func.add_middlewares_before(self.task_middlewares_before)
        if self.task_middlewares_after:
            task_func.add_middlewares_after(self.task_middlewares_after)

        executor = (
            task_func.executor if task_func.executor is not None else self.task_executor
        )
        task_executor: BaseTaskExecutor[Literal[True]] = executor(
            task_func=task_func,
            task_broker=task_broker,
            log=self.log,
            plugins=self.plugins,
        )

        try:
            result = await task_executor.execute()
            return await self._task_success(result, task_func, task_broker)
        except TaskCancelError as e:
            return await self._task_cancel(e, task_func, task_broker)
        except BaseException as e:
            return await self._task_error(e, task_func, task_broker)

    async def _task_success(
        self, result: Any, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema:
        """Событие успешного завершения задачи."""
        model = TaskStatusSuccessSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            returning=result,
            created_at=task_broker.created_at,
            updated_at=time(),
            args=json.dumps(task_broker.args),
            kwargs=json.dumps(task_broker.kwargs),
        )
        if self.log:
            self.log.info(
                f"Задача {task_broker.uuid} успешно завершена, результат: {result}"
            )
        return model

    async def _task_error(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusErrorSchema:
        """Событие завершения задачи с ошибкой."""
        trace = traceback.format_exc()

        # plugin: retry
        plugin_result = None

        should_retry = task_func.retry and (
            not task_func.retry_on_exc or type(e) in task_func.retry_on_exc
        )
        if should_retry and task_func.retry:
            plugin_result = await self._plugin_trigger(
                "worker_task_error_retry",
                broker=self.broker,
                task_func=task_func,
                task_broker=task_broker,
                trace=trace,
            )

        model = TaskStatusErrorSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            traceback=trace,
            created_at=task_broker.created_at,
            updated_at=time(),
            args=json.dumps(task_broker.args),
            kwargs=json.dumps(task_broker.kwargs),
        )
        if plugin_result:
            model: TaskStatusErrorSchema = plugin_result.get("model", model)
        #

        if plugin_result and model.retry != 0:
            if self.log:
                self.log.error(
                    f"Задача {task_broker.uuid} завершена с ошибкой и будет повторена."
                )
        else:
            if self.log:
                self.log.error(f"Задача {task_broker.uuid} завершена с ошибкой:\n{trace}")
        return model

    async def _task_cancel(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusCancelSchema:
        """Событие отмены задачи."""
        model = TaskStatusCancelSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            cancel_reason=str(e),
            created_at=task_broker.created_at,
            updated_at=time(),
        )
        if self.log:
            self.log.error(f"Задача {task_broker.uuid} была отменена по причине: {e}")
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
            if self.log:
                self.log.warning(f"Задачи {e.args[0]} не существует!")
            trace = traceback.format_exc()
            model = TaskStatusErrorSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time(),
            )
            await self.remove_finished_task(
                task_func=None, task_broker=task_broker, model=model
            )
            if self.log:
                self.log.error(f"Задача {task_broker.name} завершена с ошибкой:\n{trace}")
            return None

    async def remove_finished_task(
        self,
        task_func: Annotated[
            TaskExecSchema | None,
            Doc(
                """
                    Схема функции задачи.
                    """
            ),
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
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
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
            model (TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Модель результата задачи.
        """
        new_data = await self._plugin_trigger(
            "worker_remove_finished_task",
            worker=self,
            broker=self.broker,
            task_func=task_func,
            task_broker=task_broker,
            model=model,
            return_last=True,
        )
        if new_data:
            task_broker, model = new_data.get("task_broker", task_broker), new_data.get(
                "model", model
            )
        await self.broker.remove_finished_task(task_broker, model)

    def init_plugins(self):
        """Инициализация плагинов."""
        self.add_plugin(AsyncRetryPlugin(), trigger_names=["worker_task_error_retry"])
        self.add_plugin(
            AsyncPydanticWrapperPlugin(),
            trigger_names=[
                "task_executor_args_replace",
                "task_executor_after_execute_result_replace",
            ],
        )
        self.add_plugin(
            AsyncDependsPlugin(), trigger_names=[
                "task_executor_args_replace",
                "task_executor_task_close",
                "worker_stop",
                "broker_stop",
                "storage_stop",
                "global_config_stop"
            ]
        )
        self.add_plugin(
            AsyncStatePlugin(), trigger_names=["task_executor_args_replace"]
        )
