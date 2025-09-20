"""Sync Result."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import TYPE_CHECKING, Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import threading

from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.schemas.task import Task


class SyncResult:
    """`SyncResult` - Синхронный класс для ожидания результата задачи.

    ## Пример

    ```python

    from qtasks import QueueTasks
    from qtasks.results import SyncResult

    app = QueueTasks()

    task = app.add_task(task_name="test")
    result = SyncResult(uuid=task.uuid).result(timeout=50)
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
        """Инициализация синхронного результата.

        Args:
            uuid (UUID | str, optional): UUID задачи. По умолчанию: None.
            app (QueueTasks, optional): `QueueTasks` экземпляр. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
        """
        self._app = app
        self._update_state()
        self.log = (
            log.with_subname("SyncResult", default_level=self._app.config.logs_default_level_client)
            if log
            else Logger(
                name=self._app.name,
                subname="SyncResult",
                default_level=self._app.config.logs_default_level_client,
                format=self._app.config.logs_format,
            )
        )
        self._stop_event = threading.Event()

        self.uuid = uuid

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
    ) -> Union["Task", None]:
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

    def _execute_task(self) -> Union["Task", None]:
        uuid = self.uuid
        while True:
            if self._stop_event.is_set():
                break

            task = self._app.get(uuid=uuid)
            if hasattr(task, "retry") and hasattr(task, "retry_child_uuid"):
                uuid = task.retry_child_uuid
                continue
            if not task or task.status not in self._app.config.result_statuses_end:
                time.sleep(self._app.config.result_time_interval)
                continue

            return task

    def _update_state(self) -> "QueueTasks":
        import qtasks._state

        if not self._app:
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            self._app = qtasks._state.app_main
