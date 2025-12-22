# Depends

QTasks supports managed dependencies for tasks through the `Depends` mechanism.
It allows you to declare task parameters so that their values are automatically
created and correctly cleared in the appropriate context.

---

## Example of using Depends

```python
from typing import Annotated
from contextlib import asynccontextmanager

from qtasks.plugins.depends import Depends, ScopeEnum


@asynccontextmanager
async def test_dep():
    print("Open")
    yield 123
    print("Close")


@app.task
async def test(dep: Annotated[int, Depends(test_dep, scope=ScopeEnum.TASK)]):
    print(dep)
```

When the task is executed, the output will be as follows:

```text
Open
123
Close
```

What happens:

* When the task starts, the `test_dep()` context opens.
* The value `123` is passed to the task body.
* When the task finishes, the context closes and `Close` is printed.

---

## How Depends works "under the hood"

The Depends mechanism is implemented in a built-in worker plugin — `(A)syncDependsPlugin`.
Below is a simplified description of the steps.

### 1. Searching for Depends in task parameters

When preparing to execute a task, the plugin:

* checks for the presence of `Depends` as an explicit parameter value (`dep = Depends(...)`);
* or searches for it inside `Annotated[..., Depends(...)]` (takes the last element
of `Annotated`).

If `Depends` is found, the task is marked as having a dependency.

### 2. Creating a context via (Async)ExitStack

`AsyncExitStack` (or `ExitStack` for synchronous tasks) is used to manage the
dependency lifecycle:

1. The plugin enters the `test_dep()` context via the context manager stack.
2. The value obtained from `yield` (in the example — `123`) is saved as a parameter
value.

### 3. Processing the scope (lifetime of the dependency)

The dependency lives in a specific "scope" defined by `ScopeEnum`:

```python
class ScopeEnum(Enum):
    TASK = "task"
    WORKER = "worker"
    BROKER = "broker"
    STORAGE = "storage"
    GLOBAL_CONFIG = "global_config"
```

Logic:

* `TASK` — the context opens when the task starts and closes when it finishes.
* The other options (`WORKER`, `BROKER`, `STORAGE`, `GLOBAL_CONFIG`) link
the context to the component resource.

Technically, this is implemented through triggers:

* `TASK` — closes on the `task_executor_task_close` trigger;
* the rest — on component completion triggers: `"{component}_stop"`.

### 4. Task argument substitution

After receiving a value from the dependency function, the plugin:

* replaces the task parameter (`dep`) with the result of `test_dep()`;
* the task receives a ready-made value (for example, an open connection, a
session object,
a number, a config, etc.).

---

## Why Depends is needed

Depends solves the problem of managed dependencies:

* creating and closing resources in the right context
(at the task or component level);
* no need to manually work with context managers inside
the body of tasks;
* a single point of description of dependencies for different tasks.

This is a convenient way to embed a connection to a database, an external service
client, a cache, a config,
and other resources into QTasks tasks so that their lifecycle is controlled by
the framework.
