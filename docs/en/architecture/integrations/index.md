# Integration with libraries

This section describes the architectural principles that allow QTasks to be integrated
with external libraries and frameworks without imposing strict conditions or restrictions.

Although QTasks is a full-fledged framework with its own rules for building applications,
its architecture is designed so that developers can integrate it into existing
systems on their own terms.

---
, its architecture is designed so that developers can integrate it into existing
systems on their own terms.

---

## QTasks architectural position

QTasks does not seek to be the "center of the world" for an application. It can
act as:

* as a standalone task processing server;
* as a built-in component within another framework;
* as an infrastructure layer serving multiple applications.

This is achieved through a minimal amount of global state and strict
isolation of components.

---

## Minimizing global state

In the QTasks architecture, global variables are used deliberately and to a
limited extent.

### Global reference to the application

The main default entry point is created via:

```python
app = QueueTasks()
```

When the application instance is initialized, `self._set_state()` is called,
resulting in:

* the global reference to the application is stored in `qtasks._state.app_main`;
* it is used as the default value in places where there is no explicit reference
to the application.

It is important to note that the presence of `app_main`
**is not a prerequisite for the system to work**.

In all cases where possible:

* tasks declared via `@app.task` receive a reference to a specific instance of
`app` directly;
* `(A)syncRouter` routers connected via `app.include_router(router)` also use an
explicit reference.

A global reference is only used in scenarios where the application instance has
not been explicitly passed, for example when using `@shared_task()`.

---

## Global logger

In addition to the reference to the application, QTasks has a single point of
aggregation for logging.

When the application is initialized in `_set_state()`, a global logger can also
be created:

* it is stored in `qtasks._state.logger_main`;
* it is based on the `qtasks.logs.Logger` class.

By default, the logger is initialized as follows:

```text
Logger(
    name=app.name,
    subname="QueueTasks",
    default_level=app.config.logs_default_level_server,
    format=app.config.logs_format,)

```

If there is no global logger, components and plugins that request a logger
must create their own instance based on the same class.

Thus, logging can be:

* centralized — if `logger_main` is present;
* local — if there is no global logger.

---

## Architectural implications for integrations

This approach to global state offers the following advantages:

* QTasks can be integrated into an existing project without conflicting global objects;
* integration with frameworks such as Django, FastAPI, or custom services does not
require rewriting the architecture;
* the developer controls where and how the application and logger are created;
* Multiple instances of QTasks can run within a single process.

---

## Purpose of this section

This section lays the architectural foundation for all subsequent pages dedicated
to specific integrations.

Next, we will discuss:

The following topics will be covered:

* Features of embedding QTasks into other frameworks;
* Application lifecycle management in a third-party environment;
* Typical architectural patterns of integration.

All of them are based on the principles described on this page.
