# QTasks - Фреймворк для очередей задач

![CI](https://github.com/txello/qtasks/actions/workflows/ci.yml/badge.svg)
![Docs](https://github.com/txello/qtasks/actions/workflows/docs.yml/badge.svg)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/qtasks?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/qtasks)

Документация: [https://txello.github.io/qtasks/](https://txello.github.io/qtasks/)

PyPI: [https://pypi.org/project/qtasks/](https://pypi.org/project/qtasks/)

QTasks — это современный фреймворк для обработки задач,
разработанный с упором на простоту, гибкость и расширяемость.
Он легко интегрируется в проекты любого масштаба
и подходит как новичкам, так и опытным разработчикам.

## Особенности

* Простой — Легко настраивается и быстро осваивается. Интуитивный API
и понятная структура проекта.
* Настраиваемый — Каждый компонент можно заменить или адаптировать под
свои нужды. Вы управляете логикой выполнения.
* Расширяемый — Поддержка плагинов и модулей позволяет легко добавлять новые
возможности и интеграции.

## Установка

### Базовая установка (Redis по умолчанию)

```bash
pip install qtasks
```

### Установка с поддержкой других брокеров

#### RabbitMQ

```bash
pip install qtasks[rabbitmq]
```

#### Kafka

```bash
pip install qtasks[kafka]
```

## Пример

```py
from qtasks import QueueTasks

app = QueueTasks()

@app.task(name="mytest") # Пример обычной задачи
def mytest(text: str):
    print(text)
    return text

@app.task(name="error_zero") # Пример задачи с ошибкой
def error_zero():
    result = 1/0
    return


# Поддерживает генераторы!
def gen_func(result):
    return result + 1
@app.task(generate_handler=gen_func)
async def test_gen(n: int):
    for _ in range(n):
        n += 1
        yield n

if __name__ == "__main__":
    app.run_forever()

# Вызов задачи:
# app.add_task("mytest", args=("Тест",)). task.returning: "Тест"
# error_zero.add_task(). task.status: "ERROR"
# test_gen.add_task(args=(5,)). task.returning: [7, 8, 9, 10, 11]
```
