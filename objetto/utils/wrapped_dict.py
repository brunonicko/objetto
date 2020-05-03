# -*- coding: utf-8 -*-
"""Read-only wrapped dictionary-like object."""

from slotted import SlottedMapping
from typing import Mapping, Hashable, Any, Iterator

from .recursive_repr import recursive_repr

__all__ = ["WrappedDict"]


class WrappedDict(SlottedMapping):
    """Wraps a dictionary object and act as a read-only container for it."""

    __slots__ = ("_dict",)

    def __init__(self, internal_dict):
        # type: (Mapping) -> None
        """Initialize with a dict/mapping."""
        self._dict = internal_dict

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Representation."""
        return self._dict.__repr__()

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """String representation."""
        return self._dict.__str__()

    def __getitem__(self, key):
        # type: (Hashable) -> Any
        """Get value associated with key."""
        return self._dict[key]

    def __len__(self):
        # type: () -> int
        """Get key count."""
        return len(self._dict)

    def __iter__(self):
        # type: () -> Iterator[Hashable, ...]
        """Iterate over keys."""
        for key in self._dict:
            yield key
