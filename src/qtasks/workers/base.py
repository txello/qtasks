"""Base worker class."""

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Type,
    Union,
    overload,
)
from uuid import UUID
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.middlewares.task import TaskMiddleware
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.plugins.base import BasePlugin
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.events.base import BaseEvents


class BaseWorker(Generic[TAsyncFlag], ABC):
    """
    `BaseWorker` - Абстрактный класс, который является фундаментом для Воркеров.

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
            Optional["BaseBroker"],
            Doc(
                """
                    Брокер `qtasks.brokers.base.BaseBroker`.

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

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
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
        """Инициализация базового воркера.

        Args:
            name (str, optional): Имя проекта. По умолчанию: None.
            broker (BaseBroker, optional): Брокер. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
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

        self._tasks: Dict[str, TaskExecSchema] = {}
        self.events: Optional["BaseEvents"] = events
        self.task_middlewares_before: List[Type[TaskMiddleware]] = []
        self.task_middlewares_after: List[Type[TaskMiddleware]] = []

        self.task_executor: Optional[Type["BaseTaskExecutor"]] = None

        self.plugins: Dict[str, List["BasePlugin"]] = {}

        self.num_workers = 0

        self.init_plugins()

    @overload
    def add(
        self: "BaseWorker[Literal[False]]",
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
        self: "BaseWorker[Literal[True]]",
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
    ) -> Union[None, Awaitable[None]]:
        """Добавление задачи в очередь.

        Args:
            name (str): Имя задачи.
            uuid (UUID): UUID задачи.
            priority (int): Приоритет задачи.
            created_at (float): Создание задачи в формате timestamp.
            args (tuple): Аргументы задачи типа args.
            kwargs (dict): Аргументы задачи типа kwargs.
        """
        pass

    @overload
    def start(
        self: "BaseWorker[Literal[False]]",
        num_workers: Annotated[
            Optional[int],
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
        self: "BaseWorker[Literal[True]]",
        num_workers: Annotated[
            Optional[int],
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
            Optional[int],
            Doc(
                """
                    Количество воркеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> Union[None, Awaitable[None]]:
        """Запускает несколько обработчиков задач. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        pass

    @overload
    def stop(self: "BaseWorker[Literal[False]]") -> None: ...

    @overload
    async def stop(self: "BaseWorker[Literal[True]]") -> None: ...

    @abstractmethod
    def stop(self) -> Union[None, Awaitable[None]]:
        """Останавливает воркеры. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
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
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return

    def add_plugin(
        self,
        plugin: Annotated[
            "BasePlugin",
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            Optional[List[str]],
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
        ] = None,
    ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    def init_plugins(self):
        """Инициализация плагинов."""
        pass
