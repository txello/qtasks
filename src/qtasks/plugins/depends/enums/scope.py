from enum import Enum


class ScopeEnum(Enum):
    TASK = "task"
    WORKER = "worker"
    BROKER = "broker"
    STORAGE = "storage"
    GLOBAL_CONFIG = "global_config"
