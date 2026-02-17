import logging

from apscheduler.triggers.cron import CronTrigger

from qtasks import QueueTasks
from qtasks.timers import SyncTimer

app = QueueTasks()
app.config.logs_default_level_server = logging.INFO
app.config.running_older_tasks = True
app.config.result_time_interval = 0.1


@app.task(
    name="test",
    description="Test task"
)
async def test(num: int):
    print(f"Number: {num}")


timer = SyncTimer(app=app)

timer.add_task(5, task_name="test", trigger=CronTrigger(second="*/5"))

timer.run_forever()
