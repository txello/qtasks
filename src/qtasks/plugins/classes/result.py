"""Result model for Plugin."""


from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class PluginResult:
    result: Optional[Dict[str, Any]] = None

    args_next: Optional[tuple | list] = None
    kwargs_next: Optional[dict] = None

    cache: Optional[dict] = None
