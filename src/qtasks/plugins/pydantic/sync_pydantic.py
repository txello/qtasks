"""Sync Pydantic Wrapper."""

from typing import Any, List, Tuple, Union
from pydantic import BaseModel

from qtasks.plugins.base import BasePlugin
from qtasks.schemas.argmeta import ArgMeta


class SyncPydanticWrapperPlugin(BasePlugin):
    """Плагин для оборачивания аргументов в Pydantic-модель."""

    def __init__(self, *args, **kwargs):
        """Инициализация плагина Pydantic."""
        super().__init__(*args, **kwargs)

        self.handlers = {
            "task_executor_args_replace": self.replace_args,
            "task_executor_after_execute_result_replace": self.replace_result,
        }

    def start(self, *args, **kwargs):
        """Запуск плагина Pydantic."""
        pass

    def stop(self, *args, **kwargs):
        """Остановка плагина Pydantic."""
        pass

    def trigger(self, name, task_executor, **kwargs):
        """Триггер плагина."""
        if name in self.handlers:
            return self.handlers[name](**kwargs)
        return None

    def replace_args(self, args: list, kwargs: dict, args_info: List[ArgMeta]) -> Union[Tuple[list, dict], None]:
        """Заменяет аргументы на Pydantic-модели.

        Args:
            args (list): Позиционные аргументы.
            kwargs (dict): Именованные аргументы.
            args_info (List[ArgMeta]): Информация об аргументах.
        """
        echo = args[0] if args_info and not args_info[0].is_kwarg and args_info[0].name == "self" else None
        start_index = 1 if echo else 0

        model_meta = next(
            (meta for meta in args_info[start_index:] if meta.annotation and isinstance(meta.annotation, type) and issubclass(meta.annotation, BaseModel) and not meta.is_kwarg),
            None
        )

        if model_meta:
            model_cls = model_meta.annotation
            model_fields = list(model_cls.model_fields.keys())
            model_data = {}

            for field_name, meta in zip(model_fields, args_info[start_index:]):
                if meta.index is None or meta.index >= len(args):
                    break
                model_data[field_name] = args[meta.index]

            if model_data:
                DynamicModel = type(model_cls.__name__, (BaseModel,), {
                    '__annotations__': {
                        k: type(v) for k, v in model_data.items()
                    },
                    **model_data
                })

                model_instance = DynamicModel()

                new_args = [model_instance]
                if echo:
                    new_args.insert(0, echo)
                return new_args, {}

        for meta in args_info:
            if not meta.is_kwarg or meta.name not in kwargs:
                continue

            value = kwargs[meta.name]
            if (
                meta.annotation
                and isinstance(meta.annotation, type)
                and issubclass(meta.annotation, BaseModel)
                and not isinstance(value, BaseModel)
                and isinstance(value, dict)
            ):
                try:
                    DynamicModel = type(meta.annotation.__name__, (BaseModel,), {
                        '__annotations__': {k: type(v) for k, v in value.items()},
                        **value
                    })
                    model_instance = DynamicModel()
                    new_kwargs = kwargs.copy()
                    new_kwargs[meta.name] = model_instance
                    if echo:
                        return [echo], new_kwargs
                    return [], new_kwargs
                except Exception as e:
                    raise ValueError(f"Ошибка при сборке DynamicModel из kwargs['{meta.name}']: {e}") from e

        return None

    def replace_result(self, result: Any) -> Any:
        """Оборачивает результат в словарь, если это Pydantic-модель."""
        if isinstance(result, BaseModel):
            return result.model_dump()
        return None
