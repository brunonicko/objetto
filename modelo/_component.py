# -*- coding: utf-8 -*-
"""Base component (simple composite pattern)."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from abc import abstractmethod
from weakref import ref
from slotted import Slotted


class Component(Slotted):
    """Adds functionality to a composite object."""

    __slots__ = ("__obj_ref", "__internal")

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize with composite object."""
        self.__obj_ref = ref(obj)

    @property
    def obj(self):
        # type: () -> CompositeMixin
        """Composite object."""
        obj = self.__obj_ref()
        if obj is not None:
            return obj
        raise ReferenceError("object is no longer alive")


class CompositeMixin(object):
    """Composite object."""

    __slots__ = ("__weakref__",)

    @abstractmethod
    def __get_component__(self, key):
        # type: (collections_abc.Hashable) -> Component
        """Get component by its unique, hashable key."""
        raise NotImplementedError()
