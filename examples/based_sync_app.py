from qtasks import QueueTasks

import shared_tasks

app = QueueTasks()

app.config.running_older_tasks = True

@app.task(name="test")
def test():
    print("Это тестовая задача!")
    
@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")
    return number

if __name__ == "__main__":
    app.run_forever()
