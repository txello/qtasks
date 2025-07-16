from qtasks.asyncio import QueueTasks
from qtasks.exc import TaskPluginTriggerError
from qtasks.plugins.base import BasePlugin
from qtasks.registries import AsyncTask


app = QueueTasks()


class TestPlugin(BasePlugin):
    def __init__(self, name=None):
        super().__init__(name)

        self.handlers = {
            "task_executor_run_task_trigger_error": self.task_trigger_error
        }

    async def start(self, *args, **kwargs):
        return super().start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        return super().stop(*args, **kwargs)

    async def trigger(self, name, **kwargs):
        handler = self.handlers.get(name)
        if handler:
            return handler(**kwargs)
        return None

    def task_trigger_error(self, **kwargs):
        print(kwargs)
        return 123


app.add_plugin(TestPlugin(), trigger_names=["task_executor_run_task_trigger_error"], component="worker")


@app.task(echo=True)
async def test_task(self: AsyncTask):
    self.ctx.plugin_error()
    # raise TaskPluginTriggerError("Test error")


if __name__ == "__main__":
    app.run_forever()
