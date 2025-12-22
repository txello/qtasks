# Integration with Django

This page describes the architectural principles of integrating QTasks with Django.
It is not about the user API, but about how QTasks is embedded in the Django
loading model and how tasks become available to the framework without a rigid
component link.

---

---

## Django architectural context

Django has its own application initialization model:

* the list of applications is defined via `INSTALLED_APPS`;
* modules are loaded when the Django process starts;
* The logic for registering signals, models, and tasks is often tied to the fact
that a module is imported.

The integration of QTasks with Django relies on these features and does not require
changing
the standard Django application lifecycle.

---

## Automatic task detection

For integration with Django, QTasks provides a mechanism for automatically importing
task modules.

```python
from qtasks.contrib.django import autodiscover_tasks

autodiscover_tasks(qtasks_app, ["tasks1", "tasks2"])
```

This mechanism allows QTasks to discover and register tasks declared within Django
applications without explicitly importing each module manually.

---

How autodiscover_tasks works

## How autodiscover_tasks works

The `autodiscover_tasks` function uses a Django architectural principle: all applications
listed in `INSTALLED_APPS` are already known to the system.

At a high level, the process looks like this:

1. A list of Django applications is obtained from `INSTALLED_APPS`.
2. For each application, an attempt is made to import the specified modules.
3. If the import is successful, the module code is executed.
4. Tasks declared in these modules are automatically registered in the passed
instance of `QueueTasks`.

Key point: QTasks **does not interfere** with the task registration process.
It only ensures that the modules are imported.

---

## autodiscover_tasks function contract

The function signature looks like this:

```python
def autodiscover_tasks(app, modules: Optional[list[str]] = None):
    """Automatically imports the specified modules from all INSTALLED_APPS to
    register tasks in QTasks.

    Args:
        app (QueueTasks): application.
        modules (List[str]): modules for autodiscovery.
            Default: ["tasks"].
    """
```

From an architectural point of view, the following is important:

* `app` is passed explicitly — integration does not rely on global state;
* the list of modules is configurable and not hard-coded;
* the function does not return data and does not affect the application lifecycle.

---

## Task registration

Task registration is done in the standard way for QTasks:

* when executing the `@app.task` decorator;
* when using routers connected to `app`.

`autodiscover_tasks` only ensures that the code with declarations will be executed
at the correct time.

Thus:

* Django manages application loading;
* QTasks manages task registration;
* The point of contact is the module import mechanism.

---

## Architectural advantages of the approach

This integration method offers several important advantages:

* No hard dependency of QTasks on Django;
* Preservation of the standard structure of Django projects;
* No global side effects.
* Ability to use multiple instances of QTasks.

The integration remains a thin layer between the systems, rather than an attempt
to merge their lifecycles.

---

## Boundaries of responsibility

* Django is responsible for discovering and loading applications;
* `autodiscover_tasks` is responsible for importing task modules;
* QTasks is responsible for registering and executing tasks.

Adhering to these boundaries allows QTasks to be used in Django projects without
violating the architecture of either system.
