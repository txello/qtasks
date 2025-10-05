"""InspectStats."""

from typing import TYPE_CHECKING, Tuple, Union
from .base import UtilsInspectStats

if TYPE_CHECKING:
    from qtasks import QueueTasks
    from qtasks.asyncio import QueueTasks as aioQueueTasks


class InspectStats(UtilsInspectStats):
    """Класс для инспекции статистики."""

    def __init__(self, app: Union["QueueTasks", "aioQueueTasks"]):
        """Инициализация инспекции статистики.

        Args:
            app (QueueTasks): Экземпляр приложения.
        """
        self._app = app

    def app(self, json: bool = False):
        """Получение информации о приложении.

        Args:
            json (bool, optional): Флаг для возврата в формате JSON. По умолчанию: `False`.

        Returns:
            str: Информация о приложении.
        """
        return self._app_parser(self._app, json=json)

    def task(self, task_name: str, json: bool = False):
        """Получение информации о задаче.

        Args:
            task_name (str): Имя задачи.
            json (bool, optional): Флаг для возврата в формате JSON. По умолчанию: `False`.

        Returns:
            TaskExecSchema: Схема функции задачи.
        """
        if json:
            return self._parser_json(self._app.tasks[task_name])
        return self._tasks_parser((self._app.tasks[task_name],))

    def tasks(self, *tasks: Tuple[str], json: bool = False):
        """Получение информации о задачах.

        Returns:
            List[TaskExecSchema]: Схемы функции задач.
            json (bool, optional): Флаг для возврата в формате JSON. По умолчанию: `False`.
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
