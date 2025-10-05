"""Sync Redis Global Config."""

from threading import Thread
import time
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Union, cast
from typing_extensions import Annotated, Doc
import redis

from qtasks.configs.config import QueueConfig
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin

from .base import BaseGlobalConfig
from qtasks.schemas.global_config import GlobalConfigSchema

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents


class SyncRedisGlobalConfig(BaseGlobalConfig[Literal[False]], SyncPluginMixin):
    """
    Глобальный Конфиг, работающий через Redis и работает с глобальными значениями.

    ## Пример

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
            Optional[redis.Redis],
            Doc(
                """
                    Внешний класс подключения к Redis.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        config_name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя Папки с Hash. Название обновляется на: `name:queue_name`.

                    По умолчанию: `name:GlobalConfig`.
                    """
            ),
        ] = None,
        log: Annotated[
            Optional[Logger],
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            Optional[QueueConfig],
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация асинхронного Redis глобального конфига.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к Redis. По умолчанию: "redis://localhost:6379/0".
            redis_connect (redis.Redis, optional): Внешний класс подключения к Redis. По умолчанию: None.
            config_name (str, optional): Имя Папки с Hash. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфигурация. По умолчанию: None.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.SyncEvents`.
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
        """Добавить новое значение.

        Args:
            name (str): Имя.
            key (str): Ключ.
            value (str): Значение.
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
        """Получить значение.

        Args:
            key (str): Ключ.
            name (str): Имя.

        Returns:
            Any: Значение.
        """
        result = self.client.hget(name=f"{self.config_name}:{key}", key=name)
        new_result = self._plugin_trigger(
            "global_config_get", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    def get_all(self, key: str) -> Dict[str, Any]:
        """Получить все значения.

        Args:
            key (str): Ключ.

        Returns:
            Dict[str, Any]: Значения.
        """
        raw = self.client.hgetall(name=f"{self.config_name}:{key}")
        result = cast(Dict, raw)
        new_result = self._plugin_trigger(
            "global_config_get_all", global_config=self, get=result, return_last=True
        )
        if new_result:
            result = new_result.get("get", result)
        return result

    def get_match(self, match: str) -> Union[Any, dict]:
        """Получить значения по паттерну.

        Args:
            match (str): Паттерн.

        Returns:
            Any | Dict[str, Any]: Значение или Значения.
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
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever."""
        self._plugin_trigger("global_config_start", global_config=self)
        self.running = True
        global_config = GlobalConfigSchema(name=self.name, status="running")
        self.client.hset(
            name=f"{self.config_name}:main", mapping=global_config.__dict__
        )
        Thread(target=self._set_status, daemon=True).start()

    def stop(self) -> None:
        """Останавливает Глобальный Конфиг. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        self._plugin_trigger("global_config_stop", global_config=self)
        self.running = False
        self.client.close()
        return

    def _set_status(self):
        """Обновляет статус запуска глобального конфига."""
        self._plugin_trigger("global_config_set_status", global_config=self)
        ttl = self.config.global_config_status_ttl
        interval = self.config.global_config_status_set_periodic
        while self.running:
            self.client.expire(f"{self.config_name}:main", ttl)
            time.sleep(interval)
