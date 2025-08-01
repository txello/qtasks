"""Async Result."""

from typing import TYPE_CHECKING, Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import asyncio

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class AsyncResult:
    """`AsyncResult` - Асинхронный класс для ожидания результата задачи.

    ## Пример

    ```python
    import asyncio

    from qtasks import QueueTasks
    from qtasks.results import AsyncResult

    app = QueueTasks()

    async def main():
        task = await app.add_task("test")
        result = await AsyncResult(uuid=task.uuid).result(timeout=50)

    asyncio.run(main())
    ```
    """

    def __init__(
        self,
        uuid: Annotated[
            Union[UUID, str],
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
        self._app = app
        self._update_state()
        self.log = (
            log.with_subname("AsyncResult", default_level=self._app.config.logs_default_level_client)
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
        self._sleep_time: float = 1

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
        """Ожидание результата задачи.

        Args:
            timeout (float, optional): Таймаут задачи. По умолчанию: `100`.

        Returns:
            Task | None: Задача или None.
        """
        self._stop_event.clear()
        try:
            result = await asyncio.wait_for(self._execute_task(), timeout)
            self.log.debug(f"Задача {result.uuid} выполнена!")
            return result
        except asyncio.TimeoutError:
            self.log.warning(f"Функция выполнялась {timeout} секунд!")
            self._stop_event.set()
            return None

    async def _execute_task(self) -> Union[Task, None]:
        uuid = self.uuid
        while True:
            if self._stop_event.is_set():
                break

            task = await self._app.get(uuid=uuid)
            if hasattr(task, "retry") and task.retry > 0:
                if hasattr(task, "retry_child_uuid"):
                    uuid = task.retry_child_uuid
                    continue
            if not task or task.status not in [
                TaskStatusEnum.SUCCESS.value,
                TaskStatusEnum.ERROR.value,
                TaskStatusEnum.CANCEL.value,
            ]:
                await asyncio.sleep(self._sleep_time)
                continue
            return task

    def _update_state(self) -> "QueueTasks":
        import qtasks._state

        if not self._app:
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            self._app = qtasks._state.app_main
