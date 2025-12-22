# QueueTasks Components

The framework is built on a component-based architecture: each element of the system
is responsible for its own part of the work and can be replaced, extended,
or redefined. This page provides an overview of all the main and additional components,
without going into depth on the internal logic.

---

## Main components

### QueueTasks

The central object of the framework. It manages task registration, configures the
execution environment, and connects the other components.

When an instance of `QueueTasks()` is created, the following are automatically formed:

* Broker (Redis by default)
* Storage (Redis)
* GlobalConfig (Redis)
* Worker (SyncThreadWorker or AsyncWorker)
* Starter (SyncStarter or AsyncStarter)

```py
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="test")
def sample_task(id: int):
    return f"User {id} recorded"
```

QueueTasks can accept connection URLs (`broker_url`, `storage_url`) as well as
fully custom components.

---

### Broker — incoming task handler

Responsible for receiving tasks and passing them to the worker. By default, a
Redis broker is used.

```py
from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRedisBroker

broker = AsyncRedisBroker(url="redis://localhost:6379/2")

app = QueueTasks(broker=broker)
```

The broker uses Storage and, if necessary, GlobalConfig.

---

### Worker — task executor

Executes tasks received from the broker. Supports synchronous (`SyncThreadWorker`)
and asynchronous (`AsyncWorker`) modes.

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker

broker = AsyncRedisBroker(url="redis://localhost:6379/2")
worker = AsyncWorker(broker=broker)

app = QueueTasks(broker=broker, worker=worker)
```

The worker interacts with the task context, retry logic, middleware, and plugins.

---

### Storage — task data storage

Stores information about tasks:

* status,
* result,
* errors,
* execution time.

It is a mandatory component, but can be replaced. Broker contains a link to Storage
inside itself.

```py

```py
from qtasks.asyncio import QueueTasks
from qtasks.storages import AsyncRedisStorage
from qtasks.brokers import AsyncRedisBroker

storage = AsyncRedisStorage(url="redis://localhost:6379/2")
broker = AsyncRedisBroker(url="redis://localhost:6379/2", storage=storage)

app = QueueTasks(broker=broker)
```

The storage also contains a link to GlobalConfig.

---

### Starter — controls the launch of components

Starter is responsible for launching and stopping all components. QueueTasks uses
Starter by default.

Starter can also control the execution flow scenarios of components.

```py
from qtasks.asyncio import QueueTasks
from qtasks.starters import AsyncStarter

starter = AsyncStarter(name="QueueTasks")
app = QueueTasks()

if __name__ == "__main__":
    app.run_forever(starter=starter)
```

---

## Additional components

### GlobalConfig — global configuration

Storage of global variables and settings available to all components.
Used, for example, when working with WebView: the interface can connect to Redis
without launching the application.

```py
from qtasks.asyncio import QueueTasks
from qtasks.configs import AsyncRedisGlobalConfig

config = AsyncRedisGlobalConfig(url="redis://localhost:6379/2")
app = QueueTasks(global_config=config)
```

GlobalConfig is available as:

```py
app.broker.storage.global_config
```

and can be `None`.

---

### Plugins — extending functionality

Plugins allow you to connect any additional logic: logging, modification
of task arguments, integrations.

All available triggers are described here: [Triggers](api/plugins/triggers.md)

Example:

```py
from qtasks import QueueTasks
from qtasks.plugins import BasePlugin

app = QueueTasks()

class TestPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.handlers = {
            "task_executor_args_replace": self.replace
        }

    def replace(self, **kwargs):
        print("ARGS:", kwargs)
        return None

app.add_plugin(
    TestPlugin(),
    trigger_names=["task_executor_args_replace"],
    component="worker")

```

---

### Timer — running tasks on a schedule

A separate component that allows you to use cron-like schedules.
Uses APScheduler (`CronTrigger`).

```py
from qtasks import QueueTasks
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

app = QueueTasks()

@app.task
def test():
    print("Running test task")


trigger = CronTrigger(second="*/10")
timer = AsyncTimer(app=app)
timer.add_task("test", trigger=trigger)

timer.run_forever()
```

---

### WebView — visual interface

A separate library for viewing the list of tasks, results, and statistics.
Installation:

```bash
pip install qtasks_webview
```

WebView works directly with Redis and does not require the application to be running.

---

## Complete example of manual assembly of all components

```py
import asyncio
from qtasks.asyncio import QueueTasks
from qtasks.configs import AsyncRedisGlobalConfig
from qtasks.storages import AsyncRedisStorage
from qtasks.brokers import AsyncRedisBroker
from qtasks.workers import AsyncWorker
from qtasks.starters import AsyncStarter

# GlobalConfig — global variables and settings
global_config = AsyncRedisGlobalConfig(
    name="QueueTasks",
    url="redis://localhost:6379/2"
)

# Storage — task storage
storage = AsyncRedisStorage(
    name="QueueTasks",
    global_config=global_config,
    url="redis://localhost:6379/2")


# Broker — incoming task handler
broker = AsyncRedisBroker(
    name="QueueTasks",
    storage=storage,
    url="redis://localhost:6379/2")


# Worker — task executor
worker = AsyncWorker(
    name="QueueTasks",
    broker=broker
)

# QueueTasks — main object
app = QueueTasks(
    name="QueueTasks",
    broker=broker,
    worker=worker)


# Application settings
app.config.max_tasks_process = 10
app.config.running_older_tasks = True
app.config.delete_finished_tasks = True


@app.task(name="test")
async def sample_task(id: int):
    result = f"User {id} recorded"
    await asyncio.sleep(id)
    return result


if __name__ == "__main__":
    starter = AsyncStarter(
        name="QueueTasks",
        worker=worker,
        broker=broker
    )
    app.run_forever(starter=starter)
```
