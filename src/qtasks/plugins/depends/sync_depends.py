"""Sync Depends."""

import inspect
from contextlib import contextmanager
from functools import partial
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Awaitable,
    Callable,
    Optional,
    get_args,
)

from qtasks.plugins.depends.contexts.sync_contexts import SyncContextPool
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

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


class SyncDependsPlugin(BasePlugin):
    """Depends plugin."""

    def __init__(self, name="AsyncDependsPlugin"):
        """Initializing the Pydantic plugin."""
        super().__init__(name=name)

        self.contexts = SyncContextPool()

        self.handlers = {
            "task_executor_args_replace": self.replace_args,
            "task_executor_task_close": self.task_close,
            "worker_stop": self.worker_close,
            "broker_stop": self.broker_close,
            "storage_stop": self.storage_close,
            "global_config_stop": self.global_config_close
        }

    def start(self, *args, **kwargs):
        """Launching the Pydantic plugin."""
        pass

    def stop(self, *args, **kwargs):
        """Stopping the Pydantic plugin."""
        pass

    def trigger(self, name, *args, **kwargs):
        """Plugin trigger."""
        if name in self.handlers:
            return self.handlers[name](**kwargs)
        return None

    def replace_args(
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
            kw[args_meta.name], cm = self._eval_dep_callable(dep_callable, dep.scope)

            if not plugin_cache or dep.scope not in plugin_cache:
                plugin_cache = {dep.scope: [cm[1]]}
                result.update({"plugin_cache": {dep.scope: [cm[1]]}})
            else:
                plugin_cache[dep.scope].append(cm[1])
                result["plugin_cache"] = plugin_cache

        result.update({"kw": kw})
        return result

    def _eval_dep_callable(self, callable_obj, scope):
        """Universally "expands" a dependency to a value. We don’t pass any arguments - if necessary, add them where you call them."""
        func = callable_obj

        # 1) sync function
        if inspect.isfunction(func):
            res = func()
            # the result may still turn out to be an awaitable/generator/CM - we'll discuss this below
        elif isinstance(func, partial) or callable(func):
            # support for partial/callable objects
            res = func()
        else:
            # This is a ready-made object (suddenly they passed a created CM/generator/coroutine)
            res = func

        # 2) Sync context manager
        if (_GCM and isinstance(res, _GCM)) or (hasattr(res, "__enter__") and hasattr(res, "__exit__")):
            return self.contexts.enter(scope, res)

        # 3) Sync generator
        if inspect.isgenerator(res):
            return self.contexts.enter(scope, self._genobj_to_cm(res))

        # 4) Normal value
        return self.contexts.enter(scope, self._sync_func_to_cm(lambda: res))

    def _sync_func_to_cm(self, func: Callable[[], Awaitable[Any]]):
        @contextmanager
        def _cm():
            value = func()
            yield value
        return _cm()


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


    def task_close(
        self,
        task_executor: "BaseTaskExecutor",
        task_func: TaskExecSchema,
        task_broker: TaskPrioritySchema,
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "task" in plugin_cache:
            for cm in plugin_cache["task"]:
                self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"task": []}}

    def worker_close(
        self,
        worker: "BaseWorker",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "worker" in plugin_cache:
            for cm in plugin_cache["worker"]:
                self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"worker": []}}

    def broker_close(
        self,
        broker: "BaseBroker",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "broker" in plugin_cache:
            for cm in plugin_cache["broker"]:
                self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"broker": []}}

    def storage_close(
        self,
        storage: "BaseStorage",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "storage" in plugin_cache:
            for cm in plugin_cache["storage"]:
                self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"storage": []}}

    def global_config_close(
        self,
        global_config: "BaseGlobalConfig",
        plugin_cache: Optional[dict] = None
    ):
        if plugin_cache and "global_config" in plugin_cache:
            for cm in plugin_cache["global_config"]:
                self.contexts.close_by_cm(cm)
            return {"plugin_cache" : {"global_config": []}}
