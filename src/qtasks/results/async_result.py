"""Async Result."""

from typing import TYPE_CHECKING, Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import asyncio

from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks
    from qtasks.schemas.task import Task


class AsyncResult:
    """`AsyncResult` - Асинхронный класс для ожидания результата задачи.

    ## Пример

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
            Optional[Union[UUID, str]],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ] = None,
        app: Annotated[
            Optional["QueueTasks"],
            Doc(
                """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
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
    ):
        """Инициализация асинхронного результата.

        Args:
            uuid (UUID | str, optional): UUID задачи. По умолчанию: None.
            app (QueueTasks, optional): `QueueTasks` экземпляр. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
        """
        self._app = self._update_state()

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
    ) -> Union["Task", None]:
        """Ожидание результата задачи.

        Args:
            timeout (float, optional): Таймаут задачи. По умолчанию: `100`.

        Returns:
            Task | None: Задача или None.
        """
        self._stop_event.clear()
        try:
            result = await asyncio.wait_for(self._execute_task(), timeout)
            self.log.debug(f"Задача {result.uuid if result else None} выполнена!")
            return result
        except asyncio.TimeoutError:
            self.log.warning(f"Функция выполнялась {timeout} секунд!")
            self._stop_event.set()
            return None

    async def _execute_task(self) -> Union["Task", None]:
        if not self.uuid:
            raise ValueError("UUID задачи не задан.")

        uuid = self.uuid
        while True:
            if self._stop_event.is_set():
                break

            task = await self._app.get(uuid=uuid)

            if not task:
                self.log.warning(f"Задача {uuid} не найдена!")
                return None

            if task.retry and task.retry > 0 and task.retry_child_uuid:
                uuid = task.retry_child_uuid
                continue

            if not task or task.status not in self._app.config.result_statuses_end:
                await asyncio.sleep(self._app.config.result_time_interval)
                continue

            return task

    def _update_state(self) -> "QueueTasks":
        import qtasks._state

        if qtasks._state.app_main is None:
            raise ImportError("Невозможно получить app!")
        app = qtasks._state.app_main
        return app  # type: ignore
