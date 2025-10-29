"""Async Depends."""

import inspect
from functools import partial
from typing import TYPE_CHECKING, Any

try:
    from contextlib import _AsyncGeneratorContextManager as _AGCM
except Exception:
    _AGCM = None

try:
    from contextlib import _GeneratorContextManager as _GCM
except Exception:
    _GCM = None


from qtasks.plugins.base import BasePlugin
from qtasks.plugins.depends.class_depends import Depends
from qtasks.schemas.argmeta import ArgMeta

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class AsyncDependsPlugin(BasePlugin):
    """Async Depends plugin."""

    def __init__(self, *args, **kwargs):
        """Инициализация плагина Pydantic."""
        super().__init__(*args, **kwargs)

        self.handlers = {"task_executor_args_replace": self.replace_args}

    async def start(self, *args, **kwargs):
        """Запуск плагина Pydantic."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина Pydantic."""
        pass

    async def trigger(self, name, *args, **kwargs):
        """Триггер плагина."""
        if name in self.handlers:
            task_executor = kwargs.pop("task_executor", None)
            return await self.handlers[name](task_executor, **kwargs)
        return None

    async def replace_args(
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
                kw[args_meta.name] = await self._eval_dep_callable(dep_callable)
        return {"kw": kw}

    def _is_async_cm_function(self, func) -> bool:
        """Функция, обёрнутая @asynccontextmanager. asynccontextmanager сохраняет исходную функцию в __wrapped__."""
        wrapped = getattr(func, "__wrapped__", None)
        return (
            inspect.isfunction(func)
            and wrapped is not None
            and inspect.isasyncgenfunction(wrapped)
        )

    def _is_sync_cm_function(self, func) -> bool:
        """Функция, обёрнутая @contextmanager (синхронный CM)."""
        wrapped = getattr(func, "__wrapped__", None)
        return (
            inspect.isfunction(func)
            and wrapped is not None
            and inspect.isgeneratorfunction(wrapped)
        )

    async def _eval_dep_callable(self, callable_obj):
        """Универсально "разворачивает" зависимость до значения. Никаких аргументов не прокидываем — если нужно, добавьте их где вызываете."""
        func = callable_obj

        # 1) Функция, помеченная @asynccontextmanager
        if self._is_async_cm_function(func):
            cm = func()  # создаём CM
            # cm должен быть _AGCM или хотя бы иметь __aenter__/__aexit__
            if (_AGCM and isinstance(cm, _AGCM)) or (
                hasattr(cm, "__aenter__") and hasattr(cm, "__aexit__")
            ):
                async with cm as v:
                    return v
            else:
                # на всякий случай — падаем в общий разбор ниже
                func = cm

        # 2) Чистая async-функция
        if inspect.iscoroutinefunction(func):
            return await func()

        # 3) async-генератор-функция (берём первый yield и закрываем)
        if inspect.isasyncgenfunction(func):
            agen = func()
            try:
                v = await agen.__anext__()
            except StopAsyncIteration:
                v = None
            finally:
                await agen.aclose()
            return v

        # 4) Синхронная функция
        if inspect.isfunction(func):
            res = func()
            # результат ещё может оказаться awaitable/генератором/CM — разберём ниже
        elif isinstance(func, partial) or callable(func):
            # поддержка partial / callable-объектов
            res = func()
        else:
            # это уже готовый объект (вдруг передали созданный CM/генератор/корутину)
            res = func

        # === Разбор результата вызова ===

        # 5) Уже созданный async context manager
        if _AGCM and isinstance(res, _AGCM):
            async with res as v:
                return v
        if hasattr(res, "__aenter__") and hasattr(res, "__aexit__"):
            # любой объект с async CM протоколом
            async with res as v:
                return v

        # 6) Короутина (awaitable)
        if inspect.isawaitable(res):
            return await res

        # 7) Синхронный context manager
        if _GCM and isinstance(res, _GCM):
            with res as v:
                return v
        if hasattr(res, "__enter__") and hasattr(res, "__exit__"):
            with res as v:
                return v

        # 8) Синхронный генератор: взять первый yield и закрыть
        if inspect.isgenerator(res):
            try:
                v = next(res)
            except StopIteration:
                v = None
            finally:
                res.close()
            return v

        # 9) Обычное значение
        return res
