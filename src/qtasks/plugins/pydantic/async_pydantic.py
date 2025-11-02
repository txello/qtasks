"""Async Pydantic Wrapper."""

from collections import deque
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ForwardRef,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ValidationError

from qtasks.plugins.base import BasePlugin
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.argmeta import ArgMeta

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class AsyncPydanticWrapperPlugin(BasePlugin):
    """Плагин для оборачивания аргументов в Pydantic-модель."""

    def __init__(self, *args, **kwargs):
        """Инициализация плагина Pydantic."""
        super().__init__(*args, **kwargs)

        self.handlers = {
            "task_executor_args_replace": self.replace_args,
            "task_executor_after_execute_result_replace": self.replace_result,
        }

    async def start(self, *args, **kwargs):
        """Запуск плагина Pydantic."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина Pydantic."""
        pass

    async def trigger(self, name, task_executor, **kwargs):
        """Триггер плагина."""
        if name in self.handlers:
            return self.handlers[name](task_executor, **kwargs)
        return None

    def replace_args(
        self,
        task_executor: "BaseTaskExecutor",
        args: list,
        kw: dict,
        args_info: list[ArgMeta],
    ) -> dict | None:
        """Заменяет аргументы на Pydantic-модели."""
        new_args, new_kwargs = args.copy(), kw.copy()
        echo = (
            new_args[0]
            if args_info
            and not args_info[0].is_kwarg
            and args_info[0].raw_type in [SyncTask, AsyncTask]
            else None
        )
        start_index = 1 if echo else 0

        for meta in args_info[start_index:]:
            model_cls = self._model_class_from_meta(meta)
            if not model_cls:
                continue

            try:
                fields = self._fields_order(model_cls)
                data_kw = {k: new_kwargs[k] for k in fields if k in new_kwargs}

                try:
                    model_instance = model_cls(**data_kw)
                    for k in data_kw:
                        new_kwargs.pop(k, None)
                except ValidationError:
                    new_args_trimmed, data_kw = self._add_missing_from_args(
                        model_cls, data_kw, new_args[start_index:]
                    )
                    model_instance = model_cls(**data_kw)
                    for k in data_kw:
                        new_kwargs.pop(k, None)
                    if echo:
                        new_args_trimmed.insert(0, echo)
                    return {
                        "args": new_args_trimmed,
                        "kw": {**new_kwargs, meta.name: model_instance},
                    }
                return {"kw": {**new_kwargs, meta.name: model_instance}}

            except Exception as e:
                raise ValueError(
                    f"Ошибка при сборке модели для '{meta.name}': {e}"
                ) from e

        return None

    def replace_result(self, task_executor, result: Any) -> Any:
        """Оборачивает результат в словарь, если это Pydantic-модель."""
        if isinstance(result, BaseModel):
            return {"result": result.model_dump()}
        return None

    def _model_class_from_meta(self, meta_or_ann, *, globalns=None, localns=None):
        """Возвращает класс Pydantic-модели из аннотации ArgMeta или самой аннотации."""
        ann = getattr(meta_or_ann, "annotation", meta_or_ann)
        if ann in (None, Any):
            return None

        if isinstance(ann, (str, ForwardRef)):
            ann = get_type_hints(
                type("Tmp", (), {"__annotations__": {"x": ann}}),
                globalns or {},
                localns or {},
            ).get("x", ann)

        if get_origin(ann) is Annotated:
            ann = get_args(ann)[0]

        if get_origin(ann) is Union:
            args = [a for a in get_args(ann) if a is not type(None)]
            if len(args) == 1:
                ann = args[0]

        if isinstance(ann, type) and issubclass(ann, BaseModel):
            return ann

        return None

    def _fields_order(self, model_cls):
        return list(
            getattr(model_cls, "model_fields", model_cls.__fields__).keys()
        )

    def _add_missing_from_args(self, model_cls, data_kw, args: list):
        """Добавляет недостающие значения из args по порядку."""
        q = deque(args)
        for f in self._fields_order(model_cls):
            if f not in data_kw and q:
                data_kw[f] = q.popleft()
        return list(q), data_kw
