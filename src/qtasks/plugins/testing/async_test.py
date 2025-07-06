"""Async Test Plugin."""

from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusProcessSchema
from qtasks.utils import _build_task


class AsyncTestPlugin(BasePlugin):
    """Плагин для асинхронной обработки тестов."""

    def __init__(self,
                 name: str = "AsyncTestPlugin"
                 ):
        """Инициализация плагина.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "AsyncTestPlugin".
        """
        super().__init__(name=name)
        self.handlers = {
            "worker_execute_before": self._execute,
            "worker_remove_finished_task": self._execute
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
        return await handler(kwargs.get("task_func"), kwargs.get("task_broker"), kwargs.get("model")) if handler else None

    async def _execute(
        self,
        task_func: TaskExecSchema | None,
        task_broker: TaskPrioritySchema | None,
        model: TaskStatusProcessSchema,
    ) -> TaskStatusErrorSchema:
        if not task_func or "test" not in task_func.extra or not task_func.extra["test"]:
            return
        model = _build_task(model, is_testing=str(task_func.extra["test"]))
        return task_broker, model
