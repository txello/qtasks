"""BaseInspectStats."""
from __future__ import annotations

import json
from collections.abc import ValuesView
from dataclasses import asdict, is_dataclass
from inspect import _empty, signature
from pprint import pformat
from typing import TYPE_CHECKING, Any, Union

from qtasks.schemas.task_exec import TaskExecSchema

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks as aioQueueTasks
    from qtasks.qtasks import QueueTasks


class UtilsInspectStats:
    """Utilities for inspection of statistics."""

    label_width = 26

    def _app_parser(
        self, app: Union[QueueTasks, aioQueueTasks], json: bool = False
    ):
        """
        Parser for application information.

        Args:
            app (QueueTasks): Application instance.

        Returns:
            str: Application information.
        """
        lines = []
        plugins_sum = (
            len(app.plugins)
            + len(app.broker.plugins)
            + len(app.worker.plugins)
            + (len(app.starter.plugins) if app.starter else 0)
            + (len(app.broker.storage.plugins) if app.broker.storage else 0)
            + (
                len(app.broker.storage.global_config.plugins)
                if app.broker.storage.global_config
                else 0
            )
        )
        task_info = {
            "Name": app.name,
            "Method": app._method,
            "Version": app.version,
            "Config": str(app.config),
            "Tasks Count": len(app.tasks),
            "Routers Count": len(app.routers),
            "Plugins Count": plugins_sum,
            "Broker": app.broker.__class__.__name__,
            "Worker": app.worker.__class__.__name__,
            "Starter": app.starter.__class__.__name__ if app.starter else "—",
            "Storage": app.broker.storage.__class__.__name__,
            "GlobalConfig": (
                app.broker.storage.global_config.__class__.__name__
                if app.broker.storage.global_config
                else "—"
            ),
            "Log": app.log.__class__.__name__,
        }
        if app.events:
            task_info.update(
                {
                    "Init Count": sum(
                        len(inits) for inits in app.events.on._events.values()
                    ),
                }
            )

        if json:
            return self._parser_json(task_info)

        task_block = "\n".join(
            f"{label:<{self.label_width}}: {value}"
            for label, value in task_info.items()
        )
        lines.append(task_block)
        lines.append("-" * 50)
        return "\n".join(lines)

    def _parser_json(self, data: Any | tuple[Any]) -> str:
        def formatter(d):
            if is_dataclass(d) and not isinstance(d, type):
                return asdict(d)
            return d

        data = (
            [formatter(d) for d in data]
            if isinstance(data, (tuple, list, ValuesView))
            else formatter(data)
        )
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def _tasks_parser(
        self,
        tasks: tuple[TaskExecSchema] | list[TaskExecSchema] | ValuesView[TaskExecSchema],
    ) -> str:
        """Formatted output of all registered tasks."""
        lines = []

        for task in tasks:
            args, kwargs = self._task_get_args_kwargs(task.func)

            task_info = {
                "Task nane": task.name,
                "Priority": task.priority,
                "Description": task.description or "—",
                "Tags": ", ".join(task.tags) if task.tags else "—",
                "Awaiting": task.awaiting,
                "Generating": task.generating,
                "Task Self": task.echo,
                "Args": ", ".join(args) if args else "—",
                "Kwargs": (
                    ", ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else "—"
                ),
            }

            if task.retry is not None:
                task_info["Retry Count"] = task.retry
            if task.retry_on_exc:
                task_info["Retry on Exception"] = pformat(task.retry_on_exc)
            if task.decode:
                task_info["Decode"] = str(task.decode)
            if task.generate_handler:
                task_info["Generator"] = str(task.generate_handler)
            if task.executor:
                task_info["Executor"] = str(task.executor)
            if task.middlewares_before:
                task_info["Middlewares Before"] = pformat(task.middlewares_before)
            if task.middlewares_after:
                task_info["Middlewares After"] = pformat(task.middlewares_after)
            if task.extra:
                extra_lines = "\n" + "\n".join(
                    f" * {k}: {v}" for k, v in task.extra.items()
                )
                task_info["Extra"] = extra_lines

            task_block = "\n".join(
                f"{label:<{self.label_width}}: {value}"
                for label, value in task_info.items()
            )

            lines.append(task_block)
            lines.append("-" * 50)

        return "\n".join(lines) or "No registered tasks."

    def _task_get_args_kwargs(self, func):
        """
        Retrieving positional and key arguments of a task function.

        Args:
            func (Callable): Task function.

        Returns:
            tuple: Positional and key arguments.
        """
        sig = signature(func)
        positional_args = []
        keyword_args = {}

        for name, param in sig.parameters.items():
            annotation = param.annotation if param.annotation is not _empty else None

            type_str = (
                f": {annotation.__name__}"
                if isinstance(annotation, type)
                else f": {annotation}" if annotation else ""
            )

            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                if param.default is param.empty:
                    positional_args.append(f"{name}{type_str}")
                else:
                    keyword_args[f"{name}{type_str}"] = param.default
            elif param.kind == param.KEYWORD_ONLY:
                type_str = type_str or ""
                keyword_args[f"{name}{type_str}"] = (
                    param.default if param.default is not param.empty else "required"
                )
            elif param.kind == param.VAR_POSITIONAL:
                positional_args.append(f"*{name}")
            elif param.kind == param.VAR_KEYWORD:
                keyword_args[f"**{name}"] = "..."

        return positional_args, keyword_args
