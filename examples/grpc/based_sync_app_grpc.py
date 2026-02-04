from qtasks import QueueTasks
from qtasks.plugins import SyncgRPCPlugin

app = QueueTasks()


@app.task
def test():
    print(123)

@app.task
def add(x, y):
    return x + y



app.add_plugin(SyncgRPCPlugin(app=app), trigger_names=["-"])

if __name__ == "__main__":
    app.run_forever()
