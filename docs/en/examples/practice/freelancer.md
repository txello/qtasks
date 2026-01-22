# Example of using QTasks for freelancers

The QTasks framework is ideal for freelancers who need to quickly automate
tasks, process events from external APIs, and manage data flows. Below
is an example of how a freelancer can use QTasks to create a notification and
integration system.

---

## 💼 Scenario

Let's say you are a freelancer creating a Telegram bot for a client. The bot must:

1. Send reminders on a schedule.
2. Check order statuses with the client's API.
3. Log events and errors.

You want to process these tasks independently and in the background, without
relying on heavy solutions like Celery.

---

## 🚀 Application setup

```python
from qtasks.asyncio import QueueTasks
from qtasks.registries import AsyncTask
import logging

app = QueueTasks()
app.config.logs_default_level = logging.INFO
```

---

## ⏰ Time-based reminders

```python
@app.task(name="send_reminder")
async def send_reminder(chat_id: int, text: str):
    await telegram_api.send_message(chat_id, text)
```

You can run this task on a schedule using the built-in timer system:

```python
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

# Let's assume that app is already initialized

timer = AsyncTimer(app=app)
timer.add_task("send_reminder", trigger=CronTrigger(minute="*/1"),
args=(123456789, "Don't forget about your order!"))

timer.run_forever()
```

---

## 📦 Checking orders

```python
async def check_orders(self: AsyncTask):
    orders = await external_api.get_orders()
    for order in orders:
        if order.status == "delivered":
            await self.add_task(
                "send_reminder",
                order.user_id,
                "Your order has been delivered!"
            )
```

---

## 📋 Error logging

```python
@app.task(name="error_logger")
def error_logger(message: str):
    with open("errors.log", "a") as f:
        f.write(message + "\n")
```

You can use this in all tasks:

```python
try:
    ...
except Exception as e:
    await self.add_task("error_logger", args=(str(e),))
```

---

## 🧩 Why is QTasks useful for freelancers?

* Does not require Redis or RabbitMQ by default.
* Can be run via `python main.py`, without dockers or migrations.
* Flexibility: you can add retry, middleware, custom executors.
* Supports `yield`, `echo`, nested tasks, and logging.

---

## ✅ Result

You get a powerful background task system with minimal code and dependencies.
Ideal for microservices, bots, and API integrations — the typical freelancer environment.
