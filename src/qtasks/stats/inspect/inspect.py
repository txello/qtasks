"""InspectStats."""

from typing import TYPE_CHECKING, Union

from .base import UtilsInspectStats

if TYPE_CHECKING:
    from qtasks import QueueTasks
    from qtasks.asyncio import QueueTasks as aioQueueTasks


class InspectStats(UtilsInspectStats):
    """Class for inspection of statistics."""

    def __init__(self, app: Union["QueueTasks", "aioQueueTasks"]):
        """
        Initializing the statistics inspection.

        Args:
            app (QueueTasks): Application instance.
        """
        self._app = app

    def app(self, json: bool = False):
        """
        Getting information about the application.

        Args:
            json (bool, optional): Flag to return in JSON format. Default: `False`.

        Returns:
            str: Application information.
        """
        return self._app_parser(self._app, json=json)

    def task(self, task_name: str, json: bool = False):
        """
        Obtaining information about a task.

        Args:
            task_name (str): The name of the task.
            json (bool, optional): Flag to return in JSON format. Default: `False`.

        Returns:
            TaskExecSchema: Schema of the task function.
        """
        if json:
            return self._parser_json(self._app.tasks[task_name])
        return self._tasks_parser((self._app.tasks[task_name],))

    def tasks(self, *tasks: tuple[str], json: bool = False):
        """
        Obtaining information about tasks.

        Returns:
            List[TaskExecSchema]: Task function schemas.
            json (bool, optional): Flag to return in JSON format. Default: `False`.
        """
        if not tasks:
            result = self._app.tasks.values()
        else:
            result = [
                self._app.tasks[task] for task in tasks if task in self._app.tasks
            ]

        if json:
            return self._parser_json(result)

        return self._tasks_parser(result)
