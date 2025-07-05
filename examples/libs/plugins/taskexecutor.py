from typing import Any
import pydantic

from qtasks.plugins.base import BasePlugin
from pydantic import BaseModel as PydanticBaseModel

from qtasks.registries.async_task_decorator import AsyncTask

class AsyncTaskExecutorArgsPydanticPlugin(BasePlugin):
    """
    Плагин для изменения аргументов задачи.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.handlers = {
            "task_executor_args_replace": self.replace_args,
            "task_executor_result_replace": self.replace_result
        }

    async def start(self, *args, **kwargs):
        pass

    async def stop(self, *args, **kwargs):
        pass

    async def trigger(self, name, task_executor, **kwargs):
        if name in self.handlers:
            return self.handlers[name](**kwargs)
        return None

    def replace_args(self, args: tuple, kwargs: dict) -> tuple[list, dict]:
        echo = args[0] if args and isinstance(args[0], AsyncTask) else None
        if echo:
            args = args[1:]

        annotations = {}
        defaults = {}

        # args → arg0, arg1, ...
        for i, arg in enumerate(args):
            annotations[f"arg{i}"] = type(arg)
            defaults[f"arg{i}"] = arg

        # kwargs → как есть, включая "name"
        for key, value in kwargs.items():
            annotations[key] = type(value)
            defaults[key] = value

        # Создаём динамическую модель, избегая передачи name как спец-параметра
        DynamicModel = type("DynamicArgsModel", (pydantic.BaseModel,), {
            '__annotations__': annotations,
            **defaults
        })

        model_instance = DynamicModel()
        args = [model_instance,]
        if echo:
            args.insert(0, echo)
        return args, {}
    
    def replace_result(self, result: Any) -> Any:
        """
        Оборачивает результат в pydantic-модель и возвращает
        либо одно значение, либо dict — пригодный для JSON.
        """
        if not isinstance(result, pydantic.BaseModel):
            return None
        
        return result.model_dump()
