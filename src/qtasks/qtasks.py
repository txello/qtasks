"""qtasks.py - Main module for the QueueTasks framework."""

import inspect
from typing import TYPE_CHECKING, Callable, List, Optional, Type, Union, overload
from typing_extensions import Annotated, Doc
from uuid import UUID

from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.types.annotations import P, R
from qtasks.base.qtasks import BaseQueueTasks
from qtasks.logs import Logger

from qtasks.brokers.sync_redis import SyncRedisBroker
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.workers.sync_worker import SyncThreadWorker
from qtasks.starters.sync_starter import SyncStarter
from qtasks.results.sync_result import SyncResult

from qtasks.configs import QueueConfig
from qtasks.schemas.inits import InitsExecSchema

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.brokers.base import BaseBroker
    from qtasks.starters.base import BaseStarter
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.schemas.task import Task


class QueueTasks(BaseQueueTasks, SyncPluginMixin):
    """
    `QueueTasks` - Фреймворк для очередей задач.

    Читать больше:
    [Первые шаги](https://txello.github.io/qtasks/ru/getting_started/).

    ## Пример

    ```python
    from qtasks import QueueTasks

    app = QueueTasks()
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется компонентами(Воркер, Брокер и т.п.)

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker_url: Annotated[
            Optional[str],
            Doc(
                """
                    URL для Брокера. Используется Брокером по умолчанию через параметр url.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        broker: Annotated[
            Optional["BaseBroker"],
            Doc(
                """
                    Брокер. Хранит в себе обработку из очередей задач и хранилище данных.

                    По умолчанию: `qtasks.brokers.SyncRedisBroker`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional["BaseWorker"],
            Doc(
                """
                    Воркер. Хранит в себе обработку задач.

                    По умолчанию: `qtasks.workers.SyncWorker`.
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

                    По умолчанию: `qtasks.configs.QueueConfig`.
                    """
            ),
        ] = None,
    ):
        """
        Инициализация QueueTasks.

        Args:
            name (str): Имя проекта. По умолчанию: `QueueTasks`.
            broker_url (str, optional): URL для Брокера. Используется Брокером по умолчанию через параметр url. По умолчанию: `None`.
            broker (Type[BaseBroker], optional): Брокер. Хранит в себе обработку из очередей задач и хранилище данных. По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
            worker (Type[BaseWorker], optional): Воркер. Хранит в себе обработку задач. По умолчанию: `qtasks.workers.AsyncWorker`.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.QueueConfig`.
        """
        super().__init__(
            name=name, broker=broker, worker=worker, log=log, config=config
        )
        self._method = "sync"

        self.broker: "BaseBroker" = broker or SyncRedisBroker(
            name=name, url=broker_url, log=self.log, config=self.config
        )
        self.worker: "BaseWorker" = worker or SyncThreadWorker(
            name=name, broker=self.broker, log=self.log, config=self.config
        )
        self.starter: Union["BaseStarter", None] = None

        self._registry_tasks()

        self._set_state()

        self.init_plugins()

    def add_task(
        self,
        *args: Annotated[
            Optional[tuple],
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        priority: Annotated[
            Optional[int],
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Optional[dict],
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Union["Task", None]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        if task_name not in self.tasks:
            raise KeyError(f"Задача с именем {task_name} не зарегистрирована!")

        if priority is None:
            priority = self.tasks.get(task_name).priority

        args, kwargs = args or (), kwargs or {}
        extra = None

        new_args = self._plugin_trigger(
            "qtasks_add_task_before_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=priority,
            args=args,
            kwargs=kwargs,
            return_last=True
        )
        if new_args:
            task_name = new_args.get("task_name", task_name)
            priority = new_args.get("priority", priority)
            extra = new_args.get("extra", extra)
            args = new_args.get("args", args)
            kwargs = new_args.get("kwargs", kwargs)

        task = self.broker.add(
            task_name=task_name, priority=priority, extra=extra, args=args, kwargs=kwargs
        )

        self._plugin_trigger(
            "qtasks_add_task_after_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=priority,
            args=args,
            kwargs=kwargs,
            return_last=True
        )
        if timeout is not None:
            return SyncResult(uuid=task.uuid, app=self, log=self.log).result(
                timeout=timeout
            )
        return task

    def get(
        self,
        uuid: Annotated[
            Union[UUID, str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union["Task", None]:
        """Получить задачу.

        Args:
            uuid (UUID|str): UUID Задачи.

        Returns:
            Task|None: Данные задачи или None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        result = self.broker.get(uuid=uuid)
        new_result = self._plugin_trigger("qtasks_get", qtasks=self, broker=self.broker, task=result, return_last=True)
        if new_result:
            result = new_result
        return result

    def run_forever(
        self,
        starter: Annotated[
            Optional["BaseStarter"],
            Doc(
                """
                    Обновить Стартер.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество запущенных воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Обновить config у воркера и брокера.

                    По умолчанию: `True`.
                    """
            ),
        ] = True,
    ) -> None:
        """Запуск синхронно Приложение.

        Args:
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.SyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
        """
        self.starter = starter or SyncStarter(
            name=self.name,
            worker=self.worker,
            broker=self.broker,
            log=self.log,
            config=self.config,
        )

        self.starter._inits.update(
            {
                "init_starting": self._inits["init_starting"],
                "init_stoping": self._inits["init_stoping"],
            }
        )

        plugins_hash = {}
        for plugins in [
            self.plugins,
            self.worker.plugins,
            self.broker.plugins,
            self.broker.storage.plugins,
        ]:
            plugins_hash.update(plugins)

        self._set_state()

        self.starter.start(
            num_workers=num_workers, reset_config=reset_config, plugins=plugins_hash
        )

    def stop(self):
        """Останавливает все компоненты."""
        self._plugin_trigger("qtasks_stop", qtasks=self, starter=self.starter)
        self.starter.stop()

    @property
    def init_starting(self):
        """
        `init_starting` - Инициализация при запуске `QueueTasks`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_starting
        def test(worker, broker):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_starting",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_starting"].append(model)
            return func

        return wrap

    @property
    def init_stoping(self):
        """
        `init_stoping` - Инициализация при остановке `QueueTasks`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_stoping
        def test(worker, broker):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_stoping",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_stoping"].append(model)
            return func

        return wrap

    @property
    def init_worker_running(self):
        """
        `init_worker_running` - Инициализация при запуске `QueueTasks.worker.worker()`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_worker_running
        def test(worker):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_worker_running",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_worker_running"].append(model)
            self.worker.init_worker_running.append(model)
            return func

        return wrap

    @property
    def init_worker_stoping(self):
        """
        `init_worker_stoping` - Инициализация при остановке `QueueTasks.worker.worker()`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_worker_stoping
        def test(worker):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_worker_stoping",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_worker_stoping"].append(model)
            self.worker.init_worker_stoping.append(model)
            return func

        return wrap

    @property
    def init_task_running(self):
        """
        `init_task_running` - Инициализация при запуске задачи функцией `QueueTasks.worker.listen()`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_task_running
        def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_task_running",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_task_running"].append(model)
            self.worker.init_task_running.append(model)
            return func

        return wrap

    @property
    def init_task_stoping(self):
        """
        `init_task_stoping` - Инициализация при завершении задачи функцией `QueueTasks.worker.listen()`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()

        @app.init_task_stoping
        def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema, returning: TaskStatusSuccessSchema|TaskStatusErrorSchema):
            pass
        ```
        """

        def wrap(func):
            model = InitsExecSchema(
                typing="init_task_stoping",
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
            )
            self._inits["init_task_stoping"].append(model)
            self.worker.init_task_stoping.append(model)
            return func

        return wrap

    def ping(self, server: bool = True) -> bool:
        """Проверка запуска сервера.

        Args:
            server (bool, optional): Проверка через сервер. По умолчанию `True`.

        Returns:
            bool: True - Работает, False - Не работает.
        """
        self._plugin_trigger("qtasks_ping", qtasks=self, global_config=self.broker.storage.global_config)
        if server:
            status = self.broker.storage.global_config.get("main", "status")
            if status is None:
                return False
            return True
        return True

    def flush_all(self) -> None:
        """Удалить все данные."""
        self._plugin_trigger("qtasks_flush_all", qtasks=self)
        self.broker.flush_all()

    @overload
    def task(
        self,
        name: Union[str, None] = None,
        *,
        priority: Union[int, None] = None,
        echo: bool = False,
        retry: Union[int, None] = None,
        retry_on_exc: Union[List[Type[Exception]], None] = None,
        decode: Union[Callable, None] = None,
        tags: Union[List[str], None] = None,
        description: Union[str, None] = None,
        generate_handler: Union[Callable, None] = None,
        executor: Union[Type["BaseTaskExecutor"], None] = None,
        middlewares_before: Union[List["TaskMiddleware"], None] = None,
        middlewares_after: Union[List["TaskMiddleware"], None] = None,
        **kwargs
    ) -> Callable[[Callable[P, R]], SyncTask[P, R]]:
        ...

    @overload
    def task(
        self,
        func: Callable[P, R],
    ) -> SyncTask[P, R]:
        ...

    def task(self, *args, **kwargs):
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Добавить SyncTask первым параметром. По умолчанию: `False`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares_before (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены до задачи. По умолчанию: `Пустой массив`.
            middlewares_after (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            SyncTask: Декоратор для регистрации задачи.
        """
        return super().task(*args, **kwargs)
