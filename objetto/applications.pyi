from typing import Any, Optional, Type

from ._applications import BO
from ._applications import Application as Application
from ._applications import ApplicationMeta as ApplicationMeta
from ._applications import ApplicationProperty as ApplicationProperty
from ._applications import ApplicationSnapshot as ApplicationSnapshot

def root(obj_type: Type[BO], priority: Optional[int] = ..., **kwargs: Any) -> BO: ...
