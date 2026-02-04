"""Init Schemas."""

from .global_config import GlobalConfigSchema
from .task_exec import TaskExecSchema
from .task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)
from .test import TestConfig
