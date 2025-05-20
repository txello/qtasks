import asyncio
from qtasks.asyncio import QueueTasks

app = QueueTasks()

@app.task(name="test")
def test():
    print("Это тестовая задача!")
    
@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")
    return number

if __name__ == "__main__":
    app.run_forever()