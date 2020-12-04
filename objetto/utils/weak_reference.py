# -*- coding: utf-8 -*-
"""Weak reference type."""

from typing import TYPE_CHECKING, Generic, TypeVar
from weakref import ref as _ref

from .recursive_repr import recursive_repr

if TYPE_CHECKING:
    from typing import Any, Optional, Tuple, Type

__all__ = ["WeakReference"]


T = TypeVar("T")  # Any type.


class WeakReference(Generic[T], object):
    """
    Weak reference object that supports pickling.

    Inherits from:
      - :class:`typing.Generic`

    .. code:: python

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

    :param obj: Object to reference.
    :type obj: object
    """

    __slots__ = ("__weakref__", "__ref")

    def __init__(self, obj=None):
        # type: (T) -> None
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
        :rtype: int
        """
        return hash(self.__ref)

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Other.

        :return: True if equal.
        :rtype: bool or NotImplemented
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
        :rtype: bool or NotImplemented
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
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
        :rtype: str
        """
        return self.__repr__()

    def __call__(self):
        # type: () -> Optional[T]
        """
        Get strong reference to the object or None if no longer alive.

        :return: Strong reference or `None`.
        :rtype: object or None
        """
        return self.__ref()

    def __reduce__(self):
        # type: () -> Tuple[Type[WeakReference], Tuple[Optional[T]]]
        """
        Reduce for pickling.

        :return: Class and strong reference to object.
        :rtype: tuple[type[objetto.utils.weak_reference.WeakReference], tuple[object]]
        """
        return type(self), (self(),)
