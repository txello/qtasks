# Компоненты `QueueTasks`

Фреймворк `QTasks` построен по компонентной архитектуре — каждый модуль отвечает
за свою часть работы и может быть заменён или расширен.

## Основные компоненты

### `QueueTasks`

Центральный объект фреймворка. Используется для регистрации и запуска задач, а
также взаимодействия с другими компонентами.

Пример:

```py
from qtasks import QueueTasks

# Создание экземпляра приложения
app = QueueTasks()

@app.task(name="test")
def sample_task(id: int):
    return f"Пользователь {id} записан"

```

### Broker (Брокер)

Отвечает за приём и маршрутизацию задач. Передаёт задачи воркеру.

Пример:

```py
from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRedisBroker

# Broker — обработчик входящих задач
broker = AsyncRedisBroker(
    url="redis://localhost:6379/2"
)

app = QueueTasks(
    broker=broker
)
```

### Worker (Воркер)

Выполняет задачи, полученные из очереди. Поддерживает параллельную (и асинхронную
обработку, если используется асинхронный компонент).

Пример:

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker

broker = AsyncRedisBroker(
    url="redis://localhost:6379/2"
)

# Worker — исполнитель задач
worker = AsyncWorker(
    broker=broker
)

app = QueueTasks(
    broker=broker,
    worker=worker
)

```

### Storage (Хранилище)

Сохраняет данные о задачах (статус, результат, время выполнения и др.). Является
частью брокера, но может быть переопределён.

Пример:

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker
from qtasks.storages import AsyncRedisStorage


# Storage — хранилище задач
storage = AsyncRedisStorage(
    url="redis://localhost:6379/2"
)

broker = AsyncRedisBroker(
    url="redis://localhost:6379/2",
    storage=storage
)

worker = AsyncWorker(
    broker=broker
)

app = QueueTasks(
    broker=broker,
    worker=worker
)
```

### Starter (Стартер)

Отвечает за запуск всех компонентов фреймворка. Позволяет централизованно управлять
жизненным циклом приложения.

Пример:

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker
from qtasks.starters import AsyncStarter

broker = AsyncRedisBroker(
    url="redis://localhost:6379/2"
)

worker = AsyncWorker(
    broker=broker
)

app = QueueTasks(
    broker=broker,
    worker=worker
)

if __name__ == "__main__":
    # Starter - Запуск приложения
    starter = AsyncStarter(
        worker=worker,
        broker=broker
    )
    app.run_forever(starter=starter)
```

## Дополнительные компоненты

## GlobalConfig (Глобальная конфигурация)

Хранит глобальные настройки и параметры, доступные всем компонентам. Обычно реализуется
внутри хранилища.

Пример:

```py
from qtasks.asyncio import QueueTasks
from qtasks.workers import AsyncWorker
from qtasks.brokers import AsyncRedisBroker
from qtasks.storages import AsyncRedisStorage
from qtasks.configs import AsyncRedisGlobalConfig


# GlobalConfig — глобальные переменные и настройки
global_config = AsyncRedisGlobalConfig(
    url="redis://localhost:6379/2"
)


storage = AsyncRedisStorage(
    url="redis://localhost:6379/2",
    global_config=global_config
)

broker = AsyncRedisBroker(
    url="redis://localhost:6379/2",
    storage=storage
)

worker = AsyncWorker(
    broker=broker
)

app = QueueTasks(
    broker=broker,
    worker=worker
)
```

## Plugins (Плагины)

Расширяют функциональность фреймворка. Могут подключаться к любому компоненту,
например: логирование, кастомные триггеры и т.п.

Пример:

```py
from qtasks import QueueTasks

app = QueueTasks()

# Плагин для нахожения параметров `**kwargs` в `@app.task`
class TestPlugin(BasePlugin):
    def __init__(self, name=None):
        super().__init__(name)

        self.handlers = {
            "task_executor_args_replace": self.task_executor_args_replace
        }

    async def start(self, *args, **kwargs):
        return super().start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        return super().stop(*args, **kwargs)

    async def trigger(self, name, **kwargs):
        handler = self.handlers.get(name)
        if handler:
            return handler(**kwargs)
        return None

    def task_executor_args_replace(self, **kwargs):
        print(kwargs)
        return None

# Подключение плагина к приложению
app.add_plugin(TestPlugin(), trigger_names=["task_executor_args_replace"], component="worker")


@app.task(test="test")
def sample_task(id: int):
    return f"Пользователь {id} записан"

```

## Timer (Таймер)

Позволяет запускать задачи по расписанию (аналог cron).

Пример:

```py
from qtasks import QueueTasks
from qtasks.timers import AsyncTimer

app = QueueTasks()

@app.task
def test():
    print("Запуск тестовой задачи")


timer = AsyncTimer(app=app)

trigger = CronTrigger(second="*/10") # Запуск каждые 10 секунд
timer.add_task(task_name="test", trigger=trigger)

timer.run_forever()
```

## WebView (В стадии разработки...)

Отдельная библиотека, предоставляющая визуальный интерфейс для мониторинга задач.

Установка:

```bash
pip install qtasks_webview
```

## Пример настройки всех компонентов вручную

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

# Пример задачи
@app.task(name="test")
async def sample_task(id: int):
    result = f"Пользователь {id} записан"
    await asyncio.sleep(id)
    return result

# Запуск с помощью Starter
if __name__ == "__main__":
    starter = AsyncStarter(
        name="QueueTasks",
        worker=worker,
        broker=broker
    )
    app.run_forever(starter=starter)
```
