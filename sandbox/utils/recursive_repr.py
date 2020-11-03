# -*- coding: utf-8 -*-
"""Recursive-ready `repr` decorator."""

from threading import local
from typing import TYPE_CHECKING

from decorator import decorator

if TYPE_CHECKING:
    from typing import Any, Callable

__all__ = ["recursive_repr"]

_local = local()


@decorator
def recursive_repr(func, *args, **kwargs):
    # type: (Callable, Any, Any) -> str
    """Decorate a `__repr__` or a `__str__` method and prevents infinite recursion."""
    self_id = id(args[0])
    try:
        reprs = _local.reprs
    except AttributeError:
        reprs = _local.reprs = set()
    if self_id in reprs:
        return "(...)"
    else:
        reprs.add(self_id)
        try:
            return func(*args, **kwargs)
        finally:
            reprs.remove(self_id)
