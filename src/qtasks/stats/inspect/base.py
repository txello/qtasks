"""BaseInspectStats."""

from dataclasses import asdict, is_dataclass
from inspect import signature, _empty
import json
from pprint import pformat
from typing import TYPE_CHECKING, Any
from collections.abc import ValuesView

from qtasks.schemas.task_exec import TaskExecSchema

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class UtilsInspectStats:
    """Утилиты для инспекции статистики."""

    label_width = 26

    def _app_parser(self, app: "QueueTasks", json: bool = False):
        """Парсер для информации о приложении.

        Args:
            app (QueueTasks): Экземпляр приложения.

        Returns:
            str: Информация о приложении.
        """
        lines = []
        plugins_sum = (
            len(app.plugins)
            + len(app.broker.plugins)
            + len(app.worker.plugins)
            + (len(app.starter.plugins) if app.starter else 0)
            + (len(app.broker.storage.plugins) if app.broker.storage else 0)
            + (len(app.broker.storage.global_config.plugins) if app.broker.storage.global_config else 0)
        )
        task_info = {
            "Имя": app.name,
            "Метод": app._method,
            "Версия": app.version,
            "Конфигурация": str(app.config),
            "Количество задач": len(app.tasks),
            "Количество роутеров": len(app.routers),
            "Количество плагинов": plugins_sum,
            "Количество инициализаций": sum(len(inits) for inits in app._inits.values()),
            "Брокер": app.broker.__class__.__name__,
            "Воркер": app.worker.__class__.__name__,
            "Стартер": app.starter.__class__.__name__ if app.starter else "—",
            "Хранилище": app.broker.storage.__class__.__name__,
            "GlobalConfig": app.broker.storage.global_config.__class__.__name__ if app.broker.storage.global_config else "—",
            "Лог": app.log.__class__.__name__,
        }

        if json:
            return self._parser_json(task_info)

        # Форматируем словарь
        task_block = "\n".join(
            f"{label:<{self.label_width}}: {value}" for label, value in task_info.items()
        )
        lines.append(task_block)
        lines.append("-" * 50)
        return "\n".join(lines)

    def _parser_json(self, data: tuple[Any] | Any) -> str:
        def formatter(d):
            if is_dataclass(d):
                return asdict(d)
            return d
        data = [formatter(d) for d in data] if isinstance(data, (tuple, list, ValuesView)) else formatter(data)
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def _tasks_parser(self, tasks: tuple[TaskExecSchema]) -> str:
        """Форматированный вывод всех зарегистрированных задач."""
        lines = []

        for task in tasks:
            args, kwargs = self._task_get_args_kwargs(task.func)

            task_info = {
                "Имя задачи": task.name,
                "Приоритет": task.priority,
                "Описание": task.description or "—",
                "Теги": ', '.join(task.tags) if task.tags else "—",
                "Асинхронность": task.awaiting,
                "Генерация": task.generating,
                "Self перед задачей": task.echo,
                "Args": ', '.join(args) if args else "—",
                "Kwargs": ', '.join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else "—",
            }

            if task.retry is not None:
                task_info["Повторов"] = task.retry
            if task.retry_on_exc:
                task_info["Искл. для повторов"] = pformat(task.retry_on_exc)
            if task.decode:
                task_info["Декодирование"] = str(task.decode)
            if task.generate_handler:
                task_info["Генератор"] = str(task.generate_handler)
            if task.executor:
                task_info["Исполнитель"] = str(task.executor)
            if task.middlewares:
                task_info["Мидлвари"] = pformat(task.middlewares)
            if task.extra:
                # Вставляем многострочное значение с отступом
                extra_lines = "\n" + "\n".join(f" * {k}: {v}" for k, v in task.extra.items())
                task_info["Дополнительно"] = extra_lines

            # Форматируем словарь
            task_block = "\n".join(
                f"{label:<{self.label_width}}: {value}" for label, value in task_info.items()
            )

            lines.append(task_block)
            lines.append("-" * 50)

        return "\n".join(lines) or "Нет зарегистрированных задач."

    def _task_get_args_kwargs(self, func):
        """Получение позиционных и ключевых аргументов функции задачи.

        Args:
            func (Callable): Функция задачи.

        Returns:
            tuple: Позиционные и ключевые аргументы.
        """
        sig = signature(func)
        positional_args = []
        keyword_args = {}

        for name, param in sig.parameters.items():
            annotation = param.annotation if param.annotation is not _empty else None

            type_str = f": {annotation.__name__}" if isinstance(annotation, type) else f": {annotation}" if annotation else ""

            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                if param.default is param.empty:
                    positional_args.append(f"{name}{type_str}")
                else:
                    keyword_args[f"{name}{type_str}"] = param.default
            elif param.kind == param.KEYWORD_ONLY:
                type_str = type_str or ""
                keyword_args[f"{name}{type_str}"] = param.default if param.default is not param.empty else "required"
            elif param.kind == param.VAR_POSITIONAL:
                positional_args.append(f"*{name}")
            elif param.kind == param.VAR_KEYWORD:
                keyword_args[f"**{name}"] = "..."

        return positional_args, keyword_args
