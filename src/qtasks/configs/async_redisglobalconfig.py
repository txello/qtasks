"""Async Redis Global Config."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, cast

import redis.asyncio as aioredis
from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.global_config import GlobalConfigSchema

from .base import BaseGlobalConfig

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents


class AsyncRedisGlobalConfig(BaseGlobalConfig[Literal[True]], AsyncPluginMixin):
    """
    Global Config running through Redis and working with global values.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.configs import AsyncRedisGlobalConfig
    from qtasks.storage import AsyncRedisStorage
    from qtasks.brokers import AsyncRedisBroker

    global_config = AsyncRedisGlobalConfig(name="QueueTasks", url="redis://localhost:6379/2")

    storage = AsyncRedisStorage(name="QueueTasks", global_config=global_config, url="redis://localhost:6379/2")

    broker = AsyncRedisBroker(name="QueueTasks", storage=storage, url="redis://localhost:6379/2")

    app = QueueTasks(broker=broker)
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется брокером.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        url: Annotated[
            str,
            Doc(
                """
                    URL для подключения к Redis.

                    По умолчанию: `redis://localhost:6379/0`.
                    """
            ),
        ] = "redis://localhost:6379/0",
        redis_connect: Annotated[
            aioredis.Redis | None,
            Doc(
                """
                    Внешний класс подключения к Redis.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        config_name: Annotated[
            str | None,
            Doc(
                """
                    Имя Папки с Hash. Название обновляется на: `name:queue_name`.

                    По умолчанию: `name:GlobalConfig`.
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

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
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
        Initializing the asynchronous Redis global config.

        Args:
            name (str, optional): Project name. Default: "QueueTasks".
            url (str, optional): URL to connect to Redis. Default: "redis://localhost:6379/0".
            redis_connect (aioredis.Redis, optional): External Redis connection class. Default: None.
            config_name (str, optional): Name of the Hash Folder. Default: None.
            log (Logger, optional): Logger. Default: None.
            config (QueueConfig, optional): Configuration. Default: None.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        super().__init__(name=name, log=log, config=config, events=events)
        self.name = name
        self.url = url
        self.config_name = f"{self.name}:{config_name or 'GlobalConfig'}"
        self.events = self.events or AsyncEvents()

        self.client = redis_connect or aioredis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )

        self.status_event = None
        self.running = False

    async def set(self, name: str, key: str, value: str) -> None:
        """
        Add new value.

        Args:
            name (str): Name.
            key (str): Key.
            value(str): Value.
        """
        new_data = await self._plugin_trigger(
            "global_config_set",
            global_config=self,
            name_=name,
            key=key,
            value=value,
            return_last=True,
        )
        if new_data:
            name = new_data.get("name", name)
            key = new_data.get("key", key)
            value = new_data.get("value", value)

        raw = self.client.hset(name=f"{self.config_name}:{name}", key=key, value=value)
        await cast(Awaitable[int], raw)
        return

    async def get(self, key: str, name: str) -> Any:
        """
        Get value.

        Args:
            key (str): Key.
            name (str): Name.

        Returns:
            Any: Value.
        """
        raw = self.client.hget(name=f"{self.config_name}:{key}", key=name)
        result = await cast(Awaitable[str | None], raw)

        new_result = await self._plugin_trigger(
            "global_config_get", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    async def get_all(self, key: str) -> dict[str, Any]:
        """
        Get all values.

        Args:
            key (str): Key.

        Returns:
            Dict[str, Any]: Values.
        """
        raw = self.client.hgetall(name=f"{self.config_name}:{key}")
        result = await cast(Awaitable[dict], raw)
        new_result = await self._plugin_trigger(
            "global_config_get_all", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    async def get_match(self, match: str) -> Any | dict:
        """
        Get values ​​by pattern.

        Args:
            match (str): Pattern.

        Returns:
            Any | Dict[str, Any]: Value or Values.
        """
        self.config_name: str
        raw = self.client.hscan(self.config_name, match=match)
        result = await cast(Awaitable[Any], raw)
        new_result = await self._plugin_trigger(
            "global_config_get_match", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    async def start(self) -> None:
        """Launching the Broker. This function is enabled by the main instance of `QueueTasks` via `run_forever."""
        await self._plugin_trigger("global_config_start", global_config=self)
        self.running = True
        loop = asyncio.get_running_loop()
        self.status_event = loop.create_task(self._set_status())
        global_config = GlobalConfigSchema(name=self.name, status="running")
        raw = self.client.hset(
            name=f"{self.config_name}:main", mapping=global_config.__dict__
        )
        await cast(Awaitable[int], raw)

    async def stop(self) -> None:
        """Stops Global Config. This function is invoked by the main `QueueTasks` instance after the `run_forever` function completes."""
        await self._plugin_trigger("global_config_stop", global_config=self)
        self.running = False
        if self.status_event:
            self.status_event.cancel()
        await self.client.aclose()

    async def _set_status(self):
        """Updates the startup status of the global config."""
        await self._plugin_trigger("global_config_set_status", global_config=self)
        ttl = self.config.global_config_status_ttl
        interval = self.config.global_config_status_set_periodic
        while self.running:
            await self.client.expire(f"{self.config_name}:main", ttl)
            await asyncio.sleep(interval)
