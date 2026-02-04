# The uniqueness of QTasks

QTasks is not just an alternative to Celery or RQ. It is a framework with a different
approach to task queue architecture: flexible, modular, and expansion-oriented.
Below are the key features that set it apart.

---

## 🧬 Component-based architecture

* All key elements (Broker, Worker, Storage, GlobalConfig, Starter,
TaskExecutor, etc.) are fully replaceable.
* Components can be rewritten for your own infrastructure without changing the core.
* Extensions are connected via plugins and starters.

> 🆚 **Celery:** monolithic bundle.
> **QTasks:** independent components with a plug-and-play approach.

---

## 🔁 Support for `yield` in tasks

Allows you to build step-by-step, streamlined scenarios.

* Support for generators in tasks.
* Processing of `yield` results via `generate_handler`.
* The final `return` value is returned as a normal task result.

```python
@app.task(generate_handler=handler)
def task():
    step = yield "INIT"
    return step
```

> 🆚 Most frameworks do not support generator-based tasks.

---

## 🧠 Echo and access to the task via `self`

When `echo=True` is enabled, the task becomes a `Task` (Async/Sync) object, which
opens access to the infrastructure:

* `self.add_task()` — creating nested tasks
* `self.ctx.get_logger()` — contextual logger
* `self.ctx.cancel()` — terminating a task early
* `self.ctx.get_task()` — getting another task by UUID

> 🆚 In other frameworks, a task is a simple function without a self context.

---

## ⚙️ Execution context (ctx)

The task context provides:

* Task UUID
* Access to Broker, Storage, GlobalConfig
* metadata manipulation (`get_metadata()`)
* safe sleep (`ctx.sleep()`)
* task cancellation (`cancel()`)

This allows you to build complex scenarios without global variables and third-party
singletons.

---

## 🔗 State and Depends

### **State**

Thread-safe storage of intermediate data between tasks.

```python
from qtasks.plugins import AsyncState

class MyState(AsyncState):
    pass

@app.task
def sample(state: MyState):
    ...
```

### **Depends**

Injecting dependencies into tasks:

```python
@app.task
def job(data: int, db=Depends(connect_db, scope="worker")):
    return db.save(data)
```

Scopes include:

* task
* worker
* broker
* storage
* global_config

> QTasks automatically creates and completes dependencies for the specified scope.

---

## 🧩 Plugins and starters

* Plugins can be attached to any events (triggers) within the system.
* You can extend the behavior of Worker, Broker, Storage, and TaskExecutor.
* Starters manage the lifecycle of components and allow you to implement custom
flow scenarios.

> 🆚 Celery requires monkeypatching or deep modification.

---

## ⏱ Timers without a separate service

The built-in `AsyncTimer` runs tasks on a schedule:

* cron logic via `apscheduler`
* integration with the application without a separate process such as Celery Beat

---

## 🛠 Minimal dependencies, easy to start

* Can work without Redis and brokers — via in-memory queue.
* Launch:

```bash
python main.py
qtasks -A app:app run
```

* Simplicity allows QTasks to be used in microservices, automation, and freelance
projects.

---

## 🚀 Performance

* 0.6–0.7 seconds per task with Redis.
* Asynchronous processing via `PriorityQueue` and `anyio.Semaphore`.
* Low overhead even for large volumes of tasks.

---

## 🧪 Testing infrastructure

* `SyncTestCase` and `AsyncTestCase` replace components for isolated testing.
* Works without running a worker.
* Supports `pytest`, `unittest`, `pytest-asyncio`.

---

## 💡 Suitable for any level of developer

* **Junior:** simplicity of API
* **Middle:** plugins, middleware, TaskManager
* **Senior:** component replacement, context management, custom executors
* **Lead:** monitoring, scaling, system architecture on QTasks

---

QTasks is a constructor that allows you to assemble a framework for your tasks:
from a small script to a distributed service.
