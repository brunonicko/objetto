# -*- coding: utf-8 -*-
"""Base constants."""

from weakref import ref as _ref
from enum import Enum as _Enum


# Dead weak reference object
DEAD_REF = _ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())


class SpecialValue(_Enum):
    """Special value enum."""

    MISSING = "missing"  # represents the absence of a value
    DELETED = "deleted"  # indicates that the value was deleted
