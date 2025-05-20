from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import TYPE_CHECKING
from typing_extensions import Annotated, Doc
from uuid import UUID
import threading

from qtasks.enums.task_status import TaskStatusEnum
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

    def __init__(self,
            uuid: Annotated[
                UUID|str,
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ] = None,

            app: Annotated[
                "QueueTasks",
                Doc(
                    """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
                    """
                )
            ] = None
        ):
        self._app = self._update_app(app)
        self._stop_event = threading.Event()

        self.uuid = uuid
        self._sleep_time: float = 1

    def result(self,
            timeout: Annotated[
                float,
                Doc(
                    """
                    Таймаут задачи

                    По умолчанию: `100`.
                    """
                )
            ] = 100
        ) -> Task|None:
        """Ожидание результата задачи.

        Args:
            timeout (float, optional): Таймаут задачи. По умолчанию: `100`.

        Returns:
            Task|None: Задача или None.
        """

        self._stop_event.clear()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_task)
            try:
                result = future.result(timeout=timeout)
                return result
            except TimeoutError:
                print(f"[SyncResult] Функция выполнялась {timeout} секунд!")
                self._stop_event.set()
                return None

    def _execute_task(self) -> Task|None:
        while True:
            if self._stop_event.is_set():
                break

            task = self._app.get(uuid=self.uuid)
            if not task or task.status not in [TaskStatusEnum.SUCCESS.value, TaskStatusEnum.ERROR.value]:
                time.sleep(self._sleep_time)
                continue
            return task

    def _update_app(self, app: "QueueTasks" = None) -> "QueueTasks":
        if not app:
            import qtasks._state
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            return qtasks._state.app_main
        return app
