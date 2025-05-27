from typing import TYPE_CHECKING, Any, Optional, Type
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.middlewares.task import TaskMiddleware


class BaseTaskExecutor:
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
                Optional[Type["TaskMiddleware"]],
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
        self.task_func = task_func
        self.task_broker = task_broker

        self.middlewares: list["TaskMiddleware"] = middlewares or []

        self.log = log
        if self.log is None:
            import qtasks._state
            self.log = qtasks._state.log_main
        self.log = self.log.with_subname(self.__class__.__name__)


    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute_middlewares(self):
        pass

    def run_task(self) -> Any:
        pass
    
    def execute(self,
            decode: bool = True
        ) -> Any|str:
        pass

    def decode(self) -> str:
        pass
