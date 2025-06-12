import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

from qtasks.exc.task import TaskCancelError

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.logs import Logger


class AsyncContext:
    def __init__(self, **kwargs):
        self.task_uuid = kwargs.get("task_uuid")
        self.generate_handler = kwargs.get("generate_handler")

        self._app: "QueueTasks" = kwargs.get("app")
        self._update_app()

        self._log: "Logger" = kwargs.get("log")

        self._metadata: dict = {}

    def get_logger(self, name: str|None = None) -> "Logger":
        self._log = self._app.log.with_subname(name or "AsyncContext")
        return self._log
    
    def get_config(self):
        return self._app.config
    
    async def get_metadata(self, cache=True):
        if cache:
            if not self._metadata:
                self._metadata = await self._app.get(self.task_uuid)
            return self._metadata
        return await self._app.get(self.task_uuid)
    
    async def get_task(self, uuid: UUID|str):
        return await self._app.get(uuid)
    
    async def sleep(self, seconds: float):
        await asyncio.sleep(seconds)

    def cancel(self, reason: str = ""):
        raise TaskCancelError(reason or "AsyncContext.cancel")
    
    def get_component(self, name: str):
        return getattr(self._app, name, None)
    
    def _update_app(self):
        if not self._app:
            import qtasks._state
            self._app = qtasks._state.app_main
        return

    def _update(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return
