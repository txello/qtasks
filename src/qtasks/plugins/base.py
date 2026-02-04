"""Base Plugin."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Annotated, Any, Generic, Literal, overload

from typing_extensions import Doc

from qtasks.types.typing import TAsyncFlag


class BasePlugin(Generic[TAsyncFlag], ABC):
    """
    `BasePlugin` - An abstract class that is the foundation for Plugins.

    ## Example

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
            str | None,
            Doc("""
                    Project name. This name can be used for tags for Plugins.

                    Default: `None`.
                    """),
        ] = None,
        *args,
        **kwargs
    ):
        """
        Initializing the plugin.

        Args:
            name (str, optional): Project name. Default: `None`.
        """
        self.name: str | None = name

        self.plugin_cache: dict[str, Any] = {}
        pass

    @overload
    def trigger(
        self: "BasePlugin[Literal[False]]", name: str, *args, **kwargs
    ) -> dict[str, Any] | None: ...

    @overload
    async def trigger(
        self: "BasePlugin[Literal[True]]", name: str, *args, **kwargs
    ) -> dict[str, Any] | None: ...

    @abstractmethod
    def trigger(
        self, name: str, *args, **kwargs
    ) -> dict[str, Any] | None | Awaitable[dict[str, Any] | None]:
        """
        Plugin trigger.

        Args:
            name (str): Trigger name.
            args (tuple, optional): Trigger arguments of type args.
            kwargs (dict, optional): Trigger arguments of type kwargs.
        """
        pass

    @overload
    def start(self: "BasePlugin[Literal[False]]", *args, **kwargs) -> None: ...

    @overload
    async def start(self: "BasePlugin[Literal[True]]", *args, **kwargs) -> None: ...

    @abstractmethod
    def start(self, *args, **kwargs) -> None | Awaitable[None]:
        """
        Launches the Plugin.

        Args:
            args (tuple, optional): Trigger arguments of type args.
            kwargs (dict, optional): Trigger arguments of type kwargs.
        """
        pass

    @overload
    def stop(self: "BasePlugin[Literal[False]]", *args, **kwargs) -> None: ...

    @overload
    async def stop(self: "BasePlugin[Literal[True]]", *args, **kwargs) -> None: ...

    @abstractmethod
    def stop(self, *args, **kwargs) -> None | Awaitable[None]:
        """
        Stops the Plugin.

        Args:
            args (tuple, optional): Trigger arguments of type args.
            kwargs (dict, optional): Trigger arguments of type kwargs.
        """
        pass
