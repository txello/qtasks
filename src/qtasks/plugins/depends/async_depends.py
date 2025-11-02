"""Async Depends."""

import inspect
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    AsyncGenerator,
    Optional,
    cast,
    get_args,
)

from qtasks.plugins.depends.contexts.async_contexts import AsyncContextPool
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

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
    from qtasks.brokers.base import BaseBroker
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class AsyncDependsPlugin(BasePlugin):
    """Async Depends plugin."""

    def __init__(self, name="AsyncDependsPlugin"):
        """Инициализация плагина Pydantic."""
        super().__init__(name=name)

        self.contexts = AsyncContextPool()

        self.handlers = {
            "task_executor_args_replace": self.replace_args,
            "task_executor_task_close": self.task_close,
            "worker_stop": self.worker_close,
            "broker_stop": self.broker_close,
            "storage_stop": self.storage_close,
            "global_config_stop": self.global_config_close
        }

    async def start(self, *args, **kwargs):
        """Запуск плагина Pydantic."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина Pydantic."""
        pass

    async def trigger(self, name, *args, **kwargs):
        """Триггер плагина."""
        if name in self.handlers:
            return await self.handlers[name](*args, **kwargs)
        return None

    async def replace_args(
        self,
        task_executor: "BaseTaskExecutor",
        args: list[Any],
        kw: dict[str, Any],
        args_info: list[ArgMeta],
        plugin_cache: Optional[dict] = None
    ):
        """Заменяет аргументы задачи."""
        result = {}

        for args_meta in args_info:
            if args_meta.is_kwarg:
                dep = args_meta.value
            elif args_meta.origin is Annotated:
                dep = get_args(args_meta.annotation)[-1]
            else:
                continue
            if not hasattr(dep, "__class__") or not dep.__class__ == Depends:
                continue
            dep: Depends
            dep_callable = dep.func
            kw[args_meta.name], cm = await self._eval_dep_callable(dep_callable, dep.scope)

            if not plugin_cache or dep.scope not in plugin_cache:
                plugin_cache = {dep.scope: [cm[1]]}
                result.update({"plugin_cache": {dep.scope: [cm[1]]}})
            else:
                plugin_cache[dep.scope].append(cm[1])
                result["plugin_cache"] = plugin_cache

        result.update({"kw": kw})
        return result

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

    async def _eval_dep_callable(self, callable_obj, scope):
        """Универсально "разворачивает" зависимость до значения. Никаких аргументов не прокидываем — если нужно, добавьте их где вызываете."""
        func = callable_obj

        # 1) Функция, помеченная @asynccontextmanager
        if self._is_async_cm_function(func):
            cm = func()  # создаём CM
            # cm должен быть _AGCM или хотя бы иметь __aenter__/__aexit__
            if (_AGCM and isinstance(cm, _AGCM)) or (
                hasattr(cm, "__aenter__") and hasattr(cm, "__aexit__")
            ):
                return await self.contexts.enter(scope, cm)
            else:
                # на всякий случай — падаем в общий разбор ниже
                func = cm

        # 2) Чистая async-функция
        if inspect.iscoroutinefunction(func):
            return await func()

        # 3) async-генератор-функция (берём первый yield и закрываем)
        if inspect.isasyncgenfunction(func):
            agen: AsyncGenerator = func()
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
            async with cast(Any, res) as v:
                return v
        # Проверка на наличие методов __aenter__ и __aexit__
        if hasattr(res, "__aenter__") and hasattr(res, "__aexit__"):
            async with cast(Any, res) as v:
                return v

        # 6) Короутина (awaitable)
        if inspect.isawaitable(res):
            return await res

        # 7) Синхронный context manager
        if _GCM and isinstance(res, _GCM):
            with res as v:
                return v
        if hasattr(res, "__enter__") and hasattr(res, "__exit__"):
            with cast(Any, res) as v:
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

    async def task_close(
        self,
        task_executor: "BaseTaskExecutor",
        task_func: TaskExecSchema,
        task_broker: TaskPrioritySchema,
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "task" in plugin_cache:
            for cm in plugin_cache["task"]:
                await self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"task": []}}

    async def worker_close(
        self,
        worker: "BaseWorker",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "worker" in plugin_cache:
            for cm in plugin_cache["worker"]:
                await self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"worker": []}}

    async def broker_close(
        self,
        broker: "BaseBroker",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "broker" in plugin_cache:
            for cm in plugin_cache["broker"]:
                await self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"broker": []}}

    async def storage_close(
        self,
        storage: "BaseStorage",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "storage" in plugin_cache:
            for cm in plugin_cache["storage"]:
                await self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"storage": []}}

    async def global_config_close(
        self,
        global_config: "BaseGlobalConfig",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "global_config" in plugin_cache:
            for cm in plugin_cache["global_config"]:
                await self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"global_config": []}}
