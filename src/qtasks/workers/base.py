"""Base worker class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Generic,
    Literal,
    Optional,
    overload,
)
from uuid import UUID

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.middlewares.task import TaskMiddleware
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.plugins.base import BasePlugin


class BaseWorker(Generic[TAsyncFlag], ABC):
    """
    `BaseWorker` - An abstract class that is the foundation for Workers.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.workers.base import BaseWorker

    class MyWorker(BaseWorker):
        def __init__(self, name: str = None, broker: BaseBroker = None):
            super().__init__(name=name, broker=broker)
            pass
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя может быть использовано Воркером.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker: Annotated[
            Optional[BaseBroker],
            Doc(
                """
                    Брокер `qtasks.brokers.base.BaseBroker`.

                    По умолчанию: `None`.
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

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing the base worker.

        Args:
            name (str, optional): Project name. Default: None.
            broker (BaseBroker, optional): Broker. Default: None.
            log (Logger, optional): Logger. Default: None.
            config (QueueConfig, optional): Config. Default: None.
        """
        self.name = name
        self.broker = broker
        self.config = config or QueueConfig()

        self.log = (
            log.with_subname("Worker")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="Worker",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )

        self._tasks: dict[str, TaskExecSchema] = {}
        self.events: BaseEvents | None = events
        self.task_middlewares_before: list[type[TaskMiddleware]] = []
        self.task_middlewares_after: list[type[TaskMiddleware]] = []

        self.task_executor: type[BaseTaskExecutor] | None = None

        self.plugins: dict[str, list[BasePlugin]] = {}

        self.num_workers = 0

        self.init_plugins()

    @overload
    def add(
        self: BaseWorker[Literal[False]],
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
    ) -> None: ...

    @overload
    async def add(
        self: BaseWorker[Literal[True]],
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
    ) -> None: ...

    @abstractmethod
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
    ) -> None | Awaitable[None]:
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
        pass

    @overload
    def start(
        self: BaseWorker[Literal[False]],
        num_workers: Annotated[
            int | None,
            Doc(
                """
                    Количество воркеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None: ...

    @overload
    async def start(
        self: BaseWorker[Literal[True]],
        num_workers: Annotated[
            int | None,
            Doc(
                """
                    Количество воркеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None: ...

    @abstractmethod
    def start(
        self,
        num_workers: Annotated[
            int | None,
            Doc(
                """
                    Количество воркеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None | Awaitable[None]:
        """
        Runs multiple task handlers. This function is enabled by the main `QueueTasks` instance via `run_forever`.

        Args:
            num_workers (int, optional): Number of workers. Default: 4.
        """
        pass

    @overload
    def stop(self: BaseWorker[Literal[False]]) -> None: ...

    @overload
    async def stop(self: BaseWorker[Literal[True]]) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """Stops workers. This function is invoked by the main `QueueTasks` instance after the `run_forever` function completes."""
        pass

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
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
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

    def init_plugins(self):
        """Initializing plugins."""
        pass
