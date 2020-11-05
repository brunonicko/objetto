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
    """
    Check and format types by adding a module path.

    .. code:: python

        >>> from objetto.utils.type_checking import format_types

        >>> format_types((int, "chain"), module="itertools")
        (<class 'int'>, 'itertools|chain')
        >>> format_types(float)
        (<class 'float'>,)
        >>> format_types("itertools|chain")
        ('itertools|chain',)

    :param types: Types.
    :param module: Module to prefix lazy paths without one.
    :return: Formatted types.
    :raises ValueError: Invalid type path/no module provided.
    :raises TypeError: Did not provide valid types.
    """
    if isinstance(types, type):
        return (types,)
    elif isinstance(types, string_types):
        return (decorate_path(types, module=module),)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(format_types(t, module=module) for t in types))
    else:
        error = "'{}' object is not a valid type".format(
            type(types).__name__,
        )
        raise TypeError(error)


def get_type_names(types):
    # type: (LazyTypes) -> Tuple[str, ...]
    """
    Get type names without importing lazy paths.

    .. code:: python

        >>> from objetto.utils.type_checking import get_type_names

        >>> get_type_names((int, "itertools|chain"))
        ('int', 'chain')

    :param types: Types.
    :return: Type names.
    """
    return tuple(
        t.split("|")[-1].split(".")[-1]
        if isinstance(t, string_types) else t.__name__
        for t in flatten_types(types)
    )


def flatten_types(types):
    # type: (LazyTypes) -> Tuple[_LazyType, ...]
    """
    Flatten types into a tuple.

    .. code:: python

        >>> from objetto.utils.type_checking import flatten_types

        >>> flatten_types((int, ("itertools|chain", float, (str,))))
        (<class 'int'>, 'itertools|chain', <class 'float'>, <class 'str'>)
        >>> flatten_types(int)
        (<class 'int'>,)

    :param types: Types.
    :return: Flattened types.
    :raises TypeError: Invalid types.
    """
    if isinstance(types, (string_types, type)):
        return (types,)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(flatten_types(t) for t in types))
    else:
        raise TypeError(type(types).__name__)


def import_types(types):
    # type: (LazyTypes) -> Tuple[Type, ...]
    """
    Import types from lazy import paths.

    .. code:: python

        >>> from objetto.utils.type_checking import import_types

        >>> import_types("itertools|chain")
        (<class 'itertools.chain'>,)
        >>> import_types(("itertools|chain", "itertools|compress"))
        (<class 'itertools.chain'>, <class 'itertools.compress'>)
        >>> import_types(("itertools|chain", int))
        (<class 'itertools.chain'>, <class 'int'>)

    :param types: Types.
    :return: Imported types.
    """
    return tuple(
        cast(type, import_path(t)) if isinstance(t, string_types) else t
        for t in flatten_types(types)
    )


def is_instance(obj, types, subtypes=True):
    # type: (Any, LazyTypes, bool) -> bool
    """
    Get whether object is an instance of any of the provided types.

    .. code:: python

        >>> from itertools import chain
        >>> from objetto.utils.type_checking import is_instance

        >>> class SubChain(chain):
        ...     pass
        ...
        >>> is_instance(3, int)
        True
        >>> is_instance(3, (chain, int))
        True
        >>> is_instance(3, ())
        False
        >>> is_instance(SubChain(), "itertools|chain")
        True
        >>> is_instance(chain(), "itertools|chain", subtypes=False)
        True
        >>> is_instance(SubChain(), "itertools|chain", subtypes=False)
        False

    :param obj: Object.
    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :return: True if it is an instance.
    """
    imported_types = import_types(types)
    if subtypes:
        return isinstance(obj, imported_types)
    else:
        return type(obj) in imported_types


def is_subclass(cls, types, subtypes=True):
    # type: (type, LazyTypes, bool) -> bool
    """
    Get whether class is a subclass of any of the provided types.

    .. code:: python

        >>> from itertools import chain
        >>> from objetto.utils.type_checking import is_subclass

        >>> class SubChain(chain):
        ...     pass
        ...
        >>> is_subclass(int, int)
        True
        >>> is_subclass(int, (chain, int))
        True
        >>> is_subclass(int, ())
        False
        >>> is_subclass(SubChain, "itertools|chain")
        True
        >>> is_subclass(chain, "itertools|chain", subtypes=False)
        True
        >>> is_subclass(SubChain, "itertools|chain", subtypes=False)
        False

    :param cls: Class.
    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :return: True if it is a subclass.
    :raises TypeError: Did not provide a class.
    """
    if not isinstance(cls, type):
        error = "is_subclass() arg 1 must be a class"
        raise TypeError(error)
    imported_types = import_types(types)
    if subtypes:
        return issubclass(cls, import_types(types))
    else:
        return cls in imported_types


def assert_is_instance(obj, types, subtypes=True):
    # type: (Any, LazyTypes, bool) -> None
    """
    Assert object is an instance of any of the provided types.

    .. code:: python

        >>> from itertools import chain
        >>> from objetto.utils.type_checking import assert_is_instance

        >>> class SubChain(chain):
        ...     pass
        ...
        >>> assert_is_instance(3, int)
        >>> assert_is_instance(3, (chain, int))
        >>> assert_is_instance(3, ())
        Traceback (most recent call last):
        ValueError: no types were provided to perform assertion
        >>> assert_is_instance(3, "itertools|chain")
        Traceback (most recent call last):
        TypeError: got 'int' object, expected instance of 'chain' or any of its \
subclasses
        >>> assert_is_instance(chain(), "itertools|chain", subtypes=False)
        >>> assert_is_instance(SubChain(), "itertools|chain", subtypes=False)
        Traceback (most recent call last):
        TypeError: got 'SubChain' object, expected instance of 'chain' (instances of \
subclasses are not accepted)

    :param obj: Object.
    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :raises ValueError: No types were provided.
    :raises TypeError: Object is not an instance of provided types.
    """
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


def assert_is_subclass(cls, types, subtypes=True):
    # type: (type, LazyTypes, bool) -> None
    """
    Assert a class is a subclass of any of the provided types.

    .. code:: python

        >>> from itertools import chain
        >>> from objetto.utils.type_checking import assert_is_subclass

        >>> class SubChain(chain):
        ...     pass
        ...
        >>> assert_is_subclass(int, int)
        >>> assert_is_subclass(int, (chain, int))
        >>> assert_is_subclass(int, ())
        Traceback (most recent call last):
        ValueError: no types were provided to perform assertion
        >>> assert_is_subclass(int, "itertools|chain")
        Traceback (most recent call last):
        TypeError: got 'int', expected class 'chain' or any of its subclasses
        >>> assert_is_subclass(chain, "itertools|chain", subtypes=False)
        >>> assert_is_subclass(SubChain, "itertools|chain", subtypes=False)
        Traceback (most recent call last):
        TypeError: got 'SubChain', expected class 'chain' (subclasses are not accepted)

    :param cls: Class.
    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :raises ValueError: No types were provided.
    :raises TypeError: Class is not a subclass of provided types.
    """
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
    """
    Assert a value is callable.

    .. code:: python

        >>> from objetto.utils.type_checking import assert_is_subclass

        >>> assert_is_callable(int)
        >>> assert_is_callable(lambda: None)
        >>> assert_is_callable(3)
        Traceback (most recent call last):
        TypeError: got non-callable 'int' object, expected a callable

    :param value: Value.
    :raises TypeError: Value is not a match.
    """
    if not callable(value):
        error = "got non-callable '{}' object, expected a callable".format(
            type(value).__name__,
        )
        raise TypeError(error)
