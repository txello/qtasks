# Timer

There is a built-in additional component **(A)syncTimer** designed
to periodically launch QTasks tasks. The timer integrates directly with `QueueTasks`
through the `app` parameter and works with tasks as a schedule, rather than
with single calls.

(A)syncTimer allows you to remove scheduling logic from business code and use
declarative triggers to launch tasks on a schedule.

---

## How it works

Timer is a separate component that:

* registers periodic tasks;
* uses external triggers (e.g., cron);
* initiates task execution through the standard QTasks mechanism;
* does not change the logic of the tasks themselves.

A task launched through Timer remains a regular QTasks task and can be
called manually, through the API, or by other components.

---

## Example of use

```python
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

timer = AsyncTimer(app=app)

timer.add_task(
    "daily_report",
    trigger=CronTrigger(hour=23, minute=59),)


@app.task(name="daily_report")
async def daily_report():
    stats = await db.get_today_stats()
    await mailer.send(
        "owner@shop.com",
        "Daily report",
        stats.format(),
    )
```

In this example, the `daily_report` task will automatically run every day
at 23:59.

---

## Under the hood

Timer works in the following stages:

1. Timer is initialized with an instance of `QueueTasks`.
2. When `add_task` is called:

   * the task name is saved;
   * the launch trigger is registered;
   * a "trigger → task" pair is formed.
3. When the trigger is activated:

   * Timer creates a regular task call via `add_task`;
   * the task goes to the Broker and is processed by the Worker as standard.

Thus, Timer does not execute the task directly and does not bypass the queue.

---

## Triggers

(A)syncTimer does not restrict the type of trigger. In practice, triggers from `apscheduler`
are most often used, for example:

* `CronTrigger` — cron schedule;
* `IntervalTrigger` — launch at fixed intervals;
* `DateTrigger` — one-time launch at a specified time.
This allows you to flexibly manage the schedule without changing the task code.

This allows you to flexibly manage the schedule without changing the task code.

---

## Features

* Timer is an additional component and is not required for QTasks to work.
* The timer works with tasks by name, not by function reference.
* Tasks registered in Timer are fully compatible with retry, priority, middlewares,
and plugins.
* Timer does not store the execution status of tasks — this is handled by the
standard QTasks storage.

---

## Summary

(A)syncTimer provides:

* declarative task scheduling;
* integration with external scheduling systems;
* a unified mechanism for launching tasks via a queue;
* a clear separation of business logic and scheduling logic.

The page is designed as a canvas and can be used as a template for documenting
other additional QTasks components.
