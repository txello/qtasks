"""Async timer for scheduling tasks."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, Literal

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger

from .base import BaseTimer

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks


class AsyncTimer(BaseTimer[Literal[True]]):
    """
    A timer running through apscheduler that starts tasks.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.timers import AsyncTimer

    app = QueueTasks()
    timer = AsyncTimer(app=app)

    trigger = CronTrigger(second="*/10") # Trigger every 10 seconds
    timer.add_task(task_name="test", trigger=trigger)

    timer.run_forever()
    ```
    """

    def __init__(
        self,
        app: Annotated[
            QueueTasks,
            Doc("""
                    Application.
                    """),
        ],
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

        self.scheduler = AsyncIOScheduler()
        self.tasks = {}

    def add_task(
        self,
        *args: Annotated[
            Any,
            Doc("""
                    args of the task.

                    Default: `()`.
                    """),
        ],
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int | None,
            Doc("""
                    The task has priority.

                    Default: Task priority value.
                    """),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc("""
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """),
        ] = None,
        trigger: Annotated[
            Any,
            Doc("""
                    Task trigger.
                    """),
        ],
        **kwargs: Annotated[
            Any,
            Doc("""
                    kwargs tasks.

                    Default: `{}`.
                    """),
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

        return self.scheduler.add_job(
            self._add_task_async,
            trigger=trigger,
            args=(task_name, priority, args, kwargs),
        )

    async def _add_task_async(
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
        args: Annotated[
            tuple | None,
            Doc("""
                    args of the task.

                    Default: `()`.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    kwargs tasks.

                    Default: `{}`.
                    """),
        ] = None,
    ):
        """
        Run the added task asynchronously.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default is `0`.
            args (tuple, optional): task args. Defaults to `()`.
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.
        """
        args, kwargs = args or (), kwargs or {}
        task = await self.app.add_task(
            *args, task_name=task_name, priority=priority, timeout=None, **kwargs
        )
        self.log.info(f"Task {task_name} sent with UUID: {task.uuid}")

    def run_forever(self):
        """Start Timer."""
        self.log.info("Starting...")
        try:
            asyncio.run(
                self._start_scheduler()
            )
        except KeyboardInterrupt:
            self.log.info("Stopping...")

    async def _start_scheduler(self):
        """Start Timer asynchronously."""
        self.scheduler.start()
        while True:
            await asyncio.sleep(1)
