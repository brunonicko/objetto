# -*- coding: utf-8 -*-
"""Weak reference type."""

from typing import TYPE_CHECKING, Generic, TypeVar
from weakref import ref as _ref

if TYPE_CHECKING:
    from typing import Tuple, Type

_T = TypeVar("_T")


__all__ = ["WeakReference"]


class WeakReference(Generic[_T], object):
    """Weak reference object that supports pickling."""

    __slots__ = ("__weakref__", "_ref")

    def __init__(self, obj=None):
        # type: (_T) -> None
        if obj is None:
            self._ref = _ref(type("Dead", (object,), {"__slots__": ("__weakref__",)})())
        else:
            self._ref = _ref(obj)

    def __repr__(self):
        # type: () -> str
        obj = self()
        return "<{} object at {} {}>".format(
            type(self).__name__,
            hex(id(self)),
            "(dead)"
            if obj is None
            else "to {} object at {}".format(
                type(obj).__name__,
                hex(id(obj)),
            ),
        )

    def __call__(self):
        # type: () -> _T
        """Get strong reference to the object."""
        return self._ref()

    def __reduce__(self):
        # type: () -> Tuple[Type[WeakReference], _T]
        return type(self), (self(),)
