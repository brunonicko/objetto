# -*- coding: utf-8 -*-
"""Recursive-ready `repr` decorator."""

from collections import Counter as ValueCounter
from functools import wraps
from threading import local
from typing import TYPE_CHECKING

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import raise_from

from .qualname import qualname
from .simplify_exceptions import simplify_exceptions

if TYPE_CHECKING:
    from typing import Callable, Optional, TypeVar

    RT = TypeVar("RT")  # return type

__all__ = ["recursive_repr"]

_local = local()


def recursive_repr(func):
    # type: (Callable[..., RT]) -> Callable[..., RT]
    """
    Decorate a representation method/function and prevents infinite recursion.

    .. code:: python

        >>> from objetto.utils.recursive_repr import recursive_repr

        >>> class MyClass(object):
        ...
        ...     @recursive_repr
        ...     def __repr__(self):
        ...         return "MyClass<" + repr(self) + ">"
        ...
        >>> my_obj = MyClass()
        >>> repr(my_obj)
        'MyClass<...>'

    :param func: The '__repr__' and/or '__str__' method/function.
    :type func: function

    :return: Decorated method function.
    :rtype: function
    """
    max_depth = 1  # type: Optional[int]
    max_global_depth = 2  # type: Optional[int]

    @wraps(func)
    @simplify_exceptions
    def decorated(*args, **kwargs):
        try:
            self = args[0]
        except IndexError:
            exc = RuntimeError("'recursive_repr' needs to be used on a instance method")
            raise_from(exc, None)
            raise exc

        self_id = id(self)
        try:
            reprs = _local.reprs
        except AttributeError:
            reprs = _local.reprs = ValueCounter()
        try:
            global_reprs = _local.global_reprs
        except AttributeError:
            global_reprs = _local.global_reprs = [0]

        reprs[self_id] += 1
        global_reprs[0] += 1
        try:
            if max_depth is not None and reprs[self_id] > max_depth:
                return "..."
            elif max_global_depth is not None and global_reprs[0] > max_global_depth:
                try:
                    qual_name = qualname(type(self))
                except AttributeError:
                    qual_name = type(self).__name__
                return "<{} at {}>".format(qual_name, hex(id(self)))
            else:
                return func(*args, **kwargs)
        finally:
            reprs[self_id] -= 1
            if not reprs[self_id]:
                del reprs[self_id]
            if not reprs:
                del _local.reprs
            global_reprs[0] -= 1
            if not global_reprs[0]:
                del _local.global_reprs

    return decorated
