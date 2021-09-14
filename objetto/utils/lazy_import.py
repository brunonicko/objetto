# -*- coding: utf-8 -*-
"""Generate importable lazy paths and import from them."""

from re import compile as re_compile
from typing import TYPE_CHECKING

from qualname import qualname  # type: ignore

if TYPE_CHECKING:
    from typing import Any, Optional

__all__ = [
    "MODULE_SEPARATOR",
    "IMPORT_PATH_REGEX",
    "format_import_path",
    "lazy_import",
    "get_import_path",
]


MODULE_SEPARATOR = "|"
IMPORT_PATH_REGEX = re_compile(r"^(\w+[\w.]*)\|([\w.]+)$")


def format_import_path(import_path, default_module=None):
    # type: (str, Optional[str]) -> str
    """
    Validate a lazy path, add a module path if missing one, and resolve relative paths.

    :param import_path: Lazy import path.
    :param default_module: Module path.

    :return: Formatted/validated lazy import path.
    """

    # Validate import path.
    if MODULE_SEPARATOR not in import_path:
        if not import_path:
            error = "can't import from empty path"
            raise ValueError(error)
        elif default_module is not None:
            import_path = MODULE_SEPARATOR.join((default_module, import_path))
        else:
            error = (
                "import path {} does not specify a module name (missing {} "
                "separator between module path and qualified name)"
            ).format(repr(import_path), repr(MODULE_SEPARATOR))
            raise ValueError(error)

    # Match against regex and separate module from qual name.
    match = IMPORT_PATH_REGEX.match(import_path)
    if not match:
        error = "invalid import path {}".format(repr(import_path))
        raise ValueError(error)
    module, qual_name = match.groups()

    # Resolve relative paths.
    if qual_name.startswith("."):
        qual_name = qual_name[1:]
        while qual_name.startswith("."):
            qual_name = qual_name[1:]
            if "." not in module:
                error = (
                    "relative path error; can't parse parent module for {}"
                ).format(repr(module))
                raise ValueError(error)
            module = ".".join(module.split(".")[:-1])

    return MODULE_SEPARATOR.join((module, qual_name))


def lazy_import(import_path, default_module=None):
    # type: (str, Optional[str]) -> Any
    """
    Import from lazy path.

    :param import_path: Lazy import path.
    :param default_module: Module path.

    :return: Class, function, method.
    """

    # Format import path.
    import_path = format_import_path(import_path, default_module=default_module)

    # Split module and qual name.
    module, qual_name = import_path.split(MODULE_SEPARATOR)

    # Import and get object from module.
    name_parts = qual_name.split(".")
    module_obj = __import__(module, fromlist=[name_parts[0]])
    obj = module_obj
    for name_part in name_parts:
        obj = getattr(obj, name_part)

    return obj


def get_import_path(obj):
    # type: (Any) -> str
    """
    Get importable lazy path for object.

    :param obj: Class, function, method.

    :return: Lazy import path.
    """

    # Get module.
    module = obj.__module__
    if not module:
        error = "can't get module for {}".format(obj)
        raise ValueError(error)

    # Get qual name.
    try:
        qual_name = qualname(obj)
        if not qual_name:
            raise AttributeError()
    except AttributeError:
        qual_name = obj.__name__
    if not qual_name:
        error = "can't get valid name for {}".format(obj)
        raise ValueError(error)

    # Join and verify import path.
    import_path = MODULE_SEPARATOR.join((module, qual_name))
    try:
        imported_obj = lazy_import(import_path)
    except (ValueError, ImportError, AttributeError):
        imported_obj = None
    if imported_obj is not obj:
        error = "could not get consistent import path to {}".format(obj)
        raise ValueError(error)

    return import_path
