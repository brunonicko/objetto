# -*- coding: utf-8 -*-
"""Constants."""

from weakref import ref as _ref
from enum import Enum as _Enum

PACKAGE_LOADER_DOT_PATH_ENV_VAR = "MODELO_PACKAGE_LOADER_DOT_PATH"
DEAD_REF = _ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())


class EventPhase(_Enum):
    """Event phase."""

    INTERNAL_PRE = "internal_pre"
    PRE = "pre"
    POST = "post"
    INTERNAL_POST = "internal_post"


class SpecialValue(_Enum):
    """Special Value."""

    MISSING = "missing"
    DELETED = "deleted"


class AttributeAccessType(_Enum):
    """Attribute access type."""

    GETTER = "getter"
    SETTER = "setter"
    DELETER = "deleter"
