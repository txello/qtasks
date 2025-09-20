"""QTasks builds utilities."""

from dataclasses import field, fields, is_dataclass, make_dataclass
import json
import datetime
import ast


def _infer_type(value: str):
    try:
        parsed = ast.literal_eval(value)
        return type(parsed)
    except Exception:
        return str


def _convert_value(field_type, value):
    try:
        if field_type == int:
            return int(value)
        elif field_type == float:
            return float(value)
        elif field_type == bool:
            return str(value).lower() == "true"
        elif field_type in (list, dict):
            return json.loads(value)
        elif field_type == datetime.datetime:
            return datetime.datetime.fromtimestamp(float(value))
        else:
            return value
    except Exception:
        return value  # fallback: оригинальное значение


def _build_task(cls, **kwargs):
    if not is_dataclass(cls):
        raise TypeError("Expected a dataclass instance")

    base_cls = type(cls)
    base_field_defs = fields(base_cls)
    base_field_names = {f.name for f in base_field_defs}

    # 1. Извлекаем значения уже существующих полей
    known_fields = {}
    for f in base_field_defs:
        if f.name in kwargs:
            known_fields[f.name] = _convert_value(f.type, kwargs[f.name])
        else:
            known_fields[f.name] = getattr(cls, f.name)

    # 2. Новые поля
    extra_fields = []
    extra_values = {}
    for key, value in kwargs.items():
        if key not in base_field_names:
            field_type = _infer_type(value)
            extra_fields.append((key, field_type, field(default=None)))
            extra_values[key] = _convert_value(field_type, value)

    # 3. Создаём новый dataclass с расширением
    if extra_fields:
        NewCls = make_dataclass(cls.__class__.__name__, extra_fields, bases=(base_cls,))
    else:
        NewCls = base_cls

    return NewCls(**known_fields, **extra_values)
