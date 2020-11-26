# -*- coding: utf-8 -*-
"""Custom representation functions."""

from typing import TYPE_CHECKING

from six import iteritems

if TYPE_CHECKING:
    from typing import Any, Callable, Hashable, Iterable, Mapping, Optional, Tuple

__all__ = ["custom_mapping_repr", "custom_iterable_repr"]


def custom_mapping_repr(
    mapping,  # type: Mapping
    prefix="{",  # type: str
    template="{key}: {value}",  # type: str
    separator=", ",  # type: str
    suffix="}",  # type: str
    sorting=False,  # type: bool
    sort_key=None,  # type: Optional[Callable[[Any], Any]]
    reverse=False,  # type: bool
    key_repr=repr,  # type: Callable[[Any], Any]
    value_repr=repr,  # type: Callable[[Any], Any]
):
    # type: (...) -> str
    """
    Get custom representation of a mapping.

    .. code:: python

        >>> from objetto.utils.custom_repr import custom_mapping_repr

        >>> dct = {"a": 1, "b": 2}
        >>> custom_mapping_repr(dct, prefix="<", suffix=">", template="{key}={value}")
        "<'a'=1, 'b'=2>"

    :param mapping: Mapping.
    :param prefix: Prefix.
    :param template: Item format template ({key} and {value}).
    :param separator: Separator.
    :param suffix: Suffix.
    :param sorting: Whether to sort keys.
    :param sort_key: Sorting key.
    :param reverse: Reverse sorting.
    :param key_repr: Key representation function.
    :param value_repr: Value representation function.
    :return: Custom representation.
    """
    parts = []
    iterable = iteritems(mapping)  # type: Iterable[Tuple[Hashable, Any]]
    if sorting:
        iterable = sorted(iterable, key=sort_key, reverse=reverse)
    for key, value in iterable:
        part = template.format(key=key_repr(key), value=value_repr(value))
        parts.append(part)
    return prefix + separator.join(parts) + suffix


def custom_iterable_repr(
    iterable,  # type: Iterable
    prefix="[",  # type: str
    template="{value}",  # type: str
    separator=", ",  # type: str
    suffix="]",  # type: str
    sorting=False,  # type: bool
    sort_key=None,  # type: Optional[Callable[[Any], Any]]
    reverse=False,  # type: bool
    value_repr=repr,  # type: Callable[[Any], Any]
):
    # type: (...) -> str
    """
    Get custom representation of an iterable.

    .. code:: python

        >>> from objetto.utils.custom_repr import custom_iterable_repr

        >>> tup = ("a", "b", "c", 1, 2, 3)
        >>> custom_iterable_repr(tup, prefix="<", suffix=">", value_repr=str)
        '<a, b, c, 1, 2, 3>'

    :param iterable: Iterable.
    :param prefix: Prefix.
    :param template: Item format template ({key} and {value}).
    :param separator: Separator.
    :param suffix: Suffix.
    :param sorting: Whether to sort the iterable or not.
    :param sort_key: Sorting key.
    :param reverse: Reverse sorting.
    :param value_repr: Value representation function.
    :return: Custom representation.
    """
    parts = []
    if sorting:
        iterable = sorted(iterable, key=sort_key, reverse=reverse)
    for value in iterable:
        part = template.format(value=value_repr(value))
        parts.append(part)
    return prefix + separator.join(parts) + suffix
