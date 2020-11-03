# -*- coding: utf-8 -*-
"""Custom `repr` functions."""

from typing import TYPE_CHECKING

from six import iteritems

from .recursive_repr import recursive_repr

if TYPE_CHECKING:
    from typing import Any, Callable, Hashable, Iterable, Mapping, Optional, Tuple

__all__ = ["custom_mapping_repr", "custom_iterable_repr"]


@recursive_repr
def custom_mapping_repr(
    mapping,  # type: Mapping
    prefix="{",  # type: str
    template="{key}:{value}",  # type: str
    separator=", ",  # type: str
    suffix="}",  # type: str
    sorting=False,  # type: bool
    sort_key=None,  # type: Optional[Callable[[Any], Any]]
    reverse=False,  # type: bool
    key_repr=repr,  # type: Callable[[Any], Any]
    value_repr=repr,  # type: Callable[[Any], Any]
):
    # type: (...) -> str
    """Get custom string representation of a mapping."""
    parts = []
    iterable = iteritems(mapping)  # type: Iterable[Tuple[Hashable, Any]]
    if sorting:
        iterable = sorted(iterable, key=sort_key, reverse=reverse)
    for key, value in iterable:
        part = template.format(key=key_repr(key), value=value_repr(value))
        parts.append(part)
    return prefix + separator.join(parts) + suffix


@recursive_repr
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
    """Get custom string representation of an iterable."""
    parts = []
    if sorting:
        iterable = sorted(iterable, key=sort_key, reverse=reverse)
    for value in iterable:
        part = template.format(value=value_repr(value))
        parts.append(part)
    return prefix + separator.join(parts) + suffix
