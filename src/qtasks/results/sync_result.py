"""Sync Result."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import TYPE_CHECKING, Optional
from typing_extensions import Annotated, Doc
from uuid import UUID
import threading

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class SyncResult:
    """`SyncResult` - Синхронный класс для ожидания результата задачи.

    ## Пример

    ```python

    from qtasks import QueueTasks
    from qtasks.results import SyncResult

    app = QueueTasks()

    task = app.add_task("test")
    result = SyncResult(uuid=task.uuid).result(timeout=50)
    ```
    """

    def __init__(
        self,
        uuid: Annotated[
            UUID | str,
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
        """Инициализация синхронного результата.

        Args:
            uuid (UUID | str, optional): UUID задачи. По умолчанию: None.
            app (QueueTasks, optional): `QueueTasks` экземпляр. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
        """
        self._app = app
        self.log = (
            log.with_subname("AsyncResult")
            if log
            else Logger(
                name=self._app.name,
                subname="AsyncResult",
                default_level=self._app.config.logs_default_level,
                format=self._app.config.logs_format,
            )
        )
        self._update_state()
        self._stop_event = threading.Event()

        self.uuid = uuid
        self._sleep_time: float = 1

    def result(
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
    ) -> Task | None:
        """Ожидание результата задачи.

        Args:
            timeout (float, optional): Таймаут задачи. По умолчанию: `100`.

        Returns:
            Task | None: Задача или None.
        """
        self._stop_event.clear()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_task)
            try:
                result = future.result(timeout=timeout)
                self.log.debug(f"Задача {result.uuid} выполнена!")
                return result
            except TimeoutError:
                self.log.warning(f"Функция выполнялась {timeout} секунд!")
                self._stop_event.set()
                return None

    def _execute_task(self) -> Task | None:
        uuid = self.uuid
        while True:
            if self._stop_event.is_set():
                break

            task = self._app.get(uuid=uuid)
            if not task or task.status not in [
                TaskStatusEnum.SUCCESS.value,
                TaskStatusEnum.ERROR.value,
                TaskStatusEnum.CANCEL.value,
            ]:
                time.sleep(self._sleep_time)
                continue
            if hasattr(task, "retry") and hasattr(task, "retry_child_uuid"):
                uuid = task.retry_child_uuid
                continue

            return task

    def _update_state(self) -> "QueueTasks":
        import qtasks._state

        if not self._app:
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
        if not self.log:
            self.log = qtasks._state.log_main.with_subname("AsyncResult")
