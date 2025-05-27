from typing import Any, Callable, Dict, List, TypeVar, Generic
from qtasks.configs.config import QueueConfig

T = TypeVar('T', bound=QueueConfig)

class ConfigObserver(Generic[T]):
    def __init__(self, config: QueueConfig):
        self._config = config
        self._callbacks: List[Callable[[str, Any], None]] = []
        self._dynamic_fields: Dict[str, Any] = {}

    def subscribe(self, callback: Callable[[str, Any], None]):
        self._callbacks.append(callback)

    def _notify(self, config: QueueConfig, key: str, value: Any):
        for callback in self._callbacks:
            callback(config, key, value)

    def __getattr__(self, item):
        # Сначала проверяем динамические поля
        if item in self._dynamic_fields:
            return self._dynamic_fields[item]
        # Затем проверяем стандартные поля
        if hasattr(self._config, item):
            return getattr(self._config, item)
        raise AttributeError(f"'Config' has no attribute '{item}'")

    def __setattr__(self, key, value):
        if key in ('_config', '_callbacks', '_dynamic_fields'):
            super().__setattr__(key, value)
        elif hasattr(self._config, key):
            setattr(self._config, key, value)
            self._notify(self._config, key, value)
        else:
            self._dynamic_fields[key] = value
            self._notify(self._config, key, value)
