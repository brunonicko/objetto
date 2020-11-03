# -*- coding: utf-8 -*-
"""Runtime type checking with support for lazy import paths."""

from itertools import chain
from typing import TYPE_CHECKING, cast

from six import string_types
from six.moves import collections_abc

from ..utils.lazy_import import decorate_path, import_path

if TYPE_CHECKING:
    from typing import Any, Iterable, Optional, Tuple, Type, Union

    _LazyType = Union[Type, str]
    _FlattenedLazyTypes = Tuple[_LazyType, ...]
    LazyTypes = Union[_LazyType, Iterable[_LazyType]]
    LazyTypesTuple = Tuple[_LazyType, ...]
else:
    _LazyType = None
    _FlattenedLazyTypes = None
    LazyTypes = None
    LazyTypesTuple = None

__all__ = [
    "LazyTypes",
    "LazyTypesTuple",
    "format_types",
    "get_type_names",
    "flatten_types",
    "import_types",
    "is_instance",
    "is_subclass",
    "assert_is_instance",
    "assert_is_subclass",
    "assert_is_callable",
]


def format_types(types, module=None):
    # type: (LazyTypes, Optional[str]) -> LazyTypesTuple
    """Check and format types by adding a module path if applicable."""
    if isinstance(types, type):
        return (types,)
    elif isinstance(types, string_types):
        return (decorate_path(types, module=module),)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(format_types(t, module=module) for t in types))
    else:
        raise TypeError(type(types).__name__)


def get_type_names(types):
    # type: (LazyTypes) -> Tuple[str, ...]
    """Get type names without importing lazy paths."""
    return tuple(
        t.split("|")[-1].split(".")[-1]
        if isinstance(t, string_types) else t.__name__
        for t in flatten_types(types)
    )


def flatten_types(types):
    # type: (LazyTypes) -> Tuple[_LazyType, ...]
    """Flatten types into a tuple."""
    if isinstance(types, (string_types, type)):
        return (types,)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(flatten_types(t) for t in types))
    else:
        raise TypeError(type(types).__name__)


def import_types(types):
    # type: (LazyTypes) -> Tuple[Type, ...]
    """Import types from lazy import paths."""
    return tuple(
        cast(type, import_path(t)) if isinstance(t, string_types) else t
        for t in flatten_types(types)
    )


def is_instance(obj, types, subtypes=True):
    # type: (Any, LazyTypes, bool) -> bool
    """Get whether object is an instance of any of the provided types."""
    imported_types = import_types(types)
    if subtypes:
        return isinstance(obj, imported_types)
    else:
        return type(obj) in imported_types


def is_subclass(cls, types, subtypes=False):
    # type: (type, LazyTypes, bool) -> bool
    """Get whether class is a subclass of any of the provided types."""
    if not isinstance(cls, type):
        error = "is_subclass() arg 1 must be a class"
        raise TypeError(error)
    imported_types = import_types(types)
    if subtypes:
        return issubclass(cls, import_types(types))
    else:
        return cls in imported_types


def assert_is_instance(obj, types, subtypes=False):
    # type: (Any, LazyTypes, bool) -> None
    """Assert object is an instance of any of the provided types."""
    if not is_instance(obj, types, subtypes=subtypes):
        types = flatten_types(types)
        if not types:
            error = "no types were provided to perform assertion"
            raise ValueError(error)
        error = "got '{}' object, expected instance of {}{}".format(
            type(obj).__name__,
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if subtypes
            else " (instances of subclasses are not accepted)",
        )
        raise TypeError(error)


def assert_is_subclass(cls, types, subtypes=False):
    # type: (type, LazyTypes, bool) -> None
    """Assert a class is a subclass of any of the provided types."""
    if not is_subclass(cls, types, subtypes=subtypes):
        types = flatten_types(types)
        if not types:
            error = "no types were provided to perform assertion"
            raise ValueError(error)

        error = "got '{}', expected {}{}{}".format(
            cls.__name__,
            "one of " if len(types) > 1 else "class ",
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if subtypes
            else " (subclasses are not accepted)",
        )
        raise TypeError(error)


def assert_is_callable(value):
    # type: (Any) -> None
    """Assert a value is callable."""
    if not callable(value):
        error = "got non-callable '{}' object, expected a callable".format(
            type(value).__name__,
        )
        raise TypeError(error)
