# Error handling via plugins

QTasks provides a system for intercepting task errors via plugins. This allows
you to:

* centrally handle exceptions;
* return an alternative result in case of an error;
* implement custom logic (e.g., logging, notifications, recovery).

---

## 📌 Trigger used

**Trigger**: [`task_executor_run_task_trigger_error`](./triggers.md#taskexecutor)

* **Component**: `TaskExecutor`
* **Call**: occurs when a `TaskPluginTriggerError` exception occurs
* **Parameters**:
  * `task_executor` — TaskExecutor instance
  * `task_func` — task being executed
  * `task_broker` — task broker
  * `e` — instance of the `TaskPluginTriggerError` error

---

## 🧠 Handling mechanism

If the following is called in the task:

```python
self.ctx.plugin_error()
```

an exception will be thrown:

```python
from qtasks.exc import TaskPluginTriggerError

raise TaskPluginTriggerError(**kwargs)
```

Inside `TaskExecutor`, the exception will be handled as follows:

```python
try:
    self._result = await self.run_task()
except TaskPluginTriggerError as e:
    new_result = await self._plugin_trigger(
        "task_executor_run_task_trigger_error",
        task_executor=self,
        task_func=self.task_func,
        task_broker=self.task_broker,
        e=e,
        return_last=True
    )
    if new_result:
        self._result = new_result
    else:
        raise e
```

If at least one plugin returns a value, it will become the result of the task.
Otherwise, the exception is thrown further.

---

## 🔧 Example of a task with an error call

```python
from qtasks.exc import TaskPluginTriggerError

@app.task(echo=True)
async def test_task(self: AsyncTask):
    self.ctx.plugin_error(message="Non-standard situation")
    # Alternative: raise TaskPluginTriggerError("Direct error")
```

---

## 🔌 Processing in the plugin

```python
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
```

---

## 📘 Related resources

* 📄 [Component triggers](./triggers.md)
* ⚠️ [Exceptions](../exceptions.md)

---

The `plugin_error` system gives you control over error logic and can be used
as an extension point for task behavior.
