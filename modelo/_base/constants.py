# -*- coding: utf-8 -*-
"""Base constants."""

from weakref import ref as _ref
from enum import Enum as _Enum


DEAD_REF = _ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())


class SpecialValue(_Enum):
    """Special value."""

    MISSING = "missing"
    DELETED = "deleted"
