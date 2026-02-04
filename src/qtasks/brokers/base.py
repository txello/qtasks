"""Base Broker."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import asdict, field, fields, make_dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    overload,
)
from uuid import UUID

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class BaseBroker(Generic[TAsyncFlag], ABC):
    """
    `BaseBroker` - An abstract class that is the foundation for Brokers.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers.base import BaseBroker

    class MyBroker(BaseBroker):
        def __init__(self, name: str = None, storage: BaseStorage = None):
            super().__init__(name=name, storage=storage)
            pass
    ```
    """

    def __init__(
        self,
        storage: Annotated[
            BaseStorage[TAsyncFlag],
            Doc("""
                    Storage `qtasks.storages.base.BaseStorage`.

                    Default: `None`.
                    """),
        ],
        name: Annotated[
            str | None,
            Doc("""
                    Project name. This name can be used for tags for Brokers.

                    Default: `None`.
                    """),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc("""
                    Config.

                    Default: `qtasks.configs.config.QueueConfig`.
                    """),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc("""
                    Events.

                    Default: `None`.
                    """),
        ] = None,
    ):
        """
        BaseBroker initialization.

        Args:
            name (str, optional): Project name. Default: `None`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `None`.
        """
        self.name = name
        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("Broker")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="Broker",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.events = events

        self.storage = storage

        self.plugins: dict[str, list[BasePlugin]] = {}

        self.init_plugins()

    @overload
    def add(
        self: BaseBroker[Literal[False]],
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.

                    Default: `0`.
                    """),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc("""
                    Additional task parameters.
                    """),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc("""
                    Task arguments of type args.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.
                    """),
        ] = None,
    ) -> Task: ...

    @overload
    async def add(
        self: BaseBroker[Literal[True]],
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.

                    Default: `0`.
                    """),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc("""
                    Additional task parameters.
                    """),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc("""
                    Task arguments of type args.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.
                    """),
        ] = None,
    ) -> Task: ...

    @abstractmethod
    def add(
        self,
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.

                    Default: `0`.
                    """),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc("""
                    Additional task parameters.
                    """),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc("""
                    Task arguments of type args.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.
                    """),
        ] = None,
    ) -> Task | Awaitable[Task]:
        """
        Adding a task to the broker.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: `0`.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `None`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `None`.

        Returns:
            Task: `schemas.task.Task`
        """
        pass

    @overload
    def get(
        self: BaseBroker[Literal[False]],
        uuid: Annotated[
            UUID | str,
            Doc("""
                    UUID of the task.
                    """),
        ],
    ) -> Task | None: ...

    @overload
    async def get(
        self: BaseBroker[Literal[True]],
        uuid: Annotated[
            UUID | str,
            Doc("""
                    UUID of the task.
                    """),
        ],
    ) -> Task | None: ...

    @abstractmethod
    def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc("""
                    UUID of the task.
                    """),
        ],
    ) -> Task | None | Awaitable[Task | None]:
        """
        Obtaining information about a task.

        Args:
            uuid (UUID|str): UUID of the task.

        Returns:
            Task|None: If there is task information, returns `schemas.task.Task`, otherwise `None`.
        """
        pass

    @overload
    def update(
        self: BaseBroker[Literal[False]],
        **kwargs: Annotated[
            Any,
            Doc("""
                    Update arguments for storage type kwargs.
                    """),
        ],
    ) -> None: ...

    @overload
    async def update(
        self: BaseBroker[Literal[True]],
        **kwargs: Annotated[
            Any,
            Doc("""
                    Update arguments for storage type kwargs.
                    """),
        ],
    ) -> None: ...

    @abstractmethod
    def update(
        self,
        **kwargs: Annotated[
            Any,
            Doc("""
                    Update arguments for storage type kwargs.
                    """),
        ],
    ) -> None | Awaitable[None]:
        """
        Updates task information.

        Args:
            kwargs (dict, optional): task data of type kwargs.
        """
        pass

    @overload
    def start(
        self: BaseBroker[Literal[False]],
        worker: Annotated[
            Optional[BaseWorker],
            Doc("""
                    Worker class.

                    Default: `None`.
                    """),
        ] = None,
    ) -> None: ...

    @overload
    async def start(
        self: BaseBroker[Literal[True]],
        worker: Annotated[
            Optional[BaseWorker],
            Doc("""
                    Worker class.

                    Default: `None`.
                    """),
        ] = None,
    ) -> None: ...

    @abstractmethod
    def start(
        self,
        worker: Annotated[
            Optional[BaseWorker],
            Doc("""
                    Worker class.

                    Default: `None`.
                    """),
        ] = None,
    ) -> None | Awaitable[None]:
        """
        Launching the Broker. This function is enabled by the main `QueueTasks` instance via `run_forever`.

        Args:
            worker (BaseWorker, optional): Worker class. Default: `None`.
        """
        pass

    @overload
    def stop(
        self: BaseBroker[Literal[False]],
    ) -> None: ...

    @overload
    async def stop(
        self: BaseBroker[Literal[True]],
    ) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """The broker stops. This function is invoked by the main `QueueTasks` instance after the `run_forever` function completes."""
        pass

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc("""
                    Config.
                    """),
        ],
    ) -> None:
        """
        Updates the broker config.

        Args:
            config (QueueConfig): Config.
        """
        self.config = config
        return

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc("""
                    Plugin.
                    """),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc("""
                    The name of the triggers for the plugin.

                    Default: Default: will be added to `Globals`.
                    """),
        ] = None,
    ) -> None:
        """
        Add a plugin to the class.

        Args:
            plugin (BasePlugin): Plugin
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    @overload
    def flush_all(self: BaseBroker[Literal[False]]) -> None: ...

    @overload
    async def flush_all(self: BaseBroker[Literal[True]]) -> None: ...

    def flush_all(self) -> None | Awaitable[None]:
        """Delete all data."""
        pass

    def init_plugins(self):
        """Initializing plugins."""
        pass

    @overload
    def remove_finished_task(
        self: BaseBroker[Literal[False]],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc("""
                    Model of the task result.
                    """),
        ],
    ) -> None: ...

    @overload
    async def remove_finished_task(
        self: BaseBroker[Literal[True]],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc("""
                    Model of the task result.
                    """),
        ],
    ) -> None: ...

    def remove_finished_task(
        self,
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc("""
                    Model of the task result.
                    """),
        ],
    ) -> None | Awaitable[None]:
        """
        Updates storage data via the `self.storage.remove_finished_task` function.

        Args:
            task_broker (TaskPrioritySchema): The priority task schema.
            model (TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Model of the task result.
        """
        pass

    def _dynamic_model(
        self,
        model: Annotated[
            TaskStatusNewSchema,
            Doc("""
                    Task model.
                    """),
        ],
        extra: Annotated[
            dict,
            Doc("""
                    Additional fields.
                    """),
        ],
    ):
        # Get the names of standard fields
        task_field_names = {f.name for f in fields(TaskStatusNewSchema)}

        # We are looking for additional keys
        extra_fields = []
        extra_values = {}

        for key, value in extra.items():
            if key not in task_field_names:
                # Typing is primitive - can be improved
                field_type = type(value)
                extra_fields.append((key, field_type, field(default=None)))
                extra_values[key] = value

        # Create a new dataclass with additional fields
        if extra_fields:
            NewTask = make_dataclass(
                "TaskStatusNewSchema", extra_fields, bases=(TaskStatusNewSchema,)
            )
        else:
            NewTask = TaskStatusNewSchema

        # Let's combine all the arguments
        return NewTask(**asdict(model), **extra_values)
