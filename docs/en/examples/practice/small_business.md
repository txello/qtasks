# Example of using QTasks for small businesses

Small businesses often face automation challenges: notifications, reports,
CRM integrations, data exchange between services. QTasks provides an easy-to-use,
yet powerful platform that allows you to build reliable solutions without heavy
infrastructure costs.

---

## 🏪 Scenario

Let's say you have an online store. You need to:

1. Automatically notify customers about their order status.
2. Collect daily sales analytics.
3. Integrate with an external CRM.

---

## 📦 Customer notifications

```python
@app.task(name="notify_status")
async def notify_status(order_id: int):
    order = await db.get_order(order_id)
    await sms_api.send(order.phone, f"Your order {order.id} is now: {order.status}")
```

---

## 📊 Daily analytics with a timer

```python
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

timer = AsyncTimer(app=app)

timer.add_task("daily_report", trigger=CronTrigger(hour=23, minute=59))

@app.task(name="daily_report")
async def daily_report():
    stats = await db.get_today_stats()
await mailer.send("owner@shop.com", "Daily report", stats.format())
```

---

## 🔗 Integration with CRM via `yield` and `generate_handler`

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

## 🛠 Error handling and task restart

```python
@app.task(retry=3, retry_on_exc=[ConnectionError])
async def sync_with_crm():
    await crm_api.sync()
```

---

## 📈 Benefits of QTasks for business

* Automation without external queues (by default)
* Convenient timers for daily and weekly tasks
* Built-in error handling and restarts
* Flexible architecture: can be extended to meet the needs of CRM, BI, warehouses,
and logistics.

---

## ✅ Result

With QTasks, small businesses can build an automated data processing system
that will work stably, scale as they grow, and does not require
a complex DevOps infrastructure from the team.
