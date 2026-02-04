# Integration with Django

Currently, QTasks implements one main integration feature with Django: **autodiscover_tasks**.

---

## 📌 What does autodiscover_tasks do?

This function automatically imports the specified modules (e.g., `tasks.py`) from
all applications listed in `INSTALLED_APPS`.
This way, tasks are registered in QTasks without the need for manual connection.
Function signature:

```python
def autodiscover_tasks(app, modules: List[str] = ["tasks"]):
    """Automatically imports the specified modules from all INSTALLED_APPS
    to register tasks in QTasks.

    Args:
        app (QueueTasks): application.
        modules (List[str]): Modules for autodiscovery. Default: ["tasks"].
"""
```

📖 A detailed description is available in [API → autodiscover_tasks](../../api/libraries/django.md).

---

## 🔧 How to use

In `settings.py`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "myapp",  # tasks.py will be here
]
```

In `myapp/tasks.py`:

```python
from qtasks import QueueTasks

app = QueueTasks()

@app.task
def hello(name: str):
    return f"Hello, {name}!"
```

In `manage.py` or the main module of the project:

```python
from qtasks.contrib.django import autodiscover_tasks
from qtasks import QueueTasks

app = QueueTasks()
autodiscover_tasks(app)
```

After calling `autodiscover_tasks(app)`, all tasks from `tasks.py` will be automatically
registered and available for execution.

---

## ✅ Summary

* `autodiscover_tasks` searches for `tasks.py` (or other modules, if specified)
in all `INSTALLED_APPS` applications.
* This simplifies the integration of QTasks into Django projects.
* There is no need to manually register tasks — simply create them in `tasks.py`
within each application.
