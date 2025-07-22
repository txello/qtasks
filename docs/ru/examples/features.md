# Особенности задач QTasks

QTasks поддерживает гибкую систему аннотаций задач и их поведения. Ниже приведены ключевые расширения и настройки задач, используемые в проекте.

---

## 📦 shared\_task

`shared_task` позволяет регистрировать задачи вне контекста приложения `QueueTasks`, обычно используется для переиспользуемых или общих задач.

```python
@shared_task()
def shared_func():
    print("Общая задача")
```

Поддерживает те же параметры, что и `@app.task`, включая:

* `executor`
* `middlewares`
* `generate_handler`
* `echo`
* `awaiting`

---

## 🔀 router\_tasks

`Router` — механизм маршрутизации задач, отделённый от основного `QueueTasks`-приложения. Позволяет подключать внешние наборы задач.

```python
from qtasks import Router

router = Router(method="sync")

@router.task()
def example():
    print("Router task")
```

В `main.py`:

```python
app.include_router(router)
```

---

## 📣 echo=True и self: Task

Если указано `echo=True`, QTasks передаёт первым аргументом в задачу её экземпляр `self`:

* Для `async` — `AsyncTask`
* Для `sync` — `SyncTask`

```python
@app.task(echo=True)
async def echo_task(self: AsyncTask):
    print(self.task_name)
```

Это позволяет вызывать `self.add_task(...)`, получать `self.ctx` и управлять вложенными задачами.

---

## 🧠 self.ctx — это (A)SyncContext

Контекст `self.ctx` даёт доступ к:

* `task_uuid`
* `get_logger()`
* `get_broker()` / `get_storage()` / `get_config()`
* `cancel()` — инициирует отмену задачи

```python
@app.task(echo=True)
def show_context(self: SyncTask):
    print(self.ctx.task_uuid)
    self.ctx.cancel()  # вызовет TaskCancelError внутри задачи
```

`self.ctx.cancel()` вызывает исключение `TaskCancelError` внутри текущей задачи. Это перехватывается воркером и инициирует переход задачи в статус `CANCEL`.

Это унифицированный способ доступа к внутренним компонентам фреймворка.

---

## 🔁 retry и retry\_on\_exc

Если указано `retry=N`, задача будет перезапущена `N` раз при ошибке.
Если задано `retry_on_exc=[...]`, то перезапуск будет происходить **только** при указанных типах ошибок.

```python
@app.task(retry=5, retry_on_exc=[ZeroDivisionError])
def retryable():
    1 / 0
```

---

## ⚙️ executor

Позволяет заменить стандартный `AsyncTaskExecutor` / `SyncTaskExecutor` на пользовательский.

```python
@shared_task(executor=MySyncTaskExecutor)
def custom_exec():
    print("Используется кастомный executor")
```

---

## 🧩 middlewares

Массив middleware'ов, вызываемых внутри executor'а до и после выполнения задачи. Позволяют реализовать логику до/после вызова задачи.

```python
@shared_task(middlewares_after=[MyTaskMiddleware], middlewares_before=[MyTaskMiddleware])
def with_mw():
    print("middleware")
```

---

## 🪢 awaiting=True (только для shared\_task)

Если указан `awaiting=True`, `shared_task` переключается в асинхронный режим и возвращает `AsyncTask`, даже если объявлена как `async def`.

```python
@shared_task(awaiting=True)
async def async_shared():
    print("async shared task")
```

Это важно для совместимости и правильного ожидания задачи в другом контексте.
