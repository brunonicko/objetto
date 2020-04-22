# -*- coding: utf-8 -*-
"""Base constants."""

from weakref import ref as _ref


DEAD_REF = _ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())
