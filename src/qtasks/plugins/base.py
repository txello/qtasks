"""Base Plugin."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from typing_extensions import Annotated, Doc


class BasePlugin(ABC):
    """
    `BasePlugin` - Абстрактный класс, который является фундаментом для Плагинов.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.plugins.base import BasePlugin

    class MyPlugin(BasePlugin):
        def __init__(self, name: str = None):
            super().__init__(name=name)
            pass
    ```
    """

    def __init__(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Плагинов.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        """Инициализация плагина.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `None`.
        """
        self.name: Union[str, None] = name
        pass

    @abstractmethod
    def trigger(self, name: str, *args, **kwargs) -> Union[Dict[str, Any], None]:
        """Триггер плагина.

        Args:
            name (str): Имя триггера.
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        pass

    @abstractmethod
    def start(self, *args, **kwargs):
        """Запускает Плагин.

        Args:
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        pass

    @abstractmethod
    def stop(self, *args, **kwargs):
        """Останавливает Плагин."""
        pass
