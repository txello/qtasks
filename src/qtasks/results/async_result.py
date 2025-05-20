from typing import TYPE_CHECKING
from typing_extensions import Annotated, Doc
from uuid import UUID
import asyncio

from qtasks.enums.task_status import TaskStatusEnum
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
        self._stop_event = asyncio.Event()

        self.uuid = uuid
        self._sleep_time: float = 1

    async def result(self,
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
