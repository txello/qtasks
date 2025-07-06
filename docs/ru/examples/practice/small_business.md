# Пример использования QTasks для малого бизнеса

Малый бизнес часто сталкивается с задачами автоматизации: уведомления, отчёты, интеграции с CRM, обмен данными между сервисами. QTasks предоставляет лёгкую, но мощную платформу, которая позволяет строить надёжные решения без тяжёлых инфраструктурных затрат.

---

## 🏪 Сценарий

Допустим, у вас есть интернет-магазин. Вам нужно:

1. Автоматически уведомлять клиентов о статусе заказа.
2. Собирать ежедневную аналитику по продажам.
3. Интегрироваться с внешней CRM.

---

## 📦 Уведомления клиентам

```python
@app.task(name="notify_status")
async def notify_status(order_id: int):
    order = await db.get_order(order_id)
    await sms_api.send(order.phone, f"Ваш заказ {order.id} сейчас: {order.status}")
```

---

## 📊 Ежедневная аналитика с таймером

```python
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

timer = AsyncTimer(app=app)

timer.add_task("daily_report", trigger=CronTrigger(hour=23, minute=59))

@app.task(name="daily_report")
async def daily_report():
    stats = await db.get_today_stats()
    await mailer.send("owner@shop.com", "Ежедневный отчёт", stats.format())
```

---

## 🔗 Интеграция с CRM через `yield` и `generate_handler`

```python
async def log_crm(result):
    await crm_api.send_log(result)
    return result

@app.task(generate_handler=log_crm, echo=True)
async def export_orders():
    for order in await db.get_exportable_orders():
        yield order.to_dict()
```

---

## 🛠 Обработка ошибок и перезапуск задач

```python
@app.task(retry=3, retry_on_exc=[ConnectionError])
async def sync_with_crm():
    await crm_api.sync()
```

---

## 📈 Преимущества QTasks для бизнеса

* Автоматизация без внешних очередей (по умолчанию)
* Удобные таймеры для ежедневных и еженедельных задач
* Встроенная обработка ошибок и перезапусков
* Гибкая архитектура: можно расширять под нужды CRM, BI, складов и логистики

---

## ✅ Результат

С помощью QTasks малый бизнес может выстроить автоматизированную систему обработки данных, которая будет работать стабильно, масштабироваться по мере роста и не потребует от команды сложной DevOps-инфраструктуры.
