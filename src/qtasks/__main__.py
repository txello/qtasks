"""Входная точка для запуска QTasks."""

from argparse import ArgumentParser
from importlib import import_module
import os
import sys
from types import FunctionType
from typing import TYPE_CHECKING, Union


from qtasks.stats.sync_stats import SyncStats

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks


sys.path.append(os.path.abspath(os.getcwd()))


def get_app(app_arg: str) -> Union["QueueTasks", "aioQueueTasks", None]:
    """Получение экземпляра приложения.

    Args:
        app_arg (str): Аргумент приложения в формате "module:app".

    Returns:
        QueueTasks: Экземпляр приложения.
    """
    try:
        if not app_arg:
            raise ValueError("Не указан аргумент приложения.")
        file_path, app_var = app_arg.split(":")[0], app_arg.split(":")[-1]
        file = import_module(file_path)
        app = getattr(file, app_var)
        return app() if isinstance(app, FunctionType) else app
    except Exception as e:
        print(f"[QTasks] Ошибка при получении приложения: {e}")
        return


def positional(args):
    """Разбор позиционных аргументов."""
    positional_args = []
    keyword_args = {}
    for arg in args.extra:
        if "=" in arg:
            key, value = arg.split("=", 1)

            lowered = value.lower()
            if lowered in {"true", "false"}:
                value = lowered == "true"
            elif lowered.isdigit():
                value = int(lowered)
            elif lowered.replace(".", "", 1).isdigit():
                value = float(lowered)
            keyword_args[key] = value
        else:
            positional_args.append(arg)

    return positional_args, keyword_args


def main():
    """Главная функция."""
    parser = ArgumentParser(
        prog="QTasks",
        description="QueueTasks framework",
        epilog="Text at the bottom of help",
    )
    parser.add_argument("-A", "-app")
    parser.add_argument("--port", type=int, default=8000)
    subparsers = parser.add_subparsers(dest="command")

    # subcommand: run
    subparsers.add_parser("run", help="Запустить приложение")

    # subcommand: web
    subparsers.add_parser("web", help="Запустить WebView")

    # subcommand: stats
    stats_parser = subparsers.add_parser("stats", help="Инспекция статистики")
    stats_parser.add_argument("--stats-app", help="Объявленное приложение для статистики")
    stats_subparsers = stats_parser.add_subparsers(dest="stats_command")

    # stats inspect <target> [*extra]
    inspect_parser = stats_subparsers.add_parser("inspect", help="Инспектировать")
    inspect_parser.add_argument("target", help="Метод инспекции (например: tasks, task, result)")
    inspect_parser.add_argument("extra", nargs="*", help="Дополнительные аргументы")

    args = parser.parse_args()

    app = get_app(args.A)

    if args.command == "run":
        if not app:
            parser.error("Не удалось получить экземпляр приложения!")
        app.run_forever()

    elif args.command == "web":
        # Эксперементально!
        import qtasks_webview

        qtasks_webview.app_qtasks = app
        qtasks_webview.run(port=args.port)

    elif args.command == "stats":
        if not app:
            parser.error("Не удалось получить экземпляр приложения!")

        stats = get_app(args.stats_app) if args.stats_app else SyncStats(app=app)

        if args.stats_command:
            handler = getattr(stats, args.stats_command, None)
            if handler is None or not callable(handler):
                raise ValueError(f"Неизвестная команда stats: {args.stats_command}")

            handler_obj = handler()
            target_func = getattr(handler_obj, args.target, None)
            if target_func is None or not callable(target_func):
                raise ValueError(f"Неизвестная подкоманда {args.stats_command}.{args.target}")

            positional_args, keyword_args = positional(args)

            print(target_func(*positional_args, **keyword_args))

        else:
            stats_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
