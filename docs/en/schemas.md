# Схемы

## Background-схема связей фреймворка

``` mermaid
sequenceDiagram
  autonumber
  Participant QueueTasks
  Participant Starter
  Participant Worker
  Participant Broker
  Participant Storage
  Participant GlobalConfig
  QueueTasks->>Starter: (Перенос логики)
  Starter->>Worker: Запуск
  Starter->>Broker: Запуск
  Broker->>Storage: Запуск
  Storage->>Broker: Остановка
  Storage->>GlobalConfig: Запуск
  GlobalConfig->>Storage: Остановка
```

На этой диаграмме показано связь компонентов.

---

## Обработка задачи сервером

``` mermaid
sequenceDiagram
  autonumber
  Participant Storage
  Participant Broker
  Participant Worker
  Participant TaskExecutor
  Broker->>Storage: Новая задача
  Broker->>Worker: Задача
  Worker->>TaskExecutor: Выполнение задачи
  Worker->>Storage: Результат
```

Этапы:

1. Сначала задача сохраняется в Хранилище
2. Затем задача отправляется в основную очередь Воркеров, и свободный
Воркер(сабворкер) получает и работает с ней
3. Воркер работает с функцией задачи через TaskExecutor и получает от него результат
4. Результат сохраняется в Хранилище

---

## Создание задачи клиентом

``` mermaid
sequenceDiagram
  autonumber
  Participant (A)syncTask.add_task()
  Participant QueueTasks.add_task()
  Participant Broker
  (A)syncTask.add_task()->>QueueTasks.add_task(): (Перенос логики)
  QueueTasks.add_task()->>Broker: Новая задача
```

Этапы:

1. Если используется (A)syncTask.add_task(), то он переносит данные на QueueTasks.add_task()
2. Отправляет новую задачу Брокеру(а точнее его серверу)

---

## Получение задачи клиентом

``` mermaid
sequenceDiagram
  autonumber
  Participant (A)syncTask.add_task()
  Participant (A)syncResult.result()
  Participant QueueTasks.get()
  Participant Storage
  (A)syncTask.add_task()->>(A)syncResult.result(): (Перенос логики)
  (A)syncResult.result()->>QueueTasks.get(): Запрос результата
  QueueTasks.get()->>Storage: Запрос результата
  Storage->>QueueTasks.get(): Получение результата
  QueueTasks.get()->>(A)syncResult.result(): Возврат результата
```

Этапы:

1. Если используется (A)syncTask.add_task(), то он переносит данные на (A)syncResult.result()
2. Запрашиваем результат через связное ядро, в котором есть Хранилище
3. Запрашиваем результат у Хранилища
4. Получаем от Хранилища данные
5. Возвращаем результат
