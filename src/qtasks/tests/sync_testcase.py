"""Sync test classes."""

import threading
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.tests.base import BaseTestCase

if TYPE_CHECKING:
    from qtasks import QueueTasks
    from qtasks.schemas.task import Task
    from qtasks.starters.base import BaseStarter


class SyncTestCase(BaseTestCase[Literal[False]]):
    """
    Synchronous testing case.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.tests import SyncTestCase

    app = QueueTasks()

    test_case = SyncTestCase(app=app)
    ```
    """

    def __init__(
        self,
        app: Annotated[
            "QueueTasks",
            Doc("""
                    Main copy.
                    """),
        ],
        name: Annotated[
            str | None,
            Doc("""
                    Project name. This name can be used for test components.

                    Default: `None`.
                    """),
        ] = None,
    ):
        """
        Synchronous test case.

        Args:
            app(QueueTasks): Main instance.
            name (str, optional): Project name. This name can be used for test components. Default: `None`.
        """
        super().__init__(app=app, name=name)
        self.app: QueueTasks

    def start_in_background(
        self,
        starter: Annotated[
            Optional["BaseStarter"],
            Doc("""
                    Starter. Stores methods for launching components.

                    Default: `qtasks.starters.AsyncStarter`.
                    """),
        ] = None,
        num_workers: Annotated[
            int,
            Doc("""
                    Number of running workers.

                    Default: `4`.
                    """),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc("""
                    Update the config of the worker and broker.

                    Default: `True`.
                    """),
        ] = True,
    ):
        """
        Run `app.run_forever()` in the background.

        Args:
            starter (BaseStarter, optional): Starter. Default: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Number of workers running. Default: 4.
            reset_config (bool, optional): Update the config of the worker and broker. Default: True.
        """

        def run():
            self.start(
                starter=starter, num_workers=num_workers, reset_config=reset_config
            )

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def start(
        self,
        starter: Annotated[
            Optional["BaseStarter"],
            Doc("""
                    Starter. Stores methods for launching components.

                    Default: `qtasks.starters.AsyncStarter`.
                    """),
        ] = None,
        num_workers: Annotated[
            int,
            Doc("""
                    Number of running workers.

                    Default: `4`.
                    """),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc("""
                    Update the config of the worker and broker.

                    Default: `True`.
                    """),
        ] = True,
    ) -> None:
        """
        Runs `app.run_forever()`.

        Args:
            starter (BaseStarter, optional): Starter. Default: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Number of workers running. Default: 4.
            reset_config (bool, optional): Update the config of the worker and broker. Default: True.
        """
        self.app.run_forever(
            starter=starter, num_workers=num_workers, reset_config=reset_config
        )

    def stop(self):
        """Stops the test case."""
        if self.test_config.global_config and self.app.broker.storage.global_config:
            self.app.broker.storage.global_config.stop()

        if self.test_config.storage:
            self.app.broker.storage.stop()

        if self.test_config.broker:
            self.app.broker.stop()

        if self.test_config.worker:
            self.app.worker.stop()

    def add_task(
        self,
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        *args: Annotated[
            Any,
            Doc("""
                    args of the task.

                    Default: `()`.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    The task has priority.

                    Default: `0`.
                    """),
        ] = 0,
        timeout: Annotated[
            float | None,
            Doc("""
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc("""
                    kwargs tasks.

                    Default: `{}`.
                    """),
        ],
    ) -> Union["Task", None]:
        """
        Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: `0`.
            args (tuple, optional): task args. Default: `()`.
            kwargs (dict, optional): kwargs of tasks. Default: `{}`
            timeout (float, optional): Task timeout. If specified, the task is called via `qtasks.results.SyncResult`.

        Returns:
            Task|None: Task data or None.
        """
        if self.test_config.broker:
            return self.app.add_task(
                task_name, *args, priority=priority, timeout=timeout, **kwargs
            )
        elif self.test_config.worker:
            return self.app.worker.add(
                name=task_name,
                uuid=uuid4(),
                priority=priority,
                created_at=time(),
                args=args,
                kwargs=kwargs,
            )
        else:
            print(
                f"[SyncTestCase: {self.name}] Be sure to enable Worker or Broker!"
            )
            return

    def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc("""
                    UUID of the task.
                    """),
        ],
    ) -> Union["Task", None]:
        """
        Get a task.

        Args:
            uuid (UUID|str): UUID of the Task.

        Returns:
            Task|None: Task data or None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        if not self.test_config.broker:
            print(f"[SyncTestCase: {self.name}] Broker is not started!")
            return
        return self.app.broker.get(uuid=uuid)
