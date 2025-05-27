from typing import Any, Callable, Dict, List
from qtasks.configs.config import QueueConfig

class ConfigObserver(QueueConfig):
    def __init__(self, config: QueueConfig):
        self._config = config
        self._callbacks: List[Callable[[str, Any], None]] = []
        self._dynamic_fields: Dict[str, Any] = {}

    def subscribe(self, callback: Callable[[str, Any], None]):
        self._callbacks.append(callback)

    def _notify(self, config: QueueConfig, key: str, value: Any):
        for callback in self._callbacks:
            callback(config, key, value)

    def __getattribute__(self, item):
        # Пропускаем внутренние поля
        if item in ('_callbacks', '_dynamic_fields', '_notify', 'subscribe', '__dict__', '__class__', '__annotations__'):
            return super().__getattribute__(item)
        # Проверяем динамические поля
        dynamic_fields = super().__getattribute__('_dynamic_fields')
        if item in dynamic_fields:
            return dynamic_fields[item]
        # Проверяем обычные атрибуты (включая dataclass)
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if key in ('_config', '_callbacks', '_dynamic_fields'):
            super().__setattr__(key, value)
        elif hasattr(self._config, key):
            setattr(self._config, key, value)
            self._notify(self._config, key, value)
        else:
            self._dynamic_fields[key] = value
            self._notify(self._config, key, value)
