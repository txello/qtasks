# Компоненты QueueTasks
Фреймворк QueueTasks построен по компонентной архитектуре — каждый модуль отвечает за свою часть работы и может быть заменён или расширен.

## Основные компоненты

### QueueTasks
Центральный объект фреймворка. Используется для регистрации и запуска задач, а также взаимодействия с другими компонентами.

### Worker (Воркер)
Выполняет задачи, полученные из очереди. Поддерживает параллельную и асинхронную обработку.

### Broker (Брокер)
Отвечает за приём и маршрутизацию задач. Передаёт задачи воркеру.

### Storage (Хранилище)
Сохраняет данные о задачах (статус, результат, время выполнения и др.). Является частью брокера, но может быть переопределён.

### Starter (Стартер)
Отвечает за запуск всех компонентов фреймворка. Позволяет централизованно управлять жизненным циклом приложения.

## Дополнительные компоненты

## GlobalConfig (Глобальная конфигурация)
Хранит глобальные настройки и параметры, доступные всем компонентам. Обычно реализуется внутри хранилища.

## Plugins (Плагины)
Расширяют функциональность фреймворка. Могут подключаться к любому компоненту, например: логирование, кастомные триггеры и т.п.

## Timer (Таймер)
Позволяет запускать задачи по расписанию (аналог cron).

## WebView
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