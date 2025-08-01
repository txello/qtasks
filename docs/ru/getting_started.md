# Начинаем работу с QueueTasks
Эта страница покажет, как за пару минут настроить и запустить первую задачу с помощью QueueTasks.

1. Создание экземпляра приложения
```py
from qtasks import QueueTasks
# или для асинхронного варианта:
# from qtasks.asyncio import QueueTasks

app = QueueTasks()
```

2. Регистрация задач. Задачи регистрируются через декоратор @app.task. Укажите имя задачи, чтобы можно было вызывать её из любого места.
```py
@app.task(name="mytest") # Обычная задача 
def mytest(text: str):
    print(text)
    return text

@app.task(name="error_zero") # Задача с ошибкой
def error_zero():
    result = 1/0
    return
```
* Запускаем QueueTasks
```py
app.run_forever()
```
4. Полный пример
```py
# file: app.py
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="mytest") # Пример обычной задачи
def mytest(text: str):
    print(text)
    return text

@app.task(name="error_zero") # Пример задачи с ошибкой
def error_zero():
    result = 1/0
    return

app.run_forever()
```

## Добавление задач в очередь.
После запуска обработчика задач, можно добавлять задачи из другого файла или интерпретатора Python:
```py
from app import app, mytest

app.add_task(task_name="mytest", "Тест")
mytest.add_task("Тест")
app.add_task(task_name="error_zero")

```