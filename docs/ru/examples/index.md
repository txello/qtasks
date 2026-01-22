# Примеры

На этой странице приведены базовые примеры использования QTasks.
Они помогут быстро освоить основные сценарии работы с задачами.

---

## Простой пример задачи (синхронно)

Задача принимает строку, выводит её в консоль и возвращает обратно.

```py
from qtasks import QueueTasks

app = QueueTasks()


@app.task(name="print_text")
def print_text(text: str):
    print(text)
    return text


if __name__ == "__main__":
    app.run_forever()

    # Добавление задачи в очередь
    app.add_task("print_text", "Привет, мир!")
    # Результат: "Привет, мир!"
```

При обращении к задаче через саму функцию (task_func) параметр `task_name` можно
указать явно, если нужно переопределить имя:

```py
print_text.add_task("Привет, мир!")              # task_name = "print_text"
print_text.add_task(task_name="echo_text")       # task_name = "echo_text"
```

---

## Асинхронная задача

Асинхронная задача, имитирующая задержку и возвращающая результат.

```py
import asyncio
from qtasks.asyncio import QueueTasks

app = QueueTasks()


@app.task(name="async_task")
async def async_task(text: str):
    await asyncio.sleep(2)
    print(f"Задача завершена: {text}")
    return text


if __name__ == "__main__":
    app.run_forever()

    # Добавление асинхронной задачи
    asyncio.run(app.add_task("async_task", "Асинхронный пример"))
    # Результат: "Задача завершена: Асинхронный пример"
```

---

## Использование Redis (брокер по умолчанию)

По умолчанию QTasks использует Redis. Можно явно указать URL:

```py
from qtasks import QueueTasks

app = QueueTasks(broker_url="redis://localhost:6379/0")


@app.task(name="redis_example")
def redis_example(value: int):
    print(f"Значение: {value}")
    return value


if __name__ == "__main__":
    app.run_forever()

    app.add_task("redis_example", 42)
    # Результат: "Значение: 42"
```

---

## Использование RabbitMQ в качестве брокера

Пример настройки RabbitMQ:

```bash
pip install qtasks[rabbitmq]
```

```py
import asyncio
from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRabbitMQBroker


broker = AsyncRabbitMQBroker(url="amqp://guest:guest@localhost/")
app = QueueTasks(broker=broker)


@app.task(name="rabbitmq_example")
async def rabbitmq_example(text: str):
    print(f"Получено сообщение: {text}")
    return text


if __name__ == "__main__":
    app.run_forever()

    asyncio.run(app.add_task("rabbitmq_example", "Сообщение через RabbitMQ"))
    # Результат: "Получено сообщение: Сообщение через RabbitMQ"
```

---

## Что посмотреть дальше

Дополнительные примеры доступны в отдельных разделах:

* Задачи и их возможности — см. раздел: `[Возможности задач](features.md)`
* Плагины — см. раздел: `[Как писать плагины](plugins.md)`
* Интеграции — см. раздел: `[Интеграция QTasks](integrations/index.md)`
* Аналитика и статистика — см. раздел: `[Аналитика](analytics.md)`
