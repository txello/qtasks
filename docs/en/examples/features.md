# Features of QTasks tasks

Tasks in QTasks are not just functions. They are extensible objects with context,
their own behavior, support for middleware, retry mechanisms, generator-based
pipelines, and a dependency system.
This page provides an overview of the capabilities available through the `@app.task`
and `@shared_task` decorators.

---

## 📦 shared_task — tasks outside the application

`shared_task` allows you to register tasks **outside** the `QueueTasks` application
instance
— useful for libraries, reusable modules, and code that needs to work in different
projects.

```python
from qtasks import shared_task

@shared_task()
def shared_func():
    print("Shared task")
```

### Converting shared_task to an asynchronous task

If you specify `awaiting=True`, the task returns `AsyncTask`, even if the
environment is "synchronous":

```python
@shared_task(awaiting=True)
async def async_shared():
    print("async shared task")
```

`shared_task` supports all `@app.task` parameters:

* `executor`
* `middlewares_before` / `middlewares_after`
* `generate_handler`
* `echo`
* `retry`, `retry_on_exc`
* `priority`, `tags`, `description`
* `decode`

---

## 🔀 Task routing: (A)syncRouter

Router allows you to connect sets of tasks to an application, separate logic by
modules, and reuse code.

```python
from qtasks import AsyncRouter

router = AsyncRouter()

@router.task()
async def example():
    print("Router task")
```

In the application file:

```python
app.include_router(router)
```

The router only registers tasks and passes them to the application registry.

---

## 📣 echo=True and access to self (A)SyncTask

If you specify `echo=True`, the task receives the **task** object as its first argument:

* `AsyncTask` for async
* `SyncTask` for sync

```python
@app.task(echo=True)
async def echo_task(self):
    print(self.task_name)
```

### `self` capabilities

Each task has the following fields:

| Attribute                 | Value                       |
| ------------------------- | --------------------------- |
| `self.task_name`          | Task name                   |
| `self.priority`           | Priority (default 0)        |
| `self.echo`               | Echo mode flag              |
| `self.max_time`           | Maximum execution time      |
| `self.retry`              | Number of retries           |
| `self.retry_on_exc`       | List of exceptions for retry|
| `self.decode`             | Result decoder              |
| `self.middlewares_before` | Middleware before execution |
| `self.middlewares_after`  | Middleware after execution  |
| `self.extra`              | Any additional parameters   |

This allows you to implement nested tasks:

```python
@app.task(echo=True)
async def main(self):
    self.add_task("subtask", 123)
```

---

## 🧠 Task context: self.ctx

Context is an API for interacting with the QTasks infrastructure.

```python
@app.task(echo=True)
def show(self):
    print(self.ctx.task_uuid)
```

### Context capabilities

| Method                              | Description                               |
| ----------------------------------- | ------------------------------------------|
| `self.ctx.task_uuid`                | Task UUID                                 |
| `self.ctx.get_logger(name)`         | Logger for the task                       |
| `self.ctx.get_config()`             | Application config                        |
| `self.ctx.get_metadata(cache=True)` | Task metadata (result of `app.get()`)     |
| `self.ctx.get_task(uuid)`           | Get another task                          |
| `self.ctx.sleep(sec)`               | Delay (async/ sync sleep)                 |
| `self.ctx.cancel(reason)`           | Task cancellation (TaskCancelError)       |
| `self.ctx.plugin_error(**kwargs)`   | Artificial plugin error call              |
| `self.ctx.get_component(name)`      | Getting a component (broker, storage, ...)|

The context allows you to implement complex logic without global variables and
singleton structures.

---

## 🔁 retry and retry_on_exc

Retry a task on error:

```python
@app.task(retry=5, retry_on_exc=[ZeroDivisionError])
def risky():
    return 1 / 0
```

* `retry=5` — number of retries
* `retry_on_exc=[...]` — list of exceptions that trigger a retry

---

## ⚙️ executor — custom task handler

Allows you to replace the internal execution mechanism:

```python
class MyExec:
    ...

@app.task(executor=MyExec)
def task():
    ...
```

Executor controls:

* task execution,
* middleware,
* result decoding,
* retry process,
* error handling.

---

## 🧩 Middleware

Middleware is called BEFORE and AFTER task execution.

```python
@app.task(
    middlewares_before=[MyBefore],
    middlewares_after=[MyAfter])

def example():
    pass
```

If middleware is not specified, empty lists are used.

---

## 🔁 Support for yield and generate_handler

QTasks supports generator-based tasks.

```python
@app.task(generate_handler=handler)
def mytask():
    step = yield "INIT"
    return step
```

`handler(result)` is called on each value passed through `yield`.

This allows you to implement streaming pipelines:

* step-by-step processing,
* streaming,
* progress logging,
* communication between the worker and the executor.

---

## 🪢 awaiting=True (only for shared_task)

The `awaiting=True` option forces a shared task to always run asynchronously.

```python
@shared_task(awaiting=True)
async def async_shared():
    ...
```

---

These features make QTasks a powerful tool that can be adapted
to any infrastructure and architectural style.
