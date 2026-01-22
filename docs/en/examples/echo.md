# Example of using self and self.ctx (echo=True)

When `echo=True` is specified, the task receives the `self` object of type
`AsyncTask` or `SyncTask` as its first argument. This provides access to the
execution context `self.ctx`, internal task data, and control methods.

Below is an example task demonstrating all the capabilities of `self` and `self.ctx`.

---

## 🧩 Task example

```python
@app.task(
    echo=True, tags=["test"], priority=1,
    retry=3, retry_on_exc=[KeyError], decode=json.dumps,
    # generate_handler=yield_func, executor=MyTaskExecutor,
    # middlewares_before=[MyTaskMiddleware], middlewares_after=[MyTaskMiddleware],
    test="test"
)
async def test_echo_ctx(self: AsyncTask):
    # Get the logger (with the default task name)
    self.ctx.get_logger().info("This is a test task!")

    # Pause in the task (asynchronous)
    await self.ctx.sleep(5)

    # Get the current configuration
    self.ctx.get_logger().info(self.ctx.get_config())

    # Output all available task parameters
    self.ctx.get_logger().info(
        f"""
            UUID: {self.ctx.task_uuid}
            Name: {self.task_name}
            Tags: {self.tags}
            Priority: {self.priority}
            Extra parameters: {self.extra}

            Retries via parameter: {self.retry}
            Exceptions for retry: {self.retry_on_exc}
            Function for decorator: {self.ctx.generate_handler}

            Is self called: {self.echo}
            Decoding via parameter: {self.decode}

            TaskExecutor via parameter: {self.executor}
            Middleware: {self.middlewares}
""")


# Manually canceling the task
self.ctx.cancel("Test task canceled")
return "Hello, world!"
```

---

## 📦 Self capabilities

* `self.task_name`, `self.retry`, `self.tags`, `self.echo` — task parameters
* `await self.add_task(...)` — launch nested tasks
* `self.decode`, `self.executor`, `self.middlewares` — access to task arguments

---

## 🧠 self.ctx capabilities

* `self.ctx.get_logger()` — logger with the task name or a custom name
* `self.ctx.sleep(seconds)` — execution delay
* `self.ctx.cancel(reason)` — cancel task with `status=CANCEL` set
* `self.ctx.get_config()`, `get_component(name)`, `get_task(uuid)`, `get_metadata()`
— access to infrastructure and status

---

## ✅ Result in logs

**Client:**

```bash
Task(status='cancel', uuid=..., task_name='test_echo_ctx', ...,
cancel_reason='Test task canceled')
```

**Server:**

```bash
2025-07-16 ... (test_echo_ctx) This is a test task!...

UUID: ...
Name: test_echo_ctx
Tags: ['test']...

Task ... was canceled due to: Test task canceled
```

---

Using `self` and `self.ctx` makes the task not just a function, but a full-fledged
object capable of interacting with the QTasks system at all levels.
