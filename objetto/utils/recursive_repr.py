# -*- coding: utf-8 -*-
"""Recursive-ready `repr` decorator."""

from collections import Counter as ValueCounter
from threading import local
from typing import TYPE_CHECKING

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from decorator import decorator
from qualname import qualname  # type: ignore

if TYPE_CHECKING:
    from typing import Any, Callable, Optional

__all__ = ["recursive_repr"]

_local = local()


@decorator
def recursive_repr(
    func,  # type: Callable
    max_depth=1,  # type: Optional[int]
    max_global_depth=2,  # type: Optional[int]
    *args,  # type: Any
    **kwargs  # type: Any
):
    # type: (...) -> str
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

    :param max_depth: Maximum recursion depth before returning fill value.
    :type max_depth: int

    :param max_global_depth: Maximum global depth before returning fill value.
    :type max_global_depth: int

    :return: Decorated method function.
    :rtype: function
    """
    self = args[0]
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
