"""Entry point for running QTasks."""
from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from importlib import import_module
from types import FunctionType
from typing import TYPE_CHECKING, Union

from qtasks.stats.sync_stats import SyncStats

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks
    from qtasks.qtasks import QueueTasks


sys.path.append(os.path.abspath(os.getcwd()))


def get_app(app_arg: str) -> Union[QueueTasks, aioQueueTasks, None]:
    """Get an application instance.

    Args:
        app_arg (str): Application argument in the format "module:app".

    Returns:
        QueueTasks: Application instance.
    """
    try:
        if not app_arg:
            raise ValueError("Application argument is not specified.")
        file_path, app_var = app_arg.split(":")[0], app_arg.split(":")[-1]
        file = import_module(file_path)
        app = getattr(file, app_var)
        return app() if isinstance(app, FunctionType) else app
    except Exception as e:
        print(f"[QTasks] Ошибка при получении приложения: {e}")
        return


def positional(args):
    """Analysis of positional arguments."""
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
    """Main function."""
    parser = ArgumentParser(
        prog="QTasks",
        description="QueueTasks framework",
        epilog="Text at the bottom of help",
    )
    parser.add_argument("-A", "-app")
    parser.add_argument("--port", type=int, default=8000)
    subparsers = parser.add_subparsers(dest="command")

    # subcommand: run
    subparsers.add_parser("run", help="Run the task queue app")

    # subcommand: web
    subparsers.add_parser("web", help="Run WebView")

    # subcommand: stats
    stats_parser = subparsers.add_parser("stats", help="Inspect statistics")
    stats_parser.add_argument(
        "--stats-app", help="Declared application for statistics (module:app)"
    )
    stats_subparsers = stats_parser.add_subparsers(dest="stats_command")

    # stats inspect <target> [*extra]
    inspect_parser = stats_subparsers.add_parser("inspect", help="Inspect statistics")
    inspect_parser.add_argument(
        "target", help="Target to inspect (e.g., tasks, task, result)"
    )
    inspect_parser.add_argument("extra", nargs="*", help="Extra arguments")
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
            parser.error("QTasks app is required for stats!")

        stats = get_app(args.stats_app) if args.stats_app else SyncStats(app=app)  # type: ignore

        if args.stats_command:
            handler = getattr(stats, args.stats_command, None)
            if handler is None or not callable(handler):
                raise ValueError(f"Unknown stats command: {args.stats_command}")

            handler_obj = handler()
            target_func = getattr(handler_obj, args.target, None)
            if target_func is None or not callable(target_func):
                raise ValueError(
                    f"Unknown subcommand {args.stats_command}.{args.target}"
                )

            positional_args, keyword_args = positional(args)

            print(target_func(*positional_args, **keyword_args))

        else:
            stats_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
