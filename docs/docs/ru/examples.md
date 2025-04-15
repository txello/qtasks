# Примеры
На этой странице приведены различные примеры использования QueueTasks. Эти примеры помогут вам быстрее освоить основные возможности фреймворка и начать работать с задачами.

## Простой пример задачи
Задача, которая принимает строку, выводит её и возвращает обратно.
```py
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="print_text")
def print_text(text: str):
    print(text)
    return text

app.run_forever()

# Добавление задачи в очередь
app.add_task("print_text", args=("Привет, мир!",))
```

## Асинхронная задача
Пример асинхронной задачи, которая ожидает завершения некоторого асинхронного действия (например, имитация задержки).

```py
from qtasks.asyncio import QueueTasks
import asyncio

app = QueueTasks()

@app.task(name="async_task")
async def async_task(text: str):
    await asyncio.sleep(2)
    print(f"Задача завершена: {text}")
    return text

app.run_forever()

# Добавление асинхронной задачи
app.add_task("async_task", args=("Асинхронный пример",))
```

## Использование различных брокеров
Пример установки и использования RabbitMQ в качестве брокера.

```py
pip install qtasks[rabbitmq]

from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRabbitMQBroker

broker = AsyncRabbitMQBroker(url="amqp://guest:guest@localhost/")
app = QueueTasks(broker=broker)

@app.task(name="rabbitmq_example")
def rabbitmq_example(text: str):
    print(f"Получено сообщение: {text}")
    return text

app.run_forever()

# Добавление задачи в очередь
app.add_task("rabbitmq_example", args=("Сообщение через RabbitMQ",))
```