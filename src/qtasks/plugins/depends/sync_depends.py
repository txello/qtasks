"""Sync Depends."""

import inspect
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
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
        """Инициализация плагина Pydantic."""
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
        """Универсально "разворачивает" зависимость до значения. Никаких аргументов не прокидываем — если нужно, добавьте их где вызываете."""
        func = callable_obj

        res = func() if inspect.isfunction(func) else func

        if _GCM and isinstance(res, _GCM):
            return self.contexts.enter(scope, res)
        if hasattr(res, "__enter__") and hasattr(res, "__exit__"):
            return self.contexts.enter(scope, res)

        return self.contexts.enter(scope, res)

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
