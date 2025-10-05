"""Base Plugin."""

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Dict, Generic, Literal, Optional, Union, overload
from typing_extensions import Annotated, Doc

from qtasks.types.typing import TAsyncFlag


class BasePlugin(Generic[TAsyncFlag], ABC):
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

    @overload
    def trigger(
        self: "BasePlugin[Literal[False]]", name: str, *args, **kwargs
    ) -> Union[Dict[str, Any], None]: ...

    @overload
    async def trigger(
        self: "BasePlugin[Literal[True]]", name: str, *args, **kwargs
    ) -> Union[Dict[str, Any], None]: ...

    @abstractmethod
    def trigger(
        self, name: str, *args, **kwargs
    ) -> Union[Dict[str, Any], None, Awaitable[Union[Dict[str, Any], None]]]:
        """Триггер плагина.

        Args:
            name (str): Имя триггера.
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        pass

    @overload
    def start(self: "BasePlugin[Literal[False]]", *args, **kwargs) -> None: ...

    @overload
    async def start(self: "BasePlugin[Literal[True]]", *args, **kwargs) -> None: ...

    @abstractmethod
    def start(self, *args, **kwargs) -> Union[None, Awaitable[None]]:
        """Запускает Плагин.

        Args:
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        pass

    @overload
    def stop(self: "BasePlugin[Literal[False]]", *args, **kwargs) -> None: ...

    @overload
    async def stop(self: "BasePlugin[Literal[True]]", *args, **kwargs) -> None: ...

    @abstractmethod
    def stop(self, *args, **kwargs) -> Union[None, Awaitable[None]]:
        """Останавливает Плагин.

        Args:
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        pass
