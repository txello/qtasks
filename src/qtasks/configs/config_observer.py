from typing import Any, Callable, Dict, List, get_type_hints
from qtasks.configs.config import QueueConfig

class ConfigObserver:
    def __init__(self, config: QueueConfig):
        self._config = config
        self._callbacks: List[Callable[[str, Any], None]] = []
        self._dynamic_fields: Dict[str, Any] = {}

    def subscribe(self, callback: Callable[[str, Any], None]):
        self._callbacks.append(callback)

    def _notify(self, key: str, value: Any):
        for callback in self._callbacks:
            callback(self._config, key, value)

    def __getattr__(self, item):
        # Проверяем динамические поля
        if item in self._dynamic_fields:
            return self._dynamic_fields[item]
        # Доступ к полям config
        return getattr(self._config, item)

    def __setattr__(self, key, value):
        if key in ('_config', '_callbacks', '_dynamic_fields'):
            super().__setattr__(key, value)
        elif hasattr(self._config, key):
            setattr(self._config, key, value)
            self._notify(key, value)
        else:
            self._dynamic_fields[key] = value
            self._notify(key, value)

    def __repr__(self):
        return str(self._config)
    
ConfigObserver.__annotations__ = get_type_hints(QueueConfig)
