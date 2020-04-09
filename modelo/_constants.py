from weakref import ref as _ref
from enum import Enum as _Enum

PACKAGE_LOADER_DOT_PATH_ENV_VAR = "MODELO_PACKAGE_LOADER_DOT_PATH"
DEAD_REF = _ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())


class EventPhase(_Enum):
    """Event phase."""

    INTERNAL_PRE = 1
    PRE = 2
    POST = 3
    INTERNAL_POST = 4


class SpecialValue(_Enum):
    """Special Value."""

    MISSING = 1
    DELETED = 2


class AttributeAccessType(_Enum):
    """Attribute access type."""
    GETTER = 1
    SETTER = 2
    DELETER = 3
