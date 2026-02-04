"""Sync Redis Global Config."""
from __future__ import annotations

import time
from threading import Thread
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, cast

import redis
from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.global_config import GlobalConfigSchema

from .base import BaseGlobalConfig

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents


class SyncRedisGlobalConfig(BaseGlobalConfig[Literal[False]], SyncPluginMixin):
    """
    Global Config running through Redis and working with global values.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.configs import SyncRedisGlobalConfig
    from qtasks.storage import SyncRedisStorage
    from qtasks.brokers import SyncRedisBroker

    global_config = SyncRedisGlobalConfig(name="QueueTasks", url="redis://localhost:6379/2")

    storage = SyncRedisStorage(name="QueueTasks", global_config=global_config, url="redis://localhost:6379/2")

    broker = SyncRedisBroker(name="QueueTasks", storage=storage, url="redis://localhost:6379/2")

    app = QueueTasks(broker=broker)
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc("""
                    Project name. This name is also used by the broker.

                    Default: `QueueTasks`.
                    """),
        ] = "QueueTasks",
        url: Annotated[
            str,
            Doc("""
                    URL to connect to Redis.

                    Default: `redis://localhost:6379/0`.
                    """),
        ] = "redis://localhost:6379/0",
        redis_connect: Annotated[
            redis.Redis | None,
            Doc("""
                    External connection class to Redis.

                    Default: `None`.
                    """),
        ] = None,
        config_name: Annotated[
            str | None,
            Doc("""
                    Folder name with Hash. The name is updated to: `name:queue_name`.

                    Default: `name:GlobalConfig`.
                    """),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc("""
                    Config.

                    Default: `qtasks.configs.config.QueueConfig`.
                    """),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc("""
                    Events.

                    Default: `qtasks.events.SyncEvents`.
                    """),
        ] = None,
    ):
        """
        Initializing the Redis global config.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to Redis. Default: `redis://localhost:6379/0`.
            redis_connect (redis.Redis, optional): External Redis connection class. Default: None.
            config_name (str, optional): Name of the Hash Folder. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Configuration. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.SyncEvents`.
        """
        super().__init__(name=name, log=log, config=config, events=events)
        self.name = name
        self.url = url
        self.config_name = f"{self.name}:{config_name or 'GlobalConfig'}"
        self.events = self.events or SyncEvents()

        self.client = redis_connect or redis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )
        self.running = False

    def set(self, name: str, key: str, value: str) -> None:
        """
        Add new value.

        Args:
            name (str): Name.
            key (str): Key.
            value(str): Value.
        """
        new_data = self._plugin_trigger(
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

        self.client.hset(name=f"{self.config_name}:{name}", key=key, value=value)
        return

    def get(self, key: str, name: str) -> Any:
        """
        Get value.

        Args:
            key (str): Key.
            name (str): Name.

        Returns:
            Any: Value.
        """
        result = self.client.hget(name=f"{self.config_name}:{key}", key=name)
        new_result = self._plugin_trigger(
            "global_config_get", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    def get_all(self, key: str) -> dict[str, Any]:
        """
        Get all values.

        Args:
            key (str): Key.

        Returns:
            Dict[str, Any]: Values.
        """
        raw = self.client.hgetall(name=f"{self.config_name}:{key}")
        result = cast(dict, raw)
        new_result = self._plugin_trigger(
            "global_config_get_all", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    def get_match(self, match: str) -> Any | dict:
        """
        Get value by pattern.

        Args:
            match (str): Pattern.

        Returns:
            Any | Dict[str, Any]: Value or Values.
        """
        self.config_name: str
        result = self.client.hscan(self.config_name, match=match)
        new_result = self._plugin_trigger(
            "global_config_get_match", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    def start(self) -> None:
        """Launching the Broker. This function is enabled by the main instance of `QueueTasks` via `run_forever."""
        self._plugin_trigger("global_config_start", global_config=self)
        self.running = True
        global_config = GlobalConfigSchema(name=self.name, status="running")
        self.client.hset(
            name=f"{self.config_name}:main", mapping=global_config.__dict__
        )
        Thread(target=self._set_status, daemon=True).start()

    def stop(self) -> None:
        """Stops Global Config. This function is invoked by the main `QueueTasks` instance after the `run_forever` function completes."""
        self._plugin_trigger("global_config_stop", global_config=self)
        self.running = False
        self.client.close()
        return

    def _set_status(self):
        """Updates the startup status of the global config."""
        self._plugin_trigger("global_config_set_status", global_config=self)
        ttl = self.config.global_config_status_ttl
        interval = self.config.global_config_status_set_periodic
        while self.running:
            self.client.expire(f"{self.config_name}:main", ttl)
            time.sleep(interval)
