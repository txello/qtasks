"""Base Task Executor."""
from __future__ import annotations

import inspect
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    get_args,
    get_origin,
    overload,
)

from typing_extensions import Doc

from qtasks.logs import Logger
from qtasks.schemas.argmeta import ArgMeta
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class BaseTaskExecutor(Generic[TAsyncFlag], ABC):
    """
    `BaseTaskExecutor` - An abstract class that is the foundation for task executor classes.

    ## Example

    ```python
    from qtasks.executors.base import BaseTaskExecutor

    class MyTaskExecutor(BaseTaskExecutor):
        def __init__(self, name: str):
            super().__init__(name=name)
            pass
    ```
    """

    def __init__(
        self,
        task_func: Annotated[
            TaskExecSchema,
            Doc("""
                    `TaskExecSchema` schema.
                    """),
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    `TaskPrioritySchema` schema.
                    """),
        ],
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        plugins: Annotated[
            dict[str, list[BasePlugin]] | None,
            Doc("""
                    Array of Plugins.

                    Default: `Empty array`.
                    """),
        ] = None,
    ):
        """
        Initializing the class. Occurs inside a `Worker` before a task is processed.

        Args:
            task_func (TaskExecSchema): Schema `TaskExecSchema`.
            task_broker(TaskPrioritySchema): Schema `TaskPrioritySchema`.
            log (Logger, optional): class `qtasks.logs.Logger`. Default: `qtasks._state.log_main`.
            plugins (Dict[str, List[BasePlugin]], optional): Plugin dictionary. Default: `Empty dictionary`.
        """
        self.task_func = task_func
        self.task_broker = task_broker
        self._args = self.task_broker.args.copy()
        self._kwargs = self.task_broker.kwargs.copy()
        self._result: Any = None
        self.echo = None

        self.decode_cls = lambda res: json.dumps(res, ensure_ascii=False)

        self.log = log
        if self.log is None:
            import qtasks._state

            self.log = qtasks._state.log_main
        self.log = self.log.with_subname(self.__class__.__name__)

        self.plugins = plugins or {}

    @overload
    def before_execute(self: BaseTaskExecutor[Literal[False]]) -> None: ...

    @overload
    async def before_execute(self: BaseTaskExecutor[Literal[True]]) -> None: ...

    def before_execute(self) -> None | Awaitable[None]:
        """Called before a task is executed."""
        pass

    @overload
    def after_execute(self: BaseTaskExecutor[Literal[False]]) -> None: ...

    @overload
    async def after_execute(self: BaseTaskExecutor[Literal[True]]) -> None: ...

    def after_execute(self) -> None | Awaitable[None]:
        """Called after a task has completed."""
        pass

    @overload
    def execute_middlewares_before(
        self: BaseTaskExecutor[Literal[False]],
    ) -> None: ...

    @overload
    async def execute_middlewares_before(
        self: BaseTaskExecutor[Literal[True]],
    ) -> None: ...

    def execute_middlewares_before(self) -> None | Awaitable[None]:
        """Calling middleware before the task is completed."""
        pass

    @overload
    def execute_middlewares_after(self: BaseTaskExecutor[Literal[False]]) -> None: ...

    @overload
    async def execute_middlewares_after(
        self: BaseTaskExecutor[Literal[True]],
    ) -> None: ...

    def execute_middlewares_after(self) -> None | Awaitable[None]:
        """Calling middleware after completing a task."""
        pass

    @overload
    def run_task(self: BaseTaskExecutor[Literal[False]]) -> Any: ...

    @overload
    async def run_task(self: BaseTaskExecutor[Literal[True]]) -> Any: ...

    def run_task(self) -> Any | Awaitable[Any]:
        """
        Calling a task.

        Returns:
            Any: Result of the task.
        """
        pass

    @overload
    def execute(self: BaseTaskExecutor[Literal[False]], decode: bool = True) -> str:
        """
        Task processing.

        Args:
            decode (bool, optional): Decoding. Default: `True`.

        Returns:
            str: Result of the task.
        """
        ...

    @overload
    def execute(self: BaseTaskExecutor[Literal[False]], decode: bool = False) -> Any:
        """
        Task processing.

        Args:
            decode (bool, optional): Decoding. Default: `True`.

        Returns:
            Any: Result of the task.
        """
        ...

    @overload
    async def execute(
        self: BaseTaskExecutor[Literal[True]], decode: bool = True
    ) -> str:
        """
        Task processing.

        Args:
            decode (bool, optional): Decoding. Default: `True`.

        Returns:
            str: Result of the task.
        """
        ...

    @overload
    async def execute(
        self: BaseTaskExecutor[Literal[True]], decode: bool = False
    ) -> Any:
        """
        Task processing.

        Args:
            decode (bool, optional): Decoding. Default: `True`.

        Returns:
            Any: Result of the task.
        """
        ...

    @abstractmethod
    def execute(
        self, decode=None
    ) -> Any | str | Awaitable[Any | str]:
        """
        Task processing.

        Args:
            decode (bool, optional): Decoding. Default: `True`.

        Returns:
            Any|str: Result of the task.
        """
        pass

    @overload
    def decode(self: BaseTaskExecutor[Literal[False]]) -> str: ...

    @overload
    async def decode(self: BaseTaskExecutor[Literal[True]]) -> str: ...

    def decode(self) -> str | Awaitable[str]:
        """
        Decoding the task.

        Returns:
            str: Result of the task.
        """
        return ""

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc("""
                    Plugin.
                    """),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc("""
                    The name of the triggers for the plugin.

                    Default: Default: will be added to `Globals`.
                    """),
        ] = None,
    ) -> None:
        """
        Add a plugin to the class.

        Args:
            plugin (BasePlugin): Plugin
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    def _extract_args_kwargs_from_func(self, func: Any) -> tuple[list, dict]:
        """
        Retrieves the values of the arguments from a function if they are given as default values.

        Args:
            func (Callable): The function from which args and kwargs are retrieved.

        Returns:
            Tuple[list, dict]: args and kwargs ready to be passed to `_build_args_info`.
        """
        sig = inspect.signature(func)
        args = []
        kwargs = {}

        for name, param in sig.parameters.items():
            if param.default is not inspect.Parameter.empty:
                # Именованный аргумент (имеет значение по умолчанию)
                kwargs[name] = param.default
            elif param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                # Позиционный аргумент без значения по умолчанию (просто None)
                args.append(None)

        return args, kwargs

    def _build_args_info(self, args: list, kwargs: dict) -> list[ArgMeta]:
        """
        Constructs an ArgMeta list of args and kwargs based on function annotations.

        Args:
            args (list): Positional arguments.
            kwargs (dict): Named arguments.

        Returns:
            List[ArgMeta]: List of argument metadata.
        """
        args_info: list[ArgMeta] = []
        func = self.task_func.func

        try:
            sig = inspect.signature(func)
            parameters = list(sig.parameters.items())
        except (ValueError, TypeError):
            parameters = []

        annotations = getattr(func, "__annotations__", {})

        # Обработка позиционных аргументов
        for idx, value in enumerate(args):
            param_name = parameters[idx][0] if idx < len(parameters) else f"arg{idx}"
            annotation = annotations.get(param_name)
            origin = get_origin(annotation)
            raw_type = get_args(annotation)[0] if get_args(annotation) else annotation
            args_info.append(
                ArgMeta(
                    name=param_name,
                    value=value,
                    origin=origin,
                    raw_type=raw_type,
                    annotation=annotation,
                    is_kwarg=False,
                    index=idx,
                )
            )

        # Обработка именованных аргументов
        for key, value in kwargs.items():
            annotation = annotations.get(key)
            origin = get_origin(annotation)
            raw_type = get_args(annotation)[0] if get_args(annotation) else annotation
            args_info.append(
                ArgMeta(
                    name=key,
                    value=value,
                    origin=origin,
                    raw_type=raw_type,
                    annotation=annotation,
                    is_kwarg=True,
                    key=key,
                )
            )

        return args_info
