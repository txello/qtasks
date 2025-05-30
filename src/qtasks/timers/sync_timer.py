from time import sleep
from typing import TYPE_CHECKING, Optional
from typing_extensions import Annotated, Doc
from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from .base import BaseTimer
from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks import QueueTasks



class SyncTimer(BaseTimer):
    """
    Таймер, работающий через apscheduler, запускающий задачи.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.timers import SyncTimer
    
    app = QueueTasks()
    timer = SyncTimer(app=app)

    trigger = CronTrigger(second="*/10") # Запуск каждые 10 секунд
    timer.add_task("test", trigger=trigger, args=(2,))

    timer.run_forever()
    ```
    """

    def __init__(self,
            app,
            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None
        ):
        super().__init__(app=app, log=log)
        self.app: "QueueTasks"
        self.scheduler = BackgroundScheduler()
        self.tasks = {}

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
                CronTrigger,
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
        ) -> Job:
        """Добавление задачи.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию `0`.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

        Returns:
            Any|None: Задача.
        """
        self.tasks[task_name] = trigger

        # Добавляем синхронную задачу
        return self.scheduler.add_job(
            self._add_task_sync,
            trigger=trigger,
            args=(task_name, priority, args, kwargs)
        )

    def _add_task_sync(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Название задачи.
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
        ):
        """Запуск добавленной задачи синхронно.
        
        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию `0`.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.
        """
        task = self.app.add_task(task_name=task_name, priority=priority, args=args, kwargs=kwargs)
        self.log.info(f"Отправлена задача {task_name}: {task.uuid}...")

    def run_forever(self):
        """Запуск Таймера."""
        self.log.info(f"Запуск...")

        try:
            self.scheduler.start()  # Запускаем планировщик
            while True:
                sleep(1)
                pass  # Держим основной поток активным
        except KeyboardInterrupt:
            self.log.info("Остановка...")
            self.scheduler.shutdown()
