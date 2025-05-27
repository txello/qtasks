import json
from typing import Any, Optional
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema


class AsyncTaskExecutor:
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
                Optional[Any],
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

        self.middlewares = middlewares or []
        self._result: Any = None

        self.log = log
        if self.log is None:
            import qtasks._state
            self.log = qtasks._state.log_main
        self.log = self.log.with_subname("AsyncTaskExecutor")


    async def before_execute(self):
        pass

    async def after_execute(self):
        pass

    async def execute_middlewares(self):
        for m in self.middlewares:
            self.log.debug(f"Вызван Middleware {m.name} для {self.task_func.name}")
            await m(self)

    async def run_task(self) -> Any:
        if self.task_broker.args and self.task_broker.kwargs:
            result = await self.task_func(*self.task_broker.args, **self.task_broker.kwargs)\
                if self.task_func.awaiting else self.task_func.func(*self.task_broker.args, **self.task_broker.kwargs)
        elif self.task_broker.args:
            result = await self.task_func.func(*self.task_broker.args) if self.task_func.awaiting else self.task_func.func(*self.task_broker.args)
        elif self.task_broker.kwargs:
            result = await self.task_func.func(**self.task_broker.kwargs) if self.task_func.awaiting else self.task_func.func(**self.task_broker.kwargs)
        else:
            result = await self.task_func.func() if self.task_func.awaiting else self.task_func.func()
        return result
    
    async def execute(self,
            decode: bool = True
        ) -> Any|str:
        self.log.debug(f"Вызван execute для {self.task_func.name}")
        await self.execute_middlewares()
        await self.before_execute()
        self._result = await self.run_task()
        await self.after_execute()
        if decode:
            return await self.decode()
        return self._result

    async def decode(self) -> str:
        return json.dumps(self._result, ensure_ascii=False)
