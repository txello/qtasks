"""Base Task Executor."""

from abc import ABC, abstractmethod
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
    overload,
)
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.argmeta import ArgMeta
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class BaseTaskExecutor(Generic[TAsyncFlag], ABC):
    """
    `BaseTaskExecutor` - Абстрактный класс, который является фундаментом для классов исполнителей задач.

    ## Пример

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
            Doc(
                """
                    `TaskExecSchema` схема.
                    """
            ),
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    `TaskPrioritySchema` схема.
                    """
            ),
        ],
        log: Annotated[
            Optional[Logger],
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        plugins: Annotated[
            Optional[Dict[str, List["BasePlugin"]]],
            Doc(
                """
                    Массив Плагинов.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
    ):
        """Инициализация класса. Происходит внутри `Worker` перед обработкой задачи.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
            plugins (Dict[str, List[BasePlugin]], optional): Словарь плагинов. По умолчанию: `Пустой словарь`.
        """
        self.task_func = task_func
        self.task_broker = task_broker
        self._args = self.task_broker.args.copy()
        self._kwargs = self.task_broker.kwargs.copy()
        self._result: Any = None
        self.echo = None

        self.log = log
        if self.log is None:
            import qtasks._state

            self.log = qtasks._state.log_main
        self.log = self.log.with_subname(self.__class__.__name__)

        self.plugins = plugins or {}

    @overload
    def before_execute(self: "BaseTaskExecutor[Literal[False]]") -> None: ...

    @overload
    async def before_execute(self: "BaseTaskExecutor[Literal[True]]") -> None: ...

    def before_execute(self) -> Union[None, Awaitable[None]]:
        """Вызывается перед выполнением задачи."""
        pass

    @overload
    def after_execute(self: "BaseTaskExecutor[Literal[False]]") -> None: ...

    @overload
    async def after_execute(self: "BaseTaskExecutor[Literal[True]]") -> None: ...

    def after_execute(self) -> Union[None, Awaitable[None]]:
        """Вызывается после выполнения задачи."""
        pass

    @overload
    def execute_middlewares_before(
        self: "BaseTaskExecutor[Literal[False]]",
    ) -> None: ...

    @overload
    async def execute_middlewares_before(
        self: "BaseTaskExecutor[Literal[True]]",
    ) -> None: ...

    def execute_middlewares_before(self) -> Union[None, Awaitable[None]]:
        """Вызов мидлварей до выполнения задачи."""
        pass

    @overload
    def execute_middlewares_after(self: "BaseTaskExecutor[Literal[False]]") -> None: ...

    @overload
    async def execute_middlewares_after(
        self: "BaseTaskExecutor[Literal[True]]",
    ) -> None: ...

    def execute_middlewares_after(self) -> Union[None, Awaitable[None]]:
        """Вызов мидлварей после выполнения задачи."""
        pass

    @overload
    def run_task(self: "BaseTaskExecutor[Literal[False]]") -> Any: ...

    @overload
    async def run_task(self: "BaseTaskExecutor[Literal[True]]") -> Any: ...

    def run_task(self) -> Union[Any, Awaitable[Any]]:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        pass

    @overload
    def execute(self: "BaseTaskExecutor[Literal[False]]", decode: bool = True) -> str:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            str: Результат задачи.
        """
        ...

    @overload
    def execute(self: "BaseTaskExecutor[Literal[False]]", decode: bool = False) -> Any:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            Any: Результат задачи.
        """
        ...

    @overload
    async def execute(
        self: "BaseTaskExecutor[Literal[True]]", decode: bool = True
    ) -> str:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            str: Результат задачи.
        """
        ...

    @overload
    async def execute(
        self: "BaseTaskExecutor[Literal[True]]", decode: bool = False
    ) -> Any:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            Any: Результат задачи.
        """
        ...

    @abstractmethod
    def execute(
        self, decode=None
    ) -> Union[Union[Any, str], Awaitable[Union[Any, str]]]:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            Any|str: Результат задачи.
        """
        pass

    @overload
    def decode(self: "BaseTaskExecutor[Literal[False]]") -> str: ...

    @overload
    async def decode(self: "BaseTaskExecutor[Literal[True]]") -> str: ...

    def decode(self) -> Union[str, Awaitable[str]]:
        """Декодирование задачи.

        Returns:
            str: Результат задачи.
        """
        return ""

    def add_plugin(
        self,
        plugin: Annotated[
            "BasePlugin",
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            Optional[List[str]],
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
        ] = None,
    ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    def _extract_args_kwargs_from_func(self, func: Any) -> Tuple[list, dict]:
        """
        Извлекает значения аргументов из функции, если они заданы как значения по умолчанию.

        Args:
            func (Callable): Функция, из которой извлекаются args и kwargs.

        Returns:
            Tuple[list, dict]: args и kwargs, готовые для передачи в `_build_args_info`.
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

    def _build_args_info(self, args: list, kwargs: dict) -> List[ArgMeta]:
        """Строит список ArgMeta из args и kwargs на основе аннотаций функции.

        Args:
            args (list): Позиционные аргументы.
            kwargs (dict): Именованные аргументы.

        Returns:
            List[ArgMeta]: Список метаданных аргументов.
        """
        args_info: List[ArgMeta] = []
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
