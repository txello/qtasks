# Example: Plugins

QTasks has a plugin system.
The system is based on calling **named** and **global** triggers.
For more information about triggers, see the [Plugin Trigger Reference](../api/plugins/triggers.md).

In addition to the main triggers, there is also an exception trigger inside the
task function.
Exception name: **`TaskPluginTriggerError`**.
It can be called like this:

```python
raise TaskPluginTriggerError("This is the reason")
```

or via the task context:

```python
self.ctx.plugin_error("This is the reason")
```

---

## ⚙️ How do triggers work?

* Triggers call the `trigger()` method inside the plugin.
* The call depends on whether a synchronous or asynchronous component initiated
the event.

---

## 📐 Abstract plugin class (ABC)

````python
"""Base Plugin."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from typing_extensions import Annotated, Doc

class BasePlugin(ABC):
    """
    `BasePlugin` — абстрактный класс, который является фундаментом для Плагинов.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.plugins.base import BasePlugin

    class MyPlugin(BasePlugin):
        def __init__(self, name: str = None):
            super().__init__(name=name)
            pass
    ```
    """

    def __init__(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Project name. This name can be used for Plugin tags.

                    Default: `None`.
                    """
            ),
        ] = None,
    ):
        self.name: Union[str, None] = name
        pass

    @abstractmethod
    def trigger(self, name: str, *args, **kwargs) -> Union[Dict[str, Any], None]:
        """Plugin trigger."""
        pass

@abstractmethod
def start(self, *args, **kwargs):
"""Starts the plugin."""
pass

@abstractmethod
def stop(self, *args, **kwargs):
"""Stops the plugin."""
        pass
````

---

## 🔧 Example of a user plugin

```python
from qtasks.plugins.base import BasePlugin

class TestPlugin(BasePlugin):
    def __init__(self, name=None):
        super().__init__(name)
        self.handlers = {
            "task_executor_run_task_trigger_error": self.task_trigger_error
        }

    async def start(self, *args, **kwargs):
        return super().start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
    return super().stop(*args, **kwargs)

    async def trigger(self, name, **kwargs):
        handler = self.handlers.get(name)
        if handler:
            return handler(**kwargs)
        return None

    def task_trigger_error(self, **kwargs):
        print(kwargs)
        return None
```

---

## ✅ Summary

* The plugin system in `QTasks` is based on **triggers**.
* Plugins can modify arguments, data, models, and task execution results.
* Exceptions via `TaskPluginTriggerError` allow you to replace the task result
and/or terminate tasks with a meaningful reason.
* The flexibility of the system allows you to connect both built-in plugins and
plugins from third-party developers.
