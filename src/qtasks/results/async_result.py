from typing import TYPE_CHECKING
from uuid import UUID
import asyncio

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class AsyncResult:
    def __init__(self,
            uuid: UUID|str,

            app: "QueueTasks" = None
        ):
        self._app = self._update_app(app)
        self._stop_event = asyncio.Event()

        self.uuid = uuid
        self._sleep_time: float = 1

    async def result(self, timeout: float = 100) -> Task|None:
        self._stop_event.clear()
        try:
            async with asyncio.timeout(timeout):
                result = await self._execute_task()
            return result
        except asyncio.TimeoutError:
            print(f"[AsyncResult] Функция выполнялась {timeout} секунд!")
            self._stop_event.set()
            return None

    async def _execute_task(self) -> Task|None:
        while True:
            if self._stop_event.is_set():
                break

            task = await self._app.get(uuid=self.uuid)
            if not task or task.status not in [TaskStatusEnum.SUCCESS.value, TaskStatusEnum.ERROR.value]:
                await asyncio.sleep(self._sleep_time)
                continue
            return task

    def _update_app(self, app: "QueueTasks" = None) -> "QueueTasks":
        if not app:
            import qtasks._state
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            return qtasks._state.app_main
        return app
