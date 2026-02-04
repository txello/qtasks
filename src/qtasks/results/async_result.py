"""Async Result."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Optional, Union
from uuid import UUID

from typing_extensions import Doc

from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.schemas.task import Task


class AsyncResult:
    """
    `AsyncResult` - Asynchronous class for waiting for the result of a task.

    ## Example

    ```python
    import asyncio

    from qtasks import QueueTasks
    from qtasks.results import AsyncResult

    app = QueueTasks()

    async def main():
        task = await app.add_task(task_name="test")
        result = await AsyncResult(uuid=task.uuid).result(timeout=50)

    asyncio.run(main())
    ```
    """

    def __init__(
        self,
        uuid: Annotated[
            UUID | str | None,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ] = None,
        app: Annotated[
            Optional[QueueTasks],
            Doc(
                """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
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
    ):
        """
        Initializing an asynchronous result.

        Args:
            uuid (UUID | str, optional): UUID of the task. Default: None.
            app (QueueTasks, optional): `QueueTasks` instance. Default: None.
            log (Logger, optional): Logger. Default: None.
        """
        self._app = app or self._update_state()

        self.log = (
            log.with_subname(
                "AsyncResult", default_level=self._app.config.logs_default_level_client
            )
            if log
            else Logger(
                name=self._app.name,
                subname="AsyncResult",
                default_level=self._app.config.logs_default_level_client,
                format=self._app.config.logs_format,
            )
        )
        self._stop_event = asyncio.Event()

        self.uuid = uuid

    async def result(
        self,
        timeout: Annotated[
            float,
            Doc(
                """
                    Таймаут задачи

                    По умолчанию: `100`.
                    """
            ),
        ] = 100,
    ) -> Union[Task, None]:
        """
        Waiting for the task result.

        Args:
            timeout (float, optional): Task timeout. Default: `100`.

        Returns:
            Task | None: Task or None.
        """
        self._stop_event.clear()
        try:
            result = await asyncio.wait_for(self._execute_task(), timeout)
            self.log.debug(f"Task {result.uuid if result else None} is completed!")
            return result
        except asyncio.TimeoutError:
            self.log.warning(f"Task timed out after {timeout} seconds!")
            self._stop_event.set()
            return None

    async def _execute_task(self) -> Union[Task, None]:
        if not self.uuid:
            raise ValueError("Task UUID is not set.")

        uuid = self.uuid
        while True:
            if self._stop_event.is_set():
                break

            task = await self._app.get(uuid=uuid)

            if not task:
                self.log.warning(f"Task {uuid} not found!")
                return None

            if task.retry and task.retry > 0 and task.retry_child_uuid:
                uuid = task.retry_child_uuid
                continue

            if not task or task.status not in self._app.config.result_statuses_end:
                await asyncio.sleep(self._app.config.result_time_interval)
                continue

            return task

    def _update_state(self) -> QueueTasks:
        import qtasks._state

        if qtasks._state.app_main is None:
            raise ImportError("qtasks app is not initialized.")
        app = qtasks._state.app_main
        return app  # type: ignore
