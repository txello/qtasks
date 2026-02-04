"""Sync timer for scheduling tasks."""
from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Annotated, Any, Literal

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger

from .base import BaseTimer

if TYPE_CHECKING:
    from qtasks import QueueTasks


class SyncTimer(BaseTimer[Literal[False]]):
    """
    A timer running through apscheduler that starts tasks.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.timers import SyncTimer
    
        app = QueueTasks()
        timer = SyncTimer(app=app)
    
        trigger = CronTrigger(second="*/10") # Trigger every 10 seconds
        timer.add_task(task_name="test", trigger=trigger)
    
        timer.run_forever()
        ```
    """

    def __init__(
        self,
        app: Annotated[
            QueueTasks,
            Doc(
                """
                    Приложение.
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
        super().__init__(app=app, log=log, config=config)
        self.app: QueueTasks
        self.scheduler = BackgroundScheduler()
        self.tasks = {}

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
    ) -> Job:
        """
        Adding a task.
        
                Args:
                    task_name (str): The name of the task.
                    priority (int, optional): Task priority. Default is `0`.
                    args (tuple, optional): task args. Defaults to `()`.
                    kwargs (dict, optional): kwags tasks. Defaults to `{}`.
        
                Returns:
                    Any|None: Task.
        """
        self.tasks[task_name] = trigger

        # Добавляем синхронную задачу
        return self.scheduler.add_job(
            self._add_task_sync,
            trigger=trigger,
            args=(task_name, priority, args, kwargs),
        )

    def _add_task_sync(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Название задачи.
                    """
            ),
        ],
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.

                    По умолчанию: `0`.
                    """
            ),
        ] = 0,
        args: Annotated[
            tuple | None,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ] = None,
    ):
        """
        Run the added task synchronously.
        
                Args:
                    task_name (str): The name of the task.
                    priority (int, optional): Task priority. Default is `0`.
                    args (tuple, optional): task args. Defaults to `()`.
                    kwargs (dict, optional): kwags tasks. Defaults to `{}`.
        """
        args, kwargs = args or (), kwargs or {}
        task = self.app.add_task(
            *args, task_name=task_name, priority=priority, timeout=None, **kwargs
        )
        self.log.info(f"Отправлена задача {task_name}: {task.uuid}...")

    def run_forever(self):
        """Start Timer."""
        self.log.info("Запуск...")

        try:
            self.scheduler.start()  # Запускаем планировщик
            while True:
                sleep(1)
                pass  # Держим основной поток активным
        except KeyboardInterrupt:
            self.log.info("Остановка...")
            self.scheduler.shutdown()
