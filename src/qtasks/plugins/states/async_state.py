"""Async State."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Type, get_args, get_origin

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.states.registry import AsyncStateRegistry
from qtasks.schemas.argmeta import ArgMeta

from .fsm import AsyncState

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class AsyncStatePlugin(BasePlugin):
    """Плагин для работы с асинхронными состояниями."""

    def __init__(self, accept_annotated: bool = True):
        """Инициализация плагина."""
        self.accept_annotated = accept_annotated
        self._registry = AsyncStateRegistry()

        self.handlers = {"task_executor_args_replace": self.task_executor_args_replace}

    async def start(self, *args, **kwargs):
        """Запуск плагина."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина."""
        pass

    async def trigger(self, name, **kwargs):
        """Триггер для запуска обработчика."""
        handler = self.handlers.get(name)
        if not handler:
            return
        return await handler(**kwargs)

    async def task_executor_args_replace(
        self,
        task_executor: "BaseTaskExecutor",
        args: List[Any],
        kw: Dict[str, Any],
        args_info: List[ArgMeta],
    ):
        """Заменяет аргументы и ключевые слова в задаче.

        Args:
            task_executor (BaseTaskExecutor): Экземпляр исполнителя задач.
            args (List[Any]): Позиционные аргументы задачи.
            kw (Dict[str, Any]): Именованные аргументы задачи.
            args_info (List[ArgMeta]): Метаданные аргументов.

        Returns:
            Tuple[List[Any], Dict[str, Any]]: Замененные аргументы и ключевые слова.
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
            if isinstance(existing, AsyncState):
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

    def _extract_state_class(self, ann: Any) -> Type[AsyncState] | None:
        """Извлекает класс состояния из аннотации.

        Args:
            ann (Any): Аннотация.

        Returns:
            Type[State] | None: Класс состояния или None.
        """
        if ann is None:
            return None

        if isinstance(ann, type) and issubclass(ann, AsyncState):
            return ann

        if self.accept_annotated:
            origin = get_origin(ann)
            if origin and getattr(origin, "__name__", "") == "Annotated":
                args = get_args(ann)
                if (
                    args
                    and isinstance(args[0], type)
                    and issubclass(args[0], AsyncState)
                ):
                    return args[0]

        return None
