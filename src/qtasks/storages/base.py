from abc import ABC, abstractmethod
from dataclasses import field, fields, make_dataclass
import datetime
import json
from typing import List, Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
from typing import TYPE_CHECKING

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusCancelSchema, TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusProcessSchema, TaskStatusSuccessSchema

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.plugins.base import BasePlugin


class BaseStorage(ABC):
    """
    `BaseStorage` - Абстрактный класс, который является фундаментом для Хранилищ.

    ## Пример

    ```python
    from qtasks.storages.base import BaseStorage
    
    class MyStorage(BaseStorage):
        def __init__(self, name: str = None):
            super().__init__(name=name)
            pass
    ```
    """
    
    def __init__(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя можно использовать для тегов для Storage.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            global_config: Annotated[
                Optional["BaseGlobalConfig"],
                Doc(
                    """
                    Глобальный конфиг.
                    
                    По умолчанию: `None`.
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
            ] = None,
            config: Annotated[
                Optional[QueueConfig],
                Doc(
                    """
                    Конфиг.
                    
                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
                )
            ] = None
        ):
        self.name = name
        self.client = None
        self.global_config: "BaseGlobalConfig"|None = global_config

        self.config = config or QueueConfig()
        self.log = log.with_subname("Storage") if log else Logger(name=self.name, subname="Storage", default_level=self.config.logs_default_level, format=self.config.logs_format)
        self.plugins: dict[str, List["BasePlugin"]] = {}

        self.init_plugins()
    
    @abstractmethod
    def add(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ],
            task_status: Annotated[
                TaskStatusNewSchema,
                Doc(
                    """
                    Схема статуса новой задачи.
                    """
                )
            ]
        ) -> None:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        pass
    
    @abstractmethod
    def get(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        pass
    
    @abstractmethod
    def get_all(self) -> list[Task]:
        """Получить все задачи.

        Returns:
            list[Task]: Массив задач.
        """
        pass
    
    @abstractmethod
    def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        pass
    
    @abstractmethod
    def start(self):
        """Запускает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после запуске функции `run_forever`."""
        pass
    
    @abstractmethod
    def stop(self):
        """Останавливает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass
    
    def add_plugin(self, 
            plugin: Annotated[
                "BasePlugin",
                Doc(
                    """
                    Плагин.
                    """
                )
            ],
            trigger_names: Annotated[
                Optional[List[str]],
                Doc(
                    """
                    Имя триггеров для плагина.
                    
                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
                )
            ] = None
        ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return
        
    def remove_finished_task(self,
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    Схема приоритетной задачи.
                    """
                )
            ],
            model: Annotated[
                Union[TaskStatusProcessSchema|TaskStatusErrorSchema|TaskStatusCancelSchema],
                Doc(
                    """
                    Модель результата задачи.
                    """
                )
            ]
        ) -> None:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        pass
    
    def _delete_finished_tasks(self, **kwargs) -> None:
        pass
    
    def _running_older_tasks(self, **kwargs) -> None:
        pass
    
    def update_config(self,
            config: Annotated[
                QueueConfig,
                Doc(
                    """
                    Конфиг.
                    """
                )
            ]
        ) -> None:
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return
    
    def flush_all(self) -> None:
        """Удалить все данные."""
        pass

    def _build_task(self, uuid, result: dict) -> Task:
        # Сначала собираем стандартные аргументы Task

        base_kwargs = dict(
            status=result["status"],
            uuid=uuid,
            priority=int(result["priority"]),
            task_name=result["task_name"],
            args=json.loads(result["args"]),
            kwargs=json.loads(result["kwargs"]),
            created_at=datetime.datetime.fromtimestamp(float(result["created_at"])),
            updated_at=datetime.datetime.fromtimestamp(float(result["updated_at"])),
        )

        # Вычисляем имена стандартных полей
        task_field_names = {f.name for f in fields(Task)}

        # Ищем дополнительные ключи
        extra_fields = []
        extra_values = {}

        for key, value in result.items():
            if key not in task_field_names:
                # Типизация примитивная — можно улучшить
                field_type = self._infer_type(value)
                extra_fields.append((key, field_type, field(default=None)))

                # Можно привести значение к типу
                if field_type is bool:
                    extra_values[key] = value.lower() == "true"
                elif field_type is int:
                    extra_values[key] = int(value)
                elif field_type is float:
                    extra_values[key] = float(value)
                else:
                    extra_values[key] = value

        # Создаем новый dataclass с дополнительными полями
        if extra_fields:
            NewTask = make_dataclass("Task", extra_fields, bases=(Task,))
        else:
            NewTask = Task

        # Объединяем все аргументы
        task = NewTask(**base_kwargs, **extra_values)
        if hasattr(task, "returning"):
            try: task.returning = json.loads(task.returning)
            except: pass
        return task
    
    def _infer_type(self, value: str):
        """Пытается определить реальный тип из строки."""
        if value.lower() in {"true", "false"}:
            return bool
        try:
            int(value)
            return int
        except ValueError:
            pass
        try:
            float(value)
            return float
        except ValueError:
            pass
        return str
    
    def init_plugins(self):
        pass