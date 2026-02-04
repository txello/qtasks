"""Base timer class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Union,
    overload,
)

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks
    from qtasks.qtasks import QueueTasks


class BaseTimer(Generic[TAsyncFlag], ABC):
    """
    `BaseTimer` - An abstract class that is the basis for Timers.

    ## Example

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
            Union[QueueTasks, aioQueueTasks],
            Doc(
                """
                    Задача.

                    По умолчанию: `{qtasks.QueueTasks}` или `{qtasks.asyncio.QueueTasks}`.
                    """
            ),
        ],
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
    ):
        """
        Timer initialization.

        Args:
            app (QueueTasks): Application.
            log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Config. Default: `qtasks.configs.config.QueueConfig`.
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
        self: BaseTimer[Literal[False]],
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
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
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
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Any | None: ...

    @overload
    async def add_task(
        self: BaseTimer[Literal[True]],
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
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
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
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Any | None: ...

    @abstractmethod
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
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
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
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Any | None | Awaitable[Any | None]:
        """
        Adding a task.

        Args:
            task_name (str): The name of the task.
            trigger (Any, optional): Trigger values.
            priority (int, optional): Task priority. Default is `0`.
            args (tuple, optional): task args. Defaults to `()`.
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.

        Returns:
            Any|None: Task.
        """
        pass

    def run_forever(self):
        """Start Timer."""
        pass
