"""Async State."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args, get_origin

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.states.registry import SyncStateRegistry
from qtasks.schemas.argmeta import ArgMeta

from .fsm import SyncState

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class SyncStatePlugin(BasePlugin):
    """Plugin for working with synchronous states."""

    def __init__(self, accept_annotated: bool = True):
        """Initializing the plugin."""
        super().__init__()
        self.accept_annotated = accept_annotated
        self._registry = SyncStateRegistry()

        self.handlers = {"task_executor_args_replace": self.task_executor_args_replace}

    def start(self, *args, **kwargs):
        """Launch the plugin."""
        pass

    def stop(self, *args, **kwargs):
        """Stopping the plugin."""
        pass

    def trigger(self, name, **kwargs):
        """Trigger to run the handler."""
        handler = self.handlers.get(name)
        if not handler:
            return
        return handler(**kwargs)

    def task_executor_args_replace(
        self,
        task_executor: BaseTaskExecutor,
        args: list[Any],
        kw: dict[str, Any],
        args_info: list[ArgMeta],
    ):
        """
        Replaces arguments and keywords in a task.
        
                Args:
                    task_executor (BaseTaskExecutor): A task executor instance.
                    args (List[Any]): Positional arguments to the task.
                    kw (Dict[str, Any]): Named task arguments.
                    args_info (List[ArgMeta]): Argument metadata.
        
                Returns:
                    Tuple[List[Any], Dict[str, Any]]: Replaced arguments and keywords.
        """
        new_args = list(args)
        new_kw = dict(kw)

        for meta in args_info:
            state_cls = self._extract_state_class(meta.annotation)
            if state_cls is None:
                continue

            # Если пользователь уже передал готовый State — не трогаем
            existing = None
            if meta.is_kwarg and meta.key is not None:
                existing = new_kw.get(meta.key)
            elif meta.index is not None and meta.index < len(new_args):
                existing = new_args[meta.index]
            if isinstance(existing, SyncState):
                continue

            bound = state_cls(
                self._registry, state_cls
            )  # сигнатура: (registry, state_cls)

            if meta.is_kwarg and meta.key is not None:
                new_kw[meta.key] = bound
            elif meta.index is not None:
                while len(new_args) <= meta.index:
                    new_args.append(None)
                new_args[meta.index] = bound

        return {"args": new_args, "kw": new_kw}

    def _extract_state_class(self, ann: Any) -> type[SyncState] | None:
        """
        Retrieves the state class from the annotation.
        
                Args:
                    ann (Any): Abstract.
        
                Returns:
                    Type[State] | None: State class or None.
        """
        if ann is None:
            return None

        if isinstance(ann, type) and issubclass(ann, SyncState):
            return ann

        if self.accept_annotated:
            origin = get_origin(ann)
            if origin and getattr(origin, "__name__", "") == "Annotated":
                args = get_args(ann)
                if (
                    args
                    and isinstance(args[0], type)
                    and issubclass(args[0], SyncState)
                ):
                    return args[0]

        return None
