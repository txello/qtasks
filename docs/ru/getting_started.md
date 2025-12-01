# Начинаем работу с QTasks

## Быстрый старт: первая задача за пару минут

Ниже приведён минимальный пример настройки и запуска QTasks для синхронных задач,
а также краткое указание, как использовать асинхронный вариант.

### 1. Создание экземпляра приложения

```py
from qtasks import QueueTasks
# для асинхронного варианта:
# from qtasks.asyncio import QueueTasks

app = QueueTasks()
```

!!! info
    По умолчанию в качестве брокера и хранилища используется Redis по адресу `redis://localhost:6379/0`.

### 2. Регистрация задач

Задачи регистрируются через декоратор [`@app.task`](api/registries/sync_task_decorator.md).

```py
@app.task(name="mytest")  # Обычная задача
def mytest(text: str):
    print(text)
    return text


@app.task(name="error_zero")  # Задача с ошибкой
def error_zero():
    result = 1 / 0
    return
```

!!! info
    Если имя задачи не указано явно (параметр `name`), используется имя функции.

!!! tip
    Имя задачи может быть любым, но должно быть уникальным в пределах приложения.
    Если задача с таким именем уже существует, будет вызвано исключение при регистрации.

### 3. Запуск обработчика задач

Обработчик задач можно запустить двумя способами.

#### Вариант 1: через `run_forever()`

```py
if __name__ == "__main__":
    app.run_forever()
```

#### Вариант 2: через CLI

```bash
qtasks -A app:app run
```

Где `app:app` — это `module:variable`, то есть модуль с приложением и переменная,
в которой хранится экземпляр `QueueTasks`.

### 4. Полный пример файла с задачами

```py
# file: app.py
from qtasks import QueueTasks


app = QueueTasks()


@app.task(name="mytest")  # Пример обычной задачи
def mytest(text: str):
    print(text)
    return text


@app.task(name="error_zero")  # Пример задачи с ошибкой
def error_zero():
    result = 1 / 0
    return


if __name__ == "__main__":
    app.run_forever()
```

### 5. Добавление задач в очередь

После запуска обработчика задач можно добавлять задачи из другого файла или интерактивного
интерпретатора Python:

```py
# file: add_tasks.py
from app import app, mytest

# Добавление задачи по имени через экземпляр приложения
app.add_task("mytest", "Тест")

# Вызов через зарегистрированную функцию задачи
mytest.add_task("Тест")

# Добавление задачи с ожиданием результата (timeout в секундах)
mytest.add_task("Тест", timeout=50)

# Добавление задачи, которая приведёт к ошибке
app.add_task("error_zero")
```

Метод `add_task` поддерживает позиционные и именованные аргументы (`*args`, `**kwargs`),
которые будут переданы в функцию задачи.

### 6. Асинхронный вариант (кратко)

Асинхронный вариант настраивается аналогично, но с использованием
`qtasks.asyncio.QueueTasks` и `async`-функций:

```py
from qtasks.asyncio import QueueTasks


app = QueueTasks()


@app.task(name="mytest_async")
async def mytest_async(text: str):
    print(text)
    return text


if __name__ == "__main__":
    app.run_forever()
```

---

Подробнее об асинхронных задачах, `AsyncTask` и контексте выполнения:

<div class="result" markdown>
  <div class="grid cards" markdown>

- :fontawesome-solid-laptop-code:{ .lg .middle } __(A)syncTask__

    ---

    Узнаем больше о преобразовании @app.task

    [:octicons-arrow-right-24: Декоратор задачи](features/task_decorator.md)

- :fontawesome-solid-plus:{ .lg .middle } __Task Context__

    ---

    Понимаем контекст выполнения задач и его применение

    [:octicons-arrow-right-24: Контекст задачи](features/task_context.md)

  </div>

</div>
