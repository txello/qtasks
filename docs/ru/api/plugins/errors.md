# Обработка ошибок через плагины

В QTasks предусмотрена система перехвата ошибок задач через плагины. Это позволяет:

* централизованно обрабатывать исключения;
* возвращать альтернативный результат при ошибке;
* внедрять кастомную логику (например, логирование, уведомления, восстановление).

---

## 📌 Используемый триггер

**Триггер**: [`task_executor_run_task_trigger_error`](./triggers.md)

* **Компонент**: `TaskExecutor`
* **Вызов**: происходит при возникновении исключения `TaskPluginTriggerError`
* **Параметры**:

  * `task_executor` — экземпляр TaskExecutor
  * `task_func` — выполняемая задача
  * `task_broker` — брокер задачи
  * `e` — экземпляр ошибки `TaskPluginTriggerError`

---

## 🧠 Механизм обработки

Если в задаче вызывается:

```python
self.ctx.plugin_error()
```

то будет выброшено исключение:

```python
from qtasks.exc import TaskPluginTriggerError

raise TaskPluginTriggerError(**kwargs)
```

Внутри `TaskExecutor` исключение будет обработано следующим образом:

```python
try:
    self._result = await self.run_task()
except TaskPluginTriggerError as e:
    new_result = await self._plugin_trigger(
        "task_executor_run_task_trigger_error",
        task_executor=self,
        task_func=self.task_func,
        task_broker=self.task_broker,
        e=e,
        return_last=True
    )
    if new_result:
        self._result = new_result
    else:
        raise e
```

Если хотя бы один плагин вернёт значение — оно станет результатом задачи. Иначе исключение пробрасывается дальше.

---

## 🔧 Пример задачи с вызовом ошибки

```python
from qtasks.exc import TaskPluginTriggerError

@app.task(echo=True)
async def test_task(self: AsyncTask):
    self.ctx.plugin_error(message="Нестандартная ситуация")
    # Альтернатива: raise TaskPluginTriggerError("Ошибка напрямую")
```

---

## 🔌 Обработка в плагине

```python
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
        return 123
```

---

## 📘 Связанные ресурсы

* 📄 [Триггеры компонентов](./triggers.md)
* ⚠️ [Исключения](/qtasks/ru/api/exceptions/)

---

Система `plugin_error` даёт контроль над логикой ошибок и может использоваться как точка расширения поведения задач.
