# Пример использования self и self.ctx (echo=True)

При указании `echo=True`, задача получает первым аргументом объект `self` типа `AsyncTask` или `SyncTask`. Это открывает доступ к контексту выполнения `self.ctx`, внутренним данным задачи и управляющим методам.

Ниже представлен пример задачи с демонстрацией всех возможностей `self` и `self.ctx`.

---

## 🧩 Пример задачи

```python
@app.task(
    echo=True, tags=["test"], priority=1,
    retry=3, retry_on_exc=[KeyError], decode=json.dumps,
    # generate_handler=yield_func, executor=MyTaskExecutor,
    # middlewares_before=[MyTaskMiddleware], middlewares_after=[MyTaskMiddleware],
    test="test"
)
async def test_echo_ctx(self: AsyncTask):
    # Получаем логгер (с именем задачи по умолчанию)
    self.ctx.get_logger().info("Это тестовая задача!")

    # Пауза в задаче (асинхронная)
    await self.ctx.sleep(5)

    # Получаем текущую конфигурацию
    self.ctx.get_logger().info(self.ctx.get_config())

    # Вывод всех доступных параметров задачи
    self.ctx.get_logger().info(
        f"""
            UUID: {self.ctx.task_uuid}
            Имя: {self.task_name}
            Теги: {self.tags}
            Приоритет: {self.priority}
            Дополнительные параметры: {self.extra}

            Повторений через параметр: {self.retry}
            Исключения для повтора: {self.retry_on_exc}
            Функция для декоратора: {self.ctx.generate_handler}

            Вызван ли self: {self.echo}
            Декордирование через параметр: {self.decode}

            TaskExecutor через параметр: {self.executor}
            Миддлвари: {self.middlewares}
        """
    )

    # Отмена задачи вручную
    self.ctx.cancel("Тестовая задача отменена")
    return "Hello, world!"
```

---

## 📦 Возможности self

* `self.task_name`, `self.retry`, `self.tags`, `self.echo` — параметры задачи
* `await self.add_task(...)` — запуск вложенных задач
* `self.decode`, `self.executor`, `self.middlewares` — доступ к аргументам задачи

---

## 🧠 Возможности self.ctx

* `self.ctx.get_logger()` — логгер с именем задачи или кастомным именем
* `self.ctx.sleep(seconds)` — задержка выполнения
* `self.ctx.cancel(reason)` — отмена задачи с установкой `status=CANCEL`
* `self.ctx.get_config()`, `get_component(name)`, `get_task(uuid)`, `get_metadata()` — доступ к инфраструктуре и состоянию

---

## ✅ Результат в логах

**Клиент:**

```
Task(status='cancel', uuid=..., task_name='test_echo_ctx', ..., cancel_reason='Тестовая задача отменена')
```

**Сервер:**

```
2025-07-16 ... (test_echo_ctx) Это тестовая задача!
...
UUID: ...
Имя: test_echo_ctx
Теги: ['test']
...
Задача ... была отменена по причине: Тестовая задача отменена
```

---

Использование `self` и `self.ctx` делает задачу не просто функцией, а полноценным объектом, способным взаимодействовать с системой QTasks на всех уровнях.
