"""Base QueueTasks."""

import inspect
from typing import (
    TYPE_CHECKING,
    Annotated,
    Callable,
    List,
    Optional,
    Type,
    Union,
    overload,
)
from typing_extensions import Doc

from qtasks.types.annotations import P, R
import qtasks._state
from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.task_registry import TaskRegistry
from qtasks.routers.router import Router
from qtasks.schemas.inits import InitsExecSchema
from qtasks.schemas.task_exec import TaskExecSchema

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.brokers.base import BaseBroker
    from qtasks.starters.base import BaseStarter
    from qtasks.plugins.base import BasePlugin
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.base import BaseMiddleware
    from qtasks.middlewares.task import TaskMiddleware


class BaseQueueTasks:
    """Base класс для QueueTasks. Хранит в себе общую логику для работы с задачами в очереди."""

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

                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional["BaseWorker"],
            Doc(
                """
                    Воркер. Хранит в себе обработку задач.

                    По умолчанию: `qtasks.workers.AsyncWorker`.
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
        """Инициализация базового класса для QueueTasks.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `QueueTasks`.
            broker_url (str, optional): URL для Брокера. По умолчанию: `None`.
            broker (BaseBroker, optional): Брокер. По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
            worker (BaseWorker, optional): Воркер. По умолчанию: `qtasks.workers.AsyncWorker`.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.QueueConfig`.
        """
        self.name = name

        self.version: Annotated[str, Doc("Версия проекта.")] = "1.5.0"

        self.config: Annotated[
            QueueConfig,
            Doc(
                """
                Конфиг, тип `qtasks.configs.QueueConfig`.

                По умолчанию: `QueueConfig()`.
                """
            ),
        ] = (
            config or QueueConfig()
        )
        self.config.subscribe(self._update_configs)

        self.log = (
            log.with_subname("QueueTasks")
            if log
            else Logger(
                name=self.name,
                subname="QueueTasks",
                default_level=self.config.logs_default_level,
                format=self.config.logs_format,
            )
        )

        self.broker: "BaseBroker" = broker
        self.worker: "BaseWorker" = worker
        self.starter: "BaseStarter" | None = None

        self.routers: Annotated[
            list[Router],
            Doc(
                """
                Роутеры, тип `qtasks.routers.Router`.

                По умолчанию: `Пустой массив`.
                """
            ),
        ] = []

        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.plugins: Annotated[
            dict[str, List["BasePlugin"]],
            Doc(
                """
                Задачи, тип `{trigger_name:[qtasks.plugins.base.BasePlugin]}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self._inits: Annotated[
            dict[str, list[InitsExecSchema]],
            Doc(
                """
                функции инициализаций.

                По умолчанию установлены: `init_starting, init_worker_running, init_task_running, init_task_stoping, init_task_stoping, init_worker_stoping` и `init_stoping`.
                """
            ),
        ] = {
            "init_starting": [],
            "init_worker_running": [],
            "init_task_running": [],
            "init_task_stoping": [],
            "init_worker_stoping": [],
            "init_stoping": [],
        }

        self._method: Annotated[
            Optional[str],
            Doc(
                """Метод использования QueueTasks.

                По умолчанию: `None`.
                """
            ),
        ] = None

    @overload
    def task(
        self,
        name: str | None = None,
        priority: int | None = None,
        echo: bool = False,
        retry: int | None = None,
        retry_on_exc: list[Type[Exception]] | None = None,
        generate_handler: Callable | None = None,
        executor: Type["BaseTaskExecutor"] | None = None,
        middlewares: List["TaskMiddleware"] | None = None,
    ) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
        ...

    def task(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc(
                """
                    Приоритет у задачи по умолчанию.

                    По умолчанию: `config.default_task_priority`.
                    """
            ),
        ] = None,
        echo: Annotated[
            bool,
            Doc(
                """
                    Включить вывод в консоль.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        retry: Annotated[
            int | None,
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            list[Type[Exception]] | None,
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        generate_handler: Annotated[
            Callable | None,
            Doc(
                """
                    Генератор обработчика.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            Type["BaseTaskExecutor"],
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
    ) -> Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Включить вывод в консоль. По умолчанию: `False`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (list[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares (List["TaskMiddleware"], optional): Мидлвари. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            Callable[SyncTask|AsyncTask]: Декоратор для регистрации задачи.
        """

        def wrapper(func):
            nonlocal priority, middlewares
            task_name = name or func.__name__
            priority = priority or self.config.default_task_priority

            task_name = name or func.__name__
            if task_name in self.tasks:
                raise ValueError(f"Задача с именем {task_name} уже зарегистрирована!")

            if priority is None:
                priority = self.config.default_task_priority

            generating = False
            if inspect.isgeneratorfunction(func):
                generating = "sync"
            if inspect.isasyncgenfunction(func):
                generating = "async"

            middlewares = middlewares or []

            model = TaskExecSchema(
                name=task_name,
                priority=priority,
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
                generating=generating,
                echo=echo,
                retry=retry,
                retry_on_exc=retry_on_exc,
                generate_handler=generate_handler,
                executor=executor,
                middlewares=middlewares,
            )

            self.tasks[task_name] = model
            self.worker._tasks[task_name] = model
            if self._method == "async":
                return AsyncTask(
                    app=self,
                    task_name=task_name,
                    priority=priority,
                    echo=echo,
                    retry=retry,
                    retry_on_exc=retry_on_exc,
                    generate_handler=generate_handler,
                    executor=executor,
                    middlewares=middlewares,
                )
            elif self._method == "sync":
                return SyncTask(
                    app=self,
                    task_name=task_name,
                    priority=priority,
                    echo=echo,
                    retry=retry,
                    retry_on_exc=retry_on_exc,
                    generate_handler=generate_handler,
                    executor=executor,
                    middlewares=middlewares,
                )
            else:
                raise ValueError(f"Неизвестный метод {self._method}")

        return wrapper

    def include_router(
        self,
        router: Annotated[
            Router,
            Doc(
                """
                    Роутер `qtasks.routers.Router`.
                    """
            ),
        ],
    ) -> None:
        """Добавить Router.

        Args:
            router (Router): Роутер `qtasks.routers.Router`.
        """
        self.routers.append(router)
        self.tasks.update(router.tasks)
        self.worker._tasks.update(router.tasks)

    def add_plugin(
        self,
        plugin: "BasePlugin",
        trigger_names: Optional[List[str]] = None,
        component: Optional[str] = None,
    ) -> None:
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
            "global_config": self.broker.storage.global_config,
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

    def add_middleware(self, middleware: Type["BaseMiddleware"]) -> None:
        """Добавить мидлварь.

        Args:
            middleware (Type[BaseMiddleware]): Мидлварь.

        Raises:
            ImportError: Невозможно подключить Middleware: Он не относится к классу BaseMiddleware!
        """
        if (
            not middleware.__base__ or middleware.__base__.__base__.__name__ != "BaseMiddleware"
        ):
            raise ImportError(
                f"Невозможно подключить Middleware {middleware.__name__}: Он не относится к классу BaseMiddleware!"
            )
        if middleware.__base__.__name__ == "TaskMiddleware":
            self.worker.task_middlewares.append(middleware)
        self.log.debug(f"Мидлварь {middleware.__name__} добавлен.")
        return

    def init_plugins(self):
        """Инициализация плагинов."""
        for plugin in self.plugins.values():
            plugin.init(self)

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
        """
        Обновить конфигурацию.

        Args:
            config (QueueConfig): Конфигурация.
            key (str): Ключ конфигурации.
            value (Any): Значение конфигурации.
        """
        if key == "logs_default_level":
            self.log.default_level = value
            self.log = self.log.update_logger()
            self._update_logs(default_level=value)

    def _update_logs(self, **kwargs):
        """Обновить логи."""
        if self.worker:
            self.worker.log = self.worker.log.update_logger(**kwargs)
        if self.broker:
            self.broker.log = self.broker.log.update_logger(**kwargs)
            if self.broker.storage:
                self.broker.storage.log = self.broker.storage.log.update_logger(
                    **kwargs
                )
                if self.broker.storage.global_config:
                    self.broker.storage.global_config.log = (
                        self.broker.storage.global_config.log.update_logger(**kwargs)
                    )
