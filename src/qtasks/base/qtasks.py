"""Base QueueTasks."""

import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    Union,
    overload,
)
from typing_extensions import Annotated, Doc

from qtasks.schemas.task import Task
from qtasks.types.annotations import P, R
import qtasks._state
from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.task_registry import TaskRegistry
from qtasks.routers.router import Router
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.brokers.base import BaseBroker
    from qtasks.starters.base import BaseStarter
    from qtasks.plugins.base import BasePlugin
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.events.base import BaseEvents
    from qtasks.middlewares.base import BaseMiddleware
    from qtasks.middlewares.task import TaskMiddleware


class BaseQueueTasks(Generic[TAsyncFlag]):
    """Base класс для QueueTasks. Хранит в себе общую логику для работы с задачами в очереди."""

    def __init__(
        self,
        broker: Annotated[
            "BaseBroker",
            Doc(
                """
                    Брокер. Хранит в себе обработку из очередей задач и хранилище данных.
                    """
            ),
        ],
        worker: Annotated[
            "BaseWorker",
            Doc(
                """
                    Воркер. Хранит в себе обработку задач.
                    """
            ),
        ],
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
        events: Annotated[
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `None`.
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
            events (BaseEvents, optional): События. По умолчанию: `None`.
        """
        self.name = name

        self.version: Annotated[str, Doc("Версия проекта.")] = "1.7.0"

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
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )

        self.broker = broker
        self.worker = worker
        self.starter: Union["BaseStarter", None] = None

        self.routers: Annotated[
            List[Router],
            Doc(
                """
                Роутеры, тип `qtasks.routers.Router`.

                По умолчанию: `Пустой массив`.
                """
            ),
        ] = []

        self.tasks: Annotated[
            Dict[str, TaskExecSchema],
            Doc(
                """
                Задачи, тип `{task_name:qtasks.schemas.TaskExecSchema}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.plugins: Annotated[
            Dict[str, List["BasePlugin"]],
            Doc(
                """
                Задачи, тип `{trigger_name:[qtasks.plugins.base.BasePlugin]}`.

                По умолчанию: `Пустой словарь`.
                """
            ),
        ] = {}

        self.events = events

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
        self: "BaseQueueTasks[Literal[False]]",
        name: Union[str, None] = None,
        *,
        priority: Union[int, None] = None,
        echo: bool = False,
        max_time: Union[float, None] = None,
        retry: Union[int, None] = None,
        retry_on_exc: Union[List[Type[Exception]], None] = None,
        decode: Union[Callable, None] = None,
        tags: Union[List[str], None] = None,
        description: Union[str, None] = None,
        generate_handler: Union[Callable, None] = None,
        executor: Union[Type["BaseTaskExecutor"], None] = None,
        middlewares_before: Optional[List[Type["TaskMiddleware"]]] = None,
        middlewares_after: Optional[List[Type["TaskMiddleware"]]] = None,
        **kwargs,
    ) -> Callable[[Callable[P, R]], SyncTask[P, R]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Добавить SyncTask первым параметром. По умолчанию: `False`.
            max_time (float, optional): Максимальное время выполнения задачи в секундах. По умолчанию: `None`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены до задачи. По умолчанию: `Пустой массив`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            SyncTask: Декоратор для регистрации задачи.
        """
        ...

    @overload
    def task(
        self: "BaseQueueTasks[Literal[True]]",
        name: Union[str, None] = None,
        *,
        priority: Union[int, None] = None,
        echo: bool = False,
        max_time: Union[float, None] = None,
        retry: Union[int, None] = None,
        retry_on_exc: Union[List[Type[Exception]], None] = None,
        decode: Union[Callable, None] = None,
        tags: Union[List[str], None] = None,
        description: Union[str, None] = None,
        generate_handler: Union[Callable, None] = None,
        executor: Union[Type["BaseTaskExecutor"], None] = None,
        middlewares_before: Optional[List[Type["TaskMiddleware"]]] = None,
        middlewares_after: Optional[List[Type["TaskMiddleware"]]] = None,
        **kwargs,
    ) -> Callable[[Callable[P, R]], AsyncTask[P, R]]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Добавить AsyncTask первым параметром. По умолчанию: `False`.
            max_time (float, optional): Максимальное время выполнения задачи в секундах. По умолчанию: `None`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `AsyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]],, optional): Мидлвари, которые будут выполнены до задачи. По умолчанию: `Пустой массив`.
            middlewares_after (List[Type["TaskMiddleware"]],, optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.

        Returns:
            AsyncTask: Декоратор для регистрации задачи.
        """
        ...

    @overload
    def task(
        self: "BaseQueueTasks[Literal[False]]", name: Callable[P, R]
    ) -> SyncTask[P, R]: ...

    @overload
    def task(
        self: "BaseQueueTasks[Literal[True]]", name: Callable[P, R]
    ) -> AsyncTask[P, R]: ...

    def task(
        self,
        name: Annotated[
            Optional[Union[Callable[P, R], str]],
            Doc(
                """
                    Имя задачи или функция.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        *,
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
                    Добавить (A)syncTask первым параметром.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        max_time: Annotated[
            Union[float, None],
            Doc(
                """
                    Максимальное время выполнения задачи в секундах.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry: Annotated[
            Union[int, None],
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            Union[List[Type[Exception]], None],
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Union[Callable, None],
            Doc(
                """
                    Декодер результата задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        tags: Annotated[
            Union[List[str], None],
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        description: Annotated[
            Union[str, None],
            Doc(
                """
                    Описание задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        generate_handler: Annotated[
            Union[Callable, None],
            Doc(
                """
                    Генератор обработчика.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            Optional[Type["BaseTaskExecutor"]],
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares_before: Annotated[
            Optional[List[Type["TaskMiddleware"]]],
            Doc(
                """
                    Мидлвари, которые будут выполнены до задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            Optional[List[Type["TaskMiddleware"]]],
            Doc(
                """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        **kwargs,
    ) -> Union[
        Union[SyncTask[P, R], AsyncTask[P, R]],
        Callable[[Callable[P, R]], Union[SyncTask[P, R], AsyncTask[P, R]]],
    ]:
        """Декоратор для регистрации задач.

        Args:
            name (str, optional): Имя задачи. По умолчанию: `func.__name__`.
            priority (int, optional): Приоритет у задачи по умолчанию. По умолчанию: `config.default_task_priority`.
            echo (bool, optional): Добавить (A)syncTask первым параметром. По умолчанию: `False`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены до задачи. По умолчанию: `Пустой массив`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.

        Raises:
            ValueError: Если задача с таким именем уже зарегистрирована.
            ValueError: Неизвестный метод {self._method}.
            ValueError: Неподдерживаемый метод {self._method}.

        Returns:
            SyncTask | AsyncTask: Декоратор для регистрации задачи.
        """

        def wrapper(func: Callable[P, R]):
            if not self._method:
                raise ValueError(f"Неизвестный метод {self._method}.")
            nonlocal priority, middlewares_after, middlewares_before
            task_name = name or func.__name__ if not callable(name) else name.__name__

            if task_name in self.tasks:
                raise ValueError(f"Задача с именем {task_name} уже зарегистрирована!")

            priority = (
                priority if priority is not None else self.config.default_task_priority
            )

            generating = (
                "async"
                if inspect.isasyncgenfunction(func)
                else "sync" if inspect.isgeneratorfunction(func) else False
            )

            middlewares_before = middlewares_before or []
            middlewares_after = middlewares_after or []

            model = TaskExecSchema(
                name=task_name,
                priority=priority,
                func=func,
                awaiting=inspect.iscoroutinefunction(func),
                generating=generating,
                echo=echo,
                max_time=max_time,
                retry=retry,
                retry_on_exc=retry_on_exc,
                decode=decode,
                tags=tags,
                description=description,
                generate_handler=generate_handler,
                executor=executor,
                middlewares_before=middlewares_before,
                middlewares_after=middlewares_after,
                extra=kwargs,
            )

            for registry in (self.tasks, self.worker._tasks):
                registry[task_name] = model

            method_map = {"async": AsyncTask, "sync": SyncTask}
            try:
                method = method_map[self._method]
            except KeyError as exc:
                raise ValueError(f"Неподдерживаемый метод: {self._method}") from exc

            return method(
                app=self,
                task_name=model.name,
                priority=model.priority,
                echo=model.echo,
                max_time=model.max_time,
                retry=model.retry,
                retry_on_exc=model.retry_on_exc,
                decode=model.decode,
                tags=model.tags,
                description=model.description,
                generate_handler=model.generate_handler,
                executor=model.executor,
                middlewares_before=model.middlewares_before,
                middlewares_after=model.middlewares_after,
                extra=model.extra,
            )

        if callable(name):
            func = name
            name = func.__name__
            return wrapper(func)
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

        component_data = data.get(component)
        if not component_data:
            raise KeyError(f"Невозможно получить компонент {component}!")
        component_data.add_plugin(plugin, trigger_names)
        return

    def add_middleware(self, middleware: Type["BaseMiddleware"], **kwargs) -> None:
        """Добавить мидлварь.

        Args:
            middleware (Type[BaseMiddleware]): Мидлварь.

        Raises:
            ImportError: Невозможно подключить Middleware: Он не относится к классу BaseMiddleware!
        """
        if (
            not middleware.__base__
            or (middleware.__base__.__base__ and middleware.__base__.__base__.__name__)
            != "BaseMiddleware"
        ):
            raise ImportError(
                f"Невозможно подключить Middleware {middleware.__name__}: Он не относится к классу BaseMiddleware!"
            )
        if issubclass(middleware, "TaskMiddleware"):

            position = kwargs.get("position", "before")
            if position == "before":
                self.worker.task_middlewares_before.append(middleware)
            elif position == "after":
                self.worker.task_middlewares_after.append(middleware)
        self.log.debug(f"Мидлварь {middleware.__name__} добавлен.")
        return

    def _registry_tasks(self):
        """
        Зарегистрировать задачи из реестра задач.

        Обновляет `self.tasks` и `self.worker._tasks` всеми задачами,
        зарегистрированными в `TaskRegistry`, устанавливая приоритет по умолчанию.
        """
        all_tasks = TaskRegistry.all_tasks()

        for task in all_tasks.values():
            if task.priority is None:
                task.priority = self.config.default_task_priority

        self.tasks.update(all_tasks)
        self.worker._tasks.update(all_tasks)

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
        if key == "logs_default_level_server":
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

    @overload
    def add_task(
        self,
        *args: Annotated[
            Any,
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
    ) -> Optional["Task"]: ...

    @overload
    async def add_task(
        self,
        *args: Annotated[
            Any,
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
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Optional["Task"]: ...

    @overload
    def add_task(
        self,
        *args: Annotated[
            Any,
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
            None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> "Task": ...

    @overload
    async def add_task(
        self,
        *args: Annotated[
            Any,
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
            None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> "Task": ...

    def add_task(
        self,
        *args: Annotated[
            Any,
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
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Union[
        Optional["Task"], Awaitable[Optional["Task"]], "Task", Awaitable["Task"]
    ]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncResult` или `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        pass
