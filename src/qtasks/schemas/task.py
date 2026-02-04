"""Task Schema."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, Union
from uuid import UUID

from typing_extensions import Doc

from qtasks.results.async_result import AsyncResult
from qtasks.results.sync_result import SyncResult


@dataclass
class Task:
    """
    `Task` model.
    
        Args:
            status (str): Status.
            uuid (UUID): UUID.
            priority (int): Priority.
            task_name (str): Name.
    
            args (Tuple[str]): Arguments of type args.
            kwargs (Dict[str, Any]): Arguments of type kwargs.
    
            created_at (datetime): Created date.
            updated_at (datetime): Date of update.
    
            returning (str | None): Result. Default: `None`.
            traceback (str | None): Trace errors. Default: `None`.
    """

    status: str
    uuid: UUID
    priority: int
    task_name: str

    args: tuple[str]
    kwargs: dict[str, Any]

    created_at: datetime
    updated_at: datetime

    returning: Any | None = None
    traceback: Any | None = None

    # retry
    retry: int | None = None
    retry_child_uuid: UUID | None = None
    retry_parent_uuid: UUID | None = None

    def wait_result(
        self,
        timeout: Annotated[
            float,
            Doc(
                """
                    Таймаут задачи.
                    """
            ),
        ] = 100.0,
    ) -> Union["Task", None]:
        """
        Waiting for task result Synchronously.
        
                Args:
                    timeout (Annotated[Optional[float], Doc], optional): Timeout for waiting for the result. Default: `100.0`.
        """
        return SyncResult(uuid=self.uuid).result(timeout=timeout)

    async def wait_result_async(
        self,
        timeout: Annotated[
            float,
            Doc(
                """
                    Таймаут задачи.
                    """
            ),
        ] = 100.0,
    ) -> Union["Task", None]:
        """
        Waiting for task result Asynchronously.
        
                Args:
                    timeout (Annotated[Optional[float], Doc], optional): Timeout for waiting for the result. Default: `100.0`.
        """
        return await AsyncResult(uuid=self.uuid).result(timeout=timeout)
