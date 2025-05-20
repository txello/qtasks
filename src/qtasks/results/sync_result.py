from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import TYPE_CHECKING
from uuid import UUID
import threading

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class SyncResult:
    def __init__(self,
            uuid: UUID|str,

            app: "QueueTasks" = None
        ):
        self._app = self._update_app(app)
        self._stop_event = threading.Event()

        self.uuid = uuid

    def result(self, timeout: float = 100) -> Task|None:
        self._stop_event.clear()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_task)
            try:
                result = future.result(timeout=timeout)
                return result
            except TimeoutError:
                print(f"[Timeout] Function exceeded {timeout} seconds")
                self._stop_event.set()
                return None

    def _execute_task(self) -> Task|None:
        while True:
            if self._stop_event.is_set():
                break

            task = self._app.get(uuid=self.uuid)
            if not task or task.status not in [TaskStatusEnum.SUCCESS.value, TaskStatusEnum.ERROR.value]:
                continue
            return task

    def _update_app(self, app: "QueueTasks" = None) -> "QueueTasks":
        if not app:
            import qtasks._state
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            return qtasks._state.app_main
        return app
