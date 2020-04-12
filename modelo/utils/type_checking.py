# -*- coding: utf-8 -*-
"""Type checking utilities."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from os import environ
from itertools import chain
from six import string_types
from typing import Any, Union, Type, Iterable, Tuple, Optional

PACKAGE_LOADER_DOT_PATH_ENV_VAR = "DOT_PATH_PACKAGE_LOADER"
_PACKAGE_LOADER_DOT_PATH = environ.get(PACKAGE_LOADER_DOT_PATH_ENV_VAR)
_MISSING = object()
_PACKAGE_LOADER = _MISSING

UnresolvedType = Union[str, Type]


def resolve_dot_path(dot_path, default_module_name=None):
    # type: (str, Optional[str]) -> Any
    """Import from dot path."""
    global _PACKAGE_LOADER

    if "." not in dot_path:
        if default_module_name is not None:
            dot_path = "{}.{}".format(default_module_name, dot_path)
        raise ValueError(
            "dot path '{}' does not contain a dot and no default module name was "
            "provided".format(dot_path)
        )

    parts = dot_path.split(".")
    package_name = parts[0]
    module_name = ".".join(parts[:-1])
    obj_name = parts[-1]

    import_args = module_name, globals(), locals()
    import_kwargs = dict(fromlist=[obj_name], level=-1)

    try:
        module = __import__(*import_args, **import_kwargs)
    except ImportError:
        if _PACKAGE_LOADER_DOT_PATH is None or _PACKAGE_LOADER is None:
            raise
        if _PACKAGE_LOADER is _MISSING:
            _PACKAGE_LOADER = None
            _PACKAGE_LOADER = resolve_dot_path(_PACKAGE_LOADER_DOT_PATH)
        _PACKAGE_LOADER(package_name)
        module = __import__(*import_args, **import_kwargs)

    try:
        obj = getattr(module, obj_name)
    except AttributeError:
        raise AttributeError(
            "obj named '{}' not found in module '{}'".format(obj_name, module_name)
        )
    return obj


def resolve_types(
    unresolved_types,  # type: Union[UnresolvedType, Iterable[UnresolvedType, ...]]
    default_module_name=None,  # type: Optional[str]
):
    # type: (...) -> Tuple[Type, ...]
    """Resolve types from 'types' parameter."""

    # It's the type itself, return it in a tuple
    if isinstance(unresolved_types, type):
        return (unresolved_types,)

    # It's a string, import from dot path and return it in a tuple
    elif isinstance(unresolved_types, string_types):
        return (
            resolve_dot_path(unresolved_types, default_module_name=default_module_name),
        )

    # It's an iterable, resolve recursively and return a flat tuple
    elif isinstance(unresolved_types, collections_abc.Iterable):
        return tuple(
            chain(
                *(
                    resolve_types(single_type, default_module_name=default_module_name)
                    for single_type in unresolved_types
                )
            )
        )

    raise TypeError(type(unresolved_types))


def is_instance(
    obj,  # type: Any
    types,  # type: Union[UnresolvedType, Iterable[UnresolvedType, ...]]
    optional=False,  # type: bool
    exact=False,  # type: bool
    error=False,  # type: bool
    default_module_name=None,  # type: Optional[str]
):
    # type: (...) -> bool
    """Get whether 'obj' is an instance of any of the provided 'types'."""
    resolved_types = resolve_types(types, default_module_name=default_module_name)
    if not resolved_types:
        return True
    if optional and type(None) not in resolved_types:
        resolved_types += (type(None),)
    if exact:
        result = type(obj) in resolved_types
    else:
        result = isinstance(obj, resolved_types)
    if error and not result:
        if len(resolved_types) == 1:
            message = "expected {}'{}', got '{}'".format(
                "exactly " if exact else "",
                resolved_types[0].__name__,
                type(obj).__name__,
            )
        else:
            message = "expected {}one of '{}', got '{}'".format(
                "exactly " if exact else "",
                ", ".join(r.__name__ for r in resolved_types),
                type(obj).__name__,
            )
        raise TypeError(message)
    return result


def assert_is_instance(
    obj,  # type: Any
    types,  # type: Union[UnresolvedType, Iterable[UnresolvedType, ...]]
    optional=False,  # type: bool
    exact=False,  # type: bool
    default_module_name=None,  # type: Optional[str]
):
    # type: (...) -> None
    """Assert 'obj' is an instance of any of the provided 'types'."""
    is_instance(
        obj,
        types,
        optional=optional,
        exact=exact,
        error=True,
        default_module_name=default_module_name,
    )
