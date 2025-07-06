# Пример использования QTasks для фрилансера

Фреймворк QTasks отлично подходит для фрилансеров, которым важно быстро автоматизировать задачи, обрабатывать события из внешних API и управлять потоками данных. Ниже представлен пример, как фрилансер может использовать QTasks для создания системы уведомлений и интеграций.

---

## 💼 Сценарий

Допустим, вы фрилансер, создающий Telegram-бота для клиента. Бот должен:

1. Отправлять напоминания по расписанию.
2. Проверять статусы заказов с API клиента.
3. Логировать события и ошибки.

Вы хотите обрабатывать эти задачи независимо и в фоне, без зависимостей от тяжёлых решений вроде Celery.

---

## 🚀 Настройка приложения

```python
from qtasks.asyncio import QueueTasks
from qtasks.registries import AsyncTask
import logging

app = QueueTasks()
app.config.logs_default_level = logging.INFO
```

---

## ⏰ Напоминания по времени

```python
@app.task(name="send_reminder")
async def send_reminder(chat_id: int, text: str):
    await telegram_api.send_message(chat_id, text)
```

Можно запускать эту задачу по расписанию с помощью встроенной системы таймеров:

```python
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

# Предположим, что app уже инициализирован

timer = AsyncTimer(app=app)
timer.add_task("send_reminder", trigger=CronTrigger(minute="*/1"), args=(123456789, "Не забудьте про заказ!"))

timer.run_forever()
```

---

## 📦 Проверка заказов

```python
@app.task(name="check_orders", echo=True)
async def check_orders(self: AsyncTask):
    orders = await external_api.get_orders()
    for order in orders:
        if order.status == "delivered":
            await self.add_task("send_reminder", args=(order.user_id, "Ваш заказ доставлен!"))
```

---

## 📋 Логирование ошибок

```python
@app.task(name="error_logger")
def error_logger(message: str):
    with open("errors.log", "a") as f:
        f.write(message + "\n")
```

Во всех задачах можно использовать:

```python
try:
    ...
except Exception as e:
    await self.add_task("error_logger", args=(str(e),))
```

---

## 🧩 Почему QTasks удобен для фрилансера?

* Не требует Redis или RabbitMQ по умолчанию.
* Можно запускать через `python main.py`, без докеров и миграций.
* Гибкость: можно добавлять retry, middleware, кастомные executor'ы.
* Поддержка `yield`, `echo`, вложенных задач и логирования.

---

## ✅ Результат

Вы получаете мощную систему фоновых задач с минимальным кодом и зависимостями. Идеально подходит для микросервисов, ботов и API-интеграций — типичной среды фрилансера.
