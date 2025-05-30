# QTasks - Фреймворк для очередей задач.
![CI](https://github.com/txello/qtasks/actions/workflows/ci.yml/badge.svg)
![Docs](https://github.com/txello/qtasks/actions/workflows/docs.yml/badge.svg)

Документация: https://txello.github.io/qtasks/

PyPI: https://pypi.org/project/qtasks/

QTasks — это современный фреймворк для обработки задач, разработанный с упором на простоту, гибкость и расширяемость. Он легко интегрируется в проекты любого масштаба и подходит как новичкам, так и опытным разработчикам.

## Особенности
* Простой — Легко настраивается и быстро осваивается. Интуитивный API и понятная структура проекта.
* Настраиваемый — Каждый компонент можно заменить или адаптировать под свои нужды. Вы управляете логикой выполнения.
* Расширяемый — Поддержка плагинов и модулей позволяет легко добавлять новые возможности и интеграции.

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

app.run_forever()

# Вызов задачи:
# app.add_task("mytest", args=("Тест",))
# error_zero.add_task()
```