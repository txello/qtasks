"""Sync Depends."""

import inspect
from typing import TYPE_CHECKING, Any

try:
    from contextlib import _GeneratorContextManager as _GCM
except Exception:
    _GCM = None


from qtasks.plugins.base import BasePlugin
from qtasks.plugins.depends.class_depends import Depends
from qtasks.schemas.argmeta import ArgMeta

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class SyncDependsPlugin(BasePlugin):
    """Depends plugin."""

    def __init__(self, *args, **kwargs):
        """Инициализация плагина Pydantic."""
        super().__init__(*args, **kwargs)

        self.handlers = {"task_executor_args_replace": self.replace_args}

    def start(self, *args, **kwargs):
        """Запуск плагина Pydantic."""
        pass

    def stop(self, *args, **kwargs):
        """Остановка плагина Pydantic."""
        pass

    def trigger(self, name, *args, **kwargs):
        """Триггер плагина."""
        if name in self.handlers:
            return self.handlers[name](**kwargs)
        return None

    def replace_args(
        self,
        task_executor: "BaseTaskExecutor",
        args: list[Any],
        kw: dict[str, Any],
        args_info: list[ArgMeta],
    ):
        """Заменяет аргументы задачи."""
        for args_meta in args_info:
            if not args_meta.is_kwarg:
                continue

            val = args_meta.value
            if hasattr(val, "__class__") and val.__class__ == Depends:
                dep_callable = val.func
                kw[args_meta.name] = self._eval_dep_callable(dep_callable)
        return {"kw": kw}

    def _eval_dep_callable(self, callable_obj):
        """Универсально "разворачивает" зависимость до значения. Никаких аргументов не прокидываем — если нужно, добавьте их где вызываете."""
        func = callable_obj

        res = func() if inspect.isfunction(func) else func

        if _GCM and isinstance(res, _GCM):
            with res as v:
                return v
        if hasattr(res, "__enter__") and hasattr(res, "__exit__"):
            with res as v:
                return v

        if inspect.isgenerator(res):
            try:
                v = next(res)
            except StopIteration:
                v = None
            finally:
                res.close()
            return v

        return res
