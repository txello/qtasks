# Интеграция с Django

На данный момент в `QTasks` реализована одна основная функция интеграции
с Django: **`autodiscover_tasks`**.

---

## 📌 Что делает autodiscover\_tasks?

Эта функция автоматически импортирует указанные модули (например, `tasks.py`) из
всех приложений, перечисленных в `INSTALLED_APPS`.
Таким образом задачи регистрируются в QTasks без необходимости ручного подключения.

Сигнатура функции:

```python
def autodiscover_tasks(app, modules: List[str] = ["tasks"]):
    """Автоматически импортирует указанные модули из всех INSTALLED_APPS,
    чтобы зарегистрировать задачи в QTasks.

    Args:
        app (QueueTasks): приложение.
        modules (List[str]): Модули для автодискавери. По умолчанию: ["tasks"].
    """
```

📖 Подробное описание доступно в [API → autodiscover\_tasks](/qtasks/ru/api/libraries/django/).

---

## 🔧 Как использовать

В `settings.py`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "myapp",  # здесь будет tasks.py
]
```

В `myapp/tasks.py`:

```python
from qtasks import QueueTasks

app = QueueTasks()

@app.task
def hello(name: str):
    return f"Hello, {name}!"
```

В `manage.py` или основном модуле проекта:

```python
from qtasks.contrib.django import autodiscover_tasks
from qtasks import QueueTasks

app = QueueTasks()
autodiscover_tasks(app)
```

После вызова `autodiscover_tasks(app)` все задачи из `tasks.py` будут автоматически
зарегистрированы и доступны для выполнения.

---

## ✅ Итоги

* `autodiscover_tasks` ищет `tasks.py` (или другие модули, если указаны) во всех
приложениях `INSTALLED_APPS`.
* Это упрощает интеграцию QTasks в проекты Django.
* Не нужно вручную регистрировать задачи — достаточно создать их в `tasks.py` внутри
каждого приложения.
