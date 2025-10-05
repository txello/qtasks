"""Async Test Plugin."""

from typing import Union
from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusProcessSchema
from qtasks.utils import _build_task


class AsyncTestPlugin(BasePlugin):
    """Плагин для асинхронной обработки тестов."""

    def __init__(self, name: str = "AsyncTestPlugin"):
        """Инициализация плагина.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "AsyncTestPlugin".
        """
        super().__init__(name=name)
        self.handlers = {
            "worker_execute_before": self.worker_execute_before,
            "worker_remove_finished_task": self.worker_remove_finished_task,
        }

    async def start(self, *args, **kwargs):
        """Запуск плагина."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина."""
        pass

    async def trigger(self, name, **kwargs):
        """Триггер для запуска обработчика."""
        handler = self.handlers.get(name)
        return (
            await handler(
                kwargs.get("task_func"), kwargs.get("task_broker"), kwargs.get("model")
            )
            if handler
            else None
        )

    async def worker_execute_before(self, *args, **kwargs):
        """Обработчик перед выполнением задачи."""
        result = await self._execute(*args, **kwargs)
        if not result:
            return
        return result.get("model")

    async def worker_remove_finished_task(self, *args, **kwargs):
        """Обработчик завершения задачи."""
        return await self._execute(*args, **kwargs)

    async def _execute(
        self,
        task_func: Union[TaskExecSchema, None],
        task_broker: Union[TaskPrioritySchema, None],
        model: TaskStatusProcessSchema,
    ):
        if (
            not task_func
            or "test" not in task_func.extra
            or not task_func.extra["test"]
        ):
            return
        model = _build_task(model, is_testing=task_func.extra["test"])  # type: ignore
        model.is_testing = str(model.is_testing)  # type: ignore
        return {"model": model}
