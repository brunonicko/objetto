# -*- coding: utf-8 -*-
"""Import and run factory functions/classes."""

from typing import TYPE_CHECKING

from six import string_types

from .lazy_import import decorate_path, import_path

if TYPE_CHECKING:
    from typing import Any, Callable, Iterable, Mapping, Optional, Union

    LazyFactory = Optional[Union[Callable, str]]
else:
    LazyFactory = None

__all__ = [
    "get_factory_name",
    "format_factory",
    "LazyFactory",
    "import_factory",
    "run_factory",
]


def get_factory_name(factory):
    # type: (LazyFactory) -> str
    """
    Get factory name without importing lazy paths.

    .. code:: python

        >>> from objetto.utils.factoring import get_factory_name

        >>> get_factory_name("module.submodule|Class.method")
        'method'
        >>> get_factory_name(int)
        'int'

    :param factory: Factory.
    :type factory: str or function or collections.abc.Callable or None

    :return: Factory name.
    :rtype: str
    """
    if isinstance(factory, string_types):
        return factory.split("|")[-1].split(".")[-1]
    elif factory is None:
        return "None"
    else:
        return factory.__name__


def format_factory(factory, module=None):
    # type: (LazyFactory, Optional[str]) -> LazyFactory
    """
    Check and format factory by adding a module path if applicable.

    .. code:: python

        >>> from objetto.utils.factoring import format_factory

        >>> format_factory("Class.method", module="module.submodule")
        'module.submodule|Class.method'
        >>> format_factory(int, module="module.submodule").__name__
        'int'

    :param factory: Factory.
    :type factory: str or function or collections.abc.Callable or None

    :param module: Module to prefix lazy paths without one.
    :type module: str or None

    :return: Formatted factory.
    :rtype: str or function or collections.abc.Callable or None

    :raises ValueError: Invalid import path to factory.
    :raises TypeError: Did not provide valid factory.
    """
    if factory is None or callable(factory):
        return factory
    elif isinstance(factory, string_types):
        return decorate_path(factory, module=module)
    else:
        raise TypeError(type(factory).__name__)


def import_factory(factory):
    # type: (LazyFactory) -> Optional[Callable]
    """
    Import factory from a path.

    .. code:: python

        >>> from re import match
        >>> from objetto.utils.factoring import import_factory

        >>> import_factory("abc|abstractmethod")
        <function abstractmethod at ...>
        >>> import_factory(None)  # returns None
        >>> import_factory(match)
        <function match at ...>

    :param factory: Lazy factory.
    :type factory: str or function or collections.abc.Callable or None

    :return: Imported factory.
    :rtype: function or collections.abc.Callable or None

    :raises TypeError: Invalid factory.
    """
    if factory is None or callable(factory):
        return factory
    elif isinstance(factory, string_types):
        return import_path(factory)
    else:
        raise TypeError(type(factory).__name__)


def run_factory(
    factory,  # type: LazyFactory
    args=None,  # type: Optional[Iterable[Any]]
    kwargs=None,  # type: Optional[Mapping[str, Any]]
):
    # type: (...) -> Any
    """
    Import and run factory.

    .. code:: python

        >>> from objetto.utils.factoring import run_factory

        >>> bool(run_factory("re|match", (r"^[a-z]+$", "abc")))
        True

    :param factory: Lazy factory.
    :type factory: str or function or collections.abc.Callable or None

    :param args: Arguments to be passed to the factory function.

    :param kwargs: Keyword arguments to be passed to the factory function.

    :return: Result from factory.
    """
    factory = import_factory(factory)
    if factory is None:
        return None
    else:
        return factory(*(args or ()), **(kwargs or {}))
