# Examples

This page provides basic examples of using QTasks.
They will help you quickly learn the main scenarios for working with tasks.

---

## Simple task example (synchronous)

The task accepts a string, outputs it to the console, and returns it back.

```py
from qtasks import QueueTasks

app = QueueTasks()


@app.task(name="print_text")
def print_text(text: str):
    print(text)
    return text


if __name__ == "__main__":
    app.run_forever()

    # Adding a task to the queue
    app.add_task("print_text", "Hello, world!")
    # Result: "Hello, world!"
```

When accessing a task through the function itself (task_func), the `task_name`
parameter can be explicitly specified if you need to override the name:

```py
print_text.add_task("Hello, world!")              # task_name = "print_text"
print_text.add_task(task_name="echo_text")       # task_name = "echo_text"
```

---

## Asynchronous task

An asynchronous task that simulates a delay and returns a result.

```py
import asyncio
from qtasks.asyncio import QueueTasks

app = QueueTasks()


@app.task(name="async_task")
async def async_task(text: str):
    await asyncio.sleep(2)
    print(f"Task completed: {text}")
    return text


if __name__ == "__main__":
    app.run_forever()

    # Adding an asynchronous task
    asyncio.run(app.add_task("async_task", "Asynchronous example"))
    # Result: "Task completed: Asynchronous example"
```

---

## Using Redis (default broker)

By default, QTasks uses Redis. You can explicitly specify the URL:

```py
from qtasks import QueueTasks

app = QueueTasks(broker_url="redis://localhost:6379/0")


@app.task(name="redis_example")
def redis_example(value: int):
    print(f"Value: {value}")
    return value


if __name__ == "__main__":
    app.run_forever()

    app.add_task("redis_example", 42)
    # Result: "Value: 42"
```

---

## Using RabbitMQ as a broker

Example of RabbitMQ configuration:

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
    print(f"Message received: {text}")
    return text


if __name__ == "__main__":
    app.run_forever()

    asyncio.run(app.add_task("rabbitmq_example", "Message via RabbitMQ"))
    # Result: "Message received: Message via RabbitMQ"
```

---

## What to look at next

Additional examples are available in separate sections:

* Tasks and their capabilities — see section: `[Task capabilities](features.md)`
* Plugins — see section: `[How to write plugins](plugins.md)`
* Integrations — see section: `[QTasks integration](integrations/index.md)`
* Analytics and statistics — see section: `[Analytics](analytics.md)`
