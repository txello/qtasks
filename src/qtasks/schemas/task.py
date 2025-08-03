"""Task Schema."""

from dataclasses import InitVar, dataclass
from datetime import datetime
from typing import Annotated, Any, Dict, Optional, Tuple, Union
from typing_extensions import Doc
from uuid import UUID

from qtasks.results.async_result import AsyncResult
from qtasks.results.sync_result import SyncResult


@dataclass
class Task:
    """`Task` модель.

    Args:
        status (str): Статус.
        uuid (UUID): UUID.
        priority (int): Приоритет.
        task_name (str): Название.

        args (Tuple[str]): Аргументы типа args.
        kwargs (Dict[str, Any]): Аргументы типа kwargs.

        created_at (datetime): Дата создания.
        updated_at (datetime): Дата обновления.

        returning (str | None): Результат. По умолчанию: `None`.
        traceback (str | None): Трассировка ошибок. По умолчанию: `None`.
    """

    status: str
    uuid: UUID
    priority: int
    task_name: str

    args: Tuple[str]
    kwargs: Dict[str, Any]

    created_at: datetime
    updated_at: datetime

    returning: InitVar[Union[str, None]] = None
    traceback: InitVar[Union[str, None]] = None

    def wait_result(
        self,
        timeout: Annotated[
            Optional[float],
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.SyncTask`.
                    """
            ),
        ] = None
    ) -> Union["Task", None]:
        """Ожидание результата задачи Синхронно.

        Args:
            timeout (Annotated[Optional[float], Doc], optional): Таймаут ожидания результата. По умолчанию: `None`.
        """
        return SyncResult(uuid=self.uuid).result(timeout=timeout)

    async def wait_result_async(
        self,
        timeout: Annotated[
            Optional[float],
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None
    ) -> Union["Task", None]:
        """Ожидание результата задачи Асинхронно.

        Args:
            timeout (Annotated[Optional[float], Doc], optional): Таймаут ожидания результата. По умолчанию: `None`.
        """
        return await AsyncResult(uuid=self.uuid).result(timeout=timeout)
