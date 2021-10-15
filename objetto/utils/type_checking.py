
from itertools import chain
from typing import TYPE_CHECKING, cast

from six import string_types
from six.moves import collections_abc

from .unique_iterator import unique_iterator
from .lazy_import import MODULE_SEPARATOR, format_import_path, lazy_import

if TYPE_CHECKING:
    from typing import Any, Callable, Union, Iterable, Tuple, Type, TypeVar, Optional

    _T = TypeVar("_T")
    _Type = Union[Type[_T], str, None]
    Types = Union[_Type[_T], Iterable[_Type[_T]]]
    TypesTuple = Tuple[_Type[_T], ...]
    ImportedTypesTuple = Tuple[Type[_T], ...]
else:
    Types = None
    TypesTuple = None
    ImportedTypesTuple = None

__all__ = [
    "Types",
    "TypesTuple",
    "ImportedTypesTuple",
    "format_types",
    "get_type_names",
    "import_types",
    "is_instance",
    "is_subclass",
    "assert_is_instance",
    "assert_is_subclass",
]


def format_types(types, default_module=None):
    # type: (Types[_T], Optional[str]) -> TypesTuple[_T]
    if types is None:
        return (cast("Type[_T]", type(None)),)
    elif isinstance(types, type):
        return (cast("Type[_T]", types),)
    elif isinstance(types, string_types):
        return (format_import_path(types, default_module=default_module),)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(
            unique_iterator(
                chain.from_iterable(
                    format_types(t, default_module=default_module) for t in types
                )
            )
        )

    error = (
        "invalid types; expected one or more types or import paths, got instance of {}"
    ).format(repr(type(types).__name__))
    raise TypeError(error)


def get_type_names(types):
    # type: (Types) -> Tuple[str, ...]
    return tuple(
        t.split(MODULE_SEPARATOR)[-1].split(".")[-1] if isinstance(t, string_types)
        else (t.__name__ if isinstance(t, type) else type(t).__name__)
        for t in format_types(types)
    )


def import_types(types):
    # type: (Types[_T]) -> ImportedTypesTuple[_T]
    return tuple(
        lazy_import(t) if isinstance(t, string_types) else t
        for t in format_types(types)
    )


def is_instance(obj, types, accept_subtypes=True):
    # type: (Any, Types, bool) -> bool
    imported_types = import_types(types)
    if accept_subtypes:
        return isinstance(obj, imported_types)
    else:
        return type(obj) in imported_types


def is_subclass(cls, types, accept_subtypes=True):
    # type: (Any, Types, bool) -> bool
    if not isinstance(cls, type):
        error = "is_subclass() arg 1 must be a class"
        raise TypeError(error)
    imported_types = import_types(types)
    if accept_subtypes:
        return issubclass(cls, import_types(types))
    else:
        return cls in imported_types


def assert_is_instance(obj, types, accept_subtypes=True):
    # type: (Any, Types, bool) -> None
    if not is_instance(obj, types, accept_subtypes=accept_subtypes):
        types = format_types(types)
        if not types:
            error = "no types were provided to perform assertion"
            raise TypeError(error)
        error = "got '{}' object; expected instance of {}{}".format(
            type(obj).__name__,
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if accept_subtypes
            else " (instances of subclasses are not accepted)",
        )
        raise TypeError(error)


def assert_is_subclass(cls, types, accept_subtypes=True):
    # type: (Any, Types, bool) -> None
    if not is_instance(cls, type):
        types = format_types(types)
        if not types:
            error = "no types were provided to perform assertion"
            raise TypeError(error)
        error = "got instance of '{}'; expected {}{}{}".format(
            type(cls).__name__,
            "one of " if len(types) > 1 else "class ",
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if accept_subtypes
            else " (subclasses are not accepted)",
        )
        raise TypeError(error)

    if not is_subclass(cls, types, accept_subtypes=accept_subtypes):
        types = format_types(types)
        error = "got '{}'; expected {}{}{}".format(
            cls.__name__,
            "one of " if len(types) > 1 else "class ",
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if accept_subtypes
            else " (subclasses are not accepted)",
        )
        raise TypeError(error)
