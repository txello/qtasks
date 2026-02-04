"""Async context for tasks."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, NoReturn, Union
from uuid import UUID

from qtasks.configs.config import QueueConfig
from qtasks.exc.plugins import TaskPluginTriggerError
from qtasks.exc.task import TaskCancelError

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.logs import Logger
    from qtasks.schemas.task import Task


class AsyncContext:
    """
    Context associated with asynchronous tasks.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.registries import AsyncTask

    app = QueueTasks()

    @app.task(echo=True)
    async def my_task(self: AsyncTask):
        self.ctx #AsyncContext
    ```
    """

    def __init__(self, **kwargs):
        """Initializing the context."""
        self.task_name = kwargs.get("task_name")
        """Имя задачи."""

        self.task_uuid: UUID | str | None = kwargs.get("task_uuid")
        """UUID задачи."""

        self.generate_handler = kwargs.get("generate_handler")
        """Функция-генератор для создания задач."""

        self._app: QueueTasks = kwargs.get("app", self._update_app())
        """Приложение, к которому принадлежит задача."""

        self._log: Logger = kwargs.get("log", self._update_logger())
        """Логгер."""

        self._metadata: Task | None = None
        """Метаданные задачи."""

    def get_logger(self, name: str | None = None) -> Logger:
        """
        Returns a logger for the current context.

        Args:
            name (str|None): Logger name. If not specified, the task name or `AsyncContext` is used.

        Returns:
            Logger: Logger for the current context.
        """
        self._log = self._log.with_subname(name or self.task_name or "AsyncContext")
        return self._log

    def get_config(self) -> QueueConfig:
        """
        Returns the application configuration.

                Returns:
                    QueueConfig: Application configuration.
        """
        return self._app.config

    async def get_metadata(self, cache=True) -> Union[Task, None]:
        """
        Returns task metadata.

        Args:
            cache (bool): Use cached metadata.

        Returns:
            Task|None: Task metadata or None if not found.

        Raises:
            ValueError: Если Task UUID is not set.
        """
        if not self.task_uuid:
            raise ValueError("Task UUID is not set.")

        if cache:
            if not self._metadata:
                self._metadata = await self._app.get(self.task_uuid)
            return self._metadata
        return await self._app.get(self.task_uuid)

    async def get_task(self, uuid: UUID | str) -> Union[Task, None]:
        """
        Returns the task by UUID.

        Args:
            uuid (UUID|str): UUID of the task.

        Returns:
            Task|None: Task or None if not found.
        """
        return await self._app.get(uuid)

    async def sleep(self, seconds: float) -> None:
        """
        Pauses execution for the specified number of seconds.

        Args:
            seconds (float): Number of seconds to pause.
        """
        await asyncio.sleep(seconds)

    def cancel(self, reason: str = "") -> NoReturn:
        """
        Cancels the task.

        Args:
            reason (str): Reason for canceling the task.

        Raises:
            TaskCancelError: The exception thrown when a task is canceled.
        """
        raise TaskCancelError(reason or f"{self.task_name}.cancel")

    def plugin_error(self, **kwargs):
        """
        Causes a plugin error.

        Args:
            **kwargs: Arguments to pass to the plugin error handler.
        """
        raise TaskPluginTriggerError(**kwargs)

    def get_component(self, name: str):
        """
        Returns the application component by name.

        Args:
            name (str): Component name.

        Returns:
            Any: Application component or None if not found.
        """
        return getattr(self._app, name, None)

    def _update_app(self):
        """Updates the application for the current context."""
        import qtasks._state

        app = qtasks._state.app_main  # type: ignore
        return app

    def _update_logger(self) -> Logger:
        if self._app and self._app.log:
            log = self._app.log.with_subname(self.task_name or "AsyncContext")
        else:
            import qtasks._state

            log = qtasks._state.log_main.with_subname(self.task_name or "AsyncContext")
        return log

    def _update(self, **kwargs):
        """
        Updates context attributes.

        Args:
            kwargs (dict, optional): New context attribute values.
        """
        for name, value in kwargs.items():
            setattr(self, name, value)
        return
