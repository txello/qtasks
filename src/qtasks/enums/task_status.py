from enum import Enum

class TaskStatusEnum(Enum):
    NEW = "new"
    PROCESS = "process"
    
    SUCCESS = "success"
    ERROR = "error"