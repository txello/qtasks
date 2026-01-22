# Task decorator

The `@app.task` decorator is the key point for registering tasks in QTasks. When
the decorator is applied, the task function is converted into a management object
that stores both the task metadata and the methods for calling and executing it.

When a task is registered, two related views are generated:

When a task is registered, two related representations are formed:

* **(A)syncTask** — the user interface of the task, through which
`add_task` calls and execution control are performed.
* **TaskExecSchema** — a dataclass used inside `app.tasks` and `app.worker.tasks`
to transfer and store executable task information, including the function itself.

Both objects contain a consistent set of data, but are used at different levels
of the system.

---

## General model

For further description, we will assume that `task_func` is a function wrapped by
the `@app.task()` decorator.

```python
@app.task()
async def task_func(...):
    ...
```

After registration, `task_func` ceases to be a regular function and becomes an
instance of **(A)syncTask**.

---

## Task parameters

The `@app.task` decorator accepts the following task configuration parameters:

| Parameter           | Type                                    | Description                                                                       |
| --------------------| --------------------------------------- | --------------------------------------------------------------------------------- |
| `name`              | `str, optional`                         | Task name. Default: `func.__name__`.                                              |
| `priority`          | `int, optional`                         | Task priority. Default: `config.task_default_priority`.                           |
| `echo`              | `bool, optional`                        | Adds AsyncTask as the first parameter. Default: `False`.                          |
| `max_time`          | `float, optional`                       | Maximum task execution time in seconds. Default: `None`.                          |
| `retry`             | `int, optional`                         | Number of attempts to retry the task. Default: `None`.                            |
| `retry_on_exc`      | `List[Type[Exception]], optional`       | Exceptions that will cause the task to be retried. Default: `None`.               |
| `decode`            | `Callable, optional`                    | Decoder for the task result. Default: `None`.                                     |
| `tags`              | `List[str], optional`                   | Task tags. Default: `None`.                                                       |
| `description`       | `str, optional`                         | Task description. Default: `None`.                                                |
| `generate_handler`  | `Callable, optional`                    | Handler generator. Default: `None`.                                               |
| `executor`          | `Type["BaseTaskExecutor"], optional`    | `BaseTaskExecutor` class. Default: `AsyncTaskExecutor`.                           |
| `middlewares_before`| `List[Type["TaskMiddleware"]], optional`| Middlewares that will be executed before the task. Default: `Empty array`.        |
| `middlewares_after` | `List[Type["TaskMiddleware"]], optional`| Middleware that will be executed after the task. Default: `Empty array`.          |
| `**kwargs`          | -                                       | Additional task parameters. Passed as extra in `(A)syncTask` and `TaskExecSchema`.|

---

## (A)syncTask

(A)syncTask is a wrapper object over a task and provides an API for calling it
and pre-configuring it.

### Pre-building a task

```python
cls = task_func(*args, **kwargs, priority=0, timeout=None)
```

In this case:

* arguments and parameters are saved in advance;
* an instance of **(A)syncTaskCls** (a descendant of `BaseTaskCls`) is created;
* the object is a dataclass and contains all the data necessary to queue the task.

Such an object can be passed, modified, or called later.

---

### Calling a task

There are two equivalent ways to start a task:

```python
task_func.add_task(*args, **kwargs, priority=0, timeout=None)
```

or

```python
cls.add_task()
```

In both cases, `app.add_task` is called:

* either through `app`, passed at the time of creating `(A)syncTask`;
* or through `qtasks._state.app_main`, if the task was called outside the explicit
context of the application.

This allows tasks to be used both within the application and in isolated modules.

---

### Waiting for a result (timeout)

The `timeout: float | None` parameter determines the behavior of the task call.

* If `timeout is None`, `add_task` immediately returns a `Task` object with
status `new`.
* If `timeout` is specified, the call is blocked until the result is received and
returns an
`(A)syncResult` object.

The wait ends when one of the final statuses specified in the
application configuration is reached:

```python
app.config.result_statuses_end = [
    TaskStatusEnum.SUCCESS.value,
    TaskStatusEnum.ERROR.value,
    TaskStatusEnum.CANCEL.value,
]
```

---

## TaskExecSchema

`TaskExecSchema` is a dataclass used to transfer tasks between
QTasks components.

It stores:

* task name;
* priority;
* execution parameters;
* reference to the task function;
* additional metadata.

`TaskExecSchema` instances are created when a task is registered and are
available in:

* `app.tasks`;
* `app.worker.tasks`.

Worker uses `TaskExecSchema` to actually execute the task.

---

## Separation of responsibilities

This separation allows you to:

* isolate the user API from internal execution;
* safely transfer tasks between components;
* extend the task model through plugins and schemas;
* support synchronous and asynchronous modes without duplicating logic.

---

## Summary

The `@app.task` decorator:

* registers the function as a QTasks task;
* creates an `(A)syncTask` object to manage calls;
* forms `TaskExecSchema` for internal execution;
* provides flexible control over launch parameters and result waiting.

The page is designed as a canvas and can be used as basic material for sections
about tasks, context, and execution.
