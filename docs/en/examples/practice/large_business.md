# Example of using QTasks in large businesses

QTasks scales for use in high-load systems and is suitable
for enterprise-level use thanks to its modular architecture, expandability,
and task execution control. This system can be used for task processing in
microservice architecture, automation of complex chains, and load distribution.

---

## 🏢 Scenario

A large company has dozens of microservices:

1. They need to be connected via background task processing.
2. Ensure reliable execution and control.
3. Maintain scalability, fault tolerance, and integration with
external systems (Kafka, Redis, PostgreSQL, REST, gRPC).

---

## ⚙️ Distributed task processing

Deploy workers on different servers/containers:

```bash
py -m qtasks -A myproject.qtasks_app run --worker-id node1
py -m qtasks -A myproject.qtasks_app run --worker-id node2
```

Can be run with different configurations using environment variables or command
line arguments.

---

## 🔀 Integration with Kafka and other brokers

```python
from my_kafka_broker import KafkaBroker

app = QueueTasks(broker=KafkaBroker(...))
```

Custom `Storage`, `GlobalConfig`, and other components are also supported.

---

## 🧩 TaskManager for managing task strategies

```python
from qtasks.components.task_manager import TaskManager

class MyManager(TaskManager):
    def mutate(self, task):
        if task.name == "heavy_task":
            task.timeout = 120
        return task

app.config.task_manager = MyManager()
```

---

## 📊 Integration with BI and internal services

Using `generate_handler`, `yield`, `middlewares`, tasks can be used to build complex
pipelines:

```python
@app.task(generate_handler=send_to_bi)
def export_metrics():
    for report in generate_big_reports():
        yield report
```

---

## 🧠 Control and monitoring

In conjunction with QTasks WebView, you can:

* track task status;
* filter by type/error/time;
* cancel, restart, view logs;
* integrate into corporate dashboards.

---

## ✅ Result

QTasks in a large company allows you to:

* flexibly configure components (broker, storage, config);
* manage distributed task processing;
* extend task behavior without rewriting the core;
* integrate with BI, monitoring, logging, Kafka, REST, gRPC, etc.

This makes QTasks the foundation of a framework for enterprise-level automation
and event processing.
