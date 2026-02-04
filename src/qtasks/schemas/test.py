"""Test Schema."""

from dataclasses import dataclass


@dataclass
class TestConfig:
    """
    Configuration for testing task queues.

    Attributes:
        worker (bool): Worker.
        broker (bool): Broker.
        storage (bool): Storage.
        global_config (bool): Global config.
        plugins (bool): Plugins.
    """

    __test__ = False

    worker: bool = False
    broker: bool = False
    storage: bool = False
    global_config: bool = False
    plugins: bool = False

    @classmethod
    def full(cls):
        """Create a complete testing configuration."""
        return cls(
            worker=True, broker=True, storage=True, global_config=True, plugins=True
        )

    @classmethod
    def only_worker(cls, plugins: bool = False):
        """Create a testing configuration for the worker only."""
        return cls(worker=True, plugins=plugins)

    @classmethod
    def only_broker(cls, plugins: bool = False):
        """Create a test configuration for the broker only."""
        return cls(broker=True, plugins=plugins)

    @classmethod
    def full_broker(cls):
        """Create a complete testing configuration for the broker."""
        return cls(broker=True, storage=True, global_config=True, plugins=True)
