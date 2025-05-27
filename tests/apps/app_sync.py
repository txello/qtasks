from qtasks import QueueTasks
from qtasks.brokers import SyncRedisBroker
from qtasks.workers import SyncThreadWorker

broker = SyncRedisBroker(name="QueueTasks")
worker = SyncThreadWorker(name="QueueTasks", broker=broker)

app = QueueTasks(name="QueueTasks", broker=broker, worker=worker)

@app.task(name="test")
def sample_task(id: int):
    # Логика задачи...
    result = f"Пользователь {id} записан"
    return result

@app.task(name="error_task")
def error_zero():
    result = 1/0

if __name__ == "__main__":
    app.run_forever()
