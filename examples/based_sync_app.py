from qtasks import QueueTasks

import shared_tasks

app = QueueTasks()

@app.task(name="test")
def test():
    print("Это тестовая задача!")
    
@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")

test_num.add_task(args=(1, ))

app.run_forever()