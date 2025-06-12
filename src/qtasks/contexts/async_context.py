import asyncio
from typing import TYPE_CHECKING, NoReturn
from uuid import UUID

from qtasks.configs.config import QueueConfig
from qtasks.exc.task import TaskCancelError
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.logs import Logger


class AsyncContext:
    """
    Контекст, связанный с асинхронными задачами.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.registries import AsyncTask

    app = QueueTasks()

    @app.task(echo=True)
    async def my_task(self: AsyncTask):
        self.ctx # AsyncContext
    ```
    """
    def __init__(self, **kwargs):
        self.task_uuid = kwargs.get("task_uuid")
        """UUID задачи."""

        self.generate_handler = kwargs.get("generate_handler")
        """Функция-генератор для создания задач."""

        self._app: "QueueTasks" = kwargs.get("app")
        """Приложение, к которому принадлежит задача."""
        self._update_app()

        self._log: "Logger" = kwargs.get("log")
        """Логгер."""

        self._metadata: Task|None = None
        """Метаданные задачи."""

    def get_logger(self, name: str|None = None) -> "Logger":
        """Возвращает логгер для текущего контекста.

        Args:
            name (str|None): Имя логгера. Если не указано, используется "AsyncContext".

        Returns:
            Logger: Логгер для текущего контекста.
        """
        self._log = self._app.log.with_subname(name or "AsyncContext")
        return self._log
    
    def get_config(self) -> QueueConfig:
        """Возвращает конфигурацию приложения.

        Returns:
            QueueConfig: Конфигурация приложения.
        """
        return self._app.config

    async def get_metadata(self, cache=True) -> Task|None:
        """Возвращает метаданные задачи.

        Args:
            cache (bool): Использовать кэшированные метаданные.

        Returns:
            Task|None: Метаданные задачи или None, если не найдены.
        """
        if cache:
            if not self._metadata:
                self._metadata = await self._app.get(self.task_uuid)
            return self._metadata
        return await self._app.get(self.task_uuid)

    async def get_task(self, uuid: UUID|str) -> Task|None:
        """Возвращает задачу по UUID.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Задача или None, если не найдена.
        """
        return await self._app.get(uuid)

    async def sleep(self, seconds: float) -> None:
        """Приостанавливает выполнение на заданное количество секунд.

        Args:
            seconds (float): Количество секунд для приостановки.
        """
        await asyncio.sleep(seconds)

    def cancel(self, reason: str = "") -> NoReturn:
        """Отменяет задачу.

        Args:
            reason (str): Причина отмены задачи.

        Raises:
            TaskCancelError: Исключение, вызываемое при отмене задачи.
        """

        raise TaskCancelError(reason or "AsyncContext.cancel")

    def get_component(self, name: str):
        """Возвращает компонент приложения по имени.

        Args:
            name (str): Имя компонента.

        Returns:
            Any: Компонент приложения или None, если не найден.
        """
        return getattr(self._app, name, None)

    def _update_app(self):
        """Обновляет приложение для текущего контекста."""
        if not self._app:
            import qtasks._state
            self._app = qtasks._state.app_main
        return

    def _update(self, **kwargs):
        """Обновляет атрибуты контекста.

        Args:
            kwargs (dict, optional): Новые значения атрибутов контекста.
        """
        for name, value in kwargs.items():
            setattr(self, name, value)
        return
