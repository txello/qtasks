"""Async Test Plugin."""


from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusProcessSchema
from qtasks.utils import _build_task


class AsyncTestPlugin(BasePlugin):
    """Plugin for asynchronous test processing."""

    def __init__(self, name: str = "AsyncTestPlugin"):
        """
        Initializing the plugin.

        Args:
            name (str, optional): Project name. Default: "AsyncTestPlugin".
        """
        super().__init__(name=name)
        self.handlers = {
            "worker_execute_before": self.worker_execute_before,
            "worker_remove_finished_task": self.worker_remove_finished_task,
        }

    async def start(self, *args, **kwargs):
        """Launch the plugin."""
        pass

    async def stop(self, *args, **kwargs):
        """Stopping the plugin."""
        pass

    async def trigger(self, name, **kwargs):
        """Trigger to run the handler."""
        handler = self.handlers.get(name)
        return (
            await handler(
                kwargs.get("task_func"), kwargs.get("task_broker"), kwargs.get("model")
            )
            if handler
            else None
        )

    async def worker_execute_before(self, *args, **kwargs):
        """A handler before executing a task."""
        result = await self._execute(*args, **kwargs)
        if not result:
            return
        return result.get("model")

    async def worker_remove_finished_task(self, *args, **kwargs):
        """Task completion handler."""
        return await self._execute(*args, **kwargs)

    async def _execute(
        self,
        task_func: TaskExecSchema | None,
        task_broker: TaskPrioritySchema | None,
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
