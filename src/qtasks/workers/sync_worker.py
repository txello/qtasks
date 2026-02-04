"""Init module for sync worker."""
from __future__ import annotations

import json
import traceback
from dataclasses import asdict
from datetime import datetime
from queue import PriorityQueue
from threading import Event, Lock, Semaphore, Thread
from time import sleep, time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID

from typing_extensions import Doc

from qtasks.brokers import SyncRedisBroker
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.exc.task import TaskCancelError
from qtasks.executors.sync_task_executor import SyncTaskExecutor
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.plugins.depends.sync_depends import SyncDependsPlugin
from qtasks.plugins.pydantic import SyncPydanticWrapperPlugin
from qtasks.plugins.retries import SyncRetryPlugin
from qtasks.plugins.states.sync_state import SyncStatePlugin
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


class SyncThreadWorker(BaseWorker, SyncPluginMixin):
    """
    Worker, Receiving tasks from the Broker and processing them.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.workers import SyncThreadWorker
    
        worker = SyncThreadWorker()
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

                    По умолчанию: `qtasks.brokers.SyncRedisBroker`.
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

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing a synchronous worker.
        
                Args:
                    name (str, optional): Project name. Default: "QueueTasks".
                    broker (BaseBroker, optional): Broker. Default: `None`.
                    log (Logger, optional): Logger. Default: `None`.
                    config (QueueConfig, optional): Config. Default: `None`.
                    events (BaseEvents, optional): Events. Default: `qtasks.events.SyncEvents`.
        """
        super().__init__(
            name=name, broker=broker, log=log, config=config, events=events
        )

        self.events = self.events or SyncEvents()
        self.events: BaseEvents[Literal[False]]

        self.broker = broker or SyncRedisBroker(
            name=self.name, log=self.log, config=self.config
        )
        self.broker: BaseBroker[Literal[False]]

        self.queue = PriorityQueue()
        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event = Event()
        self.lock = Lock()
        self.threads: list[Thread] = []
        self.semaphore = Semaphore(self.config.max_tasks_process)

        self.task_executor = SyncTaskExecutor

    def worker(
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
        """
        Task processor.
        
                Args:
                    number (int): Worker number.
        
                Raises:
                    RuntimeError: The worker is not running.
        """
        if not self._stop_event:
            raise RuntimeError("Воркер не запущен")

        self.events.fire("worker_running", worker=self, number=number)

        try:
            while not self._stop_event.is_set():
                with self.lock:
                    if self.queue.empty():
                        sleep(0.1)
                        continue
                    task_broker: TaskPrioritySchema = self.queue.get()

                if task_broker is None:
                    break
                Thread(
                    target=self._execute_task, args=(task_broker,), daemon=True
                ).start()

        finally:
            self.events.fire("worker_stopping", worker=self, number=number)

    def _execute_task(
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
        """
        Performs task independently.
        
                Args:
                    task_broker (TaskPrioritySchema): The priority task schema.
        """
        with self.semaphore:
            model = TaskStatusProcessSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                created_at=task_broker.created_at,
                updated_at=time(),
                args=json.dumps(task_broker.args),
                kwargs=json.dumps(task_broker.kwargs),
            )

            task_func = self._task_exists(task_broker=task_broker)
            if not task_func:
                self.queue.task_done()
                return

            new_model = self._plugin_trigger(
                "worker_execute_before",
                worker=self,
                task_broker=task_broker,
                task_func=task_func,
                model=model,
                return_last=True,
            )
            if new_model:
                model = new_model.get("model", model)

            self.broker.update(
                name=f"{self.name}:{task_broker.uuid}", mapping=asdict(model)
            )

            self.events.fire(
                "task_running",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
            )
            model = self._run_task(task_func=task_func, task_broker=task_broker)
            self.events.fire(
                "task_stopping",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

            self.remove_finished_task(
                task_func=task_func, task_broker=task_broker, model=model
            )

            self._plugin_trigger(
                "worker_execute_after",
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

            self.queue.task_done()

    def add(
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
        """
        Adding a task to the queue.
        
                Args:
                    name (str): Name of the task.
                    uuid (UUID): UUID of the task.
                    priority (int): Task priority.
                    created_at (float): Create a task in timestamp format.
                    args (tuple): Task arguments of type args.
                    kwargs (dict): Task arguments of type kwargs.
        """
        new_data = self._plugin_trigger(
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
        with self.lock:
            self.queue.put(model)

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

    def start(
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
        """
        Runs multiple task handlers.
        
                Args:
                    num_workers (int, optional): Number of workers. Default: 4.
        """
        self.num_workers = num_workers
        self._plugin_trigger("worker_start", worker=self)

        for number in range(self.num_workers):
            thread = Thread(target=self.worker, args=(number,), daemon=True)
            thread.start()
            self.threads.append(thread)

    def stop(self):
        """Stops workers."""
        self._plugin_trigger("worker_stop", worker=self)
        self._stop_event.set()
        for thread in self.threads:
            thread.join()

    def update_config(self, config: QueueConfig):
        """Updates the config."""
        self.config = config
        self.semaphore = Semaphore(config.max_tasks_process)

    def _run_task(
        self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema:
        """
        Run the task function.
        
                Args:
                    task_func (TaskExecSchema): Schema `qtasks.schemas.TaskExecSchema`.
                    task_broker(TaskPrioritySchema): Schema `qtasks.schemas.TaskPrioritySchema`.
        
                Returns:
                    TaskStatusSuccessSchema|TaskStatusErrorSchema: The result of the task function.
        
                Raises:
                    RuntimeError: task_executor is not defined.
        """
        if not self.task_executor:
            raise RuntimeError("task_executor не определен.")

        if self.log:
            self.log.info(
                f"Выполняю задачу {task_broker.uuid} ({task_broker.name}), приоритет: {task_broker.priority}./n",
                f"Аргументы задачи: {task_broker.args}, {task_broker.kwargs}"
            )

        new_data = self._plugin_trigger(
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
        executor = executor(
            task_func=task_func,
            task_broker=task_broker,
            log=self.log,
            plugins=self.plugins,
        )

        try:
            result = executor.execute()
            return self._task_success(result, task_func, task_broker)
        except TaskCancelError as e:
            return self._task_cancel(e, task_func, task_broker)
        except BaseException as e:
            return self._task_error(e, task_func, task_broker)

    def _task_success(
        self, result: Any, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema:
        """Event of successful completion of a task."""
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

    def _task_error(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusErrorSchema:
        """Event of task completion with an error."""
        trace = traceback.format_exc()

        # plugin: retry
        plugin_result = None

        should_retry = task_func.retry and (
            not task_func.retry_on_exc or type(e) in task_func.retry_on_exc
        )
        if should_retry and task_func.retry:
            plugin_result = self._plugin_trigger(
                "worker_task_error_retry",
                broker=self.broker,
                task_func=task_func,
                task_broker=task_broker,
                trace=trace,
                return_last=True,
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

    def _task_cancel(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusCancelSchema:
        """Task cancellation event."""
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

    def _task_exists(
        self, task_broker: TaskPrioritySchema
    ) -> TaskExecSchema | None:
        """
        Checking the existence of a task.
        
                Args:
                    task_broker(TaskPrioritySchema): Schema `TaskPrioritySchema`.
        
                Returns:
                    TaskExecSchema|None: Schema `TaskExecSchema` or `None`.
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
            self.remove_finished_task(
                task_func=None, task_broker=task_broker, model=model
            )
            if self.log:
                self.log.error(f"Задача {task_broker.name} завершена с ошибкой:\n{trace}")
            return None

    def remove_finished_task(
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
        """
        Updates storage data via the `self.storage.remove_finished_task` function.
        
                Args:
                    task_func (TaskExecSchema, optional): Task function schema. Default: `None`.
                    task_broker (TaskPrioritySchema): The priority task schema.
                    model (TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Model of the task result.
        """
        new_data = self._plugin_trigger(
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
        self.broker.remove_finished_task(task_broker, model)

    def init_plugins(self):
        """Initializing plugins."""
        self.add_plugin(SyncRetryPlugin(), trigger_names=["worker_task_error_retry"])
        self.add_plugin(
            SyncPydanticWrapperPlugin(),
            trigger_names=[
                "task_executor_args_replace",
                "task_executor_after_execute_result_replace",
            ],
        )
        self.add_plugin(
            SyncDependsPlugin(), trigger_names=[
                "task_executor_args_replace",
                "task_executor_task_close",
                "worker_stop",
                "broker_stop",
                "storage_stop",
                "global_config_stop"
            ]
        )
        self.add_plugin(
            SyncStatePlugin(), trigger_names=["task_executor_args_replace"]
        )
