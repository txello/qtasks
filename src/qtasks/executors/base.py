from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional, Type
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.middlewares.task import TaskMiddleware


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
    def __init__(self,
            task_func: Annotated[
                TaskExecSchema,
                Doc(
                    """
                    `TaskExecSchema` схема.
                    """
                )
            ],
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    `TaskPrioritySchema` схема.
                    """
                )
            ],
            middlewares: Annotated[
                Optional[List[Type["TaskMiddleware"]]],
                Doc(
                    """
                    Массив Миддлварей.
                    
                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None,
            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None
        ):
        """Инициализация класса. Происходит внутри `Worker` перед обработкой задачи.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            middlewares (List[Type[TaskMiddleware]], optional): _description_. По умолчанию `None`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
        """
        self.task_func = task_func
        self.task_broker = task_broker

        self.middlewares: list["TaskMiddleware"] = middlewares or []

        self.log = log
        if self.log is None:
            import qtasks._state
            self.log = qtasks._state.log_main
        self.log = self.log.with_subname(self.__class__.__name__)


    def before_execute(self):
        """Вызывается перед выполнением задачи."""
        pass

    def after_execute(self):
        """Вызывается после выполнения задачи."""
        pass

    def execute_middlewares(self):
        """Вызов мидлварей."""
        pass

    def run_task(self) -> Any:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        pass
    
    @abstractmethod
    def execute(self,
            decode: bool = True
        ) -> Any|str:
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
