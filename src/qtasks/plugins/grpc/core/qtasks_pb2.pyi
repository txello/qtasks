from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

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
    def __init__(self, name: str | None = ..., args_json: str | None = ..., kwargs_json: str | None = ..., timeout: float | None = ..., priority: int | None = ...) -> None: ...

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
    def __init__(self, ok: bool = ..., uuid: str | None = ..., result_json: str | None = ..., error: str | None = ...) -> None: ...

class GetTaskRequest(_message.Message):
    __slots__ = ("uuid", "include_result")
    UUID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_RESULT_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    include_result: bool
    def __init__(self, uuid: str | None = ..., include_result: bool = ...) -> None: ...

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
    def __init__(self, ok: bool = ..., status: str | None = ..., result_json: str | None = ..., traceback: str | None = ..., error: str | None = ...) -> None: ...
