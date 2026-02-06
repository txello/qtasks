"""Async Depends."""

import inspect
from contextlib import asynccontextmanager, contextmanager
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Optional,
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
from qtasks.types import T

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class AsyncDependsPlugin(BasePlugin):
    """Async Depends plugin."""

    def __init__(self, name="AsyncDependsPlugin"):
        """Initializing the Pydantic plugin."""
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
        """Launching the Pydantic plugin."""
        pass

    async def stop(self, *args, **kwargs):
        """Stopping the Pydantic plugin."""
        pass

    async def trigger(self, name, *args, **kwargs):
        """Plugin trigger."""
        if name in self.handlers:
            return await self.handlers[name](**kwargs)
        return None

    async def replace_args(
        self,
        task_executor: "BaseTaskExecutor",
        args: list[Any],
        kw: dict[str, Any],
        args_info: list[ArgMeta],
        plugin_cache: Optional[dict] = None
    ):
        """Replaces task arguments."""
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
        """Function wrapped by @asynccontextmanager. asynccontextmanager stores the original function in __wrapped__."""
        wrapped = getattr(func, "__wrapped__", None)
        return (
            inspect.isfunction(func)
            and wrapped is not None
            and inspect.isasyncgenfunction(wrapped)
        )

    def _is_sync_cm_function(self, func) -> bool:
        """Function wrapped by @contextmanager (synchronous CM)."""
        wrapped = getattr(func, "__wrapped__", None)
        return (
            inspect.isfunction(func)
            and wrapped is not None
            and inspect.isgeneratorfunction(wrapped)
        )

    async def _eval_dep_callable(self, callable_obj, scope):
        """Universally "expands" a dependency to a value. We don’t pass any arguments - if necessary, add them where you call them."""
        func = callable_obj

        # 1) A function annotated with @asynccontextmanager
        if self._is_async_cm_function(func):
            cm = func()  # create CM
            # cm should be _AGCM or at least have __aenter__/__aexit__ methods
            if (_AGCM and isinstance(cm, _AGCM)) or (
                hasattr(cm, "__aenter__") and hasattr(cm, "__aexit__")
            ):
                return await self.contexts.enter(scope, cm)
            else:
                # Just in case, let's dive into the general analysis below.
                func = cm

        # 2) Pure async function
        if inspect.iscoroutinefunction(func):
            return await self.contexts.enter(scope, self._async_func_to_cm(func))

        # 3) async generator function (take the first yield and close it)
        if inspect.isasyncgenfunction(func):
            return await self.contexts.enter(scope, self._async_agen_to_acm(func))

        # 4) sync function
        if inspect.isfunction(func):
            res = func()
            # the result may still turn out to be an awaitable/generator/CM - we'll discuss this below
        elif isinstance(func, partial) or callable(func):
            # support for partial/callable objects
            res = func()
        else:
            # This is a ready-made object (suddenly they passed a created CM/generator/coroutine)
            res = func

        # === Parsing the call result ===

        # 6) Coroutine (awaitable)
        if inspect.isawaitable(res):
            return await self.contexts.enter(scope, self._awaitable_to_acm(res))

        # 7) Sync context manager
        if (_GCM and isinstance(res, _GCM)) or (hasattr(res, "__enter__") and hasattr(res, "__exit__")):
            return await self.contexts.enter(scope, res)

        # 8) Sync generator
        if inspect.isgenerator(res):
            return await self.contexts.enter(scope, self._genobj_to_cm(res))

        # 9) Normal value
        return await self.contexts.enter(scope, self._sync_func_to_cm(lambda: res))

    def _async_func_to_cm(self, func: Callable[[], Awaitable[Any]]):
        @asynccontextmanager
        async def _cm():
            value = await func()
            yield value
        return _cm()

    def _sync_func_to_cm(self, func: Callable[[], Awaitable[Any]]):
        @contextmanager
        def _cm():
            value = func()
            yield value
        return _cm()

    def _async_agen_to_acm(self, factory: Callable[[], AsyncGenerator[Any, None]]):
        @asynccontextmanager
        async def _acm():
            agen = factory()
            try:
                yield await agen.__anext__()
            except StopAsyncIteration as e:
                raise RuntimeError("Dependency async generator didn't yield a value") from e
        return _acm()

    def _genobj_to_cm(self, gen):
        """
        Treat raw sync generator as a context manager:
        - first yield => dependency value
        - generator finalization => cleanup
        """
        @contextmanager
        def _cm():
            try:
                value = next(gen)
            except StopIteration as e:
                raise RuntimeError("Sync generator dependency didn't yield a value") from e

            try:
                yield value
            finally:
                # Prefer normal completion to run code after yield and finally.
                try:
                    next(gen)
                except StopIteration:
                    pass
                else:
                    # If it yielded more than once — that's a bug in dependency.
                    raise RuntimeError("Sync generator dependency yielded more than once")

        return _cm()

    def _awaitable_to_acm(self, awaitable: Awaitable[T]):
        @asynccontextmanager
        async def _acm():
            value = await awaitable
            yield value
        return _acm()

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
