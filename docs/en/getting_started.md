# Getting started with QTasks

## Quick start: your first task in a couple of minutes

Below is a minimal example of setting up and running QTasks for synchronous tasks,
as well as a brief guide on how to use the asynchronous version.

### 1. Creating an application instance

```py
from qtasks import QueueTasks
# for the asynchronous version:
# from qtasks.asyncio import QueueTasks

app = QueueTasks()
```

!!! info
    By default, Redis at `redis://localhost:6379/0` is used as the broker and storage.

### 2. Registering tasks

Tasks are registered using the [`@app.task`](api/registries/sync_task_decorator.md)
decorator.

```py
@app.task(name=“mytest”)  # Regular task
def mytest(text: str):
    print(text)
    return text


@app.task(name=“error_zero”)  # Task with an error
def error_zero():
    result = 1 / 0
    return
```

!!! info
    If the task name is not explicitly specified (`name` parameter), the function
    name is used.

!!! tip
    The task name can be anything, but it must be unique within the application.
    If a task with that name already exists, an exception will be raised during
    registration.

### 3. Running the task handler

There are two ways to start the task handler.

#### Option 1: via `run_forever()`

```py
if __name__ == “__main__”:
    app.run_forever()
```

#### Option 2: via CLI

```bash
qtasks -A app:app run
```

Where `app:app` is `module:variable`, i.e. the module with the application and
the variable that stores the `QueueTasks` instance.

### 4. Complete example of a file with tasks

```py
# file: app.py
from qtasks import QueueTasks


app = QueueTasks()


@app.task(name=“mytest”)  # Example of a normal task
def mytest(text: str):
    print(text)
    return text


@app.task(name=“error_zero”)  # Example of a task with an error
def error_zero():
    result = 1 / 0
    return


if __name__ == “__main__”:
    app.run_forever()
```

### 5. Adding tasks to the queue

After starting the task handler, you can add tasks from another file or from the
interactive Python interpreter:

```py
# file: add_tasks.py
from app import app, mytest

# Adding a task by name via an application instance
app.add_task(“mytest”, “Test”)

# Calling via a registered task function
mytest.add_task(“Test”)

# Adding a task with a timeout (in seconds)
mytest.add_task(“Test”, timeout=50)

# Adding a task that will result in an error
app.add_task(“error_zero”)
```

The `add_task` method supports positional and named arguments (`*args`, `**kwargs`)
that will be passed to the task function.

### 6. Asynchronous option (briefly)

The asynchronous option is configured similarly, but using
`qtasks.asyncio.QueueTasks` and `async` functions:

```py
from qtasks.asyncio import QueueTasks


app = QueueTasks()


@app.task(name=“mytest_async”)
async def mytest_async(text: str):
    print(text)
    return text


if __name__ == “__main__”:
    app.run_forever()
```

---

More about asynchronous tasks, `AsyncTask`, and the execution context:

<div class="result" markdown>
  <div class="grid cards" markdown>

- :fontawesome-solid-laptop-code:{ .lg .middle } __(A)syncTask__

    ---

    Learn more about converting @app.task

    [:octicons-arrow-right-24: Task decorator](features/task.md)

- :fontawesome-solid-plus:{ .lg .middle } __Task Context__

    ---

    Understand task execution context and its application

    [:octicons-arrow-right-24: Task context](features/contexts.md)

  </div>

</div>
