"""Base timer class."""

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Generic,
    Literal,
    Optional,
    Union,
    overload,
)
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks


class BaseTimer(Generic[TAsyncFlag], ABC):
    """
    `BaseTimer` - Абстрактный класс, который является фундаментом для Таймеров.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.timers.base import BaseTimer

    class MyTimer(BaseTimer):
        def __init__(self, app: QueueTasks):
            super().__init__(app=app)
            pass
    ```
    """

    def __init__(
        self,
        app: Annotated[
            Union["QueueTasks", "aioQueueTasks"],
            Doc(
                """
                    Задача.

                    По умолчанию: `{qtasks.QueueTasks}` или `{qtasks.asyncio.QueueTasks}`.
                    """
            ),
        ],
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
    ):
        """Инициализация таймера.

        Args:
            app (QueueTasks): Приложение.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.config.QueueConfig`.
        """
        self.app = app
        self.config = config or self.app.config
        self.log = (
            log.with_subname("Timer")
            if log
            else Logger(
                name=self.app.name,
                subname="Timer",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )

    @overload
    def add_task(
        self: "BaseTimer[Literal[False]]",
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
        trigger: Annotated[
            Any,
            Doc(
                """
                    Триггер задачи.
                    """
            ),
        ],
        **kwargs: Annotated[
            Optional[dict],
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Optional[Any]: ...

    @overload
    async def add_task(
        self: "BaseTimer[Literal[True]]",
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
        trigger: Annotated[
            Any,
            Doc(
                """
                    Триггер задачи.
                    """
            ),
        ],
        **kwargs: Annotated[
            Optional[dict],
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Optional[Any]: ...

    @abstractmethod
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
        trigger: Annotated[
            Any,
            Doc(
                """
                    Триггер задачи.
                    """
            ),
        ],
        **kwargs: Annotated[
            Optional[dict],
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Union[Optional[Any], Awaitable[Optional[Any]]]:
        """Добавление задачи.

        Args:
            task_name (str): Имя задачи.
            trigger (Any, optional): Значения триггера.
            priority (int, optional): Приоритет задачи. По умолчанию `0`.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

        Returns:
            Any|None: Задача.
        """
        pass

    def run_forever(self):
        """Запуск Таймера."""
        pass
