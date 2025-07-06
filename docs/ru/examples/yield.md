# Пример: Задача-генератор (yield)

QTasks поддерживает задачи с `yield`, как в **асинхронной**, так и **синхронной** форме. Это позволяет обрабатывать значения по мере генерации, при этом задача может быть запущена из асинхронного приложения QueueTasks, независимо от типа функции.

---

## 🔧 Пример 1: Асинхронная генерация с промежуточной обработкой

```python
async def yield_func(result):
    print(f"Обработан: {result}")
    return result + 2

@app.task(generate_handler=yield_func, echo=True)
async def test_yield(n: int):
    for _ in range(n):
        n += 1
        yield n
```
**Входные данные:** `5`

**Результат задачи:** `[8, 9, 10, 11, 12]`

---

## 🔧 Пример 2: Синхронная генерация с постобработкой

```python
def sync_handler(value):
    print("SYNC:", value)
    return value * 2

@app.task(generate_handler=sync_handler)
def sync_gen(n: int):
    for i in range(n):
        yield i + 1
```
**Входные данные:** `5`

**Результат задачи:** `[2, 4, 6, 8, 10]`

---

## 🔧 Пример 3: Генерация и сбор ID через внешний сервис

```python
async def save_to_db(value):
    db.insert({"value": value})
    return value

@app.task(generate_handler=save_to_db)
def ids():
    for id_ in range(5):
        yield f"user_{id_}"
```

**Применение:** автоматическая запись в базу данных и возврат списка записей.

---

## ⚙️ Как работает generate\_handler внутри QTasks?

* Аргумент `generate_handler` вызывается на **каждое значение**, сгенерированное `yield`.
* Результат `return` из handler'а добавляется в результирующий список (`list`) задачи.
* Если `generate_handler` определён, задача выполняется через `run_task_gen`, иначе — обычным способом.
* Настройка `generating` в `TaskExecSchema` управляет переключением на генераторный режим.

---

## 🏢 Пример использования в компании

Допустим, у вас есть задача, отправляющая уведомления сотрудникам по расписанию:

```python
async def log_notification(msg):
    logger.info("Отправлено:", msg)
    return msg

@app.task(generate_handler=log_notification)
def send_notifications():
    for employee in get_employees():
        yield f"Отправлено уведомление: {employee.email}"
```

**Результат:**

* Генератор перебирает список сотрудников.
* На каждое сообщение вызывается `generate_handler`, которое логирует или отправляет данные в систему.
* Возвращается список уведомлений.

**Такой подход удобен для:**

* Интеграций с внешними API
* Постепенного стриминга
* Задач, где важна **трансформация и контроль каждого шага**

---

## ✅ Итоги

Задачи с `yield` + `generate_handler` — это мощный инструмент реактивной обработки, который делает QTasks гибким для real-time обработки, логирования, стриминга и более сложных пайплайнов.

Поддержка как `async`, так и `sync` делает его удобным в любом стиле разработки.
