# Компоненты QueueTasks

Фреймворк построен на компонентной архитектуре: каждый элемент системы отвечает за
свою часть работы, может быть заменён, расширен или переопределён. Эта страница
даёт обзор всех основных и дополнительных компонентов, без углублённой внутренней
логики.

---

## Основные компоненты

### QueueTasks

Центральный объект фреймворка. Управляет регистрацией задач, настройкой среды
выполнения и связывает между собой остальные компоненты.

При создании экземпляра `QueueTasks()` автоматически формируются:

* Broker (по умолчанию Redis)
* Storage (Redis)
* GlobalConfig (Redis)
* Worker (SyncThreadWorker или AsyncWorker)
* Starter (SyncStarter или AsyncStarter)

```py
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="test")
def sample_task(id: int):
    return f"Пользователь {id} записан"
```

QueueTasks может принимать URL подключений (`broker_url`, `storage_url`), а также
полностью кастомные компоненты.

---

### Broker — обработчик входящих задач

Отвечает за приём задач и передачу их воркеру. По умолчанию используется Redis-брокер.

```py
from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRedisBroker

broker = AsyncRedisBroker(url="redis://localhost:6379/2")

app = QueueTasks(broker=broker)
```

Broker использует Storage и, при необходимости, GlobalConfig.

---

### Worker — исполнитель задач

Выполняет задачи, поступающие от брокера. Поддерживает синхронный (`SyncThreadWorker`)
и асинхронный (`AsyncWorker`) режимы.

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker

broker = AsyncRedisBroker(url="redis://localhost:6379/2")
worker = AsyncWorker(broker=broker)

app = QueueTasks(broker=broker, worker=worker)
```

Worker взаимодействует с контекстом задач, retry-логикой, middleware и плагинами.

---

### Storage — хранилище данных задач

Сохраняет информацию о задачах:

* статус,
* результат,
* ошибки,
* время выполнения.

Является обязательным компонентом, но может быть заменён. Broker содержит внутри
себя ссылку на Storage.

```py
from qtasks.asyncio import QueueTasks
from qtasks.storages import AsyncRedisStorage
from qtasks.brokers import AsyncRedisBroker

storage = AsyncRedisStorage(url="redis://localhost:6379/2")
broker = AsyncRedisBroker(url="redis://localhost:6379/2", storage=storage)

app = QueueTasks(broker=broker)
```

Хранилище также содержит связку с GlobalConfig.

---

### Starter — управляющий запуском компонентов

Starter отвечает за запуск и остановку всех компонентов. QueueTasks использует
Starter по умолчанию.

Starter также может управлять сценариями потоков выполнения компонентов.

```py
from qtasks.asyncio import QueueTasks
from qtasks.starters import AsyncStarter

starter = AsyncStarter(name="QueueTasks")
app = QueueTasks()

if __name__ == "__main__":
    app.run_forever(starter=starter)
```

---

## Дополнительные компоненты

### GlobalConfig — глобальная конфигурация

Хранилище глобальных переменных и настроек, доступных всем компонентам.
Используется, например, при работе WebView: интерфейс может подключаться к Redis
без запуска приложения.

```py
from qtasks.asyncio import QueueTasks
from qtasks.configs import AsyncRedisGlobalConfig

config = AsyncRedisGlobalConfig(url="redis://localhost:6379/2")
app = QueueTasks(global_config=config)
```

GlobalConfig доступен как:

```py
app.broker.storage.global_config
```

и может быть `None`.

---

### Plugins — расширение функциональности

Плагины позволяют подключать любую дополнительную логику: логирование, модификацию
аргументов задач, интеграции.

Все доступные триггеры описаны здесь: [Триггеры](api/plugins/triggers.md)

Пример:

```py
from qtasks import QueueTasks
from qtasks.plugins import BasePlugin

app = QueueTasks()

class TestPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.handlers = {
            "task_executor_args_replace": self.replace
        }

    def replace(self, **kwargs):
        print("ARGS:", kwargs)
        return None

app.add_plugin(
    TestPlugin(),
    trigger_names=["task_executor_args_replace"],
    component="worker"
)
```

---

### Timer — запуск задач по расписанию

Отдельный компонент, позволяющий использовать cron-подобные расписания.
Использует APScheduler (`CronTrigger`).

```py
from qtasks import QueueTasks
from qtasks.timers import AsyncTimer
from apscheduler.triggers.cron import CronTrigger

app = QueueTasks()

@app.task
def test():
    print("Запуск тестовой задачи")


trigger = CronTrigger(second="*/10")
timer = AsyncTimer(app=app)
timer.add_task("test", trigger=trigger)

timer.run_forever()
```

---

### WebView — визуальный интерфейс

Отдельная библиотека для просмотра списка задач, результатов и статистики.
Установка:

```bash
pip install qtasks_webview
```

WebView работает напрямую с Redis и не требует запущенного приложения.

---

## Полный пример ручной сборки всех компонентов

```py
import asyncio
from qtasks.asyncio import QueueTasks
from qtasks.configs import AsyncRedisGlobalConfig
from qtasks.storages import AsyncRedisStorage
from qtasks.brokers import AsyncRedisBroker
from qtasks.workers import AsyncWorker
from qtasks.starters import AsyncStarter

# GlobalConfig — глобальные переменные и настройки
global_config = AsyncRedisGlobalConfig(
    name="QueueTasks",
    url="redis://localhost:6379/2"
)

# Storage — хранилище задач
storage = AsyncRedisStorage(
    name="QueueTasks",
    global_config=global_config,
    url="redis://localhost:6379/2"
)

# Broker — обработчик входящих задач
broker = AsyncRedisBroker(
    name="QueueTasks",
    storage=storage,
    url="redis://localhost:6379/2"
)

# Worker — исполнитель задач
worker = AsyncWorker(
    name="QueueTasks",
    broker=broker
)

# QueueTasks — основной объект
app = QueueTasks(
    name="QueueTasks",
    broker=broker,
    worker=worker
)

# Настройки приложения
app.config.max_tasks_process = 10
app.config.running_older_tasks = True
app.config.delete_finished_tasks = True


@app.task(name="test")
async def sample_task(id: int):
    result = f"Пользователь {id} записан"
    await asyncio.sleep(id)
    return result


if __name__ == "__main__":
    starter = AsyncStarter(
        name="QueueTasks",
        worker=worker,
        broker=broker
    )
    app.run_forever(starter=starter)
```
