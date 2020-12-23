# -*- coding: utf-8 -*-
"""Generate importable lazy paths and import from them."""

from re import match as re_match
from typing import TYPE_CHECKING

from qualname import qualname  # type: ignore

if TYPE_CHECKING:
    from typing import Any, Optional

__all__ = [
    "PRE_IMPORT_PATH_VALIDATION_REGEX",
    "PARTIAL_IMPORT_PATH_REGEX",
    "RELATIVE_IMPORT_PATH_REGEX",
    "IMPORT_PATH_REGEX",
    "import_path",
    "get_path",
    "decorate_path",
]


PRE_IMPORT_PATH_VALIDATION_REGEX = r"^[\w\-\|\.]+$"
"""Pre import path regex validation regex."""

PARTIAL_IMPORT_PATH_REGEX = r"^((?:\w+\.{0,1})+)$"
"""Partial lazy import path regex."""

RELATIVE_IMPORT_PATH_REGEX = (
    r"^((?:(?:\.+)|(?:\.*)(?:\w+\.{0,1})+))\|((?:\w+\.{0,1})+)$"
)
"""Relative lazy import path regex."""

IMPORT_PATH_REGEX = r"^((?:\w+\.{0,1})+)\|((?:\w+\.{0,1})+)$"
"""Full lazy import path regex."""


def import_path(path):
    # type: (str) -> Any
    """
    Import object from a full import path.

    .. code:: python

        >>> from objetto.utils.lazy_import import import_path

        >>> import_path("abc|abstractmethod")
        <function abstractmethod at ...>

    :param path: Import path.
    :type path: str

    :return: Imported object.

    :raises ValueError: Invalid or empty path.
    :raises AttributeError: No object with the provided name.
    """
    if "|" not in path:
        if not path:
            error = "can't import from empty path"
        else:
            error = (
                "import path '{}' does not specify a module name (missing '|' "
                "separator between module path and qualified name)"
            ).format(path)
        raise ValueError(error)
    elif path.startswith("."):
        error = "import path '{}' is not absolute".format(path)
        raise ValueError(error)

    match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, path) and re_match(
        IMPORT_PATH_REGEX, path
    )
    if not match:
        error = "invalid import path '{}'".format(path)
        raise ValueError(error)

    module, qual_name = match.groups()
    name_parts = qual_name.split(".")
    module_obj = __import__(module, fromlist=[name_parts[0]])

    obj = module_obj
    for name_part in name_parts:
        obj = getattr(obj, name_part)

    return obj


def get_path(obj):
    # type: (Any) -> str
    """
    Get full import path to an object.

    .. code:: python

        >>> from abc import abstractmethod
        >>> from objetto.utils.lazy_import import get_path

        >>> get_path(abstractmethod)
        'abc|abstractmethod'

    :param obj: Object.

    :return: Import path.
    :rtype: str

    :raises ValueError: Can't determine consistent import path.
    """

    module = obj.__module__
    if not module:
        error = "can't get module for {}".format(obj)
        raise ValueError(error)

    try:
        qual_name = qualname(obj)
        if not qual_name:
            raise AttributeError()
    except AttributeError:
        qual_name = obj.__name__

    if not qual_name:
        error = "can't get name for {}".format(obj)
        raise ValueError(error)

    path = "|".join((module, qual_name))

    try:
        imported_obj = import_path(path)
    except (ValueError, ImportError):
        imported_obj = None

    if imported_obj is not obj:
        error = "can't get consistent import path to {}".format(obj)
        raise ValueError(error)

    return path


def decorate_path(path, module=None):
    # type: (str, Optional[str]) -> str
    """
    Validate and decorate partial/relative import path with module if applicable.

    .. code:: python

        >>> from objetto.utils.lazy_import import decorate_path

        >>> decorate_path("abstractmethod", module="abc")
        'abc|abstractmethod'

    :param path: Import path (partial or full)
    :type path: str

    :param module: Optional module path.
    :type module: str or None

    :return: Full import path.
    :rtype: str

    :raises ValueError: Invalid path or no module provided.
    """
    if not path:
        error = "can't decorate empty path"
        raise ValueError(error)

    # Partial path, need to add module.
    if "|" not in path:
        path_match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, path) and re_match(
            PARTIAL_IMPORT_PATH_REGEX, path
        )
        if not path_match:
            error = "invalid partial import path '{}'".format(path)
            raise ValueError(error)

        if not module:
            error = (
                "can't add module to partial path '{}' since it was not provided"
            ).format(path)
            raise ValueError(error)

        module_match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, module) and re_match(
            PARTIAL_IMPORT_PATH_REGEX, module
        )
        if not module_match:
            error = "invalid module path '{}'".format(module)
            raise ValueError(error)

        return module + "|" + path

    # Relative path, need to resolve module and decorate it.
    elif path.startswith("."):
        path_match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, path) and re_match(
            RELATIVE_IMPORT_PATH_REGEX, path
        )
        if not path_match:
            error = "invalid relative import path '{}'".format(path)
            raise ValueError(error)

        if not module:
            error = (
                "can't resolve module to relative path '{}' since it was not provided"
            ).format(path)
            raise ValueError(error)

        module_match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, module) and re_match(
            PARTIAL_IMPORT_PATH_REGEX, module
        )
        if not module_match:
            error = "invalid module path '{}'".format(module)
            raise ValueError(error)

        path = path[1:]
        if path.startswith("|"):
            return module + path
        elif not path.startswith("."):
            path_parts = path.split("|")
            return module + "." + path_parts[0] + "|" + path_parts[1]
        else:
            while path.startswith("."):
                module_parts = module.split(".")
                if len(module_parts) < 2:
                    error = "can't get parent module for '{}'".format(module)
                    raise ValueError(error)
                module, path = ".".join(module_parts[:-1]), path[1:]
            if "|" in path and not path.startswith("|"):
                module, path = (
                    module + "." + path.split("|")[0],
                    "|" + path.split("|")[1],
                )

        return module + path

    # Full path, no need to decorate it with module.
    else:
        match = re_match(PRE_IMPORT_PATH_VALIDATION_REGEX, path) and re_match(
            IMPORT_PATH_REGEX, path
        )
        if not match:
            error = "invalid import path '{}'".format(path)
            raise ValueError(error)

        return path
