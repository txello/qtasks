import inspect
from typing import TYPE_CHECKING, List, Optional, Type, Union
from typing_extensions import Annotated, Doc
from uuid import UUID

import qtasks._state
from qtasks.executors.base import BaseTaskExecutor
from qtasks.logs import Logger
from qtasks.middlewares.task import TaskMiddleware
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.task_registry import TaskRegistry
from qtasks.results.sync_result import SyncResult
from qtasks.workers.sync_worker import SyncThreadWorker
from qtasks.starters.sync_starter import SyncStarter
from qtasks.brokers.sync_redis import SyncRedisBroker
from qtasks.routers import Router

from qtasks.configs import QueueConfig
from qtasks.schemas.inits import InitsExecSchema
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.workers.base import BaseWorker
    from qtasks.starters.base import BaseStarter
    from qtasks.plugins.base import BasePlugin
    from qtasks.middlewares.base import BaseMiddleware

class QueueTasks:
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
                    
                    По умолчанию: `qtasks.brokers.SyncRedisBroker`.
                    """
                )
            ] = None,
            worker: Annotated[
                Optional["BaseWorker"],
                Doc(
                    """
                    Воркер. Хранит в себе обработку задач.
                    
                    По умолчанию: `qtasks.workers.SyncWorker`.
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
            ] = None
        ):
        """
        Инициализация QueueTasks.

        Args:
            name (str): Имя проекта. По умолчанию: `QueueTasks`.
            broker_url (str, optional): URL для Брокера. Используется Брокером по умолчанию через параметр url. По умолчанию: `None`.
            broker (Type[BaseBroker], optional): Брокер. Хранит в себе обработку из очередей задач и хранилище данных. По умолчанию: `qtasks.brokers.SyncRedisBroker`.
            worker (Type[BaseWorker], optional): Воркер. Хранит в себе обработку задач. По умолчанию: `qtasks.workers.SyncWorker`.
        """
        self.name = name

        self.config: Annotated[
            QueueConfig,
            Doc(
                """
                Конфиг, тип `qtasks.configs.QueueConfig`.
                
                По умолчанию: `QueueConfig()`.
                """
            )
        ] = QueueConfig()
        self.config.subscribe(self._update_configs)
        
        self.log = log.with_subname("QueueTasks") if log else Logger(name=self.name, subname="QueueTasks", default_level=self.config.logs_default_level, format=self.config.logs_format)

        self.broker = broker or SyncRedisBroker(name=name, url=broker_url, log=self.log, config=self.config)
        self.worker = worker or SyncThreadWorker(name=name, broker=self.broker, log=self.log, config=self.config)
        self.starter: "BaseStarter"|None = None
        
        self.routers: Annotated[
            list[Router],
            Doc(
                """
                Роутеры, тип `qtasks.routers.Router`.
                
                По умолчанию: `Пустой массив`.
                """
            )
        ] = []
        
        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.
                
                По умолчанию: `Пустой словарь`.
                """
            )
        ] = {}
        
        self.plugins: Annotated[
            dict[str, List["BasePlugin"]],
            Doc(
                """
                Задачи, тип `{trigger_name:[qtasks.plugins.base.BasePlugin]}`.
                
                По умолчанию: `Пустой словарь`.
                """
            )
        ] = {}
        
        self._inits: Annotated[
            dict[str, list[InitsExecSchema]],
            Doc(
                """
                функции инициализаций.
                
                По умолчанию установлены: `init_starting, init_worker_running, init_task_running, init_task_stoping, init_task_stoping, init_worker_stoping` и `init_stoping`.
                """
            )
        ] = {
            "init_starting":[],
            "init_worker_running":[],
            "init_task_running":[],
            "init_task_stoping":[],
            "init_worker_stoping":[],
            "init_stoping":[]
        }

        self._method: Annotated[
            str,
            Doc(
                """Метод использования QueueTasks.
                
                Указано: `sync`.
                """
            )
        ] = "sync"
        
        self._registry_tasks()

        self._set_state()
    
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
                List[TaskMiddleware],
                Doc(
                    """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None
        ):
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
        """
        def wrapper(func):
            nonlocal name, priority, executor, middlewares, echo, retry
            
            task_name = name or func.__name__
            if task_name in self.tasks:
                raise ValueError(f"Задача с именем {task_name} уже зарегистрирована!")
            
            if priority is None:
                priority = self.config.default_task_priority
            
            middlewares = middlewares or []
            model = TaskExecSchema(
                name=task_name, priority=priority, func=func, awaiting=inspect.iscoroutinefunction(func),
                echo=echo,
                retry=retry,
                executor=executor, middlewares=middlewares
            )
            
            self.tasks[task_name] = model
            self.worker._tasks[task_name] = model
            return SyncTask(app=self, task_name=task_name, priority=priority, echo=echo, executor=executor, middlewares=middlewares)
        return wrapper
    
    def add_task(self, 
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
                    Приоритет задачи.
                    
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
                    
                    Если указан, задача возвращается через `qtasks.results.SyncTask`.
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

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        if task_name not in self.tasks:
            raise KeyError(f"Задача с именем {task_name} не зарегистрирована!")
        
        if priority is None:
            priority = self.tasks.get(task_name).priority
        
        args, kwargs = args or (), kwargs or {}
        task = self.broker.add(task_name=task_name, priority=priority, extra=None, args=args, kwargs=kwargs)
        if timeout is not None:
            return SyncResult(uuid=task.uuid, app=self, log=self.log).result(timeout=timeout)
        return task
        
    
    def get(self,
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
        
        return self.broker.get(uuid=uuid)
    
    def include_router(self,
            router: Annotated[
                Router,
                Doc(
                    """
                    Роутер `qtasks.routers.Router`.
                    """
                )
            ]
        ) -> None:
        """Добавить Router.

        Args:
            router (Router): Роутер `qtasks.routers.Router`.
        """
        self.routers.append(router)
        self.tasks.update(router.tasks)
        self.worker._tasks.update(router.tasks)

    def run_forever(self,
            starter: Annotated[
                Optional["BaseStarter"],
                Doc(
                    """
                    Обновить Стартер.
                    
                    По умолчанию: `None`.
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
        """Запуск синхронно Приложение.

        Args:
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.SyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
        """
        self.starter = starter or SyncStarter(name=self.name, worker=self.worker, broker=self.broker, log=self.log, config=self.config)
        
        self.starter._inits.update({
            "init_starting": self._inits["init_starting"],
            "init_stoping": self._inits["init_stoping"],
        })

        plugins_hash = {}
        for plugins in [self.plugins, self.worker.plugins, self.broker.plugins, self.broker.storage.plugins]:
            plugins_hash.update(plugins)

        self._set_state()

        self.starter.start(num_workers=num_workers, reset_config=reset_config, plugins = plugins_hash)
    
    def stop(self):
        """
        Останавливает все компоненты.
        """
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
        def test(worker, broker):
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
        def test(worker):
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
        def test(worker):
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
        def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema):
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
        def test(task_func: TaskExecSchema, task_broker: TaskPrioritySchema, returning: TaskStatusSuccessSchema|TaskStatusErrorSchema):
            pass
        ```
        """
        def wrap(func):
            model = InitsExecSchema(typing="init_task_stoping", func=func, awaiting=inspect.iscoroutinefunction(func))
            self._inits["init_task_stoping"].append(model)
            self.worker.init_task_stoping.append(model)
            return func
        return wrap

    def ping(self, server: bool = True) -> bool:
        """Проверка запуска сервера

        Args:
            server (bool, optional): Проверка через сервер. По умолчанию `True`.

        Returns:
            bool: True - Работает, False - Не работает.
        """
        if server:
            status = self.broker.storage.global_config.get("main", "status")
            if status is None:
                return False
            return True
        return True

    def add_plugin(self, plugin: "BasePlugin", trigger_names: Optional[List[str]] = None, component: Optional[str] = None) -> None:
        """
        Добавить плагин.

        Args:
            plugin (Type[BasePlugin]): Класс плагина.
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
            component (str, optional): Имя компонента. По умолчанию: `None`.
        """
        data = {
            "worker": self.worker,
            "broker": self.broker,
            "storage": self.broker.storage,
            "global_config": self.broker.storage.global_config
        }

        trigger_names = trigger_names or ["Globals"]

        if not component:
            for name in trigger_names:
                if name not in self.plugins:
                    self.plugins.update({name: [plugin]})
                else:
                    self.plugins[name].append(plugin)
            return
        
        component_data = data.get(component, None)
        if not component_data:
            raise KeyError(f"Невозможно получить компонент {component}!")
        component_data.add_plugin(plugin, trigger_names)
        return
    
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
            
    def _registry_tasks(self):
        """
        Зарегистрировать задачи из реестра задач.

        Обновляет `self.tasks` и `self.worker._tasks` всеми задачами,
        зарегистрированными в `TaskRegistry`.
        """
        self.tasks.update(TaskRegistry.all_tasks())
        self.worker._tasks.update(TaskRegistry.all_tasks())

    def _set_state(self):
        """Установить параметры в `qtasks._state`."""
        qtasks._state.app_main = self
        qtasks._state.log_main = self.log

    def _update_configs(self, config: QueueConfig, key, value):
        if key == "logs_default_level":
            self.log.default_level = value
            self.log = self.log.update_logger()
            self._update_logs(default_level=value)

    def _update_logs(self, **kwargs):
        if self.worker:
            self.worker.log = self.worker.log.update_logger(**kwargs)
        if self.broker:
            self.broker.log = self.broker.log.update_logger(**kwargs)
            if self.broker.storage:
                self.broker.storage.log = self.broker.storage.log.update_logger(**kwargs)
                if self.broker.storage.global_config:
                    self.broker.storage.global_config.log = self.broker.storage.global_config.log.update_logger(**kwargs)

    def add_middleware(self, middleware: Type["BaseMiddleware"]) -> None:
        """Добавить мидлварь.

        Args:
            middleware (Type[BaseMiddleware]): Мидлварь.

        Raises:
            ImportError: Невозможно подключить Middleware: Он не относится к классу BaseMiddleware!
        """
        if not middleware.__base__ or middleware.__base__.__base__.__name__ != "BaseMiddleware":
            raise ImportError(f"Невозможно подключить Middleware {middleware.__name__}: Он не относится к классу BaseMiddleware!")
        if middleware.__base__.__name__ == "TaskMiddleware":
            self.worker.task_middlewares.append(middleware)
        self.log.debug(f"Мидлварь {middleware.__name__} добавлен.")
        return
    
    def flush_all(self) -> None:
        """Удалить все данные."""
        self.broker.flush_all()