# -*- coding: utf-8 -*-
"""Weak reference type."""

from typing import TYPE_CHECKING, Generic, TypeVar
from weakref import ref as _ref

if TYPE_CHECKING:
    from typing import Any, Tuple, Type

_T = TypeVar("_T")


__all__ = ["WeakReference"]


class WeakReference(Generic[_T], object):
    """
    Weak reference object that supports pickling.

    .. code:: python

        >>> from pickle import dumps, loads
        >>> from objetto.utils.weak_reference import WeakReference

        >>> class MyClass(object):
        ...     pass
        ...
        >>> strong = MyClass()
        >>> weak = WeakReference(strong)
        >>> weak() is strong
        True
        >>> del strong
        >>> weak() is None
        True
        >>> type(loads(dumps(weak))) is MyClass
        True

    :param obj: Object to reference.
    """

    __slots__ = ("__weakref__", "__ref")

    def __init__(self, obj=None):
        # type: (_T) -> None
        if obj is None:
            self.__ref = _ref(
                type("Dead", (object,), {"__slots__": ("__weakref__",)})()
            )
        else:
            self.__ref = _ref(obj)

    def __hash__(self):
        """
        Get hash.

        :return: Hash.
        """
        return hash(self.__ref)

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Other.
        :return: True if equal.
        """
        if self is other:
            return True
        if not isinstance(other, WeakReference):
            return False
        return self.__ref == other.__ref

    def __ne__(self, other):
        # type: (Any) -> bool
        """
        Compare for inequality.

        :param other: Other.
        :return: True if not equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        obj = self()
        return "<{} object at {}; {}>".format(
            type(self).__name__,
            hex(id(self)),
            "dead"
            if obj is None
            else "to '{}' at {}".format(
                type(obj).__name__,
                hex(id(obj)),
            ),
        )

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    def __call__(self):
        # type: () -> _T
        """
        Get strong reference to the object or None if no longer alive.

        :return: Strong reference or None.
        """
        return self.__ref()

    def __reduce__(self):
        # type: () -> Tuple[Type[WeakReference], _T]
        """
        Reduce for pickling.

        :return: Class and strong reference to object.
        """
        return type(self), (self(),)
