from qtasks.timers import AsyncTimer
from based_async_app import app
from apscheduler.triggers.cron import CronTrigger

timer = AsyncTimer(app=app)

timer.add_task("test", trigger=CronTrigger(minute="*/1"), args=(5,))

timer.run_forever()
