"""Web App Plugin for QTasks."""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from qtasks.plugins.base import BasePlugin

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks


class TaskRequest(BaseModel):
    """Запрос на выполнение задачи."""

    name: str
    args: Optional[list[Any]] = []
    kwargs: Optional[dict[str, Any]] = {}
    timeout: Optional[int] = None


class AsyncWebAppPlugin(BasePlugin):
    """Плагин для запуска веб-приложения поверх QTasks."""

    def __init__(self, app: "QueueTasks", host: str = "127.0.0.1", port: int = 8080):
        """Инициализация плагина."""
        super().__init__(name="AsyncWebAppPlugin")
        self.app: QueueTasks = app
        self.host = host
        self.port = port
        self._server = None
        self._task = None

        # FastAPI app
        self._api = FastAPI()

        @self._api.post("/run-task")
        async def run_task(req: TaskRequest):
            """Запуск задачи через HTTP."""
            result = await self.app.add_task(
                *req.args or (),
                task_name=req.name,
                **req.kwargs or {},
                timeout=req.timeout
            )
            if result:
                return {
                    "task_id": result.uuid,
                    "status": result.status,
                    "returning": result.returning,
                    "error": result.traceback,
                }

        @self._api.get("/health")
        async def health():
            return {"status": "ok"}

    async def start(self, *args, **kwargs):
        """Запуск FastAPI-сервера в фоне."""
        config = uvicorn.Config(self._api, host=self.host, port=self.port, log_level="info")
        self._server = uvicorn.Server(config)

        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._server.serve())

    async def stop(self, *args, **kwargs):
        """Остановка FastAPI-сервера."""
        if self._server and self._server.started:
            self._server.should_exit = True
        if self._task:
            await self._task

    async def trigger(self, name, **kwargs):
        """Пустой триггер (не используется)."""
        pass
