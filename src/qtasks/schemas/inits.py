"""Init Inits."""

from dataclasses import dataclass
from types import FunctionType


@dataclass
class InitsExecSchema:
    """
    `InitsExecSchema` schema.
    
        Args:
            name (str): Event name.
            func (FunctionType): Initialization function.
    
            awaiting (bool): Asynchronous initialization. Default: False
    """

    name: str
    func: FunctionType

    awaiting: bool = False
