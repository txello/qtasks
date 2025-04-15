import asyncio
from typing import Optional
from typing_extensions import Annotated, Doc
from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from qtasks.asyncio import QueueTasks

from .base import BaseTimer


class AsyncTimer(BaseTimer):
    """
    Таймер, работающий через apscheduler, запускающий задачи.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.timers import AsyncTimer
    
    app = QueueTasks()
    timer = AsyncTimer(app=app)

    trigger = CronTrigger(second="*/10") # Запуск каждые 10 секунд
    timer.add_task("test", trigger=trigger, args=(2,))

    timer.run_forever()
    ```
    """
    
    def __init__(self, app):
        super().__init__(app=app)
        self.app: QueueTasks
        self.scheduler = AsyncIOScheduler()
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
        
        # Добавляем асинхронную задачу без вызова функции
        return self.scheduler.add_job(
            self._add_task_async,
            trigger=trigger,
            args=(task_name, priority, args, kwargs)
        )

    async def _add_task_async(self,
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
        """Запуск добавленной задачи асинхронно.
        
        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию `0`.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.
        """
        task = await self.app.add_task(task_name=task_name, priority=priority, args=args, kwargs=kwargs)
        print(f"[Timer] Отправлена задача {task_name}: {task.uuid}...")
    
    def run_forever(self):
        """Запуск Таймера."""
        print("[Timer] Запуск...")

        try:
            asyncio.run(self._start_scheduler())  # Запускаем асинхронную функцию в основном цикле
        except KeyboardInterrupt:
            print("[Timer] Остановка...")

    async def _start_scheduler(self):
        """Запуск Таймера асинхронно."""
        self.scheduler.start()  # Запускаем планировщик
        while True:
            await asyncio.sleep(1)  # Держим цикл событий активным