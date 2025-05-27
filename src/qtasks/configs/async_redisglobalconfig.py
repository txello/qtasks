import asyncio
import time
from typing import Any, Optional
from typing_extensions import Annotated, Doc
import redis.asyncio as aioredis

from qtasks.logs import Logger

from .base import BaseGlobalConfig
from qtasks.schemas.global_config import GlobalConfigSchema


class AsyncRedisGlobalConfig(BaseGlobalConfig):
    """
    Глобальный Конфиг, работающий через Redis и работает с глобальными значениями.

    ## Пример

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
    
    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется брокером.
                    
                    По умолчанию: `QueueTasks`.
                    """
                )
            ] = "QueueTasks",
            url: Annotated[
                str,
                Doc(
                    """
                    URL для подключения к Redis.
                    
                    По умолчанию: `redis://localhost:6379/0`.
                    """
                )
            ] = "redis://localhost:6379/0",
            redis_connect: Annotated[
                Optional[aioredis.Redis],
                Doc(
                    """
                    Внешний класс подключения к Redis.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            config_name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя Папки с Hash. Название обновляется на: `name:queue_name`.
                    
                    По умолчанию: `name:GlobalConfig`.
                    """
                )
                ] = None,

            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None
        ):
        super().__init__(name=name, log=log)
        self.name = name
        self.url = url
        self.config_name = f"{self.name}:{config_name or 'GlobalConfig'}"
        
        self.client = redis_connect or aioredis.from_url(self.url, decode_responses=True, encoding=u'utf-8')

        self.status_event = None
        self.running = False
        
    async def set(self, name: str, key: str, value: str) -> None:
        """Добавить новое значение.

        Args:
            name (str): Имя.
            key (str): Ключ.
            value (str): Значение.
        """
        await self.client.hset(name=f"{self.config_name}:{name}", key=key, value=value)
        return
    
    async def get(self, key: str, name: str) -> Any:
        """Получить значение.

        Args:
            key (str): Ключ.
            name (str): Имя.

        Returns:
            Any: Значение.
        """
        return await self.client.hget(name=f"{self.config_name}:{key}", key=name)
    
    async def get_all(self, key: str) -> dict[Any]:
        """Получить все значения.

        Args:
            key (str): Ключ.

        Returns:
            dict[Any]: Значения.
        """
        return await self.client.hgetall(name=f"{self.config_name}:{key}")
    
    async def get_match(self, match: str) -> Any | dict[Any]:
        """Получить значения по паттерну.

        Args:
            match (str): Паттерн.

        Returns:
            Any | dict[Any]: Значение или Значения.
        """
        return await self.client.hscan(key=self.config_name, match=match)
    
    async def start(self) -> None:
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever."""
        self.running = True
        loop = asyncio.get_running_loop()
        self.status_event = loop.create_task(self._set_status())
        global_config = GlobalConfigSchema(name=self.name, status="running")
        await self.client.hset(name=f"{self.config_name}:main", mapping=global_config.__dict__)
    
    async def stop(self) -> None:
        """Останавливает Глобальный Конфиг. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever."""
        self.running = False
        if self.status_event:
            self.status_event.cancel()
        await self.client.close()

    async def _set_status(self):
        ttl = self.config.global_config_status_ttl
        interval = self.config.global_config_status_set_periodic
        while self.running:
            await self.client.expire(f"{self.config_name}:main", ttl)
            await asyncio.sleep(interval)