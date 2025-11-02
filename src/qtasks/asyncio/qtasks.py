"""qtasks.py - Main asyncio module for the QueueTasks framework."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union, overload
from uuid import UUID

import asyncio_atexit
from typing_extensions import Doc

from qtasks.base.qtasks import BaseQueueTasks
from qtasks.brokers.async_redis import AsyncRedisBroker
from qtasks.configs import QueueConfig
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.results.async_result import AsyncResult
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.starters.async_starter import AsyncStarter
from qtasks.workers.async_worker import AsyncWorker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.schemas.task import Task
    from qtasks.starters.base import BaseStarter
    from qtasks.workers.base import BaseWorker


class QueueTasks(BaseQueueTasks[Literal[True]], AsyncPluginMixin):
    """
    `QueueTasks` - Фреймворк для очередей задач.

    Читать больше:
    [Первые шаги](https://txello.github.io/qtasks/ru/getting_started/).

    ## Пример

    ```python
    from qtasks import QueueTasks

    app = QueueTasks()
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется компонентами(Воркер, Брокер и т.п.)

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker_url: Annotated[
            str | None,
            Doc(
                """
                    URL для Брокера. Используется Брокером по умолчанию через параметр url.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        broker: Annotated[
            Optional[BaseBroker],
            Doc(
                """
                    Брокер. Хранит в себе обработку из очередей задач и хранилище данных.

                    По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Воркер. Хранит в себе обработку задач.

                    По умолчанию: `qtasks.workers.AsyncWorker`.
                    """
            ),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
                    """
            ),
        ] = None,
    ):
        """
        Инициализация QueueTasks.

        Args:
            name (str): Имя проекта. По умолчанию: `QueueTasks`.
            broker_url (str, optional): URL для Брокера. Используется Брокером по умолчанию через параметр url. По умолчанию: `None`.
            broker (Type[BaseBroker], optional): Брокер. Хранит в себе обработку из очередей задач и хранилище данных. По умолчанию: `qtasks.brokers.AsyncRedisBroker`.
            worker (Type[BaseWorker], optional): Воркер. Хранит в себе обработку задач. По умолчанию: `qtasks.workers.AsyncWorker`.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.QueueConfig`.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        broker = broker or AsyncRedisBroker(
            name=name, url=broker_url, log=log, config=config, events=events
        )
        worker = worker or AsyncWorker(
            name=name, broker=broker, log=log, config=config, events=events
        )

        events = events or AsyncEvents()

        super().__init__(
            name=name,
            broker=broker,
            worker=worker,
            log=log,
            config=config,
            events=events,
        )

        self._method = "async"

        self.broker: BaseBroker[Literal[True]]
        self.worker: BaseWorker[Literal[True]]

        self.starter: BaseStarter[Literal[True]] | None = None

        self._global_loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc(
                """
                Асинхронный loop, может быть указан.

                По умолчанию: `None`.
                """
            ),
        ] = None

        self._registry_tasks()

        self._set_state()

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = 0.0,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Task: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Union[Task, Optional[Task]]:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию `()`.
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.

            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` или `None`.
        """
        if priority is None:
            task_registry = self.tasks.get(task_name, 0)
            priority = (
                task_registry.priority
                if isinstance(task_registry, TaskExecSchema)
                else 0
            )

        args, kwargs = args or (), kwargs or {}
        extra = None

        new_args = await self._plugin_trigger(
            "qtasks_add_task_before_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=priority,
            args=args,
            kw=kwargs,
            return_last=True,
        )

        task_priority: int = priority

        if new_args:
            task_name = new_args.get("task_name", task_name)
            task_priority = new_args.get("priority", task_priority)
            extra = new_args.get("extra", extra)
            args = new_args.get("args", args)
            kwargs = new_args.get("kw", kwargs)

        task = await self.broker.add(
            task_name=task_name,
            priority=task_priority,
            extra=extra,
            args=args,
            kwargs=kwargs,
        )

        await self._plugin_trigger(
            "qtasks_add_task_after_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=task_priority,
            args=args,
            kwargs=kwargs,
        )

        if timeout is not None:
            return await AsyncResult(uuid=task.uuid, app=self, log=self.log).result(
                timeout=timeout
            )
        return task

    async def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union[Task, None]:
        """Получить задачу.

        Args:
            uuid (UUID|str): UUID Задачи.

        Returns:
            Task|None: Данные задачи или None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)

        result = await self.broker.get(uuid=uuid)
        new_result = await self._plugin_trigger(
            "qtasks_get", qtasks=self, broker=self.broker, task=result, return_last=True
        )
        if new_result:
            result = new_result.get("task", result)
        return result

    def run_forever(
        self,
        loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc(
                """
                    Асинхронный loop.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        starter: Annotated[
            Optional[BaseStarter],
            Doc(
                """
                    Стартер. Хранит в себе способы запуска компонентов.

                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
            ),
        ] = None,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество запущенных воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Обновить config у воркера и брокера.

                    По умолчанию: `True`.
                    """
            ),
        ] = True,
    ) -> None:
        """Запуск асинхронно Приложение.

        Args:
            loop (asyncio.AbstractEventLoop, optional): асинхронный loop. По умолчанию: None.
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
        """
        self.starter = starter or AsyncStarter(
            name=self.name,
            worker=self.worker,
            broker=self.broker,
            log=self.log,
            config=self.config,
            events=self.events,
        )

        plugins_hash = {}
        for plugins in [
            self.plugins,
            self.worker.plugins,
            self.broker.plugins,
            self.broker.storage.plugins,
        ]:
            plugins_hash.update(plugins)

        self._set_state()

        self.starter.start(
            loop=loop,
            num_workers=num_workers,
            reset_config=reset_config,
            plugins=plugins_hash,
        )

    async def stop(self):
        """Останавливает все компоненты."""
        await self._plugin_trigger("qtasks_stop", qtasks=self, starter=self.starter)
        if self.starter:
            await self.starter.stop()

    async def ping(self, server: bool = True) -> bool:
        """Проверка запуска сервера.

        Args:
            server (bool, optional): Проверка через сервер. По умолчанию `True`.

        Returns:
            bool: True - Работает, False - Не работает.
        """
        await self._plugin_trigger(
            "qtasks_ping", qtasks=self, global_config=self.broker.storage.global_config
        )
        if server and self.broker.storage.global_config:
            loop = asyncio.get_running_loop()
            asyncio_atexit.register(self.broker.storage.global_config.stop, loop=loop)
            status = await self.broker.storage.global_config.get("main", "status")
            return status is not None
        return True

    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self._plugin_trigger("qtasks_flush_all", qtasks=self, broker=self.broker)
        await self.broker.flush_all()
