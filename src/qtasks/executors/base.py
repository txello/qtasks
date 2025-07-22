"""Base Task Executor."""

from abc import ABC, abstractmethod
import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, get_args, get_origin
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.argmeta import ArgMeta
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class BaseTaskExecutor(ABC):
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
            Optional[Dict[str, List[Type["BasePlugin"]]]],
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
            plugins (Dict[str, List[Type[BasePlugin]]], optional): Словарь плагинов. По умолчанию: `Пустой словарь`.
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

    def before_execute(self):
        """Вызывается перед выполнением задачи."""
        pass

    def after_execute(self):
        """Вызывается после выполнения задачи."""
        pass

    def execute_middlewares_before(self):
        """Вызов мидлварей до выполнения задачи."""
        pass

    def execute_middlewares_after(self):
        """Вызов мидлварей после выполнения задачи."""
        pass

    def run_task(self) -> Any:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        pass

    @abstractmethod
    def execute(self, decode: bool = True) -> Any | str:
        """Обработка задачи.

        Args:
            decode (bool, optional): Декодирование. По умолчанию: `True`.

        Returns:
            Any|str: Результат задачи.
        """
        pass

    def decode(self) -> str:
        """Декодирование задачи.

        Returns:
            str: Результат задачи.
        """
        pass

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

    def _build_args_info(self, args: list, kwargs: dict) -> list[ArgMeta]:
        """Строит список ArgMeta из args и kwargs на основе аннотаций функции.

        Args:
            args (list): Позиционные аргументы.
            kwargs (dict): Именованные аргументы.

        Returns:
            list[ArgMeta]: Список метаданных аргументов.
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
            args_info.append(ArgMeta(
                name=param_name,
                origin=origin,
                raw_type=raw_type,
                annotation=annotation,
                is_kwarg=False,
                index=idx,
            ))

        # Обработка именованных аргументов
        for key, value in kwargs.items():
            annotation = annotations.get(key)
            origin = get_origin(annotation)
            raw_type = get_args(annotation)[0] if get_args(annotation) else annotation
            args_info.append(ArgMeta(
                name=key,
                origin=origin,
                raw_type=raw_type,
                annotation=annotation,
                is_kwarg=True,
                key=key,
            ))

        return args_info
