# Diagrams

## Background diagram of framework connections

```mermaid
sequenceDiagram
  autonumber
  participant QueueTasks
  participant Starter
  participant Worker
  participant Broker
  participant Storage
  participant GlobalConfig

  QueueTasks->>Starter: Initialization / configuration
  Starter->>Worker: Start
  Starter->>Broker: Start
  Broker->>Storage: Initialization / start
  Storage->>GlobalConfig: Initialization (if any)

  GlobalConfig-->>Storage: Stop
  Storage-->>Broker: Stop
  Broker-->>Worker: Stop
  Starter-->>QueueTasks: Termination
```

This diagram shows the relationship between components and the correct startup order:

* Starter starts **only Worker and Broker**.
* Broker starts **Storage**.
* Storage starts **GlobalConfig**, if present.
* Shutdown occurs in reverse order.

---

## Task processing by the server

```mermaid
sequenceDiagram
  autonumber
  participant Storage
  participant Broker
  participant Worker
  participant TaskExecutor

  Broker->>Storage: Save new task
  Broker->>Worker: Transfer task
  Worker->>TaskExecutor: Execute task
  TaskExecutor-->>Worker: Execution result
  Worker->>Storage: Save result
```

This diagram reflects the actual process:

1. The task is saved in Storage.
2. The broker transfers the task to the worker.
3. Worker calls TaskExecutor — a replaceable task execution component.
4. TaskExecutor executes the task function, calls middlewares_before/middlewares_after,
handles errors and retries.
5. The result is transferred to the worker and saved in Storage.

---

## Task creation by the client

```mermaid
sequenceDiagram
  autonumber
  participant AT as (A)syncTask.add_task()
  participant QT as QueueTasks.add_task()
  participant Broker

  AT->>QT: Preparing task parameters
  QT->>Broker: Registering a new task
```

The process looks like this:

1. `(A)syncTask.add_task()` or `TaskCls().__call__().add_task()` prepares
the parameters.
2. Internally, everything is translated to `QueueTasks.add_task()`.
3. The broker accepts the task and saves it via Storage.

---

## Receiving the task result by the client

```mermaid
sequenceDiagram
  autonumber
  participant AT as (A)syncTask.add_task()
  participant AR as (A)syncResult.result()
  participant QT as QueueTasks
  participant Broker
  participant Storage

  AT->>AR: Create result object
  AR->>QT: Request result
  QT->>Broker: Proxy request
  Broker->>Storage: Read result
  Storage-->>Broker: Data
  Broker-->>QT: Result
  QT-->>AR: Return result
```

Steps:

1. `(A)syncTask.add_task()` creates `(A)syncResult`.
2. `(A)syncResult.result()` calls `QueueTasks`, which proxies the request.
3. `QueueTasks.get()` is redirected to `Broker.get()`.
4. Broker requests data from Storage.
5. Storage returns the result.
6. The result is sent back through Broker → QueueTasks → (A)syncResult.
