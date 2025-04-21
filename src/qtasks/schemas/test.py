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
        return cls(worker=True, broker=True, storage=True, global_config=True, plugins=True)
    
    @classmethod
    def only_worker(cls, plugins: bool = False):
        return cls(worker=True, plugins=plugins)
    
    @classmethod
    def only_broker(cls, plugins: bool = False):
        return cls(broker=True, plugins=plugins)
    
    @classmethod
    def full_broker(cls):
        return cls(broker=True, storage=True, global_config = True, plugins = True)