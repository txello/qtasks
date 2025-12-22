# Contexts — Task contexts

During execution, each QTasks task gains access to the execution context — the
**(A)syncContext** object. The context provides a safe and unified way for the
task to interact with the application environment, worker, plugins, and
execution metadata.

The context is accessible via `self.ctx` inside the `(A)syncTask` object.

The context is accessible via `self.ctx` inside the `(A)syncTask` object.

---

## Passing the context to the task function

The context can be passed directly to the task function using the `echo=True` parameter
in the `@app.task` decorator.

```python
@app.task(echo=True)
async def my_task(self):
    print(self.ctx.task_name)
```

In this case:

* the first argument of the function is passed as a **duplicated (A)syncContext**;
* the parameter name can be anything;
* for convenience and consistency, it is recommended to use the name `self`.

The context is added at the task execution stage and does not affect its registration.

---

## Purpose of the context

(A)syncContext is intended for:

* accessing the current task data;
* interacting with the application (`QueueTasks`);
* working with logging;
* managing execution (sleep, cancel);
* interacting with plugins and triggers;
* obtaining metadata and configuration.

The context does not contain business logic and serves solely as an interface for
the execution environment.

---

### Task generation (yield)

* `self.ctx.generate_handler` — generation handler function for yield tasks.

Used in conjunction with the decorator parameter:

```python
@app.task(generate_handler=gen_func)
```

---

### Logging

```python
self.ctx.get_logger(name: str | None = None)
```

Returns an instance of `qtasks.logs.Logger` associated with the task.

* If `name` is not specified, `task_name` is used.
* If the task name is missing, `(A)syncContext` is used.

---

### Configuration and metadata

* `self.ctx.get_config()` — returns `app.config`.

* `self.ctx.get_metadata(cache: bool = True)` — returns task metadata via
`app.get(self.ctx.task_uuid)`.

When `cache=True`, the result is cached within the context and repeated calls do
not access
the storage.

---

### Working with tasks

* `self.ctx.get_task(uuid: UUID | str)` — returns the task via `app.get(uuid)`.

---

### Managing execution

* `self.ctx.sleep(seconds: float)` — calls `time.sleep` or `asyncio.sleep` depending
on the task type.
* `self.ctx.cancel(reason: str = "")` — initiates task cancellation by raising:

```python
raise TaskCancelError(reason or f"{self.ctx.task_name}.cancel")
```

```python
raise TaskCancelError(reason or f"{self.ctx.task_name}.cancel")
```

The cancellation is handled by the worker as a correct completion of the task.

---

### Interaction with plugins

* `self.ctx.plugin_error(**kwargs)` — throws `TaskPluginTriggerError(**kwargs)`.

Used to notify plugins that have a trigger:

```py
task_executor_run_task_trigger_error
```

---

### Accessing application components

* `self.ctx.get_component(name: str)` — equivalent to `getattr(app, name, None)`.
Allows you to access any registered QTasks component.

---

## app source

The `app` instance enters the context in one of the following ways:

* at the task execution stage via `TaskExecutor`, which complements `(A)syncTask`
and its `ctx`;
* via the global reference `qtasks._state.app_main`, if the task was called outside
the explicit context.

This provides unified access to the application regardless of the launch scenario.

---

## Summary

(A)syncContext:

* is the task execution environment interface;
* isolates business logic from infrastructure;
* provides access to configuration, logs, and metadata;
* is used to manage the task lifecycle;
* serves as a point of integration with plugins and components.

The page is designed as a canvas and can be used as basic documentation for
context, echo tasks, and QTasks plugin mechanisms.
