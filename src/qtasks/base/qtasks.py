"""Base QueueTasks."""
from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    Union,
    overload,
)

from typing_extensions import Doc

import qtasks._state
from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.registries.task_registry import TaskRegistry
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.types.annotations import P, R
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.base import BaseMiddleware
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.plugins.base import BasePlugin
    from qtasks.routers.async_router import AsyncRouter
    from qtasks.routers.sync_router import SyncRouter
    from qtasks.starters.base import BaseStarter
    from qtasks.workers.base import BaseWorker


class BaseQueueTasks(Generic[TAsyncFlag]):
    """Base class for QueueTasks. Stores the general logic for working with tasks in the queue."""

    def __init__(
        self,
        broker: Annotated[
            BaseBroker,
            Doc(
                """
                    Broker.
                    """
            ),
        ],
        worker: Annotated[
            BaseWorker,
            Doc(
                """
                    Worker.
                    """
            ),
        ],
        name: Annotated[
            str,
            Doc(
                """
                    Project name.

                    Default: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker_url: Annotated[
            str | None,
            Doc(
                """
                    URL for the Broker.

                    Default: `None`.
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
                    Config.

                    Default: `qtasks.configs.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc(
                """
                    Events.

                    Default: `None`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing the base class for QueueTasks.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            broker_url (str, optional): URL for the Broker. Default: `None`.
            broker (BaseBroker, optional): Broker.
            worker (BaseWorker, optional): Worker.
            log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Config. Default: `qtasks.configs.QueueConfig`.
            events (BaseEvents, optional): Events. Default: `None`.
        """
        self.name = name

        self.version: Annotated[str, Doc("Version.")] = "1.7.0"

        self.config: Annotated[
            QueueConfig,
            Doc(
                """
                Config, type is `qtasks.configs.QueueConfig`.

                Default: `QueueConfig()`.
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
        self.starter: BaseStarter | None = None

        self.routers: Annotated[
            list[SyncRouter | AsyncRouter],
            Doc(
                """
                Routers, type is `qtasks.routers.SyncRouter | qtasks.routers.AsyncRouter`.

                Default: `Empty array`.
                """
            ),
        ] = []

        self.tasks: Annotated[
            dict[str, TaskExecSchema],
            Doc(
                """
                Tasks, type is `{task_name:qtasks.schemas.TaskExecSchema}`.

                Default: `Empty dict`.
                """
            ),
        ] = {}

        self.plugins: Annotated[
            dict[str, list[BasePlugin]],
            Doc(
                """
                Plugins, type is `{trigger_name:[qtasks.plugins.base.BasePlugin]}`.

                Default: `Empty dict`.
                """
            ),
        ] = {}

        self.events = events

        self._method: Annotated[
            str | None,
            Doc(
                """Method of using QueueTasks.

                Default: `None`.
                """
            ),
        ] = None

    @overload
    def task(
        self: BaseQueueTasks[Literal[False]],
        name: str | None = None,
        *,
        priority: int | None = None,
        echo: bool = False,
        max_time: float | None = None,
        retry: int | None = None,
        retry_on_exc: list[type[Exception]] | None = None,
        decode: Callable | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
        generate_handler: Callable | None = None,
        executor: type[BaseTaskExecutor] | None = None,
        middlewares_before: list[type[TaskMiddleware]] | None = None,
        middlewares_after: list[type[TaskMiddleware]] | None = None,
        **kwargs,
    ) -> Callable[[Callable[P, R]], SyncTask[P, R]]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add SyncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.
            ValueError: Unknown method {self._method}.

        Returns:
            SyncTask: Decorator for registering a task.
        """
        ...

    @overload
    def task(
        self: BaseQueueTasks[Literal[True]],
        name: str | None = None,
        *,
        priority: int | None = None,
        echo: bool = False,
        max_time: float | None = None,
        retry: int | None = None,
        retry_on_exc: list[type[Exception]] | None = None,
        decode: Callable | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
        generate_handler: Callable | None = None,
        executor: type[BaseTaskExecutor] | None = None,
        middlewares_before: list[type[TaskMiddleware]] | None = None,
        middlewares_after: list[type[TaskMiddleware]] | None = None,
        **kwargs,
    ) -> Callable[[Callable[P, R]], AsyncTask[P, R]]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add AsyncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `AsyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]],, optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]],, optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.
            ValueError: Unknown method {self._method}.

        Returns:
            AsyncTask: Decorator for registering a task.
        """
        ...

    @overload
    def task(
        self: BaseQueueTasks[Literal[False]], name: Callable[P, R]
    ) -> SyncTask[P, R]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add SyncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.
            ValueError: Unknown method {self._method}.

        Returns:
            SyncTask: Decorator for registering a task.
        """
        ...

    @overload
    def task(
        self: BaseQueueTasks[Literal[True]], name: Callable[P, R]
    ) -> AsyncTask[P, R]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add AsyncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `AsyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]],, optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]],, optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.
            ValueError: Unknown method {self._method}.

        Returns:
            AsyncTask: Decorator for registering a task.
        """
        ...

    def task(
        self,
        name: Annotated[
            Callable[P, R] | str | None,
            Doc(
                """
                    Name of the task.

                    Default: `func.__name__`.
                    """
            ),
        ] = None,
        *,
        priority: Annotated[
            int | None,
            Doc(
                """
                    The task's default priority.

                    Default: `config.task_default_priority`.
                    """
            ),
        ] = None,
        echo: Annotated[
            bool,
            Doc(
                """
                    Add (A)syncTask as the first parameter.

                    Default: `False`.
                    """
            ),
        ] = False,
        max_time: Annotated[
            float | None,
            Doc(
                """
                    The maximum time the task will take to complete in seconds.

                    Default: `None`.
                    """
            ),
        ] = None,
        retry: Annotated[
            int | None,
            Doc(
                """
                    Number of attempts to retry the task.

                    Default: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            list[type[Exception]] | None,
            Doc(
                """
                    Exceptions under which the task will be re-executed.

                    Default: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Callable | None,
            Doc(
                """
                    Decoder of the task result.

                    Default: `None`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                    Task tags.

                    Default: `None`.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                    Description of the task.

                    Default: `None`.
                """
            ),
        ] = None,
        generate_handler: Annotated[
            Callable | None,
            Doc(
                """
                    Handler generator.

                    Default: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            type[BaseTaskExecutor] | None,
            Doc(
                """
                    `BaseTaskExecutor` class.

                    Default: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares_before: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Middleware that will be executed before the task.

                    Default: `Empty array`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Middleware that will be executed after the task.

                    Default: `Empty array`.
                    """
            ),
        ] = None,
        **kwargs,
    ) -> SyncTask[P, R] | AsyncTask[P, R] | Callable[[Callable[P, R]], SyncTask[P, R] | AsyncTask[P, R]]:
        """
        Decorator for registering tasks.

        Args:
            name (str, optional): Name of the task. Default: `func.__name__`.
            priority (int, optional): The task's default priority. Default: `config.task_default_priority`.
            echo (bool, optional): Add (A)syncTask as the first parameter. Default: `False`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): `BaseTaskExecutor` class. Default: `SyncTaskExecutor`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.

        Raises:
            ValueError: If a task with the same name is already registered.
            ValueError: Unknown method {self._method}.
            ValueError: Unsupported method {self._method}.

        Returns:
            SyncTask | AsyncTask: Decorator for registering a task.
        """

        def wrapper(func: Callable[P, R]):
            if not self._method:
                raise ValueError(f"Unknown method {self._method}.")
            nonlocal priority, middlewares_after, middlewares_before
            task_name = name or func.__name__ if not callable(name) else name.__name__

            if task_name in self.tasks:
                raise ValueError(f"Task with name {task_name} is already registered!")

            priority = (
                priority if priority is not None else self.config.task_default_priority
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
                raise ValueError(f"Unsupported method {self._method}") from exc

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
            SyncRouter | AsyncRouter,
            Doc(
                """
                    Router `qtasks.routers.SyncRouter` | `qtasks.routers.AsyncRouter`.
                    """
            ),
        ],
    ) -> None:
        """
        Add Router.

        Args:
            router (Router): Router `qtasks.routers.SyncRouter` | `qtasks.routers.AsyncRouter`.
        """
        self.routers.append(router)
        self.tasks.update(router.tasks)
        self.worker._tasks.update(router.tasks)

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc(
                """
                    Plugin class.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    The name of the triggers for the plugin.

                    Default: will be added to `Globals`.
                    """
            ),
        ] = None,
        component: Annotated[
            str | None,
            Doc(
                """
                    Component name.

                    Default: `None`.
                    """
            ),
        ] = None,
    ) -> None:
        """
        Add a plugin.

        Args:
            plugin (Type[BasePlugin]): Plugin class.
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
            component (str, optional): Component name. Default: `None`.

        Raises:
            KeyError: Unable to get component {component}!
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
            raise KeyError(f"Unable to get component {component}!")
        component_data.add_plugin(plugin, trigger_names)
        return

    def add_middleware(
        self,
        middleware: Annotated[
            type[BaseMiddleware],
            Doc(
                """
                    Middleware class.
                    """
            ),
        ],
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Kwargs.

                    Default: `{}`.
                    """
            ),
        ]
        ) -> None:
        """
        Add middleware.

        Args:
            middleware (Type[BaseMiddleware]): Middleware.
            **kwargs (Any): Kwargs.

        Raises:
            ImportError: Unable to connect Middleware: It does not belong to the BaseMiddleware class!
        """
        if (
            not middleware.__base__
            or (middleware.__base__.__base__ and middleware.__base__.__base__.__name__)
            != "BaseMiddleware"
        ):
            raise ImportError(
                f"Unable to connect Middleware {middleware.__name__}: It does not belong to the BaseMiddleware class!"
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
        Register tasks from the task registry.

        Updates `self.tasks` and `self.worker._tasks` with all tasks,
        registered in the `TaskRegistry`, setting the default priority.
        """
        all_tasks = TaskRegistry.all_tasks()

        for task in all_tasks.values():
            if task.priority is None:
                task.priority = self.config.task_default_priority

        self.tasks.update(all_tasks)
        self.worker._tasks.update(all_tasks)

    def _set_state(self):
        """Set parameters in `qtasks._state`."""
        qtasks._state.app_main = self
        qtasks._state.log_main = self.log

    def _update_configs(self, config: QueueConfig, key, value):
        """
        Update configuration.

        Args:
            config (QueueConfig): Configuration.
            key (str): Configuration key.
            value (Any): Configuration value.
        """
        if key == "logs_default_level_server":
            self.log.default_level = value
            self.log = self.log.update_logger()
            self._update_logs(default_level=value)

    def _update_logs(self, **kwargs):
        """Update logs."""
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
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    @overload
    def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Task: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Task: ...

    def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Union[
        Optional[Task], Awaitable[Optional[Task]], Task, Awaitable[Task]
    ]:
        """
        Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): Task args. Default: `()`.
            kwargs (dict, optional): Task kwargs. Default: `{}`.

            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.SyncResult` or `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` or `None`.
        """
        pass
