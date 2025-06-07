import logging

from qtasks.asyncio import QueueTasks

import shared_tasks

app = QueueTasks() 
app.config.logs_default_level = logging.DEBUG
app.config.running_older_tasks = True

@app.task(name="test")
def test():
    print("Это тестовая задача!")
    
@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")
    return number

@app.task(retry=5)
def error_zero():
    result = 1/0

if __name__ == "__main__":
    app.run_forever(num_workers=10)
