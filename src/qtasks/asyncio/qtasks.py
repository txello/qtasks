import asyncio
import asyncio_atexit
import inspect
from typing import TYPE_CHECKING, Callable, List, Optional, Type, Union, overload
from typing_extensions import Annotated, Doc
from uuid import UUID

from qtasks.types.annotations import P, R
from qtasks.base.qtasks import BaseQueueTasks
from qtasks.logs import Logger

from qtasks.brokers.async_redis import AsyncRedisBroker
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.workers.async_worker import AsyncWorker
from qtasks.starters.async_starter import AsyncStarter
from qtasks.results.async_result import AsyncResult
from qtasks.plugins.retries import async_retry_plugin

from qtasks.configs import QueueConfig
from qtasks.schemas.inits import InitsExecSchema
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.brokers.base import BaseBroker
    from qtasks.starters.base import BaseStarter
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware


class QueueTasks(BaseQueueTasks):
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
    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется компонентами(Воркер, Брокер и т.п.)
                    
                    По умолчанию: `QueueTasks`.
                    """
                )
            ] = "QueueTasks",
            
            broker_url: Annotated[
                Optional[str],
                Doc(
                    """
                    URL для Брокера. Используется Брокером по умолчанию через параметр url.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,

            broker: Annotated[
                Optional["BaseBroker"],
                Doc(
                    """
                    Брокер. Хранит в себе обработку из очередей задач и хранилище данных.
                    
                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
                )
            ] = None,
            worker: Annotated[
                Optional["BaseWorker"],
                Doc(
                    """
                    Воркер. Хранит в себе обработку задач.
                    
                    По умолчанию: `qtasks.workers.AsyncWorker`.
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
                    
                    По умолчанию: `qtasks.configs.QueueConfig`.
                    """
                )
            ] = None
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
        super().__init__(name=name, broker=broker, worker=worker, log=log, config=config)
        self._method = "async"

        self.broker: "BaseBroker" = self.broker or AsyncRedisBroker(name=name, url=broker_url, log=self.log, config=self.config)
        self.worker: "BaseWorker" = self.worker or AsyncWorker(name=name, broker=self.broker, log=self.log, config=self.config)
        self.starter: "BaseStarter"|None = None
        
        self._global_loop: Annotated[
            Optional[asyncio.AbstractEventLoop],
            Doc(
                """
                Асинхронный loop, может быть указан.
                
                По умолчанию: `None`.
                """
            )
        ] = None
        
        self._registry_tasks()

        self._set_state()

        self.init_plugins()

    async def add_task(self, 
            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            priority: Annotated[
                Optional[int],
                Doc(
                    """
                    Приоритет у задачи.
                    
                    По умолчанию: Значение приоритета у задачи.
                    """
                )
            ] = None,
            args: Annotated[
                Optional[tuple],
                Doc(
                    """
                    args задачи.
                    
                    По умолчанию: `()`.
                    """
                )
            ] = None,
            kwargs: Annotated[
                Optional[dict],
                Doc(
                    """
                    kwargs задачи.
                    
                    По умолчанию: `{}`.
                    """
                )
            ] = None,

            timeout: Annotated[
                Optional[float],
                Doc(
                    """
                    Таймаут задачи.
                    
                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
                )
            ] = None
        ) -> Task:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        if task_name not in self.tasks:
            raise KeyError(f"Задача с именем {task_name} не зарегистрирована!")
        
        if priority is None:
            priority = self.tasks.get(task_name).priority
            
        args, kwargs = args or (), kwargs or {}
        
        task = await self.broker.add(task_name=task_name, priority=priority, extra=None, args=args, kwargs=kwargs)
        if timeout is not None:
            return await AsyncResult(uuid=task.uuid, app=self, log=self.log).result(timeout=timeout)
        return task
    
    async def get(self,
            uuid: Annotated[
                Union[UUID, str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получить задачу.

        Args:
            uuid (UUID|str): UUID Задачи.

        Returns:
            Task|None: Данные задачи или None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        
        return await self.broker.get(uuid=uuid)
    
    def run_forever(self,
            loop: Annotated[
                Optional[asyncio.AbstractEventLoop],
                Doc(
                    """
                    Асинхронный loop.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            starter: Annotated[
                Optional["BaseStarter"],
                Doc(
                    """
                    Стартер. Хранит в себе способы запуска компонентов.
                    
                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
                )
            ] = None,
            num_workers: Annotated[
                int,
                Doc(
                    """
                    Количество запущенных воркеров.
                    
                    По умолчанию: `4`.
                    """
                )
            ] = 4,
            reset_config: Annotated[
                bool,
                Doc(
                    """
                    Обновить config у воркера и брокера.
                    
                    По умолчанию: `True`.
                    """
                )
            ] = True
        ) -> None:
        """Запуск асинхронно Приложение.

        Args:
            loop (asyncio.AbstractEventLoop, optional): асинхронный loop. По умолчанию: None.
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
        """
        self.starter = starter or AsyncStarter(name=self.name, worker=self.worker, broker=self.broker, log=self.log, config=self.config)
        
        self.starter._inits.update({
            "init_starting": self._inits["init_starting"],
            "init_stoping": self._inits["init_stoping"],
        })
        
        plugins_hash = {}
        for plugins in [self.plugins, self.worker.plugins, self.broker.plugins, self.broker.storage.plugins]:
            plugins_hash.update(plugins)
        
        self._set_state()
        
        self.starter.start(loop=loop, num_workers=num_workers, reset_config=reset_config, plugins = plugins_hash)
    
    async def stop(self):
        """Останавливает все компоненты."""
        await self.starter.stop()
    
    @property
    def init_starting(self):
        """
        `init_starting` - Инициализация при запуске `QueueTasks`.

        ## Примеры

        ```python
        from qtasks import QueueTasks

        app = QueueTasks()
        
        @app.init_starting
        async def test(worker, broker):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_starting", func=func, awaiting=inspect.iscoroutinefunction(func))
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
        async def test(worker, broker):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_stoping", func=func, awaiting=inspect.iscoroutinefunction(func))
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
        async def test(worker):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_worker_running", func=func, awaiting=inspect.iscoroutinefunction(func))
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
        async def test(worker):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_worker_stoping", func=func, awaiting=inspect.iscoroutinefunction(func))
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
        async def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_task_running", func=func, awaiting=inspect.iscoroutinefunction(func))
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
        async def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema, returning: TaskStatusSuccessSchema|TaskStatusErrorSchema):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_task_stoping", func=func, awaiting=inspect.iscoroutinefunction(func))
            self._inits["init_task_stoping"].append(model)
            self.worker.init_task_stoping.append(model)
            return func
        return wrap

    async def ping(self, server: bool = True) -> bool:
        """Проверка запуска сервера

        Args:
            server (bool, optional): Проверка через сервер. По умолчанию `True`.

        Returns:
            bool: True - Работает, False - Не работает.
        """
        if server:
            loop = asyncio.get_running_loop()
            asyncio_atexit.register(self.broker.storage.global_config.stop, loop=loop)

            status = await self.broker.storage.global_config.get("main", "status")
            if status is None:
                return False
            return True
        return True
        
    async def _plugin_trigger(self, name: str, *args, **kwargs):
        """
        Вызвать триггер плагина.

        Args:
            name (str): Имя триггера.
            *args: Позиционные аргументы для триггера.
            **kwargs: Именованные аргументы для триггера.
        """
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = await plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results
    
    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self.broker.flush_all()

    @overload
    def task(self,
        name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя задачи.
                    
                    По умолчанию: `func.__name__`.
                    """
                )
            ] = None,
            priority: Annotated[
                Optional[int],
                Doc(
                    """
                    Приоритет у задачи по умолчанию.
                    
                    По умолчанию: `config.default_task_priority`.
                    """
                )
            ] = None,

            echo: bool = False,
            retry: int|None = None,
            retry_on_exc: list[Type[Exception]]|None = None,
            generate_handler: Callable|None = None,

            executor: Annotated[
                Type["BaseTaskExecutor"],
                Doc(
                    """
                    Класс `BaseTaskExecutor`.
                    
                    По умолчанию: `SyncTaskExecutor`.
                    """
                )
            ] = None,
            middlewares: Annotated[
                List["TaskMiddleware"],
                Doc(
                    """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None
    ) -> Callable[[Callable[P, R]], AsyncTask[P, R]]: ...

    def task(self, *args, **kwargs):
        return super().task(*args, **kwargs)