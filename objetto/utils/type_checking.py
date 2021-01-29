# -*- coding: utf-8 -*-
"""Runtime type checking with support for lazy import paths."""

from itertools import chain
from typing import TYPE_CHECKING, cast

from jinja2 import StrictUndefined, Undefined  # type: ignore
from jinja2.nativetypes import NativeEnvironment  # type: ignore

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import string_types

from ..utils.lazy_import import decorate_path, import_path

if TYPE_CHECKING:
    from typing import Any, Iterable, Mapping, Optional, Tuple, Type, Union

    _LazyType = Union[Type, str]
    LazyTypes = Union[Optional[_LazyType], Iterable[Optional[_LazyType]]]
    LazyTypesTuple = Tuple[_LazyType, ...]
else:
    LazyTypes = None
    LazyTypesTuple = None

__all__ = [
    "LazyTypes",
    "LazyTypesTuple",
    "format_types",
    "get_type_names",
    "flatten_types",
    "expand_types",
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

        >>> from objetto.utils.type_checking import format_types, get_type_names

        >>> get_type_names(format_types((int, "chain"), module="itertools"))
        ('int', 'chain')
        >>> get_type_names(format_types(float))
        ('float',)
        >>> get_type_names(format_types("itertools|chain"))
        ('chain',)

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param module: Module to prefix lazy paths without one.
    :type module: str or None

    :return: Formatted types.
    :rtype: tuple[str or type or None]

    :raises ValueError: Invalid type path/no module provided.
    :raises TypeError: Did not provide valid types.
    """
    if types is None:
        return (type(None),)
    if isinstance(types, type):
        return (types,)

    # Lazy path.
    elif isinstance(types, string_types):
        if "{" in types or "}" in types:
            return (types,)
        else:
            return (decorate_path(types, module=module),)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(format_types(t, module=module) for t in types))
    else:
        error = "'{}' instance is not a valid type".format(type(types).__name__)
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
    :type types: str or type or None or tuple[str or type or None]

    :return: Type names.
    :rtype: tuple[str]
    """
    return tuple(
        t.split("|")[-1].split(".")[-1]
        if isinstance(t, string_types)
        else (t.__name__ if isinstance(t, type) else type(t).__name__)
        for t in flatten_types(types)
    )


def flatten_types(types):
    # type: (LazyTypes) -> Tuple[_LazyType, ...]
    """
    Flatten types into a tuple.

    .. code:: python

        >>> from objetto.utils.type_checking import flatten_types, get_type_names

        >>> get_type_names(flatten_types((int, ("itertools|chain", float, (str,)))))
        ('int', 'chain', 'float', 'str')
        >>> get_type_names(flatten_types(int))
        ('int',)

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :return: Flattened types.
    :rtype: tuple[str or type]

    :raises TypeError: Invalid types.
    """
    if types is None:
        return (type(None),)
    elif isinstance(types, (string_types, type)):
        return (types,)
    elif isinstance(types, collections_abc.Iterable):
        return tuple(chain.from_iterable(flatten_types(t) for t in types))
    else:
        raise TypeError(type(types).__name__)


def expand_types(types, environment=None):
    # type: (LazyTypes, Optional[Mapping[str, Any]]) -> LazyTypesTuple
    """
    Unpack variables in lazy import paths based on given environment using jinja.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :return: Flattened types.
    :rtype: tuple[str or type]
    """
    if environment is None:
        return flatten_types(types)

    jinja_environment = NativeEnvironment(undefined=StrictUndefined)
    expanded_types = []
    for typ in flatten_types(types):

        # Only lazy types can be expanded.
        if isinstance(typ, string_types):

            # Make jinja template.
            template = jinja_environment.from_string(typ)

            # Render template using provided environment.
            expanded_type = template.render(environment)
            if expanded_type is Undefined:
                raise ValueError(
                    "could not unpack variables in lazy import path '{}'".format(typ)
                )

            expanded_types.append(expanded_type)

        # Not lazy, do not expand.
        else:
            expanded_types.append(typ)

    return tuple(expanded_types)


def import_types(types, environment=None):
    # type: (LazyTypes, Optional[Mapping[str, Any]]) -> Tuple[Type, ...]
    """
    Import types from lazy import paths.

    .. code:: python

        >>> from objetto.utils.type_checking import import_types, get_type_names

        >>> get_type_names(import_types("itertools|chain"))
        ('chain',)
        >>> get_type_names(import_types(("itertools|chain", "itertools|compress")))
        ('chain', 'compress')
        >>> get_type_names(import_types(("itertools|chain", int)))
        ('chain', 'int')

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :return: Imported types.
    :rtype: tuple[type]
    """
    return tuple(
        cast(type, import_path(t)) if isinstance(t, string_types) else t
        for t in expand_types(types, environment=environment)
    )


def is_instance(obj, types, subtypes=True, environment=None):
    # type: (Any, LazyTypes, bool, Optional[Mapping[str, Any]]) -> bool
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
    :type obj: object

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :return: True if it is an instance.
    :rtype: bool
    """
    imported_types = import_types(types, environment=environment)
    if subtypes:
        return isinstance(obj, imported_types)
    else:
        return type(obj) in imported_types


def is_subclass(cls, types, subtypes=True, environment=None):
    # type: (type, LazyTypes, bool, Optional[Mapping[str, Any]]) -> bool
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
    :type cls: type

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :return: True if it is a subclass.
    :rtype: bool

    :raises TypeError: Did not provide a class.
    """
    if not isinstance(cls, type):
        error = "is_subclass() arg 1 must be a class"
        raise TypeError(error)
    imported_types = import_types(types, environment=environment)
    if subtypes:
        return issubclass(cls, imported_types)
    else:
        return cls in imported_types


def assert_is_instance(obj, types, subtypes=True, environment=None):
    # type: (Any, LazyTypes, bool, Optional[Mapping[str, Any]]) -> None
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
    :type obj: object

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :raises ValueError: No types were provided.
    :raises TypeError: Object is not an instance of provided types.
    """
    if not is_instance(obj, types, subtypes=subtypes, environment=environment):
        types = expand_types(types, environment=environment)
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


def assert_is_subclass(cls, types, subtypes=True, environment=None):
    # type: (type, LazyTypes, bool, Optional[Mapping[str, Any]]) -> None
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
    :type cls: type

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param environment: Map between variable names and their values.
    :type environment: collections.abc.Mapping[str, Any]

    :raises ValueError: No types were provided.
    :raises TypeError: Class is not a subclass of provided types.
    """
    if not isinstance(cls, type):
        types = expand_types(types, environment=environment)
        error = "got instance of '{}', expected {}{}{}".format(
            type(cls).__name__,
            "one of " if len(types) > 1 else "class ",
            ", ".join("'{}'".format(name) for name in get_type_names(types)),
            " or any of {} subclasses".format("their" if len(types) > 1 else "its")
            if subtypes
            else " (subclasses are not accepted)",
        )
        raise TypeError(error)

    if not is_subclass(cls, types, subtypes=subtypes, environment=environment):
        types = expand_types(types, environment=environment)
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
