# Начинаем работу с `QTasks`

## Как за пару минут настроить и запустить первую задачу с помощью `QueueTasks`

### 1. Создание экземпляра приложения

```py
from qtasks import QueueTasks
# или для асинхронного варианта:
# from qtasks.asyncio import QueueTasks

app = QueueTasks()
```

!!! info
    По умолчанию в качестве брокера и хранилища используется Redis по адресу `redis://localhost:6379/0`.

### 2. Регистрация задач

Задачи регистрируются через декоратор [`@app.task`](/qtasks/ru/api/registries/sync_task_decorator/).

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

!!! info
    Если имя задачи уже не указано, будет использовано имя функции

!!! tip
    Имя задачи может быть любым, но должно быть уникальным в пределах приложения.
    Если задача с таким именем уже существует, будет вызвано исключение

### 3. Запускаем `QueueTasks`

```py
if __name__ == "__main__":
    app.run_forever()
```

### 4. Полный пример

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


if __name__ == "__main__":
    app.run_forever()
```

### 5. Добавление задач в очередь

После запуска обработчика задач, можно добавлять задачи из другого файла или
интерпретатора Python:

```py
# file: add_tasks.py
from app import app, mytest

app.add_task(task_name="mytest", "Тест")
mytest.add_task("Тест")
app.add_task(task_name="error_zero")
```
