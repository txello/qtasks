# Установка

`QTasks` можно установить как через PyPI, так и из исходного кода на GitHub.
Поддерживаются различные брокеры сообщений, включая Redis (по умолчанию), RabbitMQ
и Kafka.

## Установка через PyPI

### Базовая установка (Redis по умолчанию)

```bash
pip install qtasks
```

### Установка WebView (опциональный компонент для мониторинга)

```bash
pip install qtasks_webview
```

### Установка с поддержкой других брокеров

!!! info
    Убедитесь, что соответствующий брокер сообщений установлен и настроен на вашем
    сервере.

#### RabbitMQ

```bash
pip install qtasks[rabbitmq]
```

#### Kafka

```bash
pip install qtasks[kafka]
```

## Установка из исходного кода (GitHub)

Если вы хотите использовать последнюю версию из репозитория или внести изменения:

```bash
git clone https://github.com/txello/qtasks.git
cd qtasks/
pip install .
```
