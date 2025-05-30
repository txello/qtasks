from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import Annotated, Doc
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from qtasks.configs.config import QueueConfig
from qtasks.configs.config_observer import ConfigObserver
from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks import QueueTasks

class BaseTimer(ABC):
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
    
    def __init__(self,
            app: Annotated[
                "QueueTasks",
                Doc(
                    """
                    Задача.
                    
                    По умолчанию: `{qtasks.QueueTasks}` или `{qtasks.asyncio.QueueTasks}`.
                    """
                )
            ],

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
                Optional[ConfigObserver],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.configs.config_observer.ConfigObserver`.
                    """
                )
            ] = None
        ):
        self.app = app
        self.config = config or self.app.config
        self.log = log.with_subname("Timer") if log else Logger(name=self.app.name, subname="Timer", default_level=self.config.logs_default_level, format=self.config.logs_format)
        self.scheduler = AsyncIOScheduler()
        
    @abstractmethod
    def add_task(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Название задачи.
                    """
                )
            ],
            trigger: Annotated[
                Any,
                Doc(
                    """
                    Триггер задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0,
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
            ] = None
        ) -> Any|None:
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