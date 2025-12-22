# QTasks Features

QTasks is a modern task queue framework built around the ideas of
**full extensibility**, **minimalist architecture**, and **ease of use**.
It is equally well suited for small projects and large distributed infrastructures.

This page describes the key features of the framework, including its unique
architectural features.

---

## Simple and quick setup

* Register tasks via `@app.task` — synchronous and asynchronous.
* Native support for `asyncio` without GIL restrictions.
* Easy application connection via CLI: `qtasks -A app:app run`.
* Flexible configuration: default parameters or custom components.

---

## Unique architectural features

### 🔧 Component-based architecture

Every element of the system can be replaced:

* Broker
* Worker
* Storage
* GlobalConfig
* Starter
* TaskExecutor

This allows QTasks to be adapted to any scenario: in-memory testing,
distributed systems, custom brokers, alternative executors.

### ⚙️ Fully replaceable **TaskExecutor**

The task execution logic is isolated in a separate class. It can be replaced via:

```python
@app.task(executor=MyTaskExecutor)
```

This gives control over:

* error handling,
* retry strategies,
* middleware,
* custom execution pipelines.

---

## Working with tasks

### ✔️ Support for `yield` in tasks

QTasks allows you to use generators in tasks.

```python
@app.task(generate_handler=gen_handler)
def mytask():
    value = yield "step1"
    return value
```

`gen_handler(result)` accepts *the value passed through yield*, and the result of
`return` is returned to the task.

This allows you to build step-by-step task execution scenarios.

### ✔️ Depends support

The Depends plugin allows you to embed dependencies in tasks.

```python
@app.task
def process(data: int, db=Depends(get_db, scope="worker")):
    return db.save(data)
```

Scopes:

* `task`
* `worker`
* `broker`
* `storage`
* `global_config`

The framework automatically creates and correctly closes the dependency context.

### ✔️ State support

A thread-safe way to transfer data between tasks.

```python
from qtasks.plugins import AsyncState

class MyState(AsyncState):
    pass

@app.task
def sample(state: MyState):
    ...
```

State allows a task to safely transfer intermediate data in stages.

---

## Integration with message brokers

* Redis — the main supported broker.
* RabbitMQ — available through additional installation.
* Kafka — also supported.

Brokers are easy to connect:

```python
app = QueueTasks(broker_url="redis://localhost:6379/0")
```

If necessary, you can pass your own broker implementation.

---

## Extensibility and plugins

QTasks provides a multi-level trigger system:

* for task execution,
* for argument changes,
* for result changes,
* for events within components.

Plugins are easy to add:

```python
app.add_plugin(MyPlugin(), trigger_names=["task_executor_args_replace"], component="worker")
```

The framework supports the creation of additional tools: gRPC task transfer,
unified middleware, Depends, State.

---

## Scalability

QTasks scales horizontally thanks to a simple, reliable model:

> "Whoever takes the task first, processes it."

This ensures:

* multiple workers running simultaneously;
* natural load balancing;
* distributed task execution without complex algorithms.

---

## Asynchronous task processing

Asynchronous mode has the following advantages:

* high performance;
* thread safety (using Semaphore and PriorityQueue);
* task context encapsulation;
* easy integration into other frameworks.

Asynchronous tasks are declared as:

```python
@app.task
async def handler(x: int):
    return x * 2
```

---

## Monitoring and statistics

(Description of analytics — on a separate page.)

Features include:

* `(A)syncStats` for obtaining application and task statistics;
* outputting statistics via CLI: `qtasks stats inspect ...`.

---

These features make QTasks more than just a task queue; it is a flexible and extensible
framework that can be easily adapted to real-world business scenarios.
