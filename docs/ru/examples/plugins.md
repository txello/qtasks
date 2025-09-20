# Пример: Плагины

У `QTasks` существует система плагинов.
Система строится на вызове **именных** и **глобальных** триггеров.
Подробнее о триггерах указано в [Справочнике триггеров плагинов](/qtasks/ru/api/plugins/triggers/).

Помимо основных триггеров также существует триггер на исключение внутри функции задачи.
Название исключения: **`TaskPluginTriggerError`**.
Его можно вызвать так:

```python
raise TaskPluginTriggerError("Это причина")
```

или через контекст задачи:

```python
self.ctx.plugin_error("Это причина")
```

---

## ⚙️ Как работают триггеры?

* Триггеры вызывают метод `trigger()` внутри плагина.
* Вызов зависит от того, синхронный или асинхронный компонент инициировал событие.

---

## 📐 Абстрактный класс плагина (ABC)

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
                    Имя проекта. Это имя можно использовать для тегов для Плагинов.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        self.name: Union[str, None] = name
        pass

    @abstractmethod
    def trigger(self, name: str, *args, **kwargs) -> Union[Dict[str, Any], None]:
        """Триггер плагина."""
        pass

    @abstractmethod
    def start(self, *args, **kwargs):
        """Запускает плагин."""
        pass

    @abstractmethod
    def stop(self, *args, **kwargs):
        """Останавливает плагин."""
        pass
````

---

## 🔧 Пример пользовательского плагина

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

## ✅ Итоги

* Система плагинов в `QTasks` основана на **триггерах**.
* Плагины могут изменять аргументы, данные, модели и результат выполнения задач.
* Исключения через `TaskPluginTriggerError` позволяют заменять результат задачи
и/или завершать задачи с осмысленной причиной.
* Гибкость системы позволяет подключать как встроенные плагины, так и плагины
сторонних разработчиков.
