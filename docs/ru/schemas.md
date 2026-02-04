# Схемы

## Background-схема связей фреймворка

```mermaid
sequenceDiagram
  autonumber
  participant QueueTasks
  participant Starter
  participant Worker
  participant Broker
  participant Storage
  participant GlobalConfig

  QueueTasks->>Starter: Инициализация / конфигурация
  Starter->>Worker: Запуск
  Starter->>Broker: Запуск
  Broker->>Storage: Инициализация / запуск
  Storage->>GlobalConfig: Инициализация (если есть)

  GlobalConfig-->>Storage: Остановка
  Storage-->>Broker: Остановка
  Broker-->>Worker: Остановка
  Starter-->>QueueTasks: Завершение
```

Эта диаграмма показывает связь компонентов и правильный порядок запуска:

* Starter запускает **только Worker и Broker**.
* Broker запускает **Storage**.
* Storage запускает **GlobalConfig**, если он присутствует.
* Остановка происходит в обратном порядке.

---

## Обработка задачи сервером

```mermaid
sequenceDiagram
  autonumber
  participant Storage
  participant Broker
  participant Worker
  participant TaskExecutor

  Broker->>Storage: Сохранить новую задачу
  Broker->>Worker: Передать задачу
  Worker->>TaskExecutor: Выполнение задачи
  TaskExecutor-->>Worker: Результат выполнения
  Worker->>Storage: Сохранить результат
```

Эта диаграмма отражает фактический процесс:

1. Задача сохраняется в Storage.
2. Брокер передаёт задачу воркеру.
3. Worker вызывает TaskExecutor — заменяемый компонент выполнения задач.
4. TaskExecutor выполняет функцию задачи, вызывает middlewares_before/middlewares_after,
обрабатывает ошибки и retry.
5. Результат передаётся воркеру и сохраняется в Storage.

---

## Создание задачи клиентом

```mermaid
sequenceDiagram
  autonumber
  participant AT as (A)syncTask.add_task()
  participant QT as QueueTasks.add_task()
  participant Broker

  AT->>QT: Подготовка параметров задачи
  QT->>Broker: Регистрация новой задачи
```

Процесс выглядит так:

1. `(A)syncTask.add_task()` или `TaskCls().__call__().add_task()` подготавливает
параметры.
2. Внутренне всё переводится на `QueueTasks.add_task()`.
3. Брокер принимает задачу и сохраняет её через Storage.

---

## Получение результата задачи клиентом

```mermaid
sequenceDiagram
  autonumber
  participant AT as (A)syncTask.add_task()
  participant AR as (A)syncResult.result()
  participant QT as QueueTasks
  participant Broker
  participant Storage

  AT->>AR: Создание объекта результата
  AR->>QT: Запрос результата
  QT->>Broker: Прокси-запрос
  Broker->>Storage: Чтение результата
  Storage-->>Broker: Данные
  Broker-->>QT: Результат
  QT-->>AR: Возврат результата
```

Этапы:

1. `(A)syncTask.add_task()` создаёт `(A)syncResult`.
2. `(A)syncResult.result()` вызывает `QueueTasks`, который проксирует запрос.
3. `QueueTasks.get()` перенаправляется в `Broker.get()`.
4. Broker запрашивает данные у Storage.
5. Storage возвращает результат.
6. Результат поднимается обратно через Broker → QueueTasks → (A)syncResult.
