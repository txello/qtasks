"""Sync Test Plugin."""


from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusProcessSchema
from qtasks.utils import _build_task


class SyncTestPlugin(BasePlugin):
    """Plugin for synchronous test processing."""

    def __init__(self, name: str = "SyncTestPlugin"):
        """
        Initializing the plugin.
        
                Args:
                    name (str, optional): Project name. Default: "SyncTestPlugin".
        """
        super().__init__(name=name)
        self.handlers = {
            "worker_execute_before": self.worker_execute_before,
            "worker_remove_finished_task": self.worker_remove_finished_task,
        }

    def start(self, *args, **kwargs):
        """Launch the plugin."""
        pass

    def stop(self, *args, **kwargs):
        """Stopping the plugin."""
        pass

    def trigger(self, name, **kwargs):
        """Trigger to run the handler."""
        handler = self.handlers.get(name)
        return (
            handler(
                kwargs.get("task_func"), kwargs.get("task_broker"), kwargs.get("model")
            )
            if handler
            else None
        )

    def worker_execute_before(self, *args, **kwargs):
        """A handler before executing a task."""
        result = self._execute(*args, **kwargs)
        if result:
            return result.get("model")

    def worker_remove_finished_task(self, *args, **kwargs):
        """Task completion handler."""
        return self._execute(*args, **kwargs)

    def _execute(
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
