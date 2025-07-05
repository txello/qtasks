"""Test Schema."""

from dataclasses import dataclass


@dataclass
class TestConfig:
    """
    Конфигурация тестирования очередей задач.

    Attributes:
        worker (bool): Воркер.
        broker (bool): Брокер.
        storage (bool): Хранилище.
        global_config (bool): Глобальный конфиг.
        plugins (bool): Плагины.

    """

    worker: bool = False
    broker: bool = False
    storage: bool = False
    global_config: bool = False
    plugins: bool = False

    @classmethod
    def full(cls):
        """Создать полную конфигурацию тестирования."""
        return cls(
            worker=True, broker=True, storage=True, global_config=True, plugins=True
        )

    @classmethod
    def only_worker(cls, plugins: bool = False):
        """Создать конфигурацию тестирования только для воркера."""
        return cls(worker=True, plugins=plugins)

    @classmethod
    def only_broker(cls, plugins: bool = False):
        """Создать конфигурацию тестирования только для брокера."""
        return cls(broker=True, plugins=plugins)

    @classmethod
    def full_broker(cls):
        """Создать полную конфигурацию тестирования для брокера."""
        return cls(broker=True, storage=True, global_config=True, plugins=True)
