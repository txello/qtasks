import os
from qtasks.asyncio import QueueTasks

os.environ["QTASKS_TASK_DEFAULT_PRIORITY"] = "21"

app = QueueTasks()

print(app.config.task_default_priority)
print(app.worker.config.task_default_priority)
print(app.broker.config.task_default_priority)
print(app.broker.storage.config.task_default_priority)
if app.broker.storage.global_config:
    print(app.broker.storage.global_config.config.task_default_priority)
