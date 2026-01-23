# QTasks

![CI](https://github.com/txello/qtasks/actions/workflows/ci.yml/badge.svg)
![Docs](https://github.com/txello/qtasks/actions/workflows/docs.yml/badge.svg)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/qtasks?period=total\&units=INTERNATIONAL_SYSTEM\&left_color=BLACK\&right_color=GREEN\&left_text=downloads)](https://pepy.tech/projects/qtasks)
![Python](https://img.shields.io/pypi/pyversions/qtasks)
![License](https://img.shields.io/github/license/txello/qtasks)

**QTasks** is a modern task queue framework for Python with a component-based
architecture and a focus on extensibility, transparency, and control over task execution.
The project is aimed at both small services and complex distributed systems
where standard solutions are redundant or inflexible.

---

## Key features

* **Component-based architecture**
  Broker, Worker, Storage, GlobalConfig, Starter — each component is isolated and
  fully replaceable.

* **Async and Sync tasks**
  Support for `asyncio`, synchronous functions, and generators.

* **Plugins instead of rigid logic**
  Retry, concurrency, logging, and execution strategies are implemented
  through plugins.

* **Typed data flow**
  Data transfer between components via schemas (`dataclasses`).

* **Transparent testing**
  In-memory brokers and storages, component isolation, tests without running workers.

* **CLI-first approach**
  Manage startup and environment through CLI without hidden magic.

---

## When to choose QTasks

* You need full control over the queue architecture.
* You need to write your own brokers, workers, and plugins.
* Predictable behavior and minimalism of the core are important.
* The project is growing and requires scalability without rewriting the logic.

---

## Installation

### Basic installation (Redis by default)

```bash
pip install qtasks
```

### Additional brokers

#### RabbitMQ

```bash
pip install qtasks[rabbitmq]
```

#### Kafka

```bash
pip install qtasks[kafka]
```

---

## Quick start

```python
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="echo")
def echo(text: str) -> str:
    return text

@app.task(name="divide")
def divide(a: int, b: int):
    return a / b

if __name__ == "__main__":
    app.run_forever()
```

Calling tasks:

```python
# echo.add_task("Hello", timeout=50).returning -> "Hello"
# divide.add_task(1, 0, timeout=50).status -> "ERROR"
```

---

## Generators and streaming tasks

QTasks supports generator tasks without additional wrappers:

```python
async def gen_handler(value: int) -> int:
    return value + 1

@app.task(generate_handler=gen_handler)
async def counter(n: int):
    for _ in range(n):
        n += 1
        yield n
```

Result of execution:

```python
# await (counter.add_task(5, timeout=50)).returning -> [7, 8, 9, 10, 11]
```

---

## CLI

Starting the worker:

```bash
qtasks -A qtasks_app:app run
```

Or directly:

```bash
python -m qtasks -A qtasks_app:app run
```

In the future, the CLI will be expanded (inspect, stats, monitoring).

---

## Architecture (briefly)

```md
┌──────────┐          ┌──────────┐
│  Broker  │ ───────▶ │          │
│          │          │          │
└────┬─────┘          │          │
     │                │ Storage  │
     ▼                │          │
┌──────────┐ ───────▶ │          │
│  Worker  │          │          │
│          │          └──────────┘
└──────────┘
```

Additionally:

* plugins;
* routers;
* background components;
* WebView (optional).

---

## Documentation

👉 [https://docs.qtasks.tech](https://docs.qtasks.tech)

---

## Project status

* Active development
* Stable versions
* Python 3.8–3.12
* Open to contributions

---

## License

MIT License
