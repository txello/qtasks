# Пример переменных в функциях задач

`QTasks` поддерживает два встроенных механизма управления логикой задач:

* **Depends** — вызов внешних функций, генераторов или контекстных менеджеров при
выполнении задачи.
* **State** — хранение и обмен состоянием между задачами.

---

## 🔧 Пример 1: Depends (зависимости)

`Depends` позволяет подключать ресурсы, которые нужно инициализировать и закрыть
по завершении.
Функция может быть простой, генераторной или асинхронным контекстным менеджером.

```python
from qtasks.plugins import Depends
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    db = await connect_to_db()
    yield db
    print("close...")
    await db.disconnect()

@app.task
async def test_depends(depends: Depends(get_db)):
    depends.execute(...)
    print("Вызов выполнен")
    return
```

**Вывод в консоль:**

```bash
<Сервер запускает задачу>
Вызов выполнен
<Сервер завершает задачу>
close...
```

**Итог:** задача использует подключение к БД, которое автоматически закрывается.

---

## 🔧 Пример 2: State (состояние между задачами)

`State` — это хранилище данных, доступное для последовательных шагов одной логики.

```python
from qtasks.plugins import AsyncState

class MyState(AsyncState):
    pass

@app.task
async def step1(state: MyState):
    await state.set("state", "await_phone")
    await state.update(step=1, prompt="Введите телефон")
    return "ok"

@app.task
async def step2(state: MyState):
    print(await state.get_all())

    cur = await state.get("state")
    if cur != "await_phone":
        return "error"
    await state.update(step=2)
    await state.delete("state")
    await state.clear()
    return "ok"
```

**Вывод в консоль:**

```bash
{"state": "await_phone", "step": 1, "prompt": "Введите телефон"}
```

**Итог:** первый шаг записал данные в состояние, второй шаг их прочитал, проверил
и очистил.

---

## ⚙️ Как это работает внутри `QTasks`?

* **Depends** регистрируется при вызове задачи и функция внутри запускается при
выполнении TaskExecutor. Это удобно для подключения к БД, API или внешним сервисам.
* **State** реализован как асинхронное key-value хранилище. Оно поддерживает
`set`, `update`, `get`, `delete`, `clear`, а также чтение всех данных разом (`get_all`).

---

## 🏢 Пример использования в компании

Допустим, реализуется пошаговая форма регистрации:

1. `step1` показывает пользователю запрос на ввод телефона.
2. `step2` проверяет, что введён телефон, и двигает процесс дальше.

При этом `Depends` может использоваться для работы с подключением к базе, а `State`
— для хранения промежуточных данных пользователя.

---

## ✅ Итоги

* **Depends** — для подключения зависимостей (ресурсы, контексты, сервисы).
* **State** — для пошагового хранения данных между задачами.

Вместе они позволяют строить гибкие пайплайны: от интеграций с БД до чат-ботов
и сложных бизнес-процессов.
