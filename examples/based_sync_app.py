from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="test")
def test():
    print("this is a test task!")

app.run_forever()