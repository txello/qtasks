# Installation

`QTasks` can be installed via PyPI or used directly from the source code.
The framework does not restrict the choice of infrastructure and supports multiple
message brokers.
Redis is used by default.

## Installation via PyPI

### Basic installation (Redis by default)

```bash
pip install qtasks
```

### WebView installation (optional)

The `QTasks WebView` component provides a web interface for monitoring tasks.

```bash
pip install qtasks_webview
```

### Installation with support for other brokers

!!! info
    Before installing, make sure that the selected broker is deployed and accessible
    to your application.

#### RabbitMQ

```bash
pip install qtasks[rabbitmq]
```

#### Kafka

```bash
pip install qtasks [kafka]
```

## Installation from source code (GitHub)

Use the source repository if you need the latest version or if you
plan to make changes:

```bash
git clone https://github.com/txello/qtasks.git
cd qtasks/
pip install .
```
