# Extensibility

This page describes QTasks' architectural approach to extensibility: the mechanisms
by which the system adapts to new scenarios, scales, and integrates with external
libraries and frameworks.

Extensibility in QTasks is determined not by the number of settings, but by the
structure of the architecture: a set of components, their contracts, and the
ability to implement additional behavior.

Extensibility in QTasks is determined not by the number of settings, but by the
structure of the architecture:
a set of components, their contracts, and the ability to implement additional
behavior through plugins.

---

## Basic principle of extensibility

QTasks was originally designed so that extension occurs **through composition**,
rather than through modification.

The main factors of extensibility are:

* replacing or adding components;
* using plugins;
* complying with abstract class contracts;
* transferring data through schemas.

Settings play a secondary role and are not the primary mechanism for scaling
or integration.

---

## Scaling through components

QTasks components are oriented towards horizontal scaling by default.

This means that the system assumes:

* duplication of server instances of the application;
* collaboration between multiple workers;
* use of a common broker and storage.

Changing the scaling model is achieved not through configuration flags, but through:

* replacing specific component implementations;
* changing their behavior using plugins;
* implementing custom load balancing strategies.

Thus, scaling becomes an architectural decision rather than a configuration setting.

---

## Plugins as an extension mechanism

Plugins in QTasks are used to introduce additional behavior into existing
execution flows.

Plugins can be used to:

* modify the task lifecycle;
* implement logging, metrics, and tracing;
* change the execution strategy without changing components;
* add integration layers.

Plugins do not violate architectural invariants and do not require changes to
component contracts.

---

## Integration with external libraries

QTasks allows integration with external libraries and frameworks with minimal
restrictions.

This is achieved by:

* the absence of signals and global dispatchers;
* minimal use of global variables;
* strict separation of responsibilities between components;
* transparent execution threads;
* explicit lifecycle management.

As a result, QTasks can be used as a background task execution system
within other applications without imposing its own management model on them.

---

## Example of integration with FastAPI

Below is an architectural example of using QTasks together with FastAPI.

### Defining tasks

```python
# tasks.py
from qtasks import AsyncRouter

router = AsyncRouter()

@router.task()
async def example_task(x: int, y: int) -> int:
    return x + y
```

### Using a task in the API

```python
# api.py
from fastapi import FastAPI
from .tasks import example_task

app = FastAPI()

@app.get("/")
async def read_root():
    task = await example_task.add_task(1, 2, timeout=50)
    return {"result": task.returning}
```

### QTasks server

```python
# qtasks_app.py
from qtasks.asyncio import QueueTasks
from .tasks import router as tasks_router

app = QueueTasks()
app.include_router(tasks_router)

if __name__ == "__main__":
    app.run_forever()
```

---

## Architectural analysis of the example

In this scenario:

* The API calls the task directly through the task object received from the router;
* The call is made through a broker (e.g., Redis), without a direct connection
to the QTasks server;
* The API waits for the result via `AsyncResult`, since `timeout` is specified;
* The QTasks server can run in another process or on another node;
* The server knows about the task thanks to `include_router`, rather than through
a hard link to the API.

The client only needs to pass the task to the broker—the rest of the processing
happens independently.

---

## About context management and global variables

The example above uses direct access to the task through the router.

If you want to avoid global variables, the task can be declared via `@app.task`.
In this case:

* the reference to `app` is stored inside `AsyncTask`;
* `AsyncResult` is automatically linked to the required application instance;
* the task call remains transparent to the client.
This emphasizes that the choice of integration model is an architectural decision
made by the user,
This emphasizes that the choice of integration model is an architectural decision
made by the user, not a limitation of QTasks.

---

## Architectural invariants

* Extensibility is achieved through components and plugins.
* Scalability is a consequence of architecture, not configuration.
* QTasks does not impose its control model on external applications;
* integrations do not require intervention in the system core.

This model allows QTasks to be used as a basis for complex and non-standard
scenarios without losing controllability.
