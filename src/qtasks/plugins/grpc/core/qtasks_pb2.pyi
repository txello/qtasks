from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AddTaskRequest(_message.Message):
    __slots__ = ("name", "args_json", "kwargs_json", "timeout", "priority")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGS_JSON_FIELD_NUMBER: _ClassVar[int]
    KWARGS_JSON_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    name: str
    args_json: str
    kwargs_json: str
    timeout: float
    priority: int
    def __init__(self, name: _Optional[str] = ..., args_json: _Optional[str] = ..., kwargs_json: _Optional[str] = ..., timeout: _Optional[float] = ..., priority: _Optional[int] = ...) -> None: ...

class AddTaskResponse(_message.Message):
    __slots__ = ("ok", "uuid", "result_json", "error")
    OK_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    uuid: str
    result_json: str
    error: str
    def __init__(self, ok: bool = ..., uuid: _Optional[str] = ..., result_json: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class GetTaskRequest(_message.Message):
    __slots__ = ("uuid", "include_result")
    UUID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_RESULT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    include_result: bool
    def __init__(self, uuid: _Optional[str] = ..., include_result: bool = ...) -> None: ...

class GetTaskResponse(_message.Message):
    __slots__ = ("ok", "status", "result_json", "traceback", "error")
    OK_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULT_JSON_FIELD_NUMBER: _ClassVar[int]
    TRACEBACK_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    status: str
    result_json: str
    traceback: str
    error: str
    def __init__(self, ok: bool = ..., status: _Optional[str] = ..., result_json: _Optional[str] = ..., traceback: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...
